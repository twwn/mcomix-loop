#!/usr/bin/env bash
# Copies the live state into base/, the OKF bundle the repository publishes as
# the seed for other installations. Run by hand, with no loop session open;
# the loop never touches base/.
#   techniques/, rejected.md, probes/   copied whole (knowledge of the code base)
#   decisions/, project.md              copied whole: the author's installation,
#                                       as the worked example (README says what to keep)
#   notes.md                            gate numbers and leads kept, the rest blanked
#   config.sh, commits.log, scratch/    never copied
# Then it regenerates the index files, adds a log.md entry, checks conformance
# and lists lines that look machine- or person-specific, for review.
set -u
. "$(dirname "$0")/paths.sh"
BASE=$SKILL_DIR/base
[ -d "$STATE" ] || { echo "no $STATE" >&2; exit 2; }
rm -rf "$BASE/techniques" "$BASE/decisions" "$BASE/probes"
mkdir -p "$BASE"
cp -r "$TECHNIQUES" "$BASE/techniques"
cp -r "$DECISIONS" "$BASE/decisions"
cp "$REJECTED" "$STATE/project.md" "$BASE/"
(cd "$STATE/probes" 2>/dev/null && find . -name __pycache__ -prune -o -type f -print | while read -r f; do
    mkdir -p "$BASE/probes/$(dirname "$f")" && cp "$f" "$BASE/probes/$f"
done)

awk '
    NR == 1 && /^---$/ { fm = 1; print; next }
    fm { print; if (/^---$/) fm = 0; next }
    /^## Gate numbers as of / { sub(/ \(.*\)$/, ""); print $0 " (seed from another installation; re-baseline)"; keep = 1; next }
    /^## Campaign/                     { print; print ""; print "None open."; print ""; keep = 0; next }
    /^## Questions for the user/       { print; print ""; print "None."; print ""; keep = 0; next }
    /^## What the last iteration changed/ {
        print; print ""
        print "Nothing on this installation yet. These notes were seeded from another installation; the gate numbers above are that checkout'"'"'s, and the leads below were true there. Re-baseline the gates on a clean tree, then rewrite this file as your own."
        print ""; keep = 0; next
    }
    /^## Leads worth picking up/       { keep = 1 }
    /^## Prompt corrections/           { print; print ""; print "None."; keep = 0; next }
    keep { print }
' "$NOTES" > "$BASE/notes.md"

# never publish the publisher's home directory
grep -rlF "$HOME/" "$BASE" --include='*.md' 2>/dev/null | while read -r f; do sed -i "s|$HOME/|/home/<user>/|g" "$f"; done

$OKF --state "$BASE" index >/dev/null
commit=$(git -C "$(resolve_repo 2>/dev/null || echo .)" rev-parse --short HEAD 2>/dev/null || echo unknown)
today=$(date -u +%F)
{
    if [ -e "$BASE/log.md" ]; then sed -n '1,2p' "$BASE/log.md"; else printf '# Update log\n\n'; fi
    printf '## %s\n* **Update**: published from an installation at %s: %s techniques, %s rulings.\n\n' \
        "$today" "$commit" "$(ls "$BASE/techniques" | grep -vc '^index.md$')" "$(ls "$BASE/decisions" | grep -vc '^index.md$')"
    if [ -e "$BASE/log.md" ]; then sed -n '3,$p' "$BASE/log.md"; fi
} > "$BASE/log.md.new"
mv "$BASE/log.md.new" "$BASE/log.md"

echo "base/ updated from state/."
$OKF --state "$BASE" check && echo "  conformance: clean"
flagged=$(grep -rnE 'GeForce|RTX [0-9]|Radeon|PR-prep|mcomix-push|/home/[a-z][a-z0-9_-]*/' \
    "$BASE/techniques" "$BASE/rejected.md" "$BASE/notes.md" "$BASE/probes" 2>/dev/null)
if [ -n "$flagged" ]; then
    printf '%s\n' "$flagged" | sed 's/^/  /'
    echo "  ^ machine- or person-specific; reword or drop before committing"
else
    echo "  nothing flagged"
fi
