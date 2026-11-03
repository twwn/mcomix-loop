#!/bin/sh
# xgettext the template, then msgmerge -N -U each catalogue (no fuzzy).
set -e
VERSION=$(grep "^VERSION" mcomix/constants.py | sed -e "s/VERSION = //" -e "s/'//g")
xgettext -LPython -omcomix.pot -pmcomix/messages/ -cTRANSLATORS \
	--from-code=utf-8 --package-name=MComix --package-version=${VERSION} \
	--msgid-bugs-address=https://github.com/twwn/mcomix/issues \
	mcomix/*.py mcomix/archive/*.py mcomix/library/*.py
for po in mcomix/messages/*/LC_MESSAGES/mcomix.po; do
	msgmerge -q -N -U --backup=none "$po" mcomix/messages/mcomix.pot
done
