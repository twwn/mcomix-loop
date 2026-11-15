import os, sys, tempfile
from PIL import Image
d = tempfile.mkdtemp()
ims = [Image.new('RGB', (200, 300), c) for c in ('red', 'green')]
p = os.path.join(d, 'photo.jpg')
ims[0].save(p, format='MPO', save_all=True, append_images=ims[1:])
with Image.open(p) as im:
    print(type(im).__name__, im.format, getattr(im, 'n_frames', 1), getattr(im, 'is_animated', None))
from mcomix import image_tools
print('file_animates', image_tools.file_animates(p))
sys.stdout.flush(); os._exit(0)
