"""How long MComix' Extractor takes to unpack a whole book, per archive
format and per "max extract threads".

Usage (from the checkout):
    timeout -k 5 600 python3 <this> <workdir> [pages]
Builds <pages> (default 120) noise JPEGs of about 1 MB in <workdir>, packs
them as zip, rar, solid rar, 7z, solid 7z and tar, then unpacks each
with 1, 2, 4 and 8 threads, three runs each, and prints the best time.
No window, no main loop; the constants are pointed into <workdir> so
nothing of the user's is read or written.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

def main():
    global work, prefs, archive_extractor
    work = os.path.abspath(sys.argv[1])
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    os.makedirs(work, exist_ok=True)
    home = os.path.join(work, 'home')
    os.makedirs(home, exist_ok=True)
    os.environ['HOME'] = home
    for var in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME'):
        os.environ[var] = os.path.join(home, var.lower())
    sys.path.insert(0, os.getcwd())

    from mcomix import constants  # noqa: E402
    constants.HOME_DIR = home
    constants.CONFIG_DIR = os.path.join(home, 'config')
    constants.DATA_DIR = os.path.join(home, 'data')
    constants.PREFERENCE_PATH = os.path.join(constants.CONFIG_DIR, 'preferences.conf')
    from mcomix.preferences import prefs  # noqa: E402
    from mcomix import archive_extractor  # noqa: E402
    # FORCE=zip,tar: let those handlers claim they can be read by several
    # threads at once, to measure what that would bring.
    from mcomix.archive import zip as zip_handler, tar as tar_handler  # noqa: E402
    for forced in filter(None, os.environ.get('FORCE', '').split(',')):
        {'zip': zip_handler.ZipArchive, 'tar': tar_handler.TarArchive}[
            forced].support_concurrent_extractions = True
    ONLY = set(filter(None, os.environ.get('ONLY', '').split(',')))

    src = os.path.join(work, 'pages')
    if not os.path.isdir(src):
        from PIL import Image
        os.makedirs(src)
        for n in range(pages):
            Image.effect_noise((900, 1300), 60).convert('RGB').save(
                os.path.join(src, '%03d.jpg' % n), quality=92)
    names = sorted(os.listdir(src))
    books = {
        'zip': ['zip', '-q', '-r'],
        'rar': ['rar', 'a', '-idq', '-m3'],
        'rar-solid': ['rar', 'a', '-idq', '-m3', '-s'],
        '7z': ['7z', 'a', '-bd', '-bso0', '-ms=off'],
        '7z-solid': ['7z', 'a', '-bd', '-bso0', '-ms=on'],
        'tar': ['tar', '-cf'],
    }
    ext = {'zip': 'zip', 'rar': 'rar', 'rar-solid': 'rar', '7z': '7z',
           '7z-solid': '7z', 'tar': 'tar'}
    paths = {}
    for kind, command in books.items():
        path = os.path.join(work, '%s.%s' % (kind, ext[kind]))
        if not os.path.exists(path):
            subprocess.run(command + [path] + names, cwd=src, check=True)
        paths[kind] = path
    pdf = os.path.join(work, 'pdf.pdf')
    if not os.path.exists(pdf):
        import pymupdf
        document = pymupdf.open()
        for name in names:
            page = document.new_page(width=900, height=1300)
            page.insert_image(page.rect, filename=os.path.join(src, name))
        document.save(pdf)
        document.close()
    paths['pdf'] = pdf
    print('pages', len(names), 'MB', round(sum(os.path.getsize(os.path.join(src, n)) for n in names) / 1e6))


    def unpack(path, threads):
        prefs['max extract threads'] = threads
        dst = tempfile.mkdtemp(dir=work)
        extractor = archive_extractor.Extractor()
        start = time.perf_counter()
        condition = extractor.setup(path, dst)
        with condition:
            while extractor.get_files() is None:
                condition.wait(0.01)
        files = extractor.get_files()
        extractor.set_files(files)
        extractor.extract()
        with condition:
            while not all(extractor.is_ready(f) for f in files):
                condition.wait(0.05)
        took = time.perf_counter() - start
        inner = getattr(extractor._archive, '_archive_list', [extractor._archive])[0]
        handler = type(inner).__module__.split('.')[-1] + ('+' if extractor._archive.support_concurrent_extractions else '-')
        extractor.close()
        shutil.rmtree(dst)
        return took, handler


    for kind, path in paths.items():
        if ONLY and kind not in ONLY:
            continue
        row = []
        handler = ''
        for threads in (1, 2, 4, 8):
            best = min(unpack(path, threads)[0] for _run in range(3))
            handler = unpack(path, threads)[1]
            row.append('%d:%.2fs' % (threads, best))
        print('%-10s %-16s' % (kind, handler), ' '.join(row), flush=True)
    sys.stdout.flush()
    os._exit(0)



if __name__ == '__main__':
    main()
