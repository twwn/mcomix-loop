"""Does each handler raise ENOSPC when the folder it unpacks into is
full?  Run inside `unshare -Urm` with a small tmpfs at argv[1]:
  unshare -Urm sh -c 'mount -t tmpfs -o size=64k tmpfs <dir> && \
      PYTHONPATH=$PWD exec timeout -k 5 60 python3 <this> <dir>'
Prints one line per handler and way of extracting."""
import errno
import os
import sys

from mcomix.archive import (lha_external, pdf_external, djvu_external,
                            rar, rar_external, sevenzip_external, tar,
                            zip as zip_archive, zip_external)

full = sys.argv[1]
files = os.path.join(os.getcwd(), 'test', 'files', 'archives')
fd = os.open(os.path.join(full, 'filler'), os.O_WRONLY | os.O_CREAT)
try:
    while True:
        os.write(fd, b'x' * 512)
except OSError:
    pass
os.close(fd)
print('free:', os.statvfs(full).f_bavail * os.statvfs(full).f_bsize)

CASES = [
    ('zip', zip_archive.ZipArchive, '01-ZIP-Normal.zip'),
    ('zip external', zip_external.ZipArchive, '01-ZIP-Normal.zip'),
    ('7z external zip', sevenzip_external.SevenZipArchive, '01-ZIP-Normal.zip'),
    ('7z external 7z', sevenzip_external.SevenZipArchive, '04-7Z-Normal.7z'),
    ('7z external solid', sevenzip_external.SevenZipArchive, 'SolidFlat.7z'),
    ('7z external lha', sevenzip_external.SevenZipArchive, 'Flat.lha'),
    ('lha external', lha_external.LhaArchive, 'Flat.lha'),
    ('rar dll', rar.RarArchive, '03-RAR-Normal.rar'),
    ('rar external', rar_external.RarArchive, '03-RAR-Normal.rar'),
    ('tar', tar.TarArchive, '02-TAR-Normal.tar'),
]
for extra in sys.argv[2:]:
    kind = pdf_external.PdfArchive if extra.endswith('.pdf') \
        else djvu_external.DjvuArchive
    CASES.append((kind.__module__.rsplit('.', 1)[1], kind, extra))


def outcome(call):
    try:
        call()
    except OSError as error:
        return 'ENOSPC' if error.errno == errno.ENOSPC else repr(error)
    except Exception as error:
        return 'other: %r' % (error,)
    return 'SILENT'


for label, kind, name in CASES:
    path = name if os.path.isabs(name) else os.path.join(files, name)
    try:
        if hasattr(kind, 'is_available') and not kind.is_available():
            print('%-20s not available' % label)
            continue
        archive = kind(path)
        names = [n for n in archive.list_contents() if not n.endswith('/')]
        big = [n for n in names if '.' in n][0]
        one = outcome(lambda: archive.extract(big, os.path.join(full, 'a')))
        archive.close()
        archive = kind(path)
        archive.list_contents()
        many = outcome(lambda: list(archive.iter_extract(
            names, os.path.join(full, 'b'))))
        archive.close()
        print('%-20s extract=%s iter_extract=%s' % (label, one, many))
    except Exception as error:
        print('%-20s broke: %r' % (label, error))
sys.stdout.flush()
os._exit(0)
