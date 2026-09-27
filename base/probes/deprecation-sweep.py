"""Every deprecated GI symbol this tree names, read out of the .gir files.

The runtime census only sees what the suite executes and only warns for
deprecated functions and methods; a deprecated class or property makes
no noise at all.  This reads the GIR XML instead.
"""
import ast
import os
import pathlib
import re
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


def strip(tag):
    return tag.split('}')[-1]


def load(namespace, filename):
    """(deprecated types, deprecated members, deprecated properties)."""
    path = os.path.join(GIR_DIR, filename)
    if not os.path.exists(path):
        return {}, {}, {}
    root = ET.parse(path).getroot()
    ns = root.find('c:namespace', NS)
    types, members, props = {}, {}, {}
    for node in ns:
        tag = strip(node.tag)
        name = node.get('name')
        if tag not in TYPE_TAGS and tag not in MEMBER_TAGS:
            continue
        since = node.get('deprecated-version') or '?'
        if tag in MEMBER_TAGS:
            # A namespace level function.
            if node.get('deprecated'):
                members['%s.%s' % (namespace, name)] = since
            continue
        if node.get('deprecated'):
            types['%s.%s' % (namespace, name)] = since
        for child in node:
            ctag = strip(child.tag)
            cname = child.get('name')
            if ctag in MEMBER_TAGS and child.get('deprecated'):
                key = '%s.%s.%s' % (namespace, name, (cname or '').replace('-', '_'))
                members[key] = child.get('deprecated-version') or '?'
            elif ctag == 'property' and child.get('deprecated'):
                props['%s.%s:%s' % (namespace, name, cname)] = \
                    child.get('deprecated-version') or '?'
    return types, members, props


dep_types, dep_members, dep_props = {}, {}, {}
for namespace, filename in FILES.items():
    t, m, p = load(namespace, filename)
    dep_types.update(t)
    dep_members.update(m)
    dep_props.update(p)

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


hits_type, hits_member, hits_prop, hits_maybe = [], [], [], []
roots = [pathlib.Path(p) for p in sys.argv[1:]] or [pathlib.Path('mcomix')]
for root in roots:
    for path in sorted(root.rglob('*.py')):
        tree = ast.parse(path.read_text(), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                name = dotted(node)
                if name is None:
                    continue
                if name in dep_members:
                    hits_member.append((str(path), node.lineno, name,
                                        dep_members[name]))
                elif name in dep_types:
                    hits_type.append((str(path), node.lineno, name,
                                      dep_types[name]))
            if isinstance(node, ast.Call):
                name = dotted(node.func)
                if name and name in dep_types:
                    pass  # already reported as a type reference
                # Constructor keywords are properties.
                if name and (name in dep_types or
                             ('.' in name and name.count('.') == 1)):
                    for kw in node.keywords:
                        if kw.arg is None:
                            continue
                        key = '%s:%s' % (name, kw.arg.replace('_', '-'))
                        if key in dep_props:
                            hits_prop.append((str(path), node.lineno, key,
                                              dep_props[key]))
                # An instance method call: the receiver's type is not
                # known here, so this is a candidate rather than a hit.
                if isinstance(node.func, ast.Attribute) and name is None:
                    attr = node.func.attr
                    if attr in by_method:
                        hits_maybe.append((str(path), node.lineno, attr,
                                           by_method[attr]))


def report(title, rows):
    print('\n== %s (%d) ==' % (title, len(rows)))
    for row in sorted(set((r[2], r[0], r[1], str(r[3])) for r in rows)):
        print('  %-46s %s:%s   deprecated %s' % (row[0], row[1], row[2], row[3]))


report('deprecated types named', hits_type)
report('deprecated functions/methods named on a namespace', hits_member)
report('deprecated properties set as constructor keywords', hits_prop)
print('\n== instance method calls whose name is deprecated somewhere (%d) =='
      % len(set((r[2], r[0], r[1]) for r in hits_maybe)))
for attr, path, line in sorted(set((r[2], r[0], r[1]) for r in hits_maybe)):
    owners = ', '.join('%s (%s)' % (k, v) for k, v in by_method[attr])
    print('  %-28s %s:%s   -> %s' % (attr, path, line, owners))
