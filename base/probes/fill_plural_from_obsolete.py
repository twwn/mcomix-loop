"""Fill a message that ngettext() replaced a plain one with.

msgmerge -N leaves the new plural entry empty and the old translation
as an obsolete #~ entry.  Each form gets the old translation, except
where FORMS gives the language's own; the obsolete entry is dropped.
Usage: python3 fill_plural_from_obsolete.py OLD_MSGID NEW_MSGID catalogue.po...
FORMS is edited for the message at hand.
"""
import re
import sys

FORMS = {
    'cs': ['Přidána %(count)d nová kniha z adresáře „%(directory)s“.',
           'Přidány %(count)d nové knihy z adresáře „%(directory)s“.',
           'Přidáno %(count)d nových knih z adresáře „%(directory)s“.'],
    'pl': ['Dodano %(count)d nową książkę z katalogu "%(directory)s".',
           'Dodano %(count)d nowe książki z katalogu "%(directory)s".',
           'Dodano %(count)d nowych książek z katalogu "%(directory)s".'],
}


def po_string(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def unquote(lines):
    return ''.join(eval(line) for line in lines)


old_id, new_id = sys.argv[1], sys.argv[2]
for path in sys.argv[3:]:
    lang = path.split('/')[-3]
    text = open(path, encoding='utf-8').read()
    nplurals = int(re.search(r'nplurals=(\d+)', text).group(1))
    # The obsolete entry: '#~ msgid ...' then '#~ msgstr ...' lines.
    blocks = text.split('\n\n')
    old = None
    kept = []
    for block in blocks:
        lines = block.split('\n')
        if any(l.startswith('#~ msgid') for l in lines):
            body = [l[3:] for l in lines if l.startswith('#~ ')]
            i = next(n for n, l in enumerate(body) if l.startswith('msgstr'))
            msgid = unquote([body[0][6:]] + body[1:i])
            if msgid == old_id:
                old = unquote([body[i][7:]] + body[i + 1:])
                continue
        kept.append(block)
    text = '\n\n'.join(kept)
    forms = FORMS.get(lang) or [old] * nplurals
    assert old, (lang, 'no old translation')
    assert len(forms) == nplurals, (lang, len(forms), nplurals)
    entry = re.search(r'msgid_plural %s\n((?:msgstr\[\d+\] ""\n?)+)' % re.escape(po_string(new_id)), text)
    assert entry, (lang, 'no empty plural entry')
    filled = ''.join('msgstr[%d] %s\n' % (n, po_string(form)) for n, form in enumerate(forms))
    text = text[:entry.start(1)] + filled + text[entry.end(1):]
    open(path, 'w', encoding='utf-8').write(text if text.endswith('\n') else text + '\n')
    print(lang, nplurals, 'own forms' if lang in FORMS else 'old text')
