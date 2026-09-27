"""Fill the plural forms of "%d page" and "%d comment" in every catalogue."""
import re
import sys

T = {
    'ca': (['%d pàgina', '%d pàgines'], ['%d comentari', '%d comentaris']),
    'cs': (['%d stránka', '%d stránky', '%d stránek'],
           ['%d komentář', '%d komentáře', '%d komentářů']),
    'de': (['%d Seite', '%d Seiten'], ['%d Kommentar', '%d Kommentare']),
    'el': (['%d σελίδα', '%d σελίδες'], ['%d σχόλιο', '%d σχόλια']),
    'es': (['%d página', '%d páginas'], ['%d comentario', '%d comentarios']),
    'fa': (['%d صفحه', '%d صفحه'], ['%d توضیح', '%d توضیح']),
    'fr': (['%d page', '%d pages'], ['%d commentaire', '%d commentaires']),
    'gl': (['%d páxina', '%d páxinas'], ['%d comentario', '%d comentarios']),
    'he': (['%d עמוד', '%d עמודים'], ['%d הערה', '%d הערות']),
    'hr': (['%d stranica', '%d stranice', '%d stranica'],
           ['%d komentar', '%d komentara', '%d komentara']),
    'hu': (['%d oldal', '%d oldal'], ['%d megjegyzés', '%d megjegyzés']),
    'id': (['%d halaman'], ['%d komentar']),
    'it': (['%d pagina', '%d pagine'], ['%d commento', '%d commenti']),
    'ja': (['%d ページ'], ['%d コメント']),
    'ko': (['%d 페이지'], ['%d 주석']),
    'lt': (['%d puslapis', '%d puslapiai', '%d puslapių'],
           ['%d komentaras', '%d komentarai', '%d komentarų']),
    'nl': (["%d pagina", "%d pagina's"], ['%d commentaar', '%d commentaren']),
    'pl': (['%d strona', '%d strony', '%d stron'],
           ['%d komentarz', '%d komentarze', '%d komentarzy']),
    'pt_BR': (['%d página', '%d páginas'], ['%d comentário', '%d comentários']),
    'ru': (['%d страница', '%d страницы', '%d страниц'],
           ['%d комментарий', '%d комментария', '%d комментариев']),
    'sv': (['%d sida', '%d sidor'], ['%d kommentar', '%d kommentarer']),
    'uk': (['%d сторінка', '%d сторінки', '%d сторінок'],
           ['%d коментар', '%d коментарі', '%d коментарів']),
    'zh_CN': (['共%d页'], ['%d 个注释']),
    'zh_TW': (['%d 頁'], ['%d 個註解']),
}

for lang, (page, comment) in T.items():
    path = 'mcomix/messages/%s/LC_MESSAGES/mcomix.po' % lang
    text = open(path, encoding='utf-8').read()
    nplurals = int(re.search(r'nplurals=(\d+)', text).group(1))
    for (singular, plural), forms in ((('%d page', '%d pages'), page),
                                      (('%d comment', '%d comments'), comment)):
        if len(forms) != nplurals:
            sys.exit('%s: %d forms for nplurals=%d' % (lang, len(forms), nplurals))
        empty = 'msgid "%s"\nmsgid_plural "%s"\n' % (singular, plural) + ''.join(
            'msgstr[%d] ""\n' % i for i in range(nplurals))
        if text.count(empty) != 1:
            sys.exit('%s: %r not found empty once' % (lang, singular))
        filled = 'msgid "%s"\nmsgid_plural "%s"\n' % (singular, plural) + ''.join(
            'msgstr[%d] "%s"\n' % (i, form) for i, form in enumerate(forms))
        text = text.replace(empty, filled)
    open(path, 'w', encoding='utf-8').write(text)
print('filled', len(T))
