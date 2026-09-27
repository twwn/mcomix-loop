"""Name the frames of a gdb backtrace into a stripped Windows DLL.

usage: symbolize_gdb.py <dll> <gdb log> <dll name as gdb prints it>

gdb on Windows prints "0x... in ?? () from .../libgtk-4-1.dll" and no
load address.  The load address is the one 64 KiB-aligned base at which
every return address (frames 1 and up) follows a call instruction in the
DLL's disassembly; then each frame is named by the nearest exported
symbol before it (a static function shows as <export>+offset).  The DLL
must be the same build the log ran (same MSYS2 package version).
"""
import bisect
import re
import subprocess
import sys

dll, log, name = sys.argv[1:4]
frames = []
for line in open(log, errors='replace'):
    m = re.search(r'#(\d+)\s+(0x[0-9a-f]+) in \?\? \(\) from \S*' + re.escape(name), line)
    if m:
        frames.append((int(m.group(1)), int(m.group(2), 16)))
head = subprocess.run(['objdump', '-p', dll], capture_output=True, text=True).stdout
image_base = int(re.search(r'ImageBase\s+([0-9a-f]+)', head).group(1), 16)
size = int(re.search(r'SizeOfImage\s+([0-9a-f]+)', head).group(1), 16)
after, labels, prev_call = set(), [], False
dis = subprocess.run(['llvm-objdump', '-d', '--no-show-raw-insn', dll],
                     capture_output=True, text=True).stdout
for line in dis.splitlines():
    m = re.match(r'([0-9a-f]+) <(.+)>:', line)
    if m:
        labels.append((int(m.group(1), 16), m.group(2)))
        continue
    m = re.match(r'\s*([0-9a-f]+):\s+(\S+)', line)
    if m:
        if prev_call:
            after.add(int(m.group(1), 16))
        prev_call = m.group(2).startswith('call')
labels.sort()
keys = [a for a, _ in labels]
returns = [a for n, a in frames if n > 0]
best = max(range((max(a for _, a in frames) - size) & ~0xffff,
                 min(a for _, a in frames) + 1, 0x10000),
           key=lambda base: sum(a - base + image_base in after for a in returns))
hits = sum(a - best + image_base in after for a in returns)
print('base %#x: %d of %d return addresses follow a call' % (best, hits, len(returns)))
for n, a in frames:
    v = a - best + image_base
    i = bisect.bisect_right(keys, v) - 1
    print('#%-3d rva %#08x  %s+%#x' % (n, a - best, labels[i][1], v - labels[i][0]))
