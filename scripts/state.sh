#!/usr/bin/env bash
# First command of every loop iteration: prints the state the skill body used
# to inject. Kept out of SKILL.md on purpose — the harness re-appends a skill's
# whole body whenever its rendered text changes, so a state block inside the
# skill re-bought the entire prompt every iteration. Read-only; output is meant
# to be read once, not grepped.

set -u
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
REPO=$(resolve_repo) || { echo "state: $PWD is not an MComix checkout (mcomix/, test/, mcomix/constants.py). Start claude in one; the loop does nothing elsewhere." >&2; exit 2; }
is_gtk4 "$REPO" || { echo "state: $REPO does not require Gtk 4.0 anywhere under mcomix/; this loop targets the GTK4 port and its rules are wrong for a GTK3 tree." >&2; exit 2; }
CAMPAIGN=$REPO/.claude/worktrees/campaign
mkdir -p "$SCRATCH"

g() { git -C "$REPO" "$@" 2>/dev/null; }

echo "== repo: $REPO on branch $(g symbolic-ref --short -q HEAD || echo "(detached at $(g rev-parse --short HEAD))") =="
echo "== state: $STATE (workers $WORKERS; timeouts $T_PYTEST/$T_FLAKE8/$T_MYPY s) =="
echo "== tree =="
st=$(g status --short)
[ -n "$st" ] && printf '%s\n' "$st" || echo "clean"

echo "== commits =="
base=$(sed -nE 's/^## Gate numbers as of ([0-9a-f]{7,40}).*/\1/p' "$NOTES" 2>/dev/null | head -1)
if [ -n "$base" ] && g cat-file -e "$base^{commit}"; then
    since=$(g log --oneline "$base..HEAD")
    if [ -n "$since" ]; then
        echo "since the notes' baseline $base (not yours unless the notes say so):"
        printf '%s\n' "$since"
    else
        echo "none since the notes' baseline $base"
    fi
    echo "HEAD: $(g log --oneline -1)"
else
    [ -n "$base" ] && echo "baseline $base from the notes is not in this repository; last 20:"
    g log --oneline -20
fi

# The issues, project items and discussions of ISSUES_REPO, in one GraphQL
# request. Print only, never fatal: without gh, offline or logged out it says
# "unavailable" and the script goes on. "Updated since" counts from the
# previous run's request (SCRATCH/github.since), so what changed while an
# iteration ran is not lost; without one, from the notes' baseline commit.
# A "Done in <hash>." comment of the user's account marks an issue finished
# by that commit; one posted before the issue was last reopened does not.
github() {
    [ -n "$ISSUES_REPO" ] || { echo "not read: $STATE/config.sh names no ISSUES_REPO"; return 0; }
    command -v gh >/dev/null 2>&1 || { echo "unavailable: no gh"; return 0; }
    local stamp=$SCRATCH/github.since since from ref=HEAD now out items="" US=$'\x1f'
    since=$(cat "$stamp" 2>/dev/null); from="the previous state.sh"
    if ! [[ "$since" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
        from="HEAD's commit date"
        [ -n "$base" ] && g cat-file -e "$base^{commit}" && { ref=$base; from="the notes' baseline $base"; }
        since=$(TZ=UTC g log -1 --date=format-local:%Y-%m-%dT%H:%M:%SZ --format=%cd "$ref")
    fi
    [ -n "$ISSUES_PROJECT" ] && items='projectItems(first: 10) { nodes { project { number owner { ... on User { login } ... on Organization { login } } }
        status: fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } } }'
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    out=$(timeout -k 1 10 gh api graphql -f owner="${ISSUES_REPO%%/*}" -f name="${ISSUES_REPO#*/}" -f since="$since" -f query='
      query($owner: String!, $name: String!, $since: DateTime!) { viewer { login } repository(owner: $owner, name: $name) {
        recent: issues(first: 20, filterBy: {since: $since}, orderBy: {field: UPDATED_AT, direction: DESC}) { totalCount nodes {
          number title state stateReason author { login } labels(first: 5) { nodes { name } } comments(last: 1) { totalCount nodes { author { login } } } } }
        open: issues(first: 100, states: OPEN) { totalCount nodes { number comments(last: 10) { nodes { author { login } createdAt body } }
          timelineItems(last: 1, itemTypes: [REOPENED_EVENT]) { nodes { ... on ReopenedEvent { createdAt } } } '"$items"' } }
        unanswered: discussions(first: 20, answered: false, states: [OPEN], orderBy: {field: UPDATED_AT, direction: DESC}) { nodes { number title category { isAnswerable } } }
        talk: discussions(first: 10, orderBy: {field: UPDATED_AT, direction: DESC}) { nodes {
          number title updatedAt author { login } category { name } comments { totalCount } } } } }' --jq '
      .data.viewer.login as $me | .data.repository as $r
      | ["V", $me, $r.open.totalCount, $r.recent.totalCount],
        ($r.recent.nodes[] | ["R", .number, (.state | ascii_downcase), (.stateReason // "" | ascii_downcase | sub("_"; " ")),
            (.author.login // "ghost"), ([.labels.nodes[].name] | join(",")), .comments.totalCount, (.comments.nodes[0].author.login // ""), .title]),
        ($r.open.nodes[] | (.timelineItems.nodes[0].createdAt // "") as $reopened | ["O", .number,
            ([.comments.nodes[] | select(.author.login == $me and .createdAt > $reopened) | .body
              | capture("^Done in (?<h>[0-9a-f]{7,40})\\b") | .h] | last // ""),
            ([.projectItems.nodes[]? | "\(.project.owner.login)/\(.project.number)=\(.status.name // "")"] | join(","))]),
        ($r.unanswered.nodes[] | select(.category.isAnswerable) | ["Q", .number, .title]),
        ($r.talk.nodes[] | ["T", .number, .updatedAt, .category.name, (.author.login // "ghost"), .comments.totalCount, .title])
      | map(tostring | gsub("[\u001f\n\t]"; " ")) + ["."] | join("\u001f")' 2>/dev/null) \
        || { echo "unavailable: gh api graphql failed (offline, logged out${ISSUES_PROJECT:+, or a token without the project scope})"; return 0; }
    printf '%s\n' "$now" > "$stamp"

    # Each record ends in "." so that read keeps a trailing empty field.
    local -a F recent=() mine=() closed=() unadded=() doing=() close=() unpushed=() questions=() talk=()
    local -A asked=()
    local me="" total=0 nrecent=0 up line c h at ae new
    up=$(g rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')
    while IFS=$US read -r -a F; do
        case "${F[0]}" in
            V) me=${F[1]}; total=${F[2]}; nrecent=${F[3]} ;;
            R) if [ "${F[2]}" = closed ]; then closed+=("#${F[1]} (${F[3]})"); continue; fi
               if [ "${F[4]}" = "$me" ] && [ "${F[7]:-$me}" = "$me" ]; then mine+=("#${F[1]}"); continue; fi
               line="#${F[1]}${F[5]:+ [${F[5]}]} by ${F[4]}"
               [ "${F[4]}" = "$me" ] || line+=" (not $me)"
               c=comments; [ "${F[6]}" = 1 ] && c=comment
               recent+=("$line, ${F[6]} $c${F[7]:+, last by ${F[7]}}: ${F[8]}") ;;
            O) case ",${F[3]}," in
                   *",$ISSUES_PROJECT=In Progress,"*) doing+=("#${F[1]}") ;;
                   *",$ISSUES_PROJECT="*) ;;
                   *) [ -n "$ISSUES_PROJECT" ] && unadded+=("#${F[1]}") ;;
               esac
               h=${F[2]}; [ -n "$h" ] || continue
               if ! g cat-file -e "$h^{commit}"; then
                   unpushed+=("#${F[1]} ($h, not in this repository)")
               elif [ -n "$up" ] && g merge-base --is-ancestor "$h" "$up"; then
                   close+=("#${F[1]} ($h)")
               else
                   # Rewritten before the push: the same author at the same author date.
                   new=""
                   if [ -n "$up" ] && read -r at ae < <(g log -1 --format='%at %ae' "$h"); then
                       new=$(g log "$up" --since="@$at" --format='%h %at %ae' | awk -v at="$at" -v ae="$ae" '$2 == at && $3 == ae { print $1; exit }')
                   fi
                   if [ -n "$new" ]; then close+=("#${F[1]} ($h, pushed as $new: edit the comment to it first)")
                   else unpushed+=("#${F[1]} ($h)"); fi
               fi ;;
            Q) asked[${F[1]}]=1; questions+=("#${F[1]} ${F[2]}") ;;
            T) [ "${F[2]//[!0-9]/}" -ge "${since//[!0-9]/}" ] && [ -z "${asked[${F[1]}]:-}" ] \
                   && talk+=("#${F[1]} [${F[3]}] by ${F[4]}, ${F[5]} comments: ${F[6]}") ;;
        esac
    done <<< "$out"

    line="$ISSUES_REPO: $total open issues"
    [ -n "$ISSUES_PROJECT" ] && line+="; In Progress in project $ISSUES_PROJECT: ${doing[*]:-none}"
    [ "$total" -gt 100 ] && line+=" (the lines below read the first 100)"
    echo "$line"
    line="updated since $since ($from): $nrecent"
    [ "$nrecent" -eq 0 ] && line="nothing updated since $since ($from)"
    [ "$nrecent" -gt 20 ] && line+=", the newest 20"
    echo "$line"
    [ ${#recent[@]} -gt 0 ] && printf '  %s\n' "${recent[@]}"
    [ ${#mine[@]} -gt 0 ] && echo "  open, by $me, no one else's comment last: ${mine[*]}"
    [ ${#closed[@]} -gt 0 ] && echo "  closed: ${closed[*]}"
    [ ${#unadded[@]} -gt 0 ] && echo "not in project $ISSUES_PROJECT, to add: ${unadded[*]}"
    [ ${#close[@]} -gt 0 ] && echo "to close, Done in a commit on $up: ${close[*]}"
    [ ${#unpushed[@]} -gt 0 ] && echo "Done in a commit not on ${up:-an upstream (BRANCH has none)} yet: ${unpushed[*]}"
    [ ${#questions[@]} -gt 0 ] && { echo "Q&A discussions without an answer:"; printf '  %s\n' "${questions[@]}"; }
    [ ${#talk[@]} -gt 0 ] && { echo "discussions updated since:"; printf '  %s\n' "${talk[@]}"; }
    return 0
}
echo "== GitHub =="
( github ) || echo "unavailable: the section failed"

echo "== worktrees =="
g worktree list
echo "== loop/* branches =="
b=$(g branch --list 'loop/*'); [ -n "$b" ] && printf '%s\n' "$b" || echo "none"
[ -e "$CAMPAIGN" ] && echo "campaign worktree present: $CAMPAIGN"

echo "== LOOP_NOTES =="
if [ -e "$NOTES" ]; then awk 'NR == 1 && /^---$/ { fm = 1; next } fm && /^---$/ { fm = 0; next } !fm' "$NOTES"
else echo "MISSING (fresh chain: baseline the gates on a clean tree, write the file from scratch at the end)"; fi

echo "== LOOP_TECHNIQUES: $TECHNIQUES/<name>.md =="
$OKF state || echo "(okf.py state failed; the bundle may be unreadable)"

echo "== protocol =="
echo "Before a lead: grep -rn its file and function in $REJECTED. A ruling from the user: record it with okf.py ruling, in their words, then act."
echo "End: rewrite LOOP_NOTES, add to LOOP_TECHNIQUES/REJECTED, delete iteration.txt, report, ScheduleWakeup last (60 s; up to 900 while only a CI run is awaited; stop only for 3 quiet / unfixable gate / user's decision, with PushNotification)."
echo "Never: stash, push, add -A, background commands, suite/probe/mypy without timeout; amend only your own unpushed tip, message only. Findings as they arrive -> $SCRATCH/iteration.txt."
