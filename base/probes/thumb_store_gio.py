"""Does GIO accept the archive thumbnails MComix writes into the shared store?"""
import os, sys, zipfile
sys.path.insert(0, '/tmp/mcomix-git')
from test import MComixTest, get_testfile_path
from gi.repository import Gio
from mcomix import thumbnail_tools


class Probe(MComixTest):
    def test_probe(self):
        cache = os.environ['PROBE_CACHE']
        for name in ('book.cbz', 'page (1).jpg'):
            src = os.path.join(self.tmp_dir, name)
            if os.path.exists(src): os.remove(src)
        for name in ('book.cbz', 'page (1).jpg'):
            src = os.path.join(self.tmp_dir, name)
            if name.endswith('.cbz'):
                with zipfile.ZipFile(src, 'w') as z:
                    z.write(get_testfile_path('images', 'landscape-exif-270-rotation.jpg'), '01.jpg')
            else:
                import shutil
                shutil.copy(get_testfile_path('images', 'landscape-exif-270-rotation.jpg'), src)
            t = thumbnail_tools.Thumbnailer(dst_dir=os.path.join(cache, 'thumbnails', 'normal'),
                                            store_on_disk=True, archive_support=True, size=(128, 128))
            t.thumbnail(src)
            path = t._path_to_thumbpath(src)
            info = Gio.File.new_for_path(src).query_info('thumbnail::*', 0, None)
            from PIL import Image
            with Image.open(path) as im:
                meta = {k: v for k, v in im.info.items() if k.startswith('Thumb::')}
            print('\nPROBE', name, 'stored', os.path.exists(path),
                  'gio path', info.get_attribute_byte_string('thumbnail::path'),
                  'valid', info.get_attribute_boolean('thumbnail::is-valid'), meta)
