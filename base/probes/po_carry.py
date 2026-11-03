"""Carry translations from old msgids to new ones, plural entries too.

Usage, from the checkout, BEFORE regenerating the template:
    python3 po_carry.py save <map.json> <out.json>
where map.json is {"<old msgid>": "<new msgid>", ...} (msgids as the .po
escapes them; for a plural entry, the singular msgid) - it reads every
catalogue's msgstr lines for each old msgid. Then regenerate and merge
(catalogue_regen.sh), and run
    python3 po_carry.py apply <out.json>
which writes those msgstr lines under each new msgid, and finish with
catalogue_finish.sh. Use it only where the new English says what every
translation says already.
"""
import glob, json, sys


def blocks(po):
    return open(po, encoding='utf-8').read().split('\n\n')


def msgid_of(lines):
    out, on = [], False
    for l in lines:
        if l.startswith('msgid '):
            on = True
            out.append(l[l.index('"') + 1:-1])
        elif on and l.startswith('"'):
            out.append(l[1:-1])
        else:
            on = False
    return ''.join(out)


def strs(lines):
    i = next(n for n, l in enumerate(lines) if l.startswith('msgstr'))
    return lines[i:]


mode = sys.argv[1]
if mode == 'save':
    mapping = json.load(open(sys.argv[2], encoding='utf-8'))
    out = {}
    for po in sorted(glob.glob('mcomix/messages/*/LC_MESSAGES/mcomix.po')):
        lang = po.split('/')[2]
        found = {}
        for b in blocks(po):
            if '#~' in b:
                continue
            lines = b.split('\n')
            if not any(l.startswith('msgid ') for l in lines):
                continue
            mid = msgid_of(lines)
            if mid in mapping:
                found[mapping[mid]] = strs(lines)
        missing = set(mapping.values()) - set(found)
        assert not missing, (lang, missing)
        out[lang] = found
    json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False)
else:
    table = json.load(open(sys.argv[2], encoding='utf-8'))
    for po in sorted(glob.glob('mcomix/messages/*/LC_MESSAGES/mcomix.po')):
        lang = po.split('/')[2]
        wanted = dict(table[lang])
        bs = blocks(po)
        for n, b in enumerate(bs):
            if '#~' in b:
                continue
            lines = b.split('\n')
            if not any(l.startswith('msgid ') for l in lines):
                continue
            mid = msgid_of(lines)
            if mid in wanted:
                i = next(k for k, l in enumerate(lines) if l.startswith('msgstr'))
                lines = [l for l in lines[:i] if l != '#, fuzzy'] + wanted.pop(mid)
                bs[n] = '\n'.join(lines)
        assert not wanted, (lang, sorted(wanted))
        open(po, 'w', encoding='utf-8').write('\n\n'.join(bs))
