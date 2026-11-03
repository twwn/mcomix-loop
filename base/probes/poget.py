"""Print each catalogue's msgstr for the msgids given (live or #~)."""
import glob, re, sys
ids = sys.argv[1:]
for po in sorted(glob.glob('mcomix/messages/*/LC_MESSAGES/mcomix.po')):
    lang = po.split('/')[2]
    text = open(po, encoding='utf-8').read()
    got = {}
    for block in text.split('\n\n'):
        lines = [l[3:] if l.startswith('#~ ') else l for l in block.split('\n')]
        mid, mstr, cur = [], [], None
        for l in lines:
            if l.startswith('msgid '): cur = mid; l = l[6:]
            elif l.startswith('msgstr '): cur = mstr; l = l[7:]
            elif not l.startswith('"'): cur = None if not l.startswith('"') else cur; continue
            if cur is not None: cur.append(l[1:-1])
        got.setdefault(''.join(mid), ''.join(mstr))
    print(lang, ' | '.join('%s' % got.get(i, '?') for i in ids))
