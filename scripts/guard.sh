#!/usr/bin/env bash
# PreToolUse guard for the MComix loop (registered by SKILL.md for the session
# that invoked /mcomix-loop; matcher "Bash|Monitor|Write|Edit").
#
# Exit 2 blocks the tool call and shows the stderr line to Claude. Exit 0
# leaves the call to the normal permission flow. The rules are the "never"
# rules of SKILL.md; the auto-mode classifier and the permission settings are
# the other two layers. This is a guard against the model's own mistakes, not
# a security boundary: it reads the command text, so `sh -c '...'` or a path
# spelled through a variable can get past it.
#
# Self-test:
#   printf '{"tool_name":"Bash","tool_input":{"command":"git stash"},"cwd":"<checkout>"}' | guard.sh; echo $?      # 2
#   printf '{"tool_name":"Bash","tool_input":{"command":"git log -3"},"cwd":"<checkout>"}' | guard.sh; echo $?   # 0

set -u
set -f   # tokens are compared as typed: `git add *` must reach the rule as `*`, not as the files it globs to
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac

# This runs before every Bash, Monitor, Write and Edit call, so it starts as
# few processes as it can: one jq (or one python3) for the hook input, bash
# itself for every pattern, and python3 again only for a commit.

deny() { printf 'mcomix-loop guard: %s\n' "$1" >&2; exit 2; }
has() { [[ "$1" =~ $2 ]]; }   # has <text> <extended regex>

# The fields this guard reads, NUL-terminated: a command may hold newlines and tabs.
if command -v jq >/dev/null 2>&1; then
    fields() { jq -j '[.tool_name, .cwd, .tool_input.file_path, .tool_input.command, .tool_input.run_in_background]
                      | map((. // "" | tostring) + "\u0000") | add' 2>/dev/null; }
else
    fields() { python3 -S -c 'import json, sys
d = json.load(sys.stdin)
t = d.get("tool_input") or {}
v = [d.get("tool_name"), d.get("cwd"), t.get("file_path"), t.get("command"), t.get("run_in_background")]
sys.stdout.write("".join(("true" if x is True else "" if x in (None, False) else str(x)) + "\0" for x in v))' 2>/dev/null; }
fi
{ IFS= read -r -d '' tool; IFS= read -r -d '' cwd; IFS= read -r -d '' path
  IFS= read -r -d '' cmd; IFS= read -r -d '' bg; } < <(fields)

REPO=$(resolve_repo "${cwd:-}") \
    || deny "this session's working directory is not an MComix checkout (mcomix/, test/, mcomix/constants.py); the loop only runs from inside one. Start claude there. To work on the skill itself, start a session without /mcomix-loop."
CAMPAIGN=$REPO/.claude/worktrees/campaign

# ---------------------------------------------------------------- file tools
case "$tool" in
    Write|Edit)
        case "$path" in
            "$STATE"/index.md|"$TECHNIQUES"/index.md|"$DECISIONS"/index.md)
                deny "index.md is generated from the concepts' frontmatter (okf.py index, run by state.sh); edit the concept instead." ;;
            "$TECHNIQUES"/*.md|"$REJECTED")
                [ "$tool" = Write ] && [ -e "$path" ] \
                    && deny "${path##*/} exists: add to it or correct it in place with Edit; never overwrite a concept. A new technique is a new file." ;;
            "$DECISIONS"/*)
                deny "a ruling is recorded with okf.py ruling (a new file) and never edited: a changed ruling is a new one naming the date of the one it replaces." ;;
            "$STATE"/config.sh|"$STATE"/project.md|"$COMMITS")
                deny "$path is the user's: settings and installation facts. Record what is wrong under 'Prompt corrections' in LOOP_NOTES." ;;
            "$STATE"/*) ;;
            "$SKILL_DIR"/*|*/.claude/commands/mcomix-loop.md)
                deny "the loop does not edit its own prompt or scripts; record the correction under 'Prompt corrections' in LOOP_NOTES." ;;
            "$HOME"/.config/mcomix*|"$HOME"/.local/share/mcomix*|*/recently-used.xbel)
                deny "real user data; every probe builds on test/__init__.py:MComixTest." ;;
            "$HOME"/.claude/projects/*/memory/*)
                deny "Claude Code's auto memory is not this loop's memory: a ruling goes to $DECISIONS, a technique to $TECHNIQUES, a dead end to $REJECTED." ;;
        esac
        for f in ${FOREIGN[@]+"${FOREIGN[@]}"}; do
            case "$path" in "$f"|"$f"/*) deny "$f belongs to another session." ;; esac
        done
        exit 0 ;;
    Bash|Monitor) ;;
    *) exit 0 ;;
esac

# ------------------------------------------------------------ shell commands
raw_cmd=$cmd
[ -z "$cmd" ] && exit 0
[ "$bg" = true ] && deny "no background commands in the loop: a hang must surface as a timeout, not vanish into a background task."

# Heredoc bodies are data (a commit message, a note being appended), not
# commands: drop every line between a `<<WORD` and its terminator before the
# text is inspected, keeping the line that carries the operator.
if [[ "$cmd" == *"<<"* ]]; then
    cmd=$(printf '%s\n' "$cmd" | awk '
        body == "" {
            if (match($0, /<<-?[[:space:]]*["'"'"']?[A-Za-z_][A-Za-z0-9_]*["'"'"']?/)) {
                d = substr($0, RSTART, RLENGTH); sub(/^<<-?[[:space:]]*/, "", d); gsub(/["'"'"']/, "", d)
                body = d
            }
            print; next
        }
        { line = $0; sub(/^\t+/, "", line); if (line == body) body = "" }
    ')
fi
flat=${cmd//$'\n'/ }
flat=${flat//$'\t'/ }
while [[ "$flat" == *"  "* ]]; do flat=${flat//  / }; done
# A quoted string with a space in it is text - a message, a pattern, a line
# being written - not a command: blank it, so "mypy" or "(a; b)" in a
# subject does not read as a command. One without a space is a word (a
# pattern, a path, `'*'`): it stays, but the separators in it separate
# nothing, so `'s/x/(mypy)/'` does not start a command either. What runs
# stays whole: the script of a `-c` (sh, bash, python) or an `eval`, and a
# double-quoted string with a command substitution in it. The checks for
# paths below see every string but a commit message's (`data`).
data=$flat
if [[ "$flat" == *[\"\']* ]]; then
    re_q="\"[^\"]*\"|'[^']*'"
    rest=${flat//\\\"/__}; rest=${rest//\\\'/__}    # an escaped quote neither opens nor closes
    flat=""; data=""
    while [[ "$rest" =~ $re_q ]]; do
        q=${BASH_REMATCH[0]}
        pre=${rest%%"$q"*}
        rest=${rest#*"$q"}
        text=$q; message=$q
        if [[ "$q" == \"* && ( "$q" == *'$('* || "$q" == *'`'* ) ]]; then
            :
        elif [[ "$q" == *[[:space:]]* ]]; then
            has "$pre" '(^|[[:space:]])(-[a-zA-Z]*c|eval)[[:space:]]+$' || text=${q:0:1}MSG${q:0:1}
            has "$pre" '(-m|--message)(=|[[:space:]]+)$' && message=${q:0:1}MSG${q:0:1}
        elif ! has "$pre" '(^|[[:space:]])(-[a-zA-Z]*c|eval)[[:space:]]+$'; then
            text=${q//[;|&()\`]/_}
        fi
        flat+=$pre$text; data+=$pre$message
    done
    flat+=$rest; data+=$rest
fi

for f in ${FOREIGN[@]+"${FOREIGN[@]}"}; do
    case "$data" in *"$f"*) deny "$f belongs to another session." ;; esac
done
case "$data" in
    *".config/mcomix"*|*".local/share/mcomix"*|*"recently-used.xbel"*)
        deny "real user data path in the command; every probe builds on test/__init__.py:MComixTest." ;;
esac
case " $flat" in
    *" sudo "*|*"|sudo "*|*";sudo "*|*"&&sudo "*) deny "no sudo." ;;
esac

# Rules below run per command segment, not over the whole string: a single
# command that appends to LOOP_TECHNIQUES and also runs `sed -i` on a source
# file, or that folds iteration.txt into LOOP_NOTES and then deletes
# iteration.txt, is two separate acts and only the wrong one is refused.

re_inplace='(^|[ ;&|(])(sed|perl)[[:space:]]+-[A-Za-z]*i|(^|[ ;&|(])truncate[[:space:]]'
re_tee='(^|[ ;&|(])tee[[:space:]]'
re_tee_append='tee[[:space:]]+(-[^ ]+[[:space:]]+)*(-a|--append)'
check_appendonly() {   # $1: one segment, $2: an append-only file it names
    local seg=$1 f=$2 name=${2##*/}
    has "$seg" "(^|[^>])>[[:space:]]*$f" && deny "$name is append-only; use '>>'."
    has "$seg" "$re_inplace" && deny "$name is append-only; no in-place edits or truncation."
    if has "$seg" "$re_tee" && ! has "$seg" "$re_tee_append"; then
        deny "$name is append-only; 'tee' needs -a."
    fi
    # shellcheck disable=SC2206
    local t=($seg)
    case "${t[0]}" in
        cp|mv|install|*/cp|*/mv) [ "${t[${#t[@]}-1]}" = "$f" ] && deny "$name is append-only; it is never replaced." ;;
    esac
    return 0
}

check_rm() {   # $@: the tokens after 'rm'
    local recursive=0 tok
    for tok in "$@"; do
        case "$tok" in
            -*[rR]*|--recursive) recursive=1 ;;
        esac
    done
    for tok in "$@"; do
        case "$tok" in
            -*) continue ;;
            "$NOTES"|"$REJECTED"|"$COMMITS"|"$TECHNIQUES"|"$TECHNIQUES"/*|"$DECISIONS"|"$DECISIONS"/*|"$STATE"/project.md)
                deny "the loop's memory is rewritten, added to or corrected, never deleted; a technique that proved wrong is corrected in place." ;;
        esac
        [ "$recursive" -eq 1 ] || continue
        case "$tok" in
            "$SCRATCH"/?*|"$EXPORT_DIR"/export-?*) ;;
            "$REPO"|"$REPO"/*|'~'|'~/'*|'$HOME'|'$HOME/'*|"$HOME"|"$HOME"/*|.|./|/*)
                deny "recursive rm only under $SCRATCH or of an export; a worktree is removed with 'git worktree remove <path>'." ;;
        esac
    done
    return 0
}

# ------------------------------------------------------------------- git
check_git() {   # $@: the tokens after 'git'; $flat is in scope
    local sub="" t
    git_dir=""
    while [ $# -gt 0 ]; do
        t=$1; shift
        case "$t" in
            -C) git_dir=${1:-}; case "$git_dir" in /*) ;; *) git_dir=$REPO/$git_dir ;; esac; shift ;;
            -c|--git-dir|--work-tree|--namespace|--exec-path|--super-prefix) shift ;;  # global option with a value
            -*) ;;                                                                        # other global option
            *) sub=$t; break ;;
        esac
    done
    [ -z "$sub" ] && return 0
    local args=" $* "
    local tok
    case "$sub" in
        stash)
            deny "git stash: the stash stack belongs to the repository and other sessions share it. Copy the file aside instead." ;;
        push)
            deny "git push: what leaves this machine is the user's decision." ;;
        commit)
            if [[ "$args" == *" --amend "* ]]; then
                target=$REPO
                [ -n "${git_dir:-}" ] && target=$git_dir
                head=$(git -C "$target" rev-parse -q --verify HEAD 2>/dev/null)
                amend_help="Fix a message the loop got wrong: its own unpushed newest commit with 'git commit --amend --only -F <file>'; any other with 'git notes append -F <file> <commit>'."
                has "$args" ' (--only|-o) ' || deny "git commit --amend changes only a message here, never content: add --only. $amend_help"
                [[ "$args" == *" -- "* ]] && deny "git commit --amend --only takes no paths: it corrects the message, not the tree. $amend_help"
                own=""
                if [ -n "$head" ] && [ -e "$COMMITS" ]; then
                    grep -qx "$head" "$COMMITS" && own=1
                    parent=$(git -C "$target" rev-parse -q --verify "HEAD^" 2>/dev/null)
                    subject=$(git -C "$target" log -1 --format=%s HEAD 2>/dev/null)
                    grep -qxF "$parent	$subject" "$COMMITS" && own=1
                fi
                [ -n "$own" ] \
                    || deny "HEAD is not a commit the loop made (no commit on its parent with its subject in $COMMITS); someone else's commit is never amended. $amend_help"
                [ -z "$(git -C "$target" branch -r --contains "$head" 2>/dev/null)" ] \
                    || deny "HEAD is on a remote branch already: pushed history is never rewritten. $amend_help"
            fi
            has "$args" ' (-[a-zA-Z]*[aipect][a-zA-Z]*|--all|--interactive|--patch|--edit|--reedit-message|--template)( |=)' \
                && deny "git commit -a/-i/-p/-e/-c/-t: stages other people's changes or waits on an editor. Name the files you stage; pass the message with -m or -F."
            has "$args" ' (-[a-zA-Z]*m|--message|-F|--file|-C|--reuse-message|--fixup|--squash|--no-edit)' \
                || deny "git commit without -m or -F opens an editor, which hangs the loop."
            # Recorded before it runs: the parent it will sit on and the subject it
            # will have. That is how an amend later tells the loop's own commit
            # from one the user made by hand, whatever the commit printed.
            ctarget=$REPO; [ -n "${git_dir:-}" ] && ctarget=$git_dir
            if [[ "$args" == *" --amend "* ]]; then
                cparent=$(git -C "$ctarget" rev-parse -q --verify "HEAD^" 2>/dev/null)
            else
                cparent=$(git -C "$ctarget" rev-parse -q --verify HEAD 2>/dev/null)
            fi
            csubject=$(printf '%s' "$raw_cmd" | python3 -S "$SKILL_DIR/scripts/commit-subject.py" "${cwd:-$REPO}")
            [ $? -eq 3 ] && deny "the guard cannot read this commit's message before the command runs (a command substitution, a variable set outside this command, or a file this command writes other than by heredoc), so it cannot note the commit as the loop's, and a wrong message could never be amended. Write the message file first, then commit with 'git commit -F /absolute/path' in a command of its own."
            if [ -n "$cparent" ] && [ -n "$csubject" ]; then
                mkdir -p "$(dirname "$COMMITS")"
                printf '%s\t%s\n' "$cparent" "$csubject" >> "$COMMITS"
            fi
            ;;
        add)
            for tok in "$@"; do
                case "$tok" in
                    -A|--all|-u|--update|.|:/|./|'*'|-p|--patch|-i|--interactive|-e|--edit)
                        deny "git add $tok: name the files you stage; other people's changes are never staged, and interactive add waits on a terminal." ;;
                    -[a-zA-Z]*[Aupie]*) deny "git add $tok: name the files you stage." ;;
                esac
            done ;;
        switch)
            deny "git switch: what is checked out is the user's; the loop works on files, or in its own worktree." ;;
        checkout|restore)
            has "$args" ' (-b|-B|--orphan|--detach|-S|--staged) ' \
                && deny "git $sub -b/-B/--orphan/--detach/--staged: what is checked out and what is staged are the user's."
            if [[ "$args" == *" -- "* ]]; then
                local spec=${args##* -- }
                for tok in $spec; do
                    case "$tok" in
                        .|:/|'*'|./) deny "git $sub -- $tok discards every working-tree change; name the files." ;;
                    esac
                done
            else
                deny "git $sub <ref>: changes what the user has checked out. The sanctioned form restores a file: git checkout HEAD -- <file>."
            fi ;;
        reset)
            has "$args" ' (--hard|--merge|--keep|--soft) ' \
                && deny "git reset --hard/--merge/--keep/--soft discards or rewrites work."
            [[ "$args" == *" -- "* ]] || deny "git reset without a pathspec unstages or moves what the user has; use 'git reset -- <file>'." ;;
        clean)
            deny "git clean deletes other people's untracked files." ;;
        rebase)
            has "$args" ' (-i|--interactive|--root) ' && deny "no interactive or root rebase."
            [[ "$flat" == *".claude/worktrees/campaign"* ]] || deny "git rebase only in the campaign worktree ($CAMPAIGN); nothing of the user's is rebased." ;;
        merge)
            [[ "$args" == *" --squash "* ]] || deny "a campaign lands as one squashed commit: git merge --squash loop/<campaign>." ;;
        branch)
            has "$args" ' (-m|-M|--move|-c|-C|--copy|-f|--force|-u|--set-upstream-to|--unset-upstream|--edit-description) ' \
                && deny "git branch rename/force/upstream: branches other sessions may have are not touched."
            if has "$args" ' (-[a-zA-Z]*[dD][a-zA-Z]*|--delete) '; then
                for tok in "$@"; do
                    case "$tok" in
                        -*|loop/*) ;;
                        *) deny "git branch delete: only loop/* branches are the loop's ($tok is not)." ;;
                    esac
                done
            fi ;;
        worktree)
            case "$args" in
                *" remove "*)
                    [[ "$flat" == *".claude/worktrees/campaign"* ]] || deny "git worktree remove: only the loop's own worktrees under $REPO/.claude/worktrees/campaign* are its to remove." ;;
                *" prune "*|*" move "*|*" lock "*|*" unlock "*|*" repair "*)
                    deny "git worktree: worktrees you did not create are not yours to touch (prune/move/lock/unlock/repair)." ;;
            esac ;;
        tag)
            [ $# -eq 0 ] || has "$args" ' (-l|--list|-n[0-9]*) ' \
                || deny "git tag: releases are the user's." ;;
        remote)
            [ $# -eq 0 ] || has "$args" ' (-v|show|get-url) ' \
                || deny "git remote: remotes are the user's." ;;
        config)
            has "$args" ' (--get|--get-all|--get-regexp|--list|-l) ' \
                || deny "git config writes are the user's; read with --get or --list." ;;
        reflog)
            has "$args" ' (expire|delete|drop) ' && deny "git reflog expire/delete: history is not pruned." ;;
        gc|prune|filter-branch|filter-repo|replace|update-ref|symbolic-ref|commit-tree|fast-import|submodule)
            deny "git $sub: history and repository state are the user's." ;;
        revert)
            [[ "$args" == *" --no-edit "* ]] || deny "git revert without --no-edit opens an editor." ;;
        cherry-pick)
            has "$args" ' (-e|--edit) ' && deny "git cherry-pick -e opens an editor." ;;
        notes)
            case " $* " in
                *" append "*)
                    has " $* " ' (-m|-F|--message|--file)' \
                        || deny "git notes append without -m or -F opens an editor." ;;
                *" show "*|*" list "*|" "|"  ") ;;
                *) deny "git notes: only 'append' (with -m or -F), 'show' and 'list'; a note is never removed or rewritten." ;;
            esac ;;
        rm)
            for tok in "$@"; do
                case "$tok" in
                    .|:/|'*'|./) deny "git rm $tok: name the files." ;;
                esac
            done ;;
    esac
    return 0
}

check_gh() {   # $@: the tokens after 'gh'. Reading is the loop's; of what reaches GitHub, only the issues and project config.sh names.
    local sub=${1:-} act=${2:-}
    case "$sub" in
        ""|--version|version|help|status|search) return 0 ;;
        auth)     [ "$act" = status ] && return 0 ;;
        run)      case "$act" in list|view|download) return 0 ;; esac ;;   # not watch: it blocks past the tool's timeout
        pr)       case "$act" in list|view|diff|checks|status) return 0 ;; esac ;;
        issue)    case "$act" in
                      list|view|status) return 0 ;;
                      create|edit|comment|close|reopen) shift 2; check_gh_issue "$act" "$@"; return 0 ;;
                  esac ;;
        project)  case "$act" in
                      list|view|item-list|field-list) return 0 ;;
                      item-add|item-edit|field-create) shift 2; check_gh_project "$act" "$@"; return 0 ;;
                  esac ;;
        label)    [ "$act" = list ] && return 0 ;;
        release)  case "$act" in list|view|download) return 0 ;; esac ;;
        repo)     [ "$act" = view ] && return 0 ;;
        workflow) case "$act" in list|view) return 0 ;; esac ;;
        api)
            if [ "$act" = graphql ]; then
                # Always a POST, but a query only reads: some reads (Discussions
                # categories) exist only there. The query is read from the raw
                # command, since quoted text is blanked above.
                has " $* " ' --input[ =]| (-F|--field)[ =]?[A-Za-z_]+=@' \
                    && deny "gh api graphql: give the query inline (-f query='query { ... }'), so the guard can read it."
                has "$raw_cmd" '(^|[^A-Za-z0-9_])mutation([^A-Za-z0-9_]|$)' \
                    && deny "gh api graphql: a mutation writes to GitHub, which is the user's; the loop sends queries only, and writes through gh issue and gh project. Sub-issues: gh issue edit <n> --repo <ISSUES_REPO> --add-sub-issue <m> (or --remove-sub-issue), gh issue create --parent <n>."
                return 0
            fi
            has " $* " ' (-X|--method)[ =]?(POST|PUT|PATCH|DELETE)| (-f|-F|--field|--raw-field|--input)[ =]' || return 0 ;;
    esac
    deny "gh $sub $act: the loop only reads GitHub (run, pr, issue, release, project, label: list and view; api GET; api graphql with a query) and writes only what state/config.sh allows (issues of ISSUES_REPO; items and fields of ISSUES_PROJECT); the rest of what reaches GitHub is the user's."
}

check_gh_issue() {   # $1: create|edit|comment|close|reopen, then its arguments
    local act=$1 t v r named=""
    shift
    [ -n "$ISSUES_REPO" ] \
        || deny "gh issue $act: $STATE/config.sh names no ISSUES_REPO, so issues are the user's. Prepare the commands for the user under 'Questions for the user'."
    while [ $# -gt 0 ]; do
        t=$1; shift
        case "$t" in
            -R|--repo) v=${1:-}; shift ;;
            --repo=*) v=${t#--repo=} ;;
            -R?*) v=${t#-R} ;;
            -p|--project|--project=*|--add-project|--add-project=*|--remove-project|--remove-project=*)
                deny "gh issue $act $t: a project is named by its title here, which the guard cannot match to ISSUES_PROJECT; add the issue with 'gh project item-add <number> --owner <owner> --url <issue>'." ;;
            --delete-last)
                deny "gh issue comment --delete-last: what was posted is corrected (--edit-last), never deleted; the comment may be the user's own." ;;
            --parent|--add-sub-issue|--remove-sub-issue|--duplicate-of|--parent=*|--add-sub-issue=*|--remove-sub-issue=*|--duplicate-of=*)
                case "$t" in *=*) v=${t#*=}; t=${t%%=*} ;; *) v=${1:-}; shift ;; esac
                for r in ${v//,/ }; do   # numbers, or URLs of issues in ISSUES_REPO
                    case "$r" in
                        [0-9]|[0-9]*[0-9]) [[ "$r" == *[!0-9]* ]] || continue ;;
                        "https://github.com/$ISSUES_REPO/issues/"[0-9]*) [[ "${r##*/}" == *[!0-9]* ]] || continue ;;
                    esac
                    deny "gh issue $act $t $r: name an issue of $ISSUES_REPO (ISSUES_REPO) by its number or its URL."
                done
                continue ;;
            *) continue ;;
        esac
        [ "$v" = "$ISSUES_REPO" ] || deny "gh issue $act --repo $v: the loop writes only the issues of $ISSUES_REPO (ISSUES_REPO)."
        named=1
    done
    [ -n "$named" ] || deny "gh issue $act: name the repository, --repo $ISSUES_REPO; without it gh picks one from the checkout's remotes."
}

check_gh_project() {   # $1: item-add|item-edit|field-create, then its arguments
    local act=$1 t v named="" owner=${ISSUES_PROJECT%/*} number=${ISSUES_PROJECT##*/}
    shift
    [ -n "$ISSUES_PROJECT" ] \
        || deny "gh project $act: $STATE/config.sh names no ISSUES_PROJECT, so projects are the user's. Prepare the commands for the user under 'Questions for the user'."
    case " $* " in
        *" --project-id "*|*" --project-id="*)
            deny "gh project $act --project-id: a node ID the guard cannot match to ISSUES_PROJECT; name the project, the item and the field instead: 'gh project item-edit $number --owner $owner --url <issue url> --field Status --value \"In Progress\"'." ;;
    esac
    [ "${1:-}" = "$number" ] \
        || deny "gh project $act: the project's number comes first, as 'gh project $act $number --owner $owner'; the loop writes only project $ISSUES_PROJECT (ISSUES_PROJECT)."
    shift
    while [ $# -gt 0 ]; do
        t=$1; shift
        case "$t" in
            --owner) v=${1:-}; shift ;;
            --owner=*) v=${t#--owner=} ;;
            *) continue ;;
        esac
        [ "$v" = "$owner" ] || deny "gh project $act --owner $v: the loop writes only project $ISSUES_PROJECT (ISSUES_PROJECT)."
        named=1
    done
    [ -n "$named" ] || deny "gh project $act: name the owner, as 'gh project $act $number --owner $owner'."
}

# Split on command separators and substitutions; inspect every segment.
nl=$'\n'
split=${flat//&&/$nl}; split=${split//||/$nl}; split=${split//;/$nl}; split=${split//|/$nl}
split=${split//\$(/$nl}; split=${split//\`/$nl}; split=${split//(/$nl}; split=${split//)/$nl}
mapfile -t segs <<< "$split"
outer_timeout=0
has "${segs[0]}" '(^|[[:space:]])timeout[[:space:]].*[[:space:]](sh|bash|dash|zsh)[[:space:]]+(-[a-z]*c)' && outer_timeout=1
for seg in "${segs[@]}"; do
    # Words as the shell passes them on, quotes removed: `bash -c 'git push'`
    # runs git, and `git add '*'` stages everything.
    # shellcheck disable=SC2206
    toks=(${seg//[\"\']/})
    [ ${#toks[@]} -eq 0 ] && continue

    [[ "$seg" == *"$REJECTED"* ]] && check_appendonly "$seg" "$REJECTED"
    if [[ "$seg" == *"$TECHNIQUES/"* ]]; then
        if has "$seg" "$TECHNIQUES/[A-Za-z0-9_.-]+\.md"; then
            tf=${BASH_REMATCH[0]}
            [ -e "$tf" ] && check_appendonly "$seg" "$tf"
        fi
    fi
    if [[ "$seg" == *"$DECISIONS"* ]] && has "$seg" "(>|tee|sed|perl|truncate|cp|mv|install)[^|;&]*$DECISIONS"; then
        deny "rulings are written only by okf.py ruling, and never changed."
    fi
    case "$seg" in
        *okf.py*" confirm"*) deny "confirming a ruling is the user's (okf.py confirm, from their own terminal)." ;;
    esac
    if [[ "$seg" == *"$COMMITS"* ]] && has "$seg" "(>|tee|sed|perl|truncate|cp|mv|install|rm)[^|;&]*$COMMITS"; then
        deny "commits.log is written only by the guard, as it lets a commit through."
    fi

    # Suite, probes and mypy carry their own timeout; the tool's timeout hides a hang.
    # What runs is the command word, past the wrappers that start another
    # command (assignments, env, nice, timeout, xvfb-run, a shell's -c); the
    # same word as an argument, a pattern or a file name runs nothing.
    needs_timeout=0; has_timeout=$outer_timeout; wrapper=""
    for ((i = 0; i < ${#toks[@]}; i++)); do
        t=${toks[i]//[\"\']/}
        case "$t" in
            [A-Za-z_]*=*) continue ;;
            env|*/env) wrapper=env; continue ;;
            nice|*/nice) wrapper=nice; continue ;;
            nohup|stdbuf|exec|command|time) wrapper=other; continue ;;
            timeout|*/timeout) wrapper=timeout; has_timeout=1; continue ;;
            xvfb-run|*/xvfb-run) wrapper=xvfb-run; needs_timeout=1; continue ;;
            sh|bash|dash|zsh|*/sh|*/bash|*/dash|*/zsh) wrapper=shell; continue ;;
            -*)
                case "$wrapper $t" in
                    "env -u"|"env -C"|"env -S"|"nice -n"|"timeout -k"|"timeout -s"|"xvfb-run -"[nsefpw]) ((i++)) ;;
                esac
                [ -n "$wrapper" ] && continue ;;
            *)
                if [ "$wrapper" = timeout ] && [[ "$t" =~ ^[0-9.]+[smhd]?$ ]]; then wrapper=other; continue; fi ;;
        esac
        break
    done
    word=${toks[i]:-}; word=${word//[\"\']/}
    case "$word" in
        pytest|*/pytest|mypy|*/mypy) needs_timeout=1 ;;
        python|python3|python3.*|*/python|*/python3|*/python3.*)
            for ((j = i + 1; j < ${#toks[@]}; j++)); do
                a=${toks[j]//[\"\']/}
                case "$a" in
                    -m) a=${toks[j + 1]:-}; case "${a//[\"\']/}" in pytest|mypy) needs_timeout=1 ;; esac; break ;;
                    -mpytest|-mmypy) needs_timeout=1; break ;;
                    -W|-X) ((j++)) ;;
                    -*) ;;
                    *) break ;;
                esac
            done ;;
    esac
    if [ "$needs_timeout" -eq 1 ] && [ "$has_timeout" -eq 0 ]; then
        deny "wrap it in 'timeout -k 5 <seconds>' (60 for the suite or a probe, 120 for mypy), or use gates.sh; the tool's own timeout backgrounds a hang instead of surfacing it."
    fi

    for ((i = 0; i < ${#toks[@]}; i++)); do
        case "${toks[$i]}" in
            git|*/git) check_git "${toks[@]:$((i + 1))}" ;;
            rm|/bin/rm|/usr/bin/rm) check_rm "${toks[@]:$((i + 1))}" ;;
            gh|*/gh) check_gh "${toks[@]:$((i + 1))}" ;;
        esac
    done
done
exit 0
