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
            "$TECHNIQUES")
                [ "$tool" = Write ] && deny "LOOP_TECHNIQUES is append-only: use Edit, or 'cat >>' in Bash, never Write." ;;
            "$STATE"/config.sh|"$STATE"/project.md)
                deny "$path is the user's: settings and installation facts. Record what is wrong under 'Prompt corrections' in LOOP_NOTES." ;;
            "$STATE"/*) ;;
            "$SKILL_DIR"/*|*/.claude/commands/mcomix-loop.md)
                deny "the loop does not edit its own prompt or scripts; record the correction under 'Prompt corrections' in LOOP_NOTES." ;;
            "$HOME"/.config/mcomix*|"$HOME"/.local/share/mcomix*|*/recently-used.xbel)
                deny "real user data; every probe builds on test/__init__.py:MComixTest." ;;
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
# file, or that folds iteration.md into LOOP_NOTES and then deletes
# iteration.md, is two separate acts and only the wrong one is refused.

check_techniques() {   # $1: one segment that names LOOP_TECHNIQUES
    printf '%s' "$1" | grep -Eq "(^|[^>])>[[:space:]]*$TECHNIQUES" \
        && deny "LOOP_TECHNIQUES is append-only; use '>>'."
    printf '%s' "$1" | grep -Eq '(^|[ ;&|(])(sed|perl)[[:space:]]+-[A-Za-z]*i|(^|[ ;&|(])truncate[[:space:]]' \
        && deny "LOOP_TECHNIQUES is append-only; no in-place edits or truncation."
    if printf '%s' "$1" | grep -Eq '(^|[ ;&|(])tee[[:space:]]' \
       && ! printf '%s' "$1" | grep -Eq 'tee[[:space:]]+(-[^ ]+[[:space:]]+)*(-a|--append)'; then
        deny "LOOP_TECHNIQUES is append-only; 'tee' needs -a."
    fi
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
            "$NOTES"|"$TECHNIQUES")
                deny "the handoff files are rewritten or appended, never deleted." ;;
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
    while [ $# -gt 0 ]; do
        t=$1; shift
        case "$t" in
            -C|-c|--git-dir|--work-tree|--namespace|--exec-path|--super-prefix) shift ;;  # global option with a value
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
            [[ "$args" == *" --amend "* ]] \
                && deny "git commit --amend: an amend once rewrote the user's hand commit. Fix forward with a new commit; correct a wrong number in LOOP_NOTES."
            printf '%s' "$args" | grep -Eq ' (-[a-zA-Z]*[aipect][a-zA-Z]*|--all|--interactive|--patch|--edit|--reedit-message|--template)( |=)' \
                && deny "git commit -a/-i/-p/-e/-c/-t: stages other people's changes or waits on an editor. Name the files you stage; pass the message with -m or -F."
            printf '%s' "$args" | grep -Eq ' (-[a-zA-Z]*m|--message|-F|--file|-C|--reuse-message|--fixup|--squash|--no-edit)' \
                || deny "git commit without -m or -F opens an editor, which hangs the loop."
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
        rm)
            for tok in "$@"; do
                case "$tok" in
                    .|:/|'*'|./) deny "git rm $tok: name the files." ;;
                esac
            done ;;
    esac
    return 0
}

# Split on command separators and substitutions; inspect every segment.
mapfile -t segs < <(printf '%s\n' "$flat" | sed -E 's/(&&|\|\||;|\||\$\(|`|\(|\))/\n/g')
outer_timeout=0
printf '%s' "${segs[0]}" | grep -Eq '(^|[[:space:]])timeout[[:space:]].*[[:space:]](sh|bash|dash|zsh)[[:space:]]+(-[a-z]*c)' && outer_timeout=1
for seg in "${segs[@]}"; do
    # shellcheck disable=SC2206
    toks=($seg)
    [ ${#toks[@]} -eq 0 ] && continue

    [[ "$seg" == *"$TECHNIQUES"* ]] && check_techniques "$seg"

    # Suite, probes and mypy carry their own timeout; the tool's timeout hides a hang.
    # (Limitation: a bare token "xvfb-run" or "mypy" in a grep pattern trips this; quote it.)
    needs_timeout=0; has_timeout=$outer_timeout
    for ((i = 0; i < ${#toks[@]}; i++)); do
        case "${toks[$i]}" in
            timeout) has_timeout=1 ;;
            xvfb-run) needs_timeout=1 ;;
            -m) case "${toks[$((i + 1))]:-}" in pytest|mypy) needs_timeout=1 ;; esac ;;
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
        esac
    done
done
exit 0
