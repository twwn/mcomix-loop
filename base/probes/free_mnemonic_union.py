"""Pick a mnemonic for a label shown in more than one menu.

Usage, from the MComix checkout, after the msgid is in every catalogue
and the .mo files are compiled:
    timeout -k 5 90 python3 STATE/probes/free_mnemonic_union.py '<msgid>'
Like free_mnemonic.py, but a msgid used in several menus carries one
mnemonic for all of them, so the letters taken are the union over every
menu (as test_messages.py::MnemonicTest reads them) that holds it.  Prints,
for English and each language, the letter kept or a suggestion with the
underscore moved to the first free letter; a CJK label, whose mnemonic
is a trailing "(_X)", gets the first free letter of the English label.
"""
import gettext
import os
import sys

sys.path.insert(0, os.getcwd())
from test import test_messages as tm  # noqa: E402

MSGID = sys.argv[1]
menus = [labels for labels in tm.MnemonicTest._all_menus().values()
         if MSGID in labels]
print('in %d menus' % len(menus))


def suggest(language, catalogue):
    taken = set()
    for labels in menus:
        for msgid in labels:
            if msgid != MSGID:
                key = tm.MnemonicTest._mnemonic(catalogue(msgid))
                if key is not None:
                    taken.add(key.lower())
    mine = catalogue(MSGID)
    key = tm.MnemonicTest._mnemonic(mine)
    if key is not None and key.lower() not in taken:
        print('%-6s %-36s keeps %s' % (language, mine, key))
        return
    if mine.endswith(')') and '(_' in mine:
        head = mine[:mine.index('(_')]
        for character in MSGID.replace('_', '').upper():
            if character.isalpha() and character.lower() not in taken:
                print('%-6s %-36s -> %s(_%s)' % (language, mine, head, character))
                return
    plain = mine.replace('_', '')
    for index, character in enumerate(plain):
        if character.isalpha() and character.lower() not in taken:
            print('%-6s %-36s -> %s' % (language, mine,
                                        plain[:index] + '_' + plain[index:]))
            return
    print('%-6s %-36s has no free letter; taken: %s'
          % (language, mine, ''.join(sorted(taken))))


suggest('en', lambda msgid: msgid)
for language in sorted(os.listdir('mcomix/messages')):
    compiled = 'mcomix/messages/%s/LC_MESSAGES/mcomix.mo' % language
    if os.path.isfile(compiled):
        with open(compiled, 'rb') as handle:
            suggest(language, gettext.GNUTranslations(handle).gettext)
