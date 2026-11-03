"""Pick access keys for several new labels of one menu at once.

Usage, from the MComix checkout, after the msgids are in every catalogue
and the .mo files are compiled:
    timeout -k 5 90 python3 STATE/probes/free_mnemonic_pair.py <menu> '<msgid>' ['<msgid>' ...]
free_mnemonic.py checks one label against the menu's others, so two new
labels can each be given a letter the other then takes.  This one
reserves each pick before choosing the next: a label keeps its letter
where that is free, or else takes its first free letter.  Prints, per
language, each label as it should be, and says where a label has no
free letter left (reword it).
"""
import gettext
import os
import sys

sys.path.insert(0, os.getcwd())
from test import test_messages as tm  # noqa: E402

MENU = sys.argv[1]
NEW = sys.argv[2:]

labels = tm.MnemonicTest._all_menus()[MENU]
for language in sorted(os.listdir('mcomix/messages')):
    compiled = 'mcomix/messages/%s/LC_MESSAGES/mcomix.mo' % language
    if not os.path.isfile(compiled):
        continue
    with open(compiled, 'rb') as handle:
        catalogue = gettext.GNUTranslations(handle)
    taken = set()
    for msgid in labels:
        if msgid in NEW:
            continue
        key = tm.MnemonicTest._mnemonic(catalogue.gettext(msgid))
        if key is not None:
            taken.add(key.lower())
    out = []
    for msgid in NEW:
        mine = catalogue.gettext(msgid)
        key = tm.MnemonicTest._mnemonic(mine)
        if key is not None and key.lower() not in taken:
            taken.add(key.lower())
            out.append(mine)
            continue
        plain = mine.replace('_', '')
        for index, character in enumerate(plain):
            if character.isalpha() and character.lower() not in taken:
                taken.add(character.lower())
                out.append(plain[:index] + '_' + plain[index:])
                break
        else:
            out.append('NO FREE LETTER: ' + mine)
    print(language + '\t' + '\t'.join(out))
