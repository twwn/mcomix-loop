"""Rewrite each file header of a RAR 5 archive as made on Windows, with
the read-only and archive attributes; the vint keeps its length."""
import sys, zlib

def vint(b, i):
    v = s = 0
    while True:
        c = b[i]; v |= (c & 0x7f) << s; i += 1; s += 7
        if not c & 0x80:
            return v, i

data = bytearray(open(sys.argv[1], 'rb').read())
i = 8
while i < len(data):
    start = i
    size, j = vint(data, i + 4)
    end = j + size
    htype, k = vint(data, j)
    flags, k = vint(data, k)
    if flags & 1:
        _, k = vint(data, k)
    datasize = 0
    if flags & 2:
        datasize, k = vint(data, k)
    if htype == 2:
        fflags, k = vint(data, k)
        _, k = vint(data, k)  # unpacked size
        a0 = k
        attr, k = vint(data, k)
        n = k - a0
        enc = [0x21 | (0x80 if n > 1 else 0)] + [0x80] * (n - 2) + ([0x00] if n > 1 else [])
        data[a0:k] = bytes(enc)
        if fflags & 2:
            k += 4
        if fflags & 4:
            k += 4
        _, k = vint(data, k)  # compression
        h0 = k
        host, k = vint(data, k)
        print('member attr %o host %d -> 0x21 host 0' % (attr, host))
        data[h0] = 0
        crc = zlib.crc32(bytes(data[start + 4:end])) & 0xffffffff
        data[start:start + 4] = crc.to_bytes(4, 'little')
    if htype == 5:
        break
    i = end + datasize
open(sys.argv[2], 'wb').write(data)
