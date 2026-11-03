"""Build the slow books test_zz_cover_block.py and test_zz_cover_typing.py read: mk_slow_covers.py <empty dir>.  About 50 s and 900 MB."""
import os, shutil, subprocess, sys, zipfile
from PIL import Image
d = os.path.abspath(sys.argv[1])
pages = os.path.join(d, 'pages'); os.makedirs(pages)
# Six bits a byte: LZMA has to decode these, as it does a JPEG's bytes. Plain noise goes in stored chunks and comes out in 80 ms.
table = bytes(i & 0x3f for i in range(256))
def noise(path, w, h):
    Image.frombytes('RGB', (w, h), os.urandom(w * h * 3).translate(table)).save(path, compress_level=0)
for n in range(1, 101):
    noise(os.path.join(pages, 'page%03d.png' % n), 1200, 1200)
noise(os.path.join(pages, 'zz-cover.png'), 1200, 1200)
names = sorted(os.listdir(pages))
# -ms=1g for one block: -ms=on -mx=1 made 7, and only the last had to be decoded.
pack = ['7z', 'a', '-t7z', '-ms=1g', '-mx=5', '-md=64m', '-bd', '-bso0']
subprocess.run(pack + [os.path.join(d, 'solid-lzma-400MB-cover-last.7z')] + names, cwd=pages, check=True)
subprocess.run(pack + [os.path.join(d, 'solid-lzma-400MB-cover-first.7z')] + [n for n in names if n.startswith('page')], cwd=pages, check=True)
huge = os.path.join(pages, 'huge.png')
Image.frombytes('RGB', (6000, 9000), os.urandom(6000 * 9000 * 3)).save(huge, compress_level=0)
with zipfile.ZipFile(os.path.join(d, 'zip-6000x9000-png.cbz'), 'w') as z:
    z.write(huge, 'huge.png')
shutil.rmtree(pages)
