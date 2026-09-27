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
. "$(dirname "$0")/paths.sh"


deny() { printf 'mcomix-loop guard: %s\n' "$1" >&2; exit 2; }

input=$(cat)
json() {   # json <dotted.path>: a field of the hook input, empty when absent; jq, or python3 without it
    local v
    if command -v jq >/dev/null 2>&1 && v=$(printf '%s' "$input" | jq -r ".$1 // empty" 2>/dev/null); then
        printf '%s' "$v"
    else
        printf '%s' "$input" | python3 -c 'import json, sys
d = json.load(sys.stdin)
for k in sys.argv[1].split("."):
    d = d.get(k) if isinstance(d, dict) else None
print("" if d in (None, False) else d if not isinstance(d, bool) else "true", end="")' "$1"
    fi
}
tool=$(json tool_name)
REPO=$(resolve_repo "$(json cwd)") \
    || deny "this session's working directory is not an MComix checkout (mcomix/, test/, mcomix/constants.py); the loop only runs from inside one. Start claude there."
CAMPAIGN=$REPO/.claude/worktrees/campaign

# ---------------------------------------------------------------- file tools
case "$tool" in
    Write|Edit)
        path=$(json tool_input.file_path)
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
cmd=$(json tool_input.command)
raw_cmd=$cmd
[ -z "$cmd" ] && exit 0
bg=$(json tool_input.run_in_background)
[ "$bg" = true ] && deny "no background commands in the loop: a hang must surface as a timeout, not vanish into a background task."

# Heredoc bodies are data (a commit message, a note being appended), not
# commands: drop every line between a `<<WORD` and its terminator before the
# text is inspected, keeping the line that carries the operator.
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
flat=$(printf '%s' "$cmd" | tr '\n\t' '  ' | tr -s ' ')
# A quoted -m/--message argument with a space in it is a message, not a
# command: blank it, so "xvfb-run" or "(a; b)" in a subject does not read as
# a command. (A module name after python's -m has no space, and stays.)
flat=$(printf '%s' "$flat" | sed -E "s/(-m|--message)(=|[[:space:]]+)(\"[^\"]* [^\"]*\"|'[^']* [^']*')/\1 MSG/g")

for f in ${FOREIGN[@]+"${FOREIGN[@]}"}; do
    case "$flat" in *"$f"*) deny "$f belongs to another session." ;; esac
done
case "$flat" in
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

check_appendonly() {   # $1: one segment, $2: an append-only file it names
    local seg=$1 f=$2 name=${2##*/}
    printf '%s' "$seg" | grep -Eq "(^|[^>])>[[:space:]]*$f" \
        && deny "$name is append-only; use '>>'."
    printf '%s' "$seg" | grep -Eq '(^|[ ;&|(])(sed|perl)[[:space:]]+-[A-Za-z]*i|(^|[ ;&|(])truncate[[:space:]]' \
        && deny "$name is append-only; no in-place edits or truncation."
    if printf '%s' "$seg" | grep -Eq '(^|[ ;&|(])tee[[:space:]]' \
       && ! printf '%s' "$seg" | grep -Eq 'tee[[:space:]]+(-[^ ]+[[:space:]]+)*(-a|--append)'; then
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

# The subject the commit this command makes will have: the first paragraph of
# its first -m, of the -F file, or of the heredoc fed to -F -, joined as git's
# %s joins it. Empty when it cannot be told.
commit_subject() {
    printf '%s' "$raw_cmd" | python3 -c '
import re, shlex, sys
raw = sys.stdin.read()
m = re.search(r"<<-?\s*[\x27\x22]?(\w+)[\x27\x22]?[^\n]*\n(.*?)\n\s*\1\s*(\n|$)", raw, re.S)
heredoc = m.group(2) if m else ""
line = next((l for l in raw.split("\n") if re.search(r"\bcommit\b", l)), "")
try:
    toks = shlex.split(re.sub(r"<<-?\s*\S+", "", line))
except ValueError:
    sys.exit()
msg = None
toks = toks[toks.index("commit") + 1:] if "commit" in toks else []
for i, t in enumerate(toks):
    nxt = toks[i + 1] if i + 1 < len(toks) else ""
    if t in ("-m", "--message"): msg = nxt
    elif t.startswith("--message="): msg = t[10:]
    elif t.startswith("-m") and len(t) > 2 and not t.startswith("--"): msg = t[2:]
    elif t in ("-F", "--file") or t.startswith("--file="):
        f = t[7:] if t.startswith("--file=") else nxt
        if f == "-": msg = heredoc
        else:
            try: msg = open(f, encoding="utf-8", errors="replace").read()
            except OSError: msg = None
    if msg is not None: break
if msg:
    paras = re.split(r"\n\s*\n", msg.strip("\n"))
    print(" ".join(paras[0].split()) if paras and paras[0].strip() else "")
' 2>/dev/null
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
                printf '%s' "$args" | grep -Eq ' (--only|-o) ' || deny "git commit --amend changes only a message here, never content: add --only. $amend_help"
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
            printf '%s' "$args" | grep -Eq ' (-[a-zA-Z]*[aipect][a-zA-Z]*|--all|--interactive|--patch|--edit|--reedit-message|--template)( |=)' \
                && deny "git commit -a/-i/-p/-e/-c/-t: stages other people's changes or waits on an editor. Name the files you stage; pass the message with -m or -F."
            printf '%s' "$args" | grep -Eq ' (-[a-zA-Z]*m|--message|-F|--file|-C|--reuse-message|--fixup|--squash|--no-edit)' \
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
            csubject=$(commit_subject)
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
            printf '%s' "$args" | grep -Eq ' (-b|-B|--orphan|--detach|-S|--staged) ' \
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
            printf '%s' "$args" | grep -Eq ' (--hard|--merge|--keep|--soft) ' \
                && deny "git reset --hard/--merge/--keep/--soft discards or rewrites work."
            [[ "$args" == *" -- "* ]] || deny "git reset without a pathspec unstages or moves what the user has; use 'git reset -- <file>'." ;;
        clean)
            deny "git clean deletes other people's untracked files." ;;
        rebase)
            printf '%s' "$args" | grep -Eq ' (-i|--interactive|--root) ' && deny "no interactive or root rebase."
            [[ "$flat" == *".claude/worktrees/campaign"* ]] || deny "git rebase only in the campaign worktree ($CAMPAIGN); nothing of the user's is rebased." ;;
        merge)
            [[ "$args" == *" --squash "* ]] || deny "a campaign lands as one squashed commit: git merge --squash loop/<campaign>." ;;
        branch)
            printf '%s' "$args" | grep -Eq ' (-m|-M|--move|-c|-C|--copy|-f|--force|-u|--set-upstream-to|--unset-upstream|--edit-description) ' \
                && deny "git branch rename/force/upstream: branches other sessions may have are not touched."
            if printf '%s' "$args" | grep -Eq ' (-[a-zA-Z]*[dD][a-zA-Z]*|--delete) '; then
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
            [ $# -eq 0 ] || printf '%s' "$args" | grep -Eq ' (-l|--list|-n[0-9]*) ' \
                || deny "git tag: releases are the user's." ;;
        remote)
            [ $# -eq 0 ] || printf '%s' "$args" | grep -Eq ' (-v|show|get-url) ' \
                || deny "git remote: remotes are the user's." ;;
        config)
            printf '%s' "$args" | grep -Eq ' (--get|--get-all|--get-regexp|--list|-l) ' \
                || deny "git config writes are the user's; read with --get or --list." ;;
        reflog)
            printf '%s' "$args" | grep -Eq ' (expire|delete|drop) ' && deny "git reflog expire/delete: history is not pruned." ;;
        gc|prune|filter-branch|filter-repo|replace|update-ref|symbolic-ref|commit-tree|fast-import|submodule)
            deny "git $sub: history and repository state are the user's." ;;
        revert)
            [[ "$args" == *" --no-edit "* ]] || deny "git revert without --no-edit opens an editor." ;;
        cherry-pick)
            printf '%s' "$args" | grep -Eq ' (-e|--edit) ' && deny "git cherry-pick -e opens an editor." ;;
        notes)
            case " $* " in
                *" append "*)
                    printf '%s' " $* " | grep -Eq ' (-m|-F|--message|--file)' \
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

check_gh() {   # $@: the tokens after 'gh'. Reading is the loop's; anything that reaches GitHub is the user's.
    local sub=${1:-} act=${2:-}
    case "$sub" in
        ""|--version|version|help|status|search) return 0 ;;
        auth)     [ "$act" = status ] && return 0 ;;
        run)      case "$act" in list|view|download) return 0 ;; esac ;;   # not watch: it blocks past the tool's timeout
        pr)       case "$act" in list|view|diff|checks|status) return 0 ;; esac ;;
        issue)    case "$act" in list|view|status) return 0 ;; esac ;;
        release)  case "$act" in list|view|download) return 0 ;; esac ;;
        repo)     [ "$act" = view ] && return 0 ;;
        workflow) case "$act" in list|view) return 0 ;; esac ;;
        api)      printf '%s' " $* " | grep -Eq ' (-X|--method)[ =]?(POST|PUT|PATCH|DELETE)| (-f|-F|--field|--raw-field|--input)[ =]' || return 0 ;;
    esac
    deny "gh $sub $act: the loop only reads GitHub (run, pr, issue, release: list and view; api GET); what reaches GitHub is the user's."
}

# Split on command separators and substitutions; inspect every segment.
mapfile -t segs < <(printf '%s\n' "$flat" | sed -E 's/(&&|\|\||;|\||\$\(|`|\(|\))/\n/g')
outer_timeout=0
printf '%s' "${segs[0]}" | grep -Eq '(^|[[:space:]])timeout[[:space:]].*[[:space:]](sh|bash|dash|zsh)[[:space:]]+(-[a-z]*c)' && outer_timeout=1
for seg in "${segs[@]}"; do
    # shellcheck disable=SC2206
    toks=($seg)
    [ ${#toks[@]} -eq 0 ] && continue

    [[ "$seg" == *"$REJECTED"* ]] && check_appendonly "$seg" "$REJECTED"
    if [[ "$seg" == *"$TECHNIQUES/"* ]]; then
        tf=$(printf '%s' "$seg" | grep -oE "$TECHNIQUES/[A-Za-z0-9_.-]+\.md" | head -1)
        [ -n "$tf" ] && [ -e "$tf" ] && check_appendonly "$seg" "$tf"
    fi
    if [[ "$seg" == *"$DECISIONS"* ]] && printf '%s' "$seg" | grep -Eq "(>|tee|sed|perl|truncate|cp|mv|install)[^|;&]*$DECISIONS"; then
        deny "rulings are written only by okf.py ruling, and never changed."
    fi
    case "$seg" in
        *okf.py*" confirm"*) deny "confirming a ruling is the user's (okf.py confirm, from their own terminal)." ;;
    esac
    if [[ "$seg" == *"$COMMITS"* ]] && printf '%s' "$seg" | grep -Eq "(>|tee|sed|perl|truncate|cp|mv|install|rm)[^|;&]*$COMMITS"; then
        deny "commits.log is written only by the guard, as it lets a commit through."
    fi

    # Suite, probes and mypy carry their own timeout; the tool's timeout hides a hang.
    # (Limitation: a bare token "xvfb-run" in a grep pattern still trips this.)
    needs_timeout=0; has_timeout=$outer_timeout
    for ((i = 0; i < ${#toks[@]}; i++)); do
        case "${toks[$i]}" in
            timeout) has_timeout=1 ;;
            xvfb-run) needs_timeout=1 ;;
            -m) nxt=${toks[$((i + 1))]:-}; case "${nxt//[\"\']/}" in pytest|mypy) needs_timeout=1 ;; esac ;;
            *gates.sh) needs_timeout=0; has_timeout=1 ;;
        esac
    done
    case "${toks[0]}" in pytest|*/pytest|mypy|*/mypy) needs_timeout=1 ;; esac
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
