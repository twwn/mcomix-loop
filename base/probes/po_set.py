"""Set msgstrs in every catalogue from a JSON file, translated or not.

Like po_fill.py, but an msgid already translated is overwritten: for
labels whose translation is replaced on purpose (another access key, a
revived obsolete entry).  Each msgid must be live in the catalogue.
"""
import glob, json, sys


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main(path):
    table = json.load(open(path, encoding='utf-8'))
    for po in sorted(glob.glob('mcomix/messages/*/LC_MESSAGES/mcomix.po')):
        lang = po.split('/')[2]
        wanted = dict(table.get(lang, {}))
        blocks = open(po, encoding='utf-8').read().split('\n\n')
        for i, block in enumerate(blocks):
            if '#~' in block:
                continue
            lines = block.split('\n')
            try:
                a = next(n for n, l in enumerate(lines) if l.startswith('msgid '))
                b = next(n for n, l in enumerate(lines) if l.startswith('msgstr '))
            except StopIteration:
                continue
            if any(l.startswith('msgid_plural') for l in lines):
                continue
            msgid = ''.join(l[l.index('"') + 1:-1] for l in lines[a:b])
            if msgid in wanted:
                lines[b:] = ['msgstr "%s"' % esc(wanted.pop(msgid))]
                lines = [l for l in lines if l != '#, fuzzy']
                blocks[i] = '\n'.join(lines)
        assert not wanted, (lang, sorted(wanted))
        open(po, 'w', encoding='utf-8').write('\n\n'.join(blocks))


main(sys.argv[1])
