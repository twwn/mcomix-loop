"""Every deprecated GI symbol this tree names, read out of the .gir files.

Usage, from the checkout: python3 deprecation-sweep.py [<dir>...]
(default: mcomix and test).

The runtime census (gates.sh deprecations) only sees what the suite
executes, and only warns for deprecated functions and methods; a
deprecated class, property or signal makes no noise at all.  This reads
the GIR XML instead, once, and walks each file's syntax tree once, for:
types, namespace functions and methods, properties set as constructor
keywords, instance method calls whose name is deprecated somewhere,
signal names connected or emitted, and property names used as strings or
through .props.
"""
import ast
import os
import pathlib
import sys
import xml.etree.ElementTree as ET

GIR_DIR = '/usr/share/gir-1.0'
NS = {'c': 'http://www.gtk.org/introspection/core/1.0',
      'glib': 'http://www.gtk.org/introspection/glib/1.0'}

FILES = {
    'Gtk': 'Gtk-4.0.gir',
    'Gdk': 'Gdk-4.0.gir',
    'Gsk': 'Gsk-4.0.gir',
    'GdkPixbuf': 'GdkPixbuf-2.0.gir',
    'Gio': 'Gio-2.0.gir',
    'GLib': 'GLib-2.0.gir',
    'GObject': 'GObject-2.0.gir',
    'Pango': 'Pango-1.0.gir',
    'PangoCairo': 'PangoCairo-1.0.gir',
    'Graphene': 'Graphene-1.0.gir',
    'Adw': 'Adw-1.gir',
}

TYPE_TAGS = ('class', 'interface', 'record', 'enumeration', 'bitfield',
             'callback', 'union', 'alias')
MEMBER_TAGS = ('method', 'function', 'constructor', 'virtual-method')
SIGNAL_CALLS = ('connect', 'connect_after', 'connect_object',
                'handler_block_by_func', 'emit')
PROPERTY_CALLS = ('set_property', 'get_property', 'bind_property')


def strip(tag):
    return tag.split('}')[-1]


dep_types, dep_members, dep_props = {}, {}, {}
by_signal, by_property = {}, {}     # bare name -> ['Namespace.Class (version)']
for namespace, filename in FILES.items():
    path = os.path.join(GIR_DIR, filename)
    if not os.path.exists(path):
        continue
    for node in ET.parse(path).getroot().find('c:namespace', NS):
        tag = strip(node.tag)
        name = node.get('name')
        if tag in MEMBER_TAGS:
            # A namespace level function.
            if node.get('deprecated'):
                dep_members['%s.%s' % (namespace, name)] = node.get('deprecated-version') or '?'
            continue
        if tag not in TYPE_TAGS:
            continue
        if node.get('deprecated'):
            dep_types['%s.%s' % (namespace, name)] = node.get('deprecated-version') or '?'
        for child in node:
            if not child.get('deprecated'):
                continue
            ctag = strip(child.tag)
            cname = child.get('name') or ''
            since = child.get('deprecated-version') or '?'
            owner = '%s.%s (%s)' % (namespace, name, since)
            if ctag in MEMBER_TAGS:
                dep_members['%s.%s.%s' % (namespace, name, cname.replace('-', '_'))] = since
            elif ctag == 'property':
                dep_props['%s.%s:%s' % (namespace, name, cname)] = since
                by_property.setdefault(cname, []).append(owner)
            elif ctag == 'signal':
                by_signal.setdefault(cname, []).append(owner)

# Every deprecated method name, whatever class it is on, for the
# instance-call heuristic.
by_method = {}
for key, since in dep_members.items():
    by_method.setdefault(key.rsplit('.', 1)[1], []).append((key, since))


def dotted(node):
    """'Gtk.Foo.bar' for an attribute chain rooted at a Name."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return '.'.join(reversed(parts))


def first_string(node):
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


hits_type, hits_member, hits_prop, hits_maybe, hits_signal, hits_named = [], [], [], [], [], []
roots = [pathlib.Path(p) for p in sys.argv[1:]] or [pathlib.Path('mcomix'), pathlib.Path('test')]
for root in roots:
    for path in sorted(root.rglob('*.py')):
        where = str(path)
        for node in ast.walk(ast.parse(path.read_text(), where)):
            if isinstance(node, ast.Attribute):
                name = dotted(node)
                if name in dep_members:
                    hits_member.append((where, node.lineno, name, dep_members[name]))
                elif name in dep_types:
                    hits_type.append((where, node.lineno, name, dep_types[name]))
                # obj.props.foo_bar
                if isinstance(node.value, ast.Attribute) and node.value.attr == 'props':
                    prop = node.attr.replace('_', '-')
                    if prop in by_property:
                        hits_named.append((where, node.lineno, prop, by_property[prop]))
            if not isinstance(node, ast.Call):
                continue
            name = dotted(node.func)
            # Constructor keywords are properties.
            if name and (name in dep_types or name.count('.') == 1):
                for kw in node.keywords:
                    if kw.arg is not None:
                        key = '%s:%s' % (name, kw.arg.replace('_', '-'))
                        if key in dep_props:
                            hits_prop.append((where, node.lineno, key, dep_props[key]))
            if not isinstance(node.func, ast.Attribute):
                continue
            attr = node.func.attr
            # An instance method call: the receiver's type is not known
            # here, so this is a candidate rather than a hit.
            if name is None and attr in by_method:
                hits_maybe.append((where, node.lineno, attr))
            text = first_string(node)
            if text is None:
                continue
            if attr in SIGNAL_CALLS and text in by_signal:
                hits_signal.append((where, node.lineno, text, by_signal[text]))
            if attr in PROPERTY_CALLS and text in by_property:
                hits_named.append((where, node.lineno, text, by_property[text]))


def report(title, rows):
    print('\n== %s (%d) ==' % (title, len(rows)))
    for row in sorted(set((r[2], r[0], r[1], str(r[3])) for r in rows)):
        print('  %-46s %s:%s   deprecated %s' % row)


def report_names(title, rows):
    rows = sorted(set((where, line, name, ', '.join(owners)) for where, line, name, owners in rows))
    print('\n== %s (%d) ==' % (title, len(rows)))
    for where, line, name, owners in rows:
        print('  %s:%s  "%s"  -> %s' % (where, line, name, owners))


report('deprecated types named', hits_type)
report('deprecated functions/methods named on a namespace', hits_member)
report('deprecated properties set as constructor keywords', hits_prop)
report_names('deprecated signal names connected or emitted', hits_signal)
report_names('deprecated property names used as strings or through .props', hits_named)
maybe = sorted(set(hits_maybe), key=lambda r: (r[2], r[0], r[1]))
print('\n== instance method calls whose name is deprecated somewhere (%d) ==' % len(maybe))
for path, line, attr in maybe:
    owners = ', '.join('%s (%s)' % (k, v) for k, v in by_method[attr])
    print('  %-28s %s:%s   -> %s' % (attr, path, line, owners))
