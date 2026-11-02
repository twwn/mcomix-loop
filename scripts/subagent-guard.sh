#!/usr/bin/env bash
# PreToolUse hook for the subagents of a loop session (settings-snippet.json).
#
# A hook in a skill's frontmatter does not fire inside a subagent, so guard.sh,
# which SKILL.md registers, never sees what the loop's subagents do. A hook in
# the settings does, and its input holds the parent's session_id beside an
# agent_id. But it fires in every session on the machine, so this script exits
# 0 unless the call comes from a subagent of a session guard.sh has marked as
# the loop's (SESSIONS in paths.sh). On that path it starts one cat and nothing
# else, and it reads no configuration that could fail.
#
# The fields are matched in the raw JSON. A double quote inside a JSON string
# is escaped, so "agent_id" with its quotes can only be a key, and the matcher
# in the settings admits only tools whose input has no such key.
#
# Inside the loop's session, a guard that fails refuses the call, as
# onFailure: block does for guard.sh in the main thread. Self-test:
#   printf '{"session_id":"s","agent_id":"a","tool_name":"Bash","tool_input":{"command":"git stash"},"cwd":"<checkout>"}' \
#       | subagent-guard.sh; echo $?     # 2 once <skill>/state/scratch/sessions/s exists, else 0

set -u

input=$(cat)
[[ "$input" == *'"agent_id"'* ]] || exit 0       # the main thread: SKILL.md's own hook has it
re='"session_id"[[:space:]]*:[[:space:]]*"([^"/]+)"'
[[ "$input" =~ $re ]] || exit 0
case "$0" in */*) dir=${0%/*} ;; *) dir=. ;; esac
[ -e "$dir/../state/scratch/sessions/${BASH_REMATCH[1]}" ] || exit 0

printf '%s' "$input" | "$dir/guard.sh"
rc=$?
case "$rc" in 0|2) exit "$rc" ;; esac
printf 'mcomix-loop guard: failed with exit %s on a call from a subagent of the loop, so the call is refused.\n' "$rc" >&2
exit 2
