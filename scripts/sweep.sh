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
#   sweep.sh tally              what each lens has returned, run by run, and
#                               whether it is due, resting or retired
#
# A lens is due unless its last run left no lead and fewer than SWEEP_EVERY
# commits have touched mcomix/ or docs/ since, so a lens runs until it is dry and
# then rests. Commits are counted by author date, which survives the user's
# rewrites of history; a recorded hash may not. At most SWEEP_WIDTH run at once,
# the longest rested first. No lens is due while a campaign is open, or until
# subagents are guarded: `start` is what hands out the prompts. A run that never
# reported (`-`) counts for nothing: neither as a run nor as a rest.
#
# A lens whose last SWEEP_RETIRE runs in a row left no lead is retired: it rests
# SWEEP_EVERY commits for each of those runs (75 after three at 25), so a lens
# that stays dry costs less and less, and new code still brings it back in time.
# One lead resets the count. Within that rest it runs only when named, which
# sweep.md leaves to the user. SWEEP_RETIRE=0 retires nothing. One empty run is
# no verdict: threads left none at 216804dc and three at ca9c257e.
#
# While $SWEEP/started exists, guard.sh holds the subagents to what an auditor
# needs. wait's slice stays under the Bash tool's timeout, which would otherwise
# move it to the background.
#
# A lens runs at SWEEP_MODEL and SWEEP_EFFORT unless `start` names another tier
# for it. The loop picks unattended, so what it may name stops at high effort;
# only config.sh goes higher. Fable may be named, but sweep.md allows it only
# where the user names it for that run: a lens on Fable took about three times
# what one on Sonnet takes (2026-11-15: five lenses at fable/high took the
# 5-hour window from 14% to 99% in ten minutes), so it counts as FABLE_WEIGHT
# lenses against the window, and a sweep that ran one is left out of the
# estimate below. `done` adds the tier to the lens's line in sweeps.log.
#
# With SWEEP_FEATURES=1 the feature lenses in sweep.md join them, under a brief
# of their own. A sweep takes at most one unless it is named, and one rests after
# every run that reported, whatever it left: such a lens nearly always finds
# something, and that must not keep the loop going.
#
# The plan's 5-hour window (statusline.sh keeps the reading) decides how many
# lenses start: what is used, plus what each lens takes, must stay under
# 100 - WINDOW_RESERVE, or the auditors are cut off with the window and their
# work is lost. `start` takes the first that fit and opens nothing when none
# does. What a lens takes is measured: `start` notes the window, the last `done`
# reads it again, and sweeps.log's eighth column holds the difference per lens
# (`-` when unmeasured: no reading, or the window reset meanwhile). The mean of
# the last three sweeps measured is the estimate, SWEEP_LENS_COST before any.
# The lines of a sweep go into sweeps.log when it closes, all at that time.
# Past the 7-day window's reserve (WEEK_RESERVE) no lens fits.

set -u
case "$0" in */*) . "${0%/*}/paths.sh" ;; *) . ./paths.sh ;; esac
REPO=$(resolve_repo) || { echo "sweep: $PWD is not an MComix checkout" >&2; exit 2; }
DOC=$SKILL_DIR/sweep.md
STARTED=$SWEEP/started
LOGGED=$SWEEP/logged
TIERS=$SWEEP/tiers
DEADLINE=3600     # seconds an auditor has; a past one took 22 minutes over more than this asks
FABLE_WEIGHT=3    # lenses' worth of the 5-hour window one lens on Fable takes

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

# A lens's runs that reported, from sweeps.log, as one tab-separated line: the
# last one's time (0 for never) and commit, the empty runs in a row at the end,
# the runs, those cut off (`-`), the leads returned and survived in all, and
# what survived run by run, oldest first.
lens_history() {   # lens_history <lens>
    [ -e "$SWEEPS" ] || { printf '0\t-\t0\t0\t0\t0\t0\t-\n'; return 0; }
    awk -F'\t' -v l="$1" '
        $2 != l { next }
        $5 == "-" { cut++; next }
        { t = $1; c = $3; z = ($5 == 0) ? z + 1 : 0; n++; r += ($4 ~ /^[0-9]+$/) ? $4 : 0; s += $5; h = h (h == "" ? "" : " ") $5 }
        END { printf "%d\t%s\t%d\t%d\t%d\t%d\t%d\t%s\n", t, (c == "" ? "-" : c), z, n, cut, r, s, (h == "" ? "-" : h) }' "$SWEEPS"
}

# rest_for <lens> <empty runs in a row>: the commits it rests after its last run.
rest_for() {
    local r=0
    [ "$2" -gt 0 ] && r=$SWEEP_EVERY
    retired "$2" && r=$((SWEEP_EVERY * $2))
    is_feature "$1" && [ "$r" -lt "$SWEEP_EVERY" ] && r=$SWEEP_EVERY
    echo "$r"
}
retired() { [ "$SWEEP_RETIRE" -gt 0 ] && [ "$1" -ge "$SWEEP_RETIRE" ]; }

# One tab-separated line per lens, in sweep.md's order: lens, last run that
# reported (0 for never), its commit, empty runs in a row, commits since.
lens_table() {
    local times lens t commit streak
    times=$(git -C "$REPO" log --format=%at -- mcomix docs 2>/dev/null)
    while IFS= read -r lens; do
        IFS=$'\t' read -r t commit streak _ < <(lens_history "$lens")
        printf '%s\t%s\t%s\t%s\t%s\n' "$lens" "$t" "$commit" "$streak" \
            "$(awk -v t="$t" '$1 > t { n++ } END { print n + 0 }' <<< "$times")"
    done < <(lenses)
}

# sort_lenses <array for the lenses due> <array for lines about those resting>
#   <array for lines about those retired>; LENS_STATE[lens] says which, before
#   SWEEP_WIDTH cuts the lenses due.
declare -A LENS_STATE=()
sort_lenses() {
    local -n due_out=$1 rest_out=$2 retired_out=$3
    local lens t commit streak since need
    due_out=() rest_out=() retired_out=() LENS_STATE=()
    local -a rows=() scouts=()
    while IFS=$'\t' read -r lens t commit streak since; do
        need=$(rest_for "$lens" "$streak")
        if [ "$t" -ne 0 ] && [ "$since" -lt "$need" ]; then
            if retired "$streak"; then
                LENS_STATE[$lens]=retired
                retired_out+=("$lens (no lead in its last $streak runs; runs again after $need commits, $since so far, or when the user names it)")
            else
                LENS_STATE[$lens]=resting
                rest_out+=("$lens ($since of $need commits since $commit)")
            fi
            continue
        fi
        LENS_STATE[$lens]=due
        if is_feature "$lens"; then
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

# What one lens takes of the 5-hour window, in percent, rounded up: the mean
# of the last three sweeps measured, leaving out any that ran a lens on Fable.
lens_cost() {
    local c=""
    [ -e "$SWEEPS" ] && c=$(awk -F'\t' '$6 == "fable" { fable[$1] }
        $8 ~ /^[0-9]+$/ && !($1 in seen) { seen[$1]; at[++n] = $1; v[n] = $8 }
        END { for (i = n; i >= 1 && k < 3; i--) if (!(at[i] in fable)) { s += v[i]; k++ }
              if (k) { m = s / k; printf "%d\n", m == int(m) ? m : int(m) + 1 } }' "$SWEEPS")
    [[ "$c" =~ ^[0-9]+$ && "$c" -ge 1 ]] || c=$SWEEP_LENS_COST
    [[ "$c" =~ ^[0-9]+$ && "$c" -ge 1 ]] || c=1
    echo "$c"
}

weight() { if [ "$1" = fable ]; then echo "$FABLE_WEIGHT"; else echo 1; fi; }   # weight <model>

# fit <weight>...: sets FIT to how many of these lenses, in order, the 5-hour
# window has room for (all when it is unknown, none past the 7-day reserve),
# COST to what one of weight 1 takes, WEEK_FULL, and the W_* of `window`.
fit() {
    window
    COST=$(lens_cost)
    FIT=$# WEEK_FULL=""
    if [ "$W7_PCT" != - ] && [ "$W7_PCT" -ge $((100 - WEEK_RESERVE)) ]; then FIT=0 WEEK_FULL=1; return 0; fi
    [ "$W_PCT" != - ] || return 0
    local room=$((100 - WINDOW_RESERVE - W_PCT)) w n=0
    for w in "$@"; do
        room=$((room - w * COST))
        [ "$room" -ge 0 ] || break
        n=$((n + 1))
    done
    FIT=$n
}

window_text() {   # after fit: the reading, for a message
    local LC_ALL=C
    if [ -n "$WEEK_FULL" ]; then
        local s="the 7-day window is $W7_PCT% used"
        [ "$W7_RESET" = - ] || s+=" until $(printf '%(%a %H:%M)T' "$W7_RESET")"
        printf '%s, at its reserve (WEEK_RESERVE %s%%)' "$s" "$WEEK_RESERVE"
        return 0
    fi
    local s="the 5-hour window is $W_PCT% used"
    [ "$W_RESET" = - ] || s+=" until $(printf '%(%H:%M)T' "$W_RESET")"
    printf '%s; a lens takes about %s%% (on Fable %s times that), and %s%% stays for the rest of the iteration (WINDOW_RESERVE)' "$s" "$COST" "$FABLE_WEIGHT" "$WINDOW_RESERVE"
}

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
    local -a due rest retired weights
    sort_lenses due rest retired
    if [ ${#due[@]} -gt 0 ]; then
        mapfile -t weights < <(for _ in "${due[@]}"; do weight "$SWEEP_MODEL"; done)
        fit "${weights[@]}"
        if [ "$FIT" -eq ${#due[@]} ]; then echo "due when no lead can be worked (read $DOC): ${due[*]}"
        elif [ "$FIT" -gt 0 ]; then echo "due when no lead can be worked (read $DOC): ${due[*]}; $(window_text), so a sweep now takes ${due[*]:0:FIT}"
        else echo "due: ${due[*]}; but $(window_text), so none fits: a sweep waits for the reset (SKILL.md, \"The 5-hour window\")"; fi
    else echo "none due"; fi
    if [ ${#rest[@]} -gt 0 ]; then printf 'resting: %s\n' "$(printf '%s; ' "${rest[@]}")"; fi
    if [ ${#retired[@]} -gt 0 ]; then printf 'retired: %s\n' "$(printf '%s; ' "${retired[@]}")"; fi
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
    text=${text//\{CALLS\}/"$SWEEP_CALLS"}
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
    local -a chosen=() due rest retired weights
    local -A tier=()
    local arg lens t commit
    sort_lenses due rest retired
    if [ $# -gt 0 ]; then
        for arg in "$@"; do
            lens=${arg%%=*}
            lenses | grep -qxF -- "$lens" || die "no lens named $lens in $DOC, or it is a feature lens and SWEEP_FEATURES is not 1"
            if [ "$lens" != "$arg" ]; then
                [[ "${arg#*=}" =~ ^(haiku|sonnet|opus|fable)/(low|medium|high)$ ]] \
                    || die "$arg: a tier is <haiku|sonnet|opus|fable>/<low|medium|high>"
                tier[$lens]=${arg#*=}
            fi
            case "${LENS_STATE[$lens]:-}" in
                resting|retired) echo "sweep: $lens is ${LENS_STATE[$lens]}, and runs because it was named" >&2 ;;
            esac
            chosen+=("$lens")
        done
    else
        chosen=("${due[@]}")
        [ ${#chosen[@]} -gt 0 ] || die "no lens is due"
    fi
    # The first that fit the 5-hour window: in the order named, or the longest
    # rested first with the feature lens last.
    weights=()
    for lens in "${chosen[@]}"; do
        t=${tier[$lens]:-$SWEEP_MODEL/$SWEEP_EFFORT}
        weights+=("$(weight "${t%/*}")")
    done
    fit "${weights[@]}"
    [ "$FIT" -gt 0 ] || die "$(window_text), so no lens fits and no sweep is opened. End the iteration and wake at the reset (SKILL.md, \"The 5-hour window\")."
    if [ "$FIT" -lt ${#chosen[@]} ]; then
        echo "sweep: $(window_text), so it takes $FIT of the ${#chosen[@]}; left for a later sweep: ${chosen[*]:FIT}" >&2
        chosen=("${chosen[@]:0:FIT}")
    fi
    commit=$(git -C "$REPO" rev-parse --short HEAD) || die "no HEAD"
    rm -rf "$SWEEP"
    mkdir -p "$SWEEP"
    for lens in "${chosen[@]}"; do
        mkdir -p "$SWEEP/$lens"
        brief "$lens" "$commit" > "$SWEEP/$lens.brief.md" || exit 2
    done
    for lens in "${chosen[@]}"; do
        t=${tier[$lens]:-$SWEEP_MODEL/$SWEEP_EFFORT}
        printf '%s\t%s\t%s\n' "$lens" "${t%/*}" "${t#*/}" >> "$TIERS"
    done
    # The fourth line is the window at the start, which `done` measures from.
    printf '%s\n%s\n%s\n%s %s\n' "$(now)" "$commit" "${chosen[*]}" "$W_PCT" "$W_RESET" > "$STARTED"
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
    # LOGGED holds a line per lens recorded, without the time and the cost,
    # which the close adds. (A line with the lens alone is from an older
    # sweep.sh, whose line is in sweeps.log already.)
    logged() { awk -F'\t' -v l="$1" '$1 == l { f = 1 } END { exit !f }' "$LOGGED" 2>/dev/null; }
    if ! logged "$lens"; then
        printf '%s\t%s\t%s\t%s\t%s\n' "$lens" "$commit" "$returned" "$survived" \
            "$(awk -F'\t' -v l="$lens" '$1 == l { print $2 "\t" $3 }' "$TIERS" 2>/dev/null)" >> "$LOGGED"
    fi
    names=$(sweep_lenses)
    for l in $names; do
        logged "$l" || left+=" $l"
    done
    if [ -n "$left" ]; then echo "recorded $lens; still to record:$left"; return 0; fi

    # What the sweep took of the 5-hour window, per lens, if one window held it all.
    local before="" reset="" cost=- n d
    read -r before reset < <(sed -n 4p "$STARTED")
    window
    n=$(wc -w <<< "$names")
    if [[ "$before" =~ ^[0-9]+$ && "$reset" =~ ^[0-9]+$ && "$W_PCT" =~ ^[0-9]+$ && "$W_RESET" =~ ^[0-9]+$ ]]; then
        d=$((W_RESET - reset))
        [ "${d#-}" -lt 600 ] && [ "$W_PCT" -gt "$before" ] && cost=$(( (W_PCT - before + n - 1) / n ))
    fi
    awk -F'\t' -v OFS='\t' -v t="$(now)" -v c="$cost" 'NF >= 4 {
        print t, $1, $2, $3, $4, ($5 == "" ? "-" : $5), ($6 == "" ? "-" : $6), c }' "$LOGGED" >> "$SWEEPS"
    rm -f "$STARTED" "$LOGGED"
    if [ "$cost" = - ]; then echo "recorded $lens; the sweep is closed (what it took of the 5-hour window is not measured)"
    else echo "recorded $lens; the sweep is closed, having taken about $cost% of the 5-hour window per lens"; fi
    # A lens this close retired is named in the report, so that the user sees it.
    local streak
    for l in $names; do
        IFS=$'\t' read -r _ _ streak _ < <(lens_history "$l")
        if [ "$SWEEP_RETIRE" -gt 0 ] && [ "$streak" -eq "$SWEEP_RETIRE" ]; then
            echo "RETIRED: $l left no lead in its last $streak runs. It runs again after $(rest_for "$l" "$streak") commits under mcomix/ or docs/, or when the user names it; say so in the report."
        fi
    done
}

# What each lens has returned, for the user and for choosing a tier.
tally() {
    local -a due rest retired
    local lens t commit streak runs cut returned survived hist
    sort_lenses due rest retired
    printf '%-9s %-8s %4s %4s %9s  %-6s %s\n' lens state runs cut survived empty "survived per run, oldest first"
    while IFS= read -r lens; do
        IFS=$'\t' read -r t commit streak runs cut returned survived hist < <(lens_history "$lens")
        printf '%-9s %-8s %4s %4s %9s  %-6s %s\n' "$lens" "${LENS_STATE[$lens]:-due}" "$runs" "$cut" \
            "$survived/$returned" "$streak" "$hist"
    done < <(lenses)
    echo "cut: runs that never reported. survived: of the leads returned. empty: runs in a row with none surviving; at $SWEEP_RETIRE (SWEEP_RETIRE) a lens is retired."
}

case "${1:-}" in
    status) status ;;
    start) shift; start "$@" ;;
    wait) wait_reports ;;
    done) shift; finish "$@" ;;
    tally) tally ;;
    -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0" ;;
    *) die "status, start [lens[=model/effort]...], wait, done <lens> <returned> <survived>, or tally" ;;
esac
