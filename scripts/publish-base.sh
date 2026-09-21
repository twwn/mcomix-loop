#!/usr/bin/env bash
# Copies the live state into base/ so it can be committed and published as the
# seed for other installations. Run by hand, with no loop session open; the
# loop never touches base/. What it does:
#   techniques.md  copied whole (nothing in it is iteration state)
#   probes/        copied whole
#   notes.md       gate numbers, Leads and Checked-and-rejected kept; the
#                  sections that belong to one installation (decisions,
#                  questions, last iteration, prompt corrections) blanked
#   config.sh, project.md   NOT copied: base/ carries the examples
# Then it lists lines that look machine- or installation-specific, for review.

set -u
. "$(dirname "$0")/paths.sh"
BASE=$SKILL_DIR/base
mkdir -p "$BASE/probes"

cp "$TECHNIQUES" "$BASE/techniques.md"
[ -d "$STATE/probes" ] && cp -r "$STATE/probes/." "$BASE/probes/"

awk '
    /^## Gate numbers as of / {
        sub(/ \(.*\)$/, ""); print $0 " (seed from another installation; re-baseline)"; keep = 1; next
    }
    /^## Campaign/                     { print; print ""; print "None open."; print ""; keep = 0; next }
    /^## Decisions from the user/      { print; print ""; print "None here; the standing ones are in STATE/project.md."; print ""; keep = 0; next }
    /^## Questions for the user/       { print; print ""; print "None."; print ""; keep = 0; next }
    /^## What the last iteration changed/ {
        print; print ""
        print "Nothing on this installation yet. These notes were seeded from another"
        print "installation; the gate numbers above are that checkout'"'"'s, and the leads"
        print "below were true there. Re-baseline the gates on a clean tree, then rewrite"
        print "this file as your own."
        print ""; keep = 0; next
    }
    /^## Leads worth picking up/       { keep = 1 }
    /^## Checked and rejected/         { keep = 1 }
    /^## Prompt corrections/           { print; print ""; print "None."; keep = 0; next }
    keep { print }
' "$NOTES" > "$BASE/notes.md"

echo "base/ updated from state/. Review before committing:"
grep -nE '/tmp/|this machine|GeForce|RTX|Radeon|PR-prep|mcomix-push|scratchpad|/home/[a-z]' \
    "$BASE/techniques.md" "$BASE/notes.md" | sed 's/^/  /' \
    && echo "  ^ machine- or installation-specific; reword or drop" \
    || echo "  nothing flagged"
echo "  leads in base/notes.md that only this installation can act on (a document to update, a push): drop them"
