"""What the UnRAR library does with symlink members MComix hands it.

Run from the checkout:
env -u WAYLAND_DISPLAY GDK_BACKEND=x11 PYTHONPATH=. timeout -k 5 60 xvfb-run -d \
    python3 <this file>

Hand-built RAR 4: a member whose attribute word holds S_IFLNK and HostOS is
Unix is a symlink, its stored data the target.  Each case prints the tree the
extraction left, so a file outside the destination shows.
"""
import os
import struct
import sys
import unittest
import zlib

from test import MComixTest

from mcomix.archive import rar


def stored_rar(path, members):
    def block(body):
        return struct.pack('<H', zlib.crc32(body) & 0xffff) + body

    out = b'Rar!\x1a\x07\x00' + block(
        b'\x73' + struct.pack('<HH', 0, 13) + bytes(6))
    for name, data, mode in members:
        encoded = name.encode('utf-8')
        out += block(b'\x74' + struct.pack('<HH', 0x8000, 32 + len(encoded))
                     + struct.pack('<IIBIIBBHI', len(data), len(data), 3,
                                   zlib.crc32(data), 0x5a210000, 29, 0x30,
                                   len(encoded), mode)
                     + encoded) + data
    out += block(b'\x7b' + struct.pack('<HH', 0x4000, 7))
    with open(path, 'wb') as archive:
        archive.write(out)


def link(name, target):
    return (name, target.encode(), 0o120777)


def plain(name, data=b'data'):
    return (name, data, 0o100644)


def tree(top):
    lines = []
    for folder, dirs, files in os.walk(top):
        for name in sorted(dirs + files):
            path = os.path.join(folder, name)
            shown = os.path.relpath(path, top)
            if os.path.islink(path):
                shown += ' -> ' + os.readlink(path)
            lines.append(shown)
    return sorted(lines)


class Probe(MComixTest):

    def run_case(self, title, members, destination=None):
        top = os.path.join(self.tmp_dir, title.replace(' ', '_'))
        os.makedirs(os.path.join(top, 'outside'))
        os.makedirs(os.path.join(top, 'x', 'y'))
        with open(os.path.join(top, 'outside', 'victim'), 'w') as victim:
            victim.write('untouched')
        destination = destination or os.path.join(top, 'x', 'y', 'dest')
        members = [(n, d.replace(b'@TOP', top.encode()), m)
                   for n, d, m in members]
        book = os.path.join(top, 'book.rar')
        stored_rar(book, members)
        handler = rar.RarArchive(book)
        names = list(handler.iter_contents())
        print('\n==', title, '\nlisted:', names, file=sys.stderr)
        for name in names:
            try:
                handler.extract(name, destination.replace('@TOP', top))
            except Exception as error:
                print('  extract', name, 'raised', repr(error), file=sys.stderr)
        handler.close()
        for line in tree(top):
            print('  ', line, file=sys.stderr)
        return top

    def test_cases(self):
        self.run_case('absolute link then through', [
            link('l', '@TOP/outside'), plain('l/evil.jpg')])
        self.run_case('relative link then through', [
            link('l', '../../../outside'), plain('l/evil.jpg')])
        self.run_case('inside link then through', [
            link('d/l', '..'), plain('d/l/in.jpg')])
        self.run_case('chain', [
            link('l1', '.'), link('l1/l2', '..'), link('l1/l2/l3', '..'),
            plain('l1/l2/l3/poc.jpg')])
        self.run_case('file link over victim', [
            link('a.jpg', '@TOP/outside/victim'), plain('a.jpg', b'overwritten')])
        self.run_case('relative file link over victim', [
            link('a.jpg', '../../../outside/victim'), plain('a.jpg', b'overwritten')])
        # A destination reached through a symlink of the user's own.
        top = os.path.join(self.tmp_dir, 'ancestor')
        os.makedirs(os.path.join(top, 'real'))
        os.symlink(os.path.join(top, 'real'), os.path.join(top, 'mine'))
        destination = os.path.join(top, 'mine', 'dest')
        self.run_case('ancestor symlink', [
            link('l', 'page.jpg'), plain('page.jpg')], destination)
        print('\nmine after:', os.path.islink(os.path.join(top, 'mine')),
              os.listdir(top), tree(top), file=sys.stderr)


if __name__ == '__main__':
    unittest.main(argv=['probe'], exit=False)
    sys.stderr.flush()
    os._exit(0)
