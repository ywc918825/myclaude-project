# -*- coding: utf-8 -*-
"""把 PNG 转成灰度，纯 Python 实现（本环境装不了 Pillow）。

用浏览器加 CSS 滤镜截图会重新布局、把图例裁掉，所以这里直接按字节改：
解 IDAT → 逐行反滤波 → 亮度换算 → 重新滤波压回去，尺寸与像素位置分毫不动。
IHDR 原样保留（位深、色彩类型、隔行方式都不变），sRGB/gAMA/pHYs 等辅助区块
也全部照抄——pHYs 存的是图像自带的 DPI，丢了就会被按默认 DPI 重新计算物理尺寸。

亮度用 Rec.601（0.299/0.587/0.114）。雷达图三条线原本靠颜色区分，
转灰度后深蓝→深灰、绿→中灰、橙→浅灰，再叠加原有的实线/虚线/点线，
仍可区分；须知要求的"不同线型或图符有说明"也满足。
"""
import struct, sys, zlib


def chunks(data):
    i = 8
    while i < len(data):
        ln = struct.unpack('>I', data[i:i + 4])[0]
        typ = data[i + 4:i + 8]
        yield typ, data[i + 8:i + 8 + ln]
        i += 12 + ln


def mk(typ, payload):
    return (struct.pack('>I', len(payload)) + typ + payload
            + struct.pack('>I', zlib.crc32(typ + payload) & 0xFFFFFFFF))


def unfilter(raw, w, h, bpp):
    out = bytearray()
    stride = w * bpp
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        ft = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                line[x] = (line[x] + a) & 0xFF
            elif ft == 2:
                line[x] = (line[x] + b) & 0xFF
            elif ft == 3:
                line[x] = (line[x] + (a + b) // 2) & 0xFF
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 0xFF
        out += line
        prev = line
    return out


def refilter(px, w, h, bpp):
    """一律用 Sub 滤波（type 1），够用且实现简单。"""
    stride = w * bpp
    out = bytearray()
    for y in range(h):
        line = px[y * stride:(y + 1) * stride]
        out.append(1)
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            out.append((line[x] - a) & 0xFF)
    return bytes(out)


def to_gray(src, dst, gamma=1.0):
    data = open(src, 'rb').read()
    idat = b''
    hdr = None
    keep = []           # IDAT/IEND 以外的区块一律原样留下，顺序不变
    sizes = []          # 原 IDAT 的分块大小，照抄回去
    for typ, pay in chunks(data):
        if typ == b'IHDR':
            hdr = pay
        elif typ == b'IDAT':
            idat += pay
            sizes.append(len(pay))
        elif typ != b'IEND':
            keep.append((typ, pay))
    w, h, depth, ctype, comp, filt, inter = struct.unpack('>IIBBBBB', hdr)
    assert depth == 8 and inter == 0 and ctype in (2, 6), (depth, ctype, inter)
    bpp = 3 if ctype == 2 else 4
    px = unfilter(zlib.decompress(idat), w, h, bpp)
    for i in range(0, len(px), bpp):
        g = int(0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2] + 0.5)
        if gamma != 1.0:
            g = int(255 * (g / 255.0) ** gamma + 0.5)
        px[i] = px[i + 1] = px[i + 2] = min(255, max(0, g))
    out = bytearray(b'\x89PNG\r\n\x1a\n')
    out += mk(b'IHDR', hdr)
    for typ, pay in keep:
        out += mk(typ, pay)
    body = zlib.compress(refilter(px, w, h, bpp), 9)
    step = sizes[0] if len(sizes) > 1 else len(body)
    for i in range(0, len(body), step) if step else [0]:
        out += mk(b'IDAT', body[i:i + step])
    out += mk(b'IEND', b'')
    print('  保留区块：%s' % (', '.join(t.decode() for t, _ in keep) or '无'))
    open(dst, 'wb').write(bytes(out))
    print('%s → %s  %dx%d  色彩类型 %d  %d bytes' % (src, dst, w, h, ctype, len(out)))


if __name__ == '__main__':
    to_gray(sys.argv[1], sys.argv[2],
            float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
