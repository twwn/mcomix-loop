import sys, math
sys.path.insert(0, '.')  # run from the checkout
import gi
gi.require_version('Gtk', '4.0'); gi.require_version('Gdk', '4.0'); gi.require_version('Gsk', '4.0')
from gi.repository import Gdk, Gsk, Gtk, Graphene
from PIL import Image
Gtk.init()
row = bytes(round(127.5 + 100 * math.sin(2 * math.pi * x / 3.3)) for x in range(600))
im = Image.frombytes('L', (600, 1), row).resize((600, 40)).convert('RGB')
tex = Gdk.MemoryTexture.new(600, 40, Gdk.MemoryFormat.R8G8B8, __import__('gi').repository.GLib.Bytes.new(im.tobytes()), 1800)
for rname, R in (('cairo', Gsk.CairoRenderer), ('vulkan', getattr(Gsk, 'VulkanRenderer', None)), ('gl', getattr(Gsk, 'GLRenderer', None))):
    if R is None: continue
    r = R()
    try:
        r.realize_for_display(Gdk.Display.get_default())
    except Exception as e:
        print(rname, 'no', e); continue
    for f in (Gsk.ScalingFilter.LINEAR, Gsk.ScalingFilter.NEAREST, Gsk.ScalingFilter.TRILINEAR):
        s = Gtk.Snapshot()
        s.append_scaled_texture(tex, f, Graphene.Rect().init(0, 0, 252, 17))
        node = s.to_node()
        out = r.render_texture(node, Graphene.Rect().init(0, 0, 252, 17))
        d = Gdk.TextureDownloader.new(out); d.set_format(Gdk.MemoryFormat.R8G8B8)
        data, stride = d.download_bytes(); data = data.get_data()
        vals = [data[8 * stride + 3 * x] for x in range(8, 244)]
        print(rname, f.value_nick, type(node).__name__, (max(vals) - min(vals)) / 2)
    s = Gtk.Snapshot()
    tex.snapshot(s, 252, 17)
    node = s.to_node()
    out = r.render_texture(node, Graphene.Rect().init(0, 0, 252, 17))
    d = Gdk.TextureDownloader.new(out); d.set_format(Gdk.MemoryFormat.R8G8B8)
    data, stride = d.download_bytes(); data = data.get_data()
    vals = [data[8 * stride + 3 * x] for x in range(8, 244)]
    print(rname, 'texture.snapshot', type(node).__name__, (max(vals) - min(vals)) / 2)
    r.unrealize()
