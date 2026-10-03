"""How name_encoding() reads fifteen sets of page names, per chardet."""
import os, sys
sys.path.insert(0, os.environ.get('TREE') or os.getcwd())   # the checkout this runs from, or TREE
import chardet
from mcomix.archive import archive_base
SETS = [
 (['Übersicht.jpg'], 'cp1252'), (['Größe.png'], 'cp1252'), (['Été/01.jpg', 'Été/02.jpg'], 'cp1252'),
 (['Café/Page 1.jpg', 'Café/Page 2.jpg'], 'cp1252'),
 (['Обложка.jpg'], 'cp1251'), (['Глава %d/%03d.jpg' % (c, i) for c in (1, 2) for i in range(1, 15)], 'cp1251'),
 (['封面.jpg'], 'gbk'), (['表紙.jpg', '第01話/001.jpg', '第01話/002.jpg', 'あとがき.png'], 'cp932'),
 (['第1巻/表紙.jpg'] + ['第1巻/%03d.jpg' % i for i in range(1, 30)], 'cp932'), (['표지.jpg'], 'cp949'),
 (['ÄRGER.JPG'], 'cp437'), (['KAPITEL Ü/SEITE01.JPG'], 'cp437'), (['CAFÉ/PAGE01.JPG', 'CAFÉ/PAGE02.JPG'], 'cp850'),
 (['Ñandú/001.jpg', 'Ñandú/002.jpg', 'Ñandú/003.jpg'], 'cp850'), (['Mañana/001.jpg'], 'cp437'),
 (['Ärger/Seite 01.jpg', 'Ärger/Seite 02.jpg', 'Übersicht.jpg', 'Größe.jpg'], 'cp437'),
]
right = 0
for names, enc in SETS:
    raw = [n.encode(enc) for n in names]
    got = archive_base.name_encoding(raw, 'cp437')
    ok = [r.decode(got) for r in raw] == names
    right += ok
    print('%-7s %-22s -> %-12s %s' % (enc, names[0][:22], got, 'right' if ok else 'WRONG ' + raw[0].decode(got)))
print('chardet', chardet.__version__, 'right', right, 'of', len(SETS))
