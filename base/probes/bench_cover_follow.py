"""How long a library cover takes to draw from its archive, against
moving the stored one to the name of the book's new path."""
import os, shutil, sys, tempfile, time
from mcomix import constants, thumbnail_tools
tmp = tempfile.mkdtemp(prefix='coverbench.', dir=sys.argv[1])
store = os.path.join(tmp, 'covers')
size = (constants.MAX_LIBRARY_COVER_SIZE,) * 2
books = []
for n, name in enumerate(('01-ZIP-Normal.zip', '03-RAR-Normal.rar', '04-7Z-Normal.7z') * 10):
    path = os.path.join(tmp, 'old', '%02d-%s' % (n, name))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy2(os.path.join('test', 'files', 'archives', name), path)
    books.append(path)
def covers():
    return thumbnail_tools.Thumbnailer(dst_dir=store, store_on_disk=True, archive_support=True, size=size, cover_orientation_required=True)
t = time.perf_counter()
made = [covers().thumbnail(book) for book in books]
drawn = time.perf_counter() - t
assert all(made), made
os.rename(os.path.join(tmp, 'old'), os.path.join(tmp, 'new'))
moved = [book.replace(os.sep + 'old' + os.sep, os.sep + 'new' + os.sep) for book in books]
t = time.perf_counter()
for book, target in zip(books, moved):
    covers().follow(book, target)
followed = time.perf_counter() - t
t = time.perf_counter()
again = [covers()._stored_thumbnail(book) for book in moved]
read = time.perf_counter() - t
assert all(again)
print('%d books: drawn %.1f ms each, followed %.3f ms each, read back %.1f ms each; %d files in the store'
      % (len(books), drawn * 1000 / len(books), followed * 1000 / len(books), read * 1000 / len(books), len(os.listdir(store))))
shutil.rmtree(tmp)
sys.stdout.flush(); os._exit(0)
