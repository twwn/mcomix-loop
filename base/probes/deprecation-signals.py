"""Deprecated signals and properties this tree names by string."""
import ast, os, pathlib, xml.etree.ElementTree as ET
NS = {'c': 'http://www.gtk.org/introspection/core/1.0',
      'glib': 'http://www.gtk.org/introspection/glib/1.0'}
FILES = ['Gtk-4.0.gir', 'Gdk-4.0.gir', 'Gsk-4.0.gir', 'GdkPixbuf-2.0.gir',
         'Gio-2.0.gir', 'GLib-2.0.gir', 'GObject-2.0.gir', 'Pango-1.0.gir',
         'PangoCairo-1.0.gir', 'Graphene-1.0.gir', 'Adw-1.gir']
dep_signals, dep_props = {}, {}
for f in FILES:
    path = '/usr/share/gir-1.0/' + f
    if not os.path.exists(path):
        continue
    ns = ET.parse(path).getroot().find('c:namespace', NS)
    prefix = ns.get('name')
    for node in ns:
        cls = node.get('name')
        for child in node:
            tag = child.tag.split('}')[-1]
            if not child.get('deprecated'):
                continue
            if tag == 'signal':
                dep_signals.setdefault(child.get('name'), []).append(
                    '%s.%s (%s)' % (prefix, cls, child.get('deprecated-version') or '?'))
            elif tag == 'property':
                dep_props.setdefault(child.get('name'), []).append(
                    '%s.%s (%s)' % (prefix, cls, child.get('deprecated-version') or '?'))

signal_hits, prop_hits = [], []
for root in (pathlib.Path('mcomix'), pathlib.Path('test')):
    for p in sorted(root.rglob('*.py')):
        tree = ast.parse(p.read_text(), str(p))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            fn = node.func.attr
            args = node.args
            if fn in ('connect', 'connect_after', 'connect_object',
                      'handler_block_by_func', 'emit') and args:
                if isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    name = args[0].value
                    if name in dep_signals:
                        signal_hits.append((str(p), node.lineno, name, dep_signals[name]))
            if fn in ('set_property', 'get_property', 'bind_property') and args:
                if isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    name = args[0].value
                    if name in dep_props:
                        prop_hits.append((str(p), node.lineno, name, dep_props[name]))
        # props.foo / .props access
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) \
               and node.value.attr == 'props':
                name = node.attr.replace('_', '-')
                if name in dep_props:
                    prop_hits.append((str(p), node.lineno, name, dep_props[name]))

print('deprecated signal names connected/emitted: %d' % len(signal_hits))
for p, line, name, owners in sorted(set((a, b, c, tuple(d)) for a, b, c, d in signal_hits)):
    print('  %s:%s  "%s"  -> %s' % (p, line, name, ', '.join(owners)))
print('deprecated property names by string: %d' % len(prop_hits))
for p, line, name, owners in sorted(set((a, b, c, tuple(d)) for a, b, c, d in prop_hits)):
    print('  %s:%s  "%s"  -> %s' % (p, line, name, ', '.join(owners)))
