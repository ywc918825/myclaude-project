# -*- coding: utf-8 -*-
"""按分片表把 FC 区间还原成文本，用于给 PAPX 段落配上正文。"""
import struct
from docread import OLE


def pieces(path):
    o = OLE(path)
    wd = o.stream('WordDocument')
    flags = struct.unpack('<H', wd[0x0a:0x0c])[0]
    tbl = o.stream('1Table' if (flags & 0x0200) else '0Table')
    csw = struct.unpack('<H', wd[32:34])[0]
    p = 34 + csw * 2
    cslw = struct.unpack('<H', wd[p:p + 2])[0]
    p += 2 + cslw * 4 + 2
    fcClx, lcbClx = struct.unpack('<II', wd[p + 264:p + 272])
    clx = tbl[fcClx:fcClx + lcbClx]
    i = 0
    while i < len(clx) and clx[i] == 0x01:
        i += 3 + struct.unpack('<H', clx[i + 1:i + 3])[0]
    lcb = struct.unpack('<I', clx[i + 1:i + 5])[0]
    plc = clx[i + 5:i + 5 + lcb]
    n = (len(plc) - 4) // 12
    cps = struct.unpack('<%dI' % (n + 1), plc[:4 * (n + 1)])
    out = []
    for k in range(n):
        pcd = plc[4 * (n + 1) + k * 8: 4 * (n + 1) + k * 8 + 8]
        fc = struct.unpack('<I', pcd[2:6])[0]
        comp = bool(fc & 0x40000000)
        base = (fc & 0x3FFFFFFF) // 2 if comp else fc
        ln = cps[k + 1] - cps[k]
        out.append((base, base + (ln if comp else ln * 2), comp))
    return wd, out


def text_of(wd, ps, a, b):
    s = []
    for base, end, comp in ps:
        lo, hi = max(a, base), min(b, end)
        if lo >= hi:
            continue
        if comp:
            s.append(wd[lo:hi].decode('cp936', 'replace'))
        else:
            lo -= (lo - base) % 2
            s.append(wd[lo:hi].decode('utf-16-le', 'replace'))
    return ''.join(s)
