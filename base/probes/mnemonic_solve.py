"""Move the access keys of the named labels to free letters, per language.

Usage, from the checkout, with the .mo files compiled:
    python3 mnemonic_solve.py out.json '<msgid>' ['<msgid>' ...]
Every menu MnemonicTest reads that holds one of the msgids counts; the
other labels keep their letters, and the named ones are settled in the
order given, each against the letters the ones before it took.  A label
whose letter is free keeps it; otherwise the underscore moves to the
first free letter that starts a word, else the first free letter.  CJK
labels written "...(_X)" take a letter of the English label.  Writes a
po_set.py JSON of the labels that changed and prints them.
"""
import gettext, json, os, re, sys
sys.path.insert(0, os.getcwd())
from test import test_messages as tm  # noqa: E402

OUT = sys.argv[1]
MOVABLE = sys.argv[2:]
MENUS = list(tm.MnemonicTest._all_menus().values())
key = tm.MnemonicTest._mnemonic


def place(label, english, taken):
    k = key(label)
    if k is not None and k.lower() not in taken:
        return label
    cjk = re.search(r'\(_.\)', label)
    if cjk:
        for c in english.replace('_', '').upper():
            if c.isalpha() and c.lower() not in taken:
                return label[:cjk.start()] + '(_%s)' % c + label[cjk.end():]
        return None
    plain = label.replace('_', '')
    starts = [i for i, c in enumerate(plain) if c.isalpha() and (i == 0 or not plain[i - 1].isalpha())]
    rest = [i for i, c in enumerate(plain) if c.isalpha() and i not in starts]
    for i in starts + rest:
        if plain[i].lower() not in taken:
            return plain[:i] + '_' + plain[i:]
    return None


result = {}
for language in ['en'] + sorted(d for d in os.listdir('mcomix/messages') if os.path.isdir('mcomix/messages/' + d)):
    if language == 'en':
        tr = lambda m: m
    else:
        with open('mcomix/messages/%s/LC_MESSAGES/mcomix.mo' % language, 'rb') as h:
            tr = gettext.GNUTranslations(h).gettext
    current = {}
    def label(m):
        return current.get(m, tr(m))
    for m in MOVABLE:
        taken = set()
        for menu in MENUS:
            if m in menu:
                for other in menu:
                    if other != m:
                        k = key(label(other))
                        if k is not None:
                            taken.add(k.lower())
        new = place(label(m), m, taken)
        if new is None:
            print('%-6s %s: NO FREE LETTER (%s)' % (language, label(m), ''.join(sorted(taken))))
            continue
        if new != label(m):
            current[m] = new
            print('%-6s %s -> %s' % (language, tr(m), new))
    if language != 'en' and current:
        result[language] = current
json.dump(result, open(OUT, 'w'), ensure_ascii=False, indent=0)
