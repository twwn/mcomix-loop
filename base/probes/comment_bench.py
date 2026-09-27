"""How i18n.to_unicode() reads eleven comment texts, per chardet."""
import sys, locale
sys.path.insert(0, '/tmp/mcomix-git')
import chardet
from mcomix import i18n
TEXTS = {
 'de': "Übersetzung und Lettering von der Gruppe. Dieser Band enthält die Kapitel 1 bis 12. Größe und Qualität der Scans wurden verbessert. Viel Spaß!",
 'fr': "Ce volume réunit les épisodes parus entre 1998 et 2001. Traduction française et lettrage : l'équipe. Merci à tous, à bientôt !",
 'es': "Traducción al español y corrección: el equipo. Este tomo reúne los capítulos publicados. ¡Gracias por leer, hasta el próximo número!",
 'ru': "Перевод и оформление: команда. Этот том содержит главы с первой по двенадцатую. Приятного чтения!",
 'ja': "翻訳とレタリング：チーム。この巻には第1話から第12話までを収録。お楽しみください。",
}
CASES = [('de', 'cp1252'), ('fr', 'cp1252'), ('es', 'cp1252'), ('de', 'cp437'), ('fr', 'cp850'), ('es', 'cp850'),
         ('ru', 'cp1251'), ('ru', 'cp866'), ('ja', 'cp932'), ('de', 'utf-8'), ('fr', 'latin-1')]

right = 0
for lang, enc in CASES:
    data = TEXTS[lang].encode(enc)
    ok = i18n.to_unicode(data) == TEXTS[lang]
    right += ok
    print('%s %-7s %s' % (lang, enc, 'right' if ok else 'WRONG'))
print('chardet', chardet.__version__, 'right', right, 'of', len(CASES))
