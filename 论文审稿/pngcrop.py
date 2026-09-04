# -*- coding: utf-8 -*-
"""把 PNG 裁掉底部多余行（纯标准库，无需 Pillow）。"""
import struct, zlib


def chunks(d):
    i = 8
    while i < len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]
        typ = d[i+4:i+8]
        yield typ, d[i+8:i+8+ln]
        i += 12 + ln


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
    return a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)


def crop_height(src, dst, new_h):
    d = open(src, 'rb').read()
    idat = b''
    for typ, body in chunks(d):
        if typ == b'IHDR':
            w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', body)
        elif typ == b'IDAT':
            idat += body
    assert depth == 8 and inter == 0, 'only 8-bit non-interlaced'
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * bpp
    raw = zlib.decompress(idat)
    out, prev = [], bytearray(stride)
    pos = 0
    for _ in range(h):
        ft = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos+stride]); pos += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i-bpp]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                c = prev[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + paeth(a, prev[i], c)) & 255
        out.append(bytes(line)); prev = line
    body = b''.join(b'\x00' + r for r in out[:new_h])
    ihdr = struct.pack('>IIBBBBB', w, new_h, depth, ctype, comp, filt, inter)

    def chunk(t, b):
        return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b) & 0xffffffff)
    open(dst, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
                          chunk(b'IDAT', zlib.compress(body, 9)) + chunk(b'IEND', b''))
    return w, new_h


if __name__ == '__main__':
    import sys
    print(crop_height(sys.argv[1], sys.argv[2], int(sys.argv[3])))
