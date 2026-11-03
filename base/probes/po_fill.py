"""Fill new msgstrs in every catalogue from a JSON file.

Usage, from the checkout, after xgettext and `msgmerge -q -N -U`:
    python3 po_fill.py translations.json
where translations.json is {"<lang>": {"<msgid>": "<msgstr>", ...}, ...}
for every directory under mcomix/messages.  Each named msgid must be
present, live (not #~) and untranslated; anything else stops the run
before a file is written.  Afterwards merge again with -o to a temporary
file for gettext's wrapping, and compile each .mo.
"""
import glob
import json
import re
import sys


def joined(lines, key):
    out = []
    on = False
    for line in lines:
        if line.startswith(key + ' '):
            on = True
            out.append(re.findall(r'"(.*)"', line)[0])
            continue
        if on and line.startswith('"'):
            out.append(line[1:-1])
            continue
        on = False
    return ''.join(out)


def main(path):
    table = json.load(open(path, encoding='utf-8'))
    pending = {}
    for po in sorted(glob.glob('mcomix/messages/*/LC_MESSAGES/mcomix.po')):
        lang = po.split('/')[2]
        wanted = table[lang]
        blocks = open(po, encoding='utf-8').read().split('\n\n')
        done = set()
        for i, block in enumerate(blocks):
            if '#~' in block:
                continue
            lines = block.split('\n')
            msgid = joined(lines, 'msgid')
            if msgid in wanted:
                assert joined(lines, 'msgstr') == '', (lang, msgid)
                k = [j for j, x in enumerate(lines) if x.startswith('msgstr')][0]
                blocks[i] = '\n'.join(lines[:k] + [
                    'msgstr ' + json.dumps(wanted[msgid], ensure_ascii=False)])
                done.add(msgid)
        assert done == set(wanted), (lang, set(wanted) - done)
        pending[po] = '\n\n'.join(blocks)
    for po, text in pending.items():
        open(po, 'w', encoding='utf-8').write(text)
    print('filled %d catalogues' % len(pending))


if __name__ == '__main__':
    main(sys.argv[1])
