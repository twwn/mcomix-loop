#!/usr/bin/env bash
# Sweeps: auditors, one lens each, for when the loop's leads run out (sweep.md).
#
#   sweep.sh status             an open sweep, the lenses due and those resting (state.sh prints it)
#   sweep.sh start [lens[=model/effort]...]
#                               opens a sweep of the lenses due, or those named:
#                               writes a brief for each and prints its model,
#                               effort and prompt
#   sweep.sh wait               blocks while the Bash tool lets it, then says which reports are in
#   sweep.sh done <lens> <returned> <survived>
#                               records a lens's result, `-` and `-` if it never
#                               reported; the last one closes the sweep
#
# A lens is due unless its last run left no lead and fewer than SWEEP_EVERY
# commits have touched mcomix/ or docs/ since, so a lens runs until it is dry and
# then rests. Commits are counted by author date, which survives the user's
# rewrites of history; a recorded hash may not. At most SWEEP_WIDTH run at once,
# the longest rested first. No lens is due while a campaign is open, or until
# subagents are guarded: `start` is what hands out the prompts.
#
# While $SWEEP/started exists, guard.sh holds the subagents to what an auditor
# needs. wait's slice stays under the Bash tool's timeout, which would otherwise
# move it to the background.
#
# A lens runs at SWEEP_MODEL and SWEEP_EFFORT unless `start` names another tier
# for it. The loop picks unattended, so what it may name stops at opus/high; only
# config.sh goes higher. `done` adds the tier to the lens's line in sweeps.log.
#
# With SWEEP_FEATURES=1 the feature lenses in sweep.md join them, under a brief
# of their own. A sweep takes at most one unless it is named, and one rests after
# every run that reported, whatever it left: such a lens nearly always finds
# something, and that must not keep the loop going.

set -u
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
REPO=$(resolve_repo) || { echo "sweep: $PWD is not an MComix checkout" >&2; exit 2; }
DOC=$SKILL_DIR/sweep.md
STARTED=$SWEEP/started
LOGGED=$SWEEP/logged
TIERS=$SWEEP/tiers
DEADLINE=3600     # seconds an auditor has; a past one took 22 minutes over more than this asks

die() { echo "sweep: $1" >&2; exit 2; }
now() { printf '%(%s)T' -1; }

# The lines under a heading, up to the next heading of its level or above.
section() {   # section <heading line> <file>
    awk -v h="$1" 'BEGIN { n = index(h, " ") }
        $0 == h { on = 1; next }
        on && /^#+ / && index($0, " ") <= n { exit }
        on' "$2"
}

audit_lenses() { section "## The lenses" "$DOC" | sed -n 's/^### //p'; }
feature_lenses() { [ "$SWEEP_FEATURES" != 1 ] || section "## The feature lenses" "$DOC" | sed -n 's/^### //p'; }
lenses() { audit_lenses; feature_lenses; }
FEATURES=" $(feature_lenses | tr '\n' ' ')"
is_feature() { [[ "$FEATURES" == *" $1 "* ]]; }

# One tab-separated line per lens, in sweep.md's order: lens, last run (0 for
# never), its commit, what survived, commits since.
lens_table() {
    local times lens t commit survived
    times=$(git -C "$REPO" log --format=%at -- mcomix docs 2>/dev/null)
    while IFS= read -r lens; do
        t=0 commit="" survived=""
        if [ -e "$SWEEPS" ]; then
            IFS=$'\t' read -r t commit survived < <(awk -F'\t' -v l="$lens" \
                '$2 == l { t = $1; c = $3; s = $5 } END { printf "%d\t%s\t%s\n", t, c, s }' "$SWEEPS")
        fi
        printf '%s\t%s\t%s\t%s\t%s\n' "$lens" "$t" "$commit" "$survived" \
            "$(awk -v t="$t" '$1 > t { n++ } END { print n + 0 }' <<< "$times")"
    done < <(lenses)
}

# due <array name for the lenses due> <array name for lines about those resting>
sort_lenses() {
    local -n due_out=$1 rest_out=$2
    local lens t commit survived since resting
    due_out=() rest_out=()
    local -a rows=() scouts=()
    while IFS=$'\t' read -r lens t commit survived since; do
        resting=0
        [ "$survived" = 0 ] && resting=1
        is_feature "$lens" && [ "$survived" != - ] && resting=1
        if [ "$t" -ne 0 ] && [ "$resting" = 1 ] && [ "$since" -lt "$SWEEP_EVERY" ]; then
            rest_out+=("$lens ($since of $SWEEP_EVERY commits since $commit)")
        elif is_feature "$lens"; then
            scouts+=("$t"$'\t'"$lens")
        else
            rows+=("$t"$'\t'"$lens")
        fi
    done < <(lens_table)
    # The feature lens longest rested takes one place, unless that would be the
    # only place and an audit lens is due: what is wrong comes before what is missing.
    local room=$SWEEP_WIDTH scout=""
    [ ${#scouts[@]} -eq 0 ] || scout=$(printf '%s\n' "${scouts[@]}" | sort -s -n -k1,1 | head -n 1 | cut -f2)
    if [ -n "$scout" ] && [ "$room" -le 1 ] && [ ${#rows[@]} -gt 0 ]; then scout=""; fi
    [ -z "$scout" ] || room=$((room - 1))
    [ ${#rows[@]} -eq 0 ] || mapfile -t due_out < <(printf '%s\n' "${rows[@]}" | sort -s -n -k1,1 | head -n "$room" | cut -f2)
    [ -z "$scout" ] || due_out+=("$scout")
}

sweep_lenses() { sed -n 3p "$STARTED"; }

reports_line() {
    local lens in="" missing=""
    for lens in $(sweep_lenses); do
        if [ -s "$SWEEP/$lens.md" ]; then in+=" $lens"; else missing+=" $lens"; fi
    done
    printf 'reports in:%s; missing:%s' "${in:- none}" "${missing:- none}"
}

status() {
    [ "$SWEEP_EVERY" -gt 0 ] || { echo "off (SWEEP_EVERY in $STATE/config.sh)"; return 0; }
    if [ -e "$STARTED" ]; then
        local at commit
        { read -r at; read -r commit; } < "$STARTED"
        echo "OPEN since $(( ($(now) - at) / 60 )) minutes ago, at $commit; $(reports_line). Read $DOC and finish it."
        return 0
    fi
    subagents_guarded "$REPO" || { echo "none: subagents run without the guard until the hook in settings-snippet.json is merged"; return 0; }
    [ -e "$REPO/.claude/worktrees/campaign" ] && { echo "none while a campaign is open"; return 0; }
    local -a due rest
    sort_lenses due rest
    if [ ${#due[@]} -gt 0 ]; then echo "due when no lead can be worked (read $DOC): ${due[*]}"
    else echo "none due"; fi
    if [ ${#rest[@]} -gt 0 ]; then printf 'resting: %s\n' "$(printf '%s; ' "${rest[@]}")"; fi
    return 0
}

# A brief holds all an auditor needs, so that it reads one file, under a
# directory the session may read, and nothing of the loop's own protocol.
brief() {   # brief <lens> <commit>
    local lens=$1 commit=$2 part="## The auditor" text rules evidence facts rulings known
    is_feature "$lens" && part="## The scout"
    text=$(section "$part" "$DOC")
    text=${text//\{COMMIT\}/"$commit"}
    text=${text//\{ISSUES\}/"${ISSUES_REPO:-none}"}
    text=${text//\{REJECTED\}/"$REJECTED"}
    text=${text//\{TECHNIQUES\}/"$TECHNIQUES"}
    text=${text//\{PROBES_READY\}/"$STATE/probes"}
    text=${text//\{PROBES\}/"$SWEEP/$lens"}
    text=${text//\{REPORT\}/"$SWEEP/$lens.md"}
    text=${text//\{LENS\}/"$lens"}
    rules=$(awk '/^\*\*Nothing may touch/ { on = 1 } /^## Handoff/ { on = 0 } on' "$SKILL_DIR/SKILL.md")
    evidence=$(section "## Evidence standards" "$SKILL_DIR/SKILL.md")
    facts=$(section "## Project facts" "$SKILL_DIR/reference.md")
    rulings=$($OKF rulings 2>/dev/null | awk '/^What MComix does/ { on = 1; next } /^[^-]/ { on = 0 } on')
    known=$(awk '/^## Questions for the user/ || /^## Leads worth/ { on = 1 } /^## What the last iteration/ || /^## Prompt corrections/ { on = 0 } on' "$NOTES" 2>/dev/null)
    # A heading renamed in SKILL.md must not leave an auditor without the rules.
    [ -n "$text" ] && [ -n "$rules" ] && [ -n "$evidence" ] && [ -n "$facts" ] \
        || die "a section the brief is built from is missing from sweep.md, SKILL.md or reference.md"
    printf '%s\n\n## Your lens: %s\n\n%s\n\nThose files are in %s.\n\n## Known already\n\n%s\n\n## What the user has ruled about the program\n\n%s\n\n## Rules for what you run\n\n%s\n\n## What counts as evidence\n\nWhere this speaks of a commit, a fix or a test to add, that is the main thread'"'"'s later.\n\n%s\n\n## Facts of the code base\n\n%s\n' \
        "$text" "$lens" "$(section "### $lens" "$DOC")" "$TECHNIQUES" "${known:-(none)}" "${rulings:-(none)}" "$rules" "$evidence" "$facts"
}

start() {
    [ "$SWEEP_EVERY" -gt 0 ] || die "sweeps are off (SWEEP_EVERY in $STATE/config.sh)"
    subagents_guarded "$REPO" || die "subagents run without the guard until the hook in settings-snippet.json is merged"
    [ ! -e "$REPO/.claude/worktrees/campaign" ] || die "a campaign is open"
    [ ! -e "$STARTED" ] || die "a sweep is open: $(reports_line). Finish it with sweep.sh done."
    [[ "$SWEEP_MODEL" =~ ^(haiku|sonnet|opus|fable)$ ]] || die "SWEEP_MODEL in $STATE/config.sh is haiku, sonnet, opus or fable, not $SWEEP_MODEL"
    [[ "$SWEEP_EFFORT" =~ ^(low|medium|high|xhigh|max)$ ]] || die "SWEEP_EFFORT in $STATE/config.sh is low, medium, high, xhigh or max, not $SWEEP_EFFORT"
    local -a chosen=() rest
    local -A tier=()
    if [ $# -gt 0 ]; then
        local arg lens
        for arg in "$@"; do
            lens=${arg%%=*}
            lenses | grep -qxF -- "$lens" || die "no lens named $lens in $DOC, or it is a feature lens and SWEEP_FEATURES is not 1"
            if [ "$lens" != "$arg" ]; then
                [[ "${arg#*=}" =~ ^(haiku|sonnet|opus)/(low|medium|high)$ ]] \
                    || die "$arg: a tier is <haiku|sonnet|opus>/<low|medium|high>"
                tier[$lens]=${arg#*=}
            fi
            chosen+=("$lens")
        done
    else
        sort_lenses chosen rest
        [ ${#chosen[@]} -gt 0 ] || die "no lens is due"
    fi
    local commit
    commit=$(git -C "$REPO" rev-parse --short HEAD) || die "no HEAD"
    rm -rf "$SWEEP"
    mkdir -p "$SWEEP"
    local lens
    for lens in "${chosen[@]}"; do
        mkdir -p "$SWEEP/$lens"
        brief "$lens" "$commit" > "$SWEEP/$lens.brief.md" || exit 2
    done
    local t
    for lens in "${chosen[@]}"; do
        t=${tier[$lens]:-$SWEEP_MODEL/$SWEEP_EFFORT}
        printf '%s\t%s\t%s\n' "$lens" "${t%/*}" "${t#*/}" >> "$TIERS"
    done
    printf '%s\n%s\n%s\n' "$(now)" "$commit" "${chosen[*]}" > "$STARTED"
    for lens in "${chosen[@]}"; do
        t=${tier[$lens]:-$SWEEP_MODEL/$SWEEP_EFFORT}
        echo "$lens ${t%/*} ${t#*/}: Read $SWEEP/$lens.brief.md in full and do what it says."
    done
}

wait_reports() {
    [ -e "$STARTED" ] || die "no sweep is open"
    local at lens missing slice
    read -r at < "$STARTED"
    slice=$(( ${BASH_DEFAULT_TIMEOUT_MS:-120000} / 1000 - 20 ))
    [ "$slice" -ge 10 ] || slice=10
    while :; do
        missing=""
        for lens in $(sweep_lenses); do
            [ -s "$SWEEP/$lens.md" ] || missing+=" $lens"
        done
        [ -n "$missing" ] || { echo "all in; $(reports_line)"; return 0; }
        [ "$(now)" -lt $((at + DEADLINE)) ] || { echo "deadline passed; $(reports_line)"; return 0; }
        [ "$SECONDS" -lt "$slice" ] || { echo "still waiting: run sweep.sh wait again now, and do not end the turn; $(reports_line)"; return 0; }
        sleep 5
    done
}

finish() {   # finish <lens> <returned> <survived>
    [ $# -eq 3 ] || die "done takes <lens> <returned> <survived>"
    [ -e "$STARTED" ] || die "no sweep is open"
    local lens=$1 returned=$2 survived=$3 at commit names left="" l
    case " $(sweep_lenses) " in *" $lens "*) ;; *) die "$lens is not in the open sweep: $(sweep_lenses)" ;; esac
    [[ "$returned" =~ ^([0-9]+|-)$ && "$survived" =~ ^([0-9]+|-)$ ]] || die "returned and survived are numbers, or - for a lens that never reported"
    { read -r at; read -r commit; } < "$STARTED"
    if ! grep -qxF -- "$lens" "$LOGGED" 2>/dev/null; then
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(now)" "$lens" "$commit" "$returned" "$survived" \
            "$(awk -F'\t' -v l="$lens" '$1 == l { print $2 "\t" $3 }' "$TIERS" 2>/dev/null)" >> "$SWEEPS"
        printf '%s\n' "$lens" >> "$LOGGED"
    fi
    names=$(sweep_lenses)
    for l in $names; do
        grep -qxF -- "$l" "$LOGGED" || left+=" $l"
    done
    if [ -n "$left" ]; then echo "recorded $lens; still to record:$left"
    else rm -f "$STARTED" "$LOGGED"; echo "recorded $lens; the sweep is closed"; fi
}

case "${1:-}" in
    status) status ;;
    start) shift; start "$@" ;;
    wait) wait_reports ;;
    done) shift; finish "$@" ;;
    -h|--help) sed -n '2,32p' "$0" ;;
    *) die "status, start [lens[=model/effort]...], wait, or done <lens> <returned> <survived>" ;;
esac
