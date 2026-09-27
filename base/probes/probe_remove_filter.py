"""Bare GTK: does removing the current filter of a Gtk.FileChooserWidget
leave the Python wrapper pointing at freed memory?  ORDER=first sets
another filter current before removing."""
import gc, os, sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import warnings
warnings.simplefilter('ignore')
Gtk.init()

def pump():
    ctx = GLib.MainContext.default()
    while ctx.pending():
        ctx.iteration(False)

keep = {}
chooser = Gtk.FileChooserWidget()
window = Gtk.Window()
window.set_child(chooser)
a = Gtk.FileFilter(); a.set_name('All files'); a.add_pattern('*')
b = Gtk.FileFilter(); b.set_name('Archives'); b.add_pattern('*.zip')
chooser.add_filter(a); chooser.add_filter(b)
keep[a] = 1; keep[b] = 1
print('current before:', chooser.get_filter().get_name(), flush=True)
if os.environ.get('ORDER') == 'first':
    chooser.set_filter(b)
chooser.remove_filter(a)
cur = chooser.get_filter()
print('current after:', cur.get_name() if cur else None, flush=True)
window.present(); pump()
window.destroy(); pump()
del cur
print('refcount a', a.__grefcount__, flush=True)
gc.collect()
print('collected', flush=True)
del window, chooser
gc.collect()
print('collected 2; a =', a.get_name(), flush=True)
os._exit(0)
