"""Every mapped Gtk.Picture on screen, and how many times over it draws
its paintable (x > 1 is a picture enlarged past its own size).

Use from inside a test, after the widgets are allocated:
    from <STATE>/probes/picture_upscale.py import report   (copy it in)
    report('tag')
Define the probe test class on its own (subclass MComixTest and copy the
setUp you need); do NOT import another module's TestCase into the probe
module, or pytest collects and runs every test that class has.
"""
from gi.repository import Gtk


def _walk(widget):
    yield widget
    child = widget.get_first_child()
    while child is not None:
        yield from _walk(child)
        child = child.get_next_sibling()


def report(tag):
    for top in Gtk.Window.list_toplevels():
        for w in _walk(top):
            if not isinstance(w, Gtk.Picture) or not w.get_mapped():
                continue
            p = w.get_paintable()
            if p is None:
                continue
            iw, ih = p.get_intrinsic_width(), p.get_intrinsic_height()
            aw, ah = w.get_width(), w.get_height()
            if iw <= 0 or ih <= 0:
                continue
            fit = w.get_content_fit()
            scale = min(aw / iw, ah / ih)
            if fit == Gtk.ContentFit.SCALE_DOWN:
                scale = min(scale, 1.0)
            print('PROBE %s %s in %s: paintable %dx%d, widget %dx%d, %s, x%.2f%s'
                  % (tag, type(w).__name__, type(top).__name__, iw, ih,
                     aw, ah, fit.value_nick, scale,
                     ' UPSCALED' if scale > 1.01 else ''), flush=True)
