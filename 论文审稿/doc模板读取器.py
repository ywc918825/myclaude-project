# -*- coding: utf-8 -*-
"""极简 .doc 读取器：OLE2 复合文档 + Word97 FIB/CLX 分片表 → 纯文本。"""
import struct, sys

class OLE:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        assert self.d[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', 'not an OLE2 file'
        ss = 1 << struct.unpack('<H', self.d[0x1e:0x20])[0]
        ms = 1 << struct.unpack('<H', self.d[0x20:0x22])[0]
        self.ss, self.ms = ss, ms
        ncfat = struct.unpack('<I', self.d[0x2c:0x30])[0]
        dirstart = struct.unpack('<I', self.d[0x30:0x34])[0]
        self.cutoff = struct.unpack('<I', self.d[0x38:0x3c])[0]
        minifat0 = struct.unpack('<I', self.d[0x3c:0x40])[0]
        ndifat = struct.unpack('<I', self.d[0x48:0x4c])[0]
        difat0 = struct.unpack('<I', self.d[0x44:0x48])[0]

        difat = list(struct.unpack('<109I', self.d[0x4c:0x4c + 436]))
        sec = difat0
        while sec not in (0xFFFFFFFE, 0xFFFFFFFF) and ndifat > 0:
            blk = self.sector(sec)
            vals = struct.unpack('<%dI' % (ss // 4), blk)
            difat += list(vals[:-1])
            sec = vals[-1]; ndifat -= 1
        self.fat = []
        for s in difat[:ncfat]:
            if s >= 0xFFFFFFFE:
                break
            self.fat += list(struct.unpack('<%dI' % (ss // 4), self.sector(s)))
        self.minifat = []
        s = minifat0
        while s < 0xFFFFFFFE:
            self.minifat += list(struct.unpack('<%dI' % (ss // 4), self.sector(s)))
            s = self.fat[s]
        # 目录
        self.dirs = []
        s = dirstart
        raw = b''
        while s < 0xFFFFFFFE:
            raw += self.sector(s); s = self.fat[s]
        for i in range(0, len(raw), 128):
            e = raw[i:i + 128]
            if len(e) < 128:
                break
            nl = struct.unpack('<H', e[0x40:0x42])[0]
            name = e[:max(0, nl - 2)].decode('utf-16-le', 'ignore')
            self.dirs.append({'name': name, 'type': e[0x42],
                              'start': struct.unpack('<I', e[0x74:0x78])[0],
                              'size': struct.unpack('<Q', e[0x78:0x80])[0] & 0xFFFFFFFF})
        root = next(d for d in self.dirs if d['type'] == 5)
        self.mini = self._chain(root['start'], root['size'], mini=False)

    def sector(self, n):
        off = 512 + n * self.ss
        return self.d[off:off + self.ss]

    def _chain(self, start, size, mini):
        out = b''
        s = start
        fat, sz = (self.minifat, self.ms) if mini else (self.fat, self.ss)
        while s < 0xFFFFFFFE and len(out) < size:
            out += (self.mini[s * self.ms:(s + 1) * self.ms] if mini else self.sector(s))
            s = fat[s] if s < len(fat) else 0xFFFFFFFE
        return out[:size]

    def stream(self, name):
        e = next(d for d in self.dirs if d['name'] == name)
        return self._chain(e['start'], e['size'], e['size'] < self.cutoff and e['name'] != 'Root Entry')


def doc_text(path):
    o = OLE(path)
    wd = o.stream('WordDocument')
    flags = struct.unpack('<H', wd[0x0a:0x0c])[0]
    tbl = o.stream('1Table' if (flags & 0x0200) else '0Table')
    csw = struct.unpack('<H', wd[32:34])[0]
    p = 34 + csw * 2
    cslw = struct.unpack('<H', wd[p:p + 2])[0]
    p += 2 + cslw * 4
    p += 2                                    # cbRgFcLcb
    fcClx, lcbClx = struct.unpack('<II', wd[p + 264:p + 272])
    clx = tbl[fcClx:fcClx + lcbClx]
    # 跳过 Prc，定位 Pcdt
    i = 0
    while i < len(clx) and clx[i] == 0x01:
        cb = struct.unpack('<H', clx[i + 1:i + 3])[0]
        i += 3 + cb
    assert clx[i] == 0x02, clx[i]
    lcb = struct.unpack('<I', clx[i + 1:i + 5])[0]
    plc = clx[i + 5:i + 5 + lcb]
    n = (len(plc) - 4) // 12
    cps = struct.unpack('<%dI' % (n + 1), plc[:4 * (n + 1)])
    out = []
    for k in range(n):
        pcd = plc[4 * (n + 1) + k * 8: 4 * (n + 1) + k * 8 + 8]
        fc = struct.unpack('<I', pcd[2:6])[0]
        ln = cps[k + 1] - cps[k]
        if fc & 0x40000000:
            off = (fc & 0x3FFFFFFF) // 2
            out.append(wd[off:off + ln].decode('cp936', 'replace'))
        else:
            out.append(wd[fc:fc + ln * 2].decode('utf-16-le', 'replace'))
    return ''.join(out)


if __name__ == '__main__':
    t = doc_text(sys.argv[1])
    t = t.replace('\r', '\n').replace('\x07', ' | ').replace('\x0c', '\n')
    lines = [l.rstrip() for l in t.split('\n')]
    for l in lines:
        if l.strip():
            print(l)
