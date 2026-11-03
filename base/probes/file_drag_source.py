"""A window whose label drags out one file, as a file manager does: as a
Gdk.FileList and as text.  Prints READY and its X window id."""
import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkX11', '4.0')
from gi.repository import Gdk, Gio, GLib, GObject, Gtk, GdkX11  # noqa: E402

path = sys.argv[1]
loop = GLib.MainLoop()
window = Gtk.Window(title='file-drag-source')
window.set_default_size(200, 200)
label = Gtk.Label(label='drag me')
label.set_hexpand(True)
label.set_vexpand(True)
source = Gtk.DragSource()
source.set_actions(Gdk.DragAction.COPY | Gdk.DragAction.MOVE)


def prepare(source, x, y):
    files = Gdk.FileList.new_from_list([Gio.File.new_for_path(path)])
    value = GObject.Value(Gdk.FileList, files)
    return Gdk.ContentProvider.new_union([
        Gdk.ContentProvider.new_for_value(value),
        Gdk.ContentProvider.new_for_value(path)])


source.connect('prepare', prepare)
source.connect('drag-end', lambda *args: print('DRAG-END', flush=True))
source.connect('drag-cancel', lambda s, d, reason: print('DRAG-CANCEL', reason, flush=True) or False)
label.add_controller(source)
window.set_child(label)
window.present()


def ready():
    surface = window.get_surface()
    if surface is None or not label.get_mapped():
        return True
    print('READY', surface.get_xid(), flush=True)
    return False


GLib.timeout_add(50, ready)
GLib.timeout_add_seconds(20, loop.quit)
loop.run()
