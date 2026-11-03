#!/bin/sh
# Rewrap each catalogue as gettext would, compile it, print statistics.
set -e
for po in mcomix/messages/*/LC_MESSAGES/mcomix.po; do
	tmp=$(mktemp)
	msgmerge -q -N -o "$tmp" "$po" mcomix/messages/mcomix.pot
	mv "$tmp" "$po"
	msgfmt -c -o "${po%.po}.mo" "$po"
	printf '%s ' "$(echo "$po" | cut -d/ -f3)"; msgfmt --statistics -o /dev/null "$po" 2>&1
done
