"""Screenshots of the status bar in each colour scheme, and the colour
its separators and text are drawn in.  SHOT_OUT=<prefix>; ALPHAS=0.5,0.35
tries other strengths of the separator rule (theme._STATUS_SEPARATORS)."""
import os, subprocess
from gi.repository import Gsk, Gtk
from test import MComixTest, wait_for
from mcomix import status, theme
from mcomix.preferences import prefs

OUT = os.environ['SHOT_OUT']
ALPHAS = os.environ.get('ALPHAS', '0.5').split(',')


def colours(node, found):
    if node is None:
        return found
    if isinstance(node, Gsk.ColorNode):
        found.append(node.get_color().to_string())
    for getter in ('get_child',):
        if hasattr(node, getter):
            colours(getattr(node, getter)(), found)
    if hasattr(node, 'get_n_children'):
        for index in range(node.get_n_children()):
            colours(node.get_child(index), found)
    return found


class Shot(MComixTest):
    def test_shot(self):
        prefs['statusbar fields'] = 127
        rows = []
        for scheme in (theme.LIGHT, theme.DARK, theme.BLACK):
            prefs['colour scheme'] = scheme
            theme.follow_theme()
            for alpha in ['theme'] + ALPHAS:
                provider = None
                if alpha != 'theme':
                    provider = Gtk.CssProvider()
                    provider.load_from_string('separator.x-probe { background-color: alpha(currentColor, %s); }' % alpha)
                    Gtk.StyleContext.add_provider_for_display(
                        Gtk.Window().get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
                bar = status.Statusbar()
                for separator in bar._separators.values():
                    separator.remove_css_class(theme.STATUS_SEPARATOR_CLASS)
                    if alpha != 'theme':
                        separator.add_css_class('x-probe')
                window = Gtk.Window()
                window.set_default_size(1100, -1)
                window.set_decorated(False)
                column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                column.append(bar)
                filler = Gtk.Label(label='page area'); filler.set_vexpand(True); column.append(filler)
                window.set_child(column)
                window.present()
                bar.set_root('Pepper & Carrot.cbz')
                bar.set_page_number([2, 3], 120)
                bar.set_file_number(3, 12)
                bar.set_filename('page-002.jpg · page-003.jpg')
                bar.set_filesize('870.4 KiB · 1.2 MiB')
                bar.set_resolution(((1200, 1800, 0.453, False), (1200, 1800, 0.453, False)))
                bar.set_date('2024-05-06, 07:08:09')
                bar.update()
                wait_for(lambda: False, seconds=1)
                separator = next(s for s in bar._separators.values() if s.get_visible())
                snap = Gtk.Snapshot()
                Gtk.WidgetPaintable(widget=separator).snapshot(snap, separator.get_width(), separator.get_height())
                print('COLOURS', scheme, alpha, 'separator', colours(snap.to_node(), []), 'text', bar._fields[1].get_color().to_string())
                path = '%s-%s-%s.png' % (OUT, scheme, alpha)
                subprocess.run(['import', '-window', 'root', '-crop', '1100x26+0+0', path], check=True)
                rows.append(path)
                window.destroy()
                if provider is not None:
                    Gtk.StyleContext.remove_provider_for_display(Gtk.Window().get_display(), provider)
        subprocess.run(['magick'] + rows + ['-append', OUT + '-all.png'], check=True)
        prefs['colour scheme'] = theme.SYSTEM
        theme.apply_colour_scheme()
