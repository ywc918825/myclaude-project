# -*- coding: utf-8 -*-
"""从 .doc 里挖出逐段的排版参数：字体、字号、对齐、缩进、行距、段距。"""
import struct, sys
from docread import OLE

W_JC = {0: '左', 1: '居中', 2: '右', 3: '两端', 4: '分散'}


def sprm_len(sprm, data, i):
    spra = (sprm >> 13) & 7
    if spra in (0, 1):
        return 1
    if spra in (2, 4, 5):
        return 2
    if spra == 3:
        return 4
    if spra == 7:
        return 3
    if spra == 6:
        return data[i] + 1
    return 0


def parse_sprms(g):
    out = {}
    i = 0
    while i + 2 <= len(g):
        sprm = struct.unpack('<H', g[i:i + 2])[0]
        i += 2
        n = sprm_len(sprm, g, i)
        out.setdefault(sprm, []).append(g[i:i + n])
        i += n
    return out


class Doc:
    def __init__(self, path):
        o = OLE(path)
        self.wd = o.stream('WordDocument')
        flags = struct.unpack('<H', self.wd[0x0a:0x0c])[0]
        self.tbl = o.stream('1Table' if (flags & 0x0200) else '0Table')
        csw = struct.unpack('<H', self.wd[32:34])[0]
        p = 34 + csw * 2
        cslw = struct.unpack('<H', self.wd[p:p + 2])[0]
        p += 2 + cslw * 4 + 2
        self.fib = p
        self.fcs = {}
        for name, k in (('Stshf', 2), ('Plcfsed', 7), ('PlcfbteChpx', 13),
                        ('PlcfbtePapx', 14), ('Sttbfffn', 16), ('Clx', 34)):
            self.fcs[name] = struct.unpack('<II', self.wd[p + (k - 1) * 8: p + (k - 1) * 8 + 8])

    # ── 字体表 ────────────────────────────────────────────────────
    def fonts(self):
        fc, lcb = self.fcs['Sttbfffn']
        b = self.tbl[fc:fc + lcb]
        out, i = [], 6                      # 跳过 fExtend/cData/cbExtra
        while i < len(b):
            cb = b[i]
            if cb == 0:
                break
            blk = b[i + 1:i + 1 + cb]
            best = ''
            for off in (38,):
                if len(blk) <= off:
                    continue
                cand = blk[off:].decode('utf-16-le', 'ignore').split('\x00')[0].strip()
                if cand and (len(cand) > len(best)) and cand[0].isprintable():
                    best = cand
            out.append(best)
            i += 1 + cb
        return out

    # ── FKP 里的 PAPX / CHPX ──────────────────────────────────────
    def _bte(self, key, papx):
        fc, lcb = self.fcs[key]
        b = self.tbl[fc:fc + lcb]
        n = (len(b) - 4) // 8
        fcs = struct.unpack('<%dI' % (n + 1), b[:4 * (n + 1)])
        pns = struct.unpack('<%dI' % n, b[4 * (n + 1):4 * (n + 1) + 4 * n])
        runs = []
        for pn in pns:
            pg = self.wd[pn * 512:(pn + 1) * 512]
            if len(pg) < 512:
                continue
            crun = pg[511]
            rgfc = struct.unpack('<%dI' % (crun + 1), pg[:4 * (crun + 1)])
            base = 4 * (crun + 1)
            for k in range(crun):
                if papx:
                    off = pg[base + k * 13]
                    if off == 0:
                        g = b''
                    else:
                        q = off * 2
                        cb = pg[q]
                        if cb == 0:
                            cb2 = pg[q + 1]
                            g = pg[q + 2:q + 2 + cb2 * 2 - 2]
                        else:
                            g = pg[q + 1:q + 1 + cb * 2 - 1]
                        g = g[2:]            # 去掉 istd
                else:
                    off = pg[base + k]
                    if off == 0:
                        g = b''
                    else:
                        q = off * 2
                        cb = pg[q]
                        g = pg[q + 1:q + 1 + cb]
                runs.append((rgfc[k], rgfc[k + 1], g))
        return runs

    def papx(self):
        return self._bte('PlcfbtePapx', True)

    def chpx(self):
        return self._bte('PlcfbteChpx', False)


def describe(pg, cg, fonts):
    d = {}
    if 0x2403 in pg:
        d['对齐'] = W_JC.get(pg[0x2403][-1][0], '?')
    for sprm, key in ((0x840F, '左缩进'), (0x840E, '右缩进'), (0x8411, '首行缩进')):
        if sprm in pg:
            v = struct.unpack('<h', pg[sprm][-1][:2])[0]
            d[key] = '%.1f 字符' % (v / 210.0) if key == '首行缩进' else '%d twip' % v
    for sprm, key in ((0xA413, '段前'), (0xA414, '段后')):
        if sprm in pg:
            d[key] = '%d twip' % struct.unpack('<h', pg[sprm][-1][:2])[0]
    if 0x6412 in pg and len(pg[0x6412][-1]) >= 4:
        dya, mult = struct.unpack('<hH', pg[0x6412][-1][:4])
        d['行距'] = ('%.2f 倍' % (dya / 240.0)) if mult else ('固定 %.1f 磅' % (abs(dya) / 20.0))
    if 0x4A43 in cg:
        d['字号'] = '%.1f 磅' % (struct.unpack('<H', cg[0x4A43][-1][:2])[0] / 2.0)
    for sprm, key in ((0x4A4F, '西文'), (0x4A50, '中文'), (0x4A51, '其他')):
        if sprm in cg:
            i = struct.unpack('<H', cg[sprm][-1][:2])[0]
            if i < len(fonts):
                d[key] = fonts[i]
    if 0x0835 in cg and cg[0x0835][-1][0]:
        d['加粗'] = '是'
    return d


if __name__ == '__main__':
    doc = Doc(sys.argv[1])
    fonts = doc.fonts()
    print('【字体表】', ', '.join(fonts[:14]))
    print()
    paps = doc.papx()
    chps = doc.chpx()
    print('【段落数】PAPX %d 段, CHPX %d 段' % (len(paps), len(chps)))
    # 用文本定位关键段落
    import txtmap
    wd, ps = txtmap.pieces(sys.argv[1])
    print()
    for i, (a, b, g) in enumerate(paps):
        pg = parse_sprms(g)
        cg = {}
        for ca, cb, cgb in chps:
            if ca >= a and ca < b:
                cg = parse_sprms(cgb)
                break
        s = txtmap.text_of(wd, ps, a, b).replace('\r', '').replace('\x07', '|')[:24]
        d = describe(pg, cg, fonts)
        if s.strip():
            print('%2d %-28r %s' % (i, s, d))
