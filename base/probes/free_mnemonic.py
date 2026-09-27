"""Pick a mnemonic for a new menu label that no sibling has taken.

Usage: run from the MComix checkout, after the new msgid is in every
catalogue and the .mo files are compiled:
    timeout -k 5 90 python3 STATE/probes/free_mnemonic.py '_Copy page' right-click
It reads the same menus test_messages.py::MnemonicTest does, and for
each language prints the label and, where its letter is already taken
in that menu, the same label with the underscore moved to the first
letter that is free.  Apply the suggestions to the .po files, compile,
and let MnemonicTest have the last word: a suggestion inside a word is
ordinary GTK style, but one that lands on an article or a particle is
worth replacing by hand.
"""
import gettext
import os
import sys

# The checkout's own "test" package, not the standard library's: a
# script is started with its own directory on the path, not the one it
# was run from.
sys.path.insert(0, os.getcwd())
from test import test_messages as tm  # noqa: E402

MSGID = sys.argv[1] if len(sys.argv) > 1 else '_Copy page'
MENU = sys.argv[2] if len(sys.argv) > 2 else 'right-click'

labels = tm.MnemonicTest._all_menus()[MENU]
for language in sorted(os.listdir('mcomix/messages')):
    compiled = 'mcomix/messages/%s/LC_MESSAGES/mcomix.mo' % language
    if not os.path.isfile(compiled):
        continue
    with open(compiled, 'rb') as handle:
        catalogue = gettext.GNUTranslations(handle)
    taken = set()
    mine = None
    for msgid in labels:
        text = catalogue.gettext(msgid)
        if msgid == MSGID:
            mine = text
            continue
        key = tm.MnemonicTest._mnemonic(text)
        if key is not None:
            taken.add(key.lower())
    if mine is None:
        print('%-6s %s is in no such menu' % (language, MSGID))
        continue
    key = tm.MnemonicTest._mnemonic(mine)
    if key is not None and key.lower() not in taken:
        print('%-6s %-28s keeps %s' % (language, mine, key))
        continue
    plain = mine.replace('_', '')
    for index, character in enumerate(plain):
        if character.isalpha() and character.lower() not in taken:
            print('%-6s %-28s -> %s'
                  % (language, mine, plain[:index] + '_' + plain[index:]))
            break
    else:
        print('%-6s %-28s has no free letter' % (language, mine))
