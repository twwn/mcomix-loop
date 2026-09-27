"""How long MComix' archive writers take to write a whole book, and how
many cores they keep busy (CPU time over wall time; children counted).

Usage (from the checkout):
    timeout -k 5 600 python3 <this> <pages dir> <workdir>
Writes every file of <pages dir> with each writer make_writer() offers:
zip, tar, tar.gz, tar.bz2, tar.xz, 7z and rar.  No window, no main loop.
"""
import os
import resource
import sys
import time


def cpu():
    own = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + kids.ru_utime + kids.ru_stime


def main():
    pages, work = map(os.path.abspath, sys.argv[1:3])
    os.makedirs(work, exist_ok=True)
    sys.path.insert(0, os.getcwd())
    from mcomix import archive_packer, constants
    names = sorted(os.listdir(pages))
    size = sum(os.path.getsize(os.path.join(pages, n)) for n in names)
    print('pages %d, %.1f MB' % (len(names), size / 1e6))
    only = set(filter(None, os.environ.get('ONLY', '').split(',')))
    for label, name, kind in (
            ('zip', 'b.cbz', constants.ZIP),
            ('tar', 'b.tar', constants.TAR),
            ('tar.gz', 'b.tar.gz', constants.GZIP),
            ('tar.bz2', 'b.tar.bz2', constants.BZIP2),
            ('tar.xz', 'b.tar.xz', constants.TAR),
            ('7z', 'b.cb7', constants.SEVENZIP),
            ('rar', 'b.cbr', constants.RAR)):
        if only and label not in only:
            continue
        target = os.path.join(work, name)
        if os.path.exists(target):
            os.unlink(target)
        start, used = time.perf_counter(), cpu()
        writer = archive_packer.make_writer(target, kind)
        for n in names:
            writer.add(os.path.join(pages, n), n)
        writer.close()
        wall, used = time.perf_counter() - start, cpu() - used
        print('%-8s %6.2f s wall %6.2f s cpu  x%.1f  %.1f MB' % (
            label, wall, used, used / wall, os.path.getsize(target) / 1e6),
            flush=True)
    os._exit(0)


if __name__ == '__main__':
    main()
