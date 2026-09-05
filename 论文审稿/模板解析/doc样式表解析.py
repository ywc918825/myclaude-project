# -*- coding: utf-8 -*-
"""解析 .doc 样式表，取出各命名样式的字号/加粗/对齐/行距。"""
import struct, sys
from fmt import Doc, parse_sprms

d = Doc(sys.argv[1] if len(sys.argv) > 1 else 'a.doc')
fc, lcb = d.fcs['Stshf']
b = d.tbl[fc:fc + lcb]
cbStshi = struct.unpack('<H', b[:2])[0]
stshi = b[2:2 + cbStshi]
cstd = struct.unpack('<H', stshi[0:2])[0]
cbSTDBaseInFile = struct.unpack('<H', stshi[2:4])[0]

styles = {}
i = 2 + cbStshi
istd = 0
while i + 2 <= len(b) and istd < cstd:
    cbStd = struct.unpack('<H', b[i:i + 2])[0]
    std = b[i + 2:i + 2 + cbStd]
    i += 2 + cbStd
    if cbStd == 0:
        istd += 1
        continue
    base = std[:cbSTDBaseInFile]
    w2 = struct.unpack('<H', base[2:4])[0]
    sgc = w2 & 0x000F
    cupx = struct.unpack('<H', base[4:6])[0] & 0x000F
    p = cbSTDBaseInFile
    cch = struct.unpack('<H', std[p:p + 2])[0]
    name = std[p + 2:p + 2 + cch * 2].decode('utf-16-le', 'ignore')
    p += 2 + cch * 2 + 2
    upx = []
    for _ in range(cupx):
        if p + 2 > len(std):
            break
        cb = struct.unpack('<H', std[p:p + 2])[0]
        upx.append(std[p + 2:p + 2 + cb])
        p += 2 + cb
        if p % 2:
            p += 1
    styles[istd] = (name, sgc, upx)
    istd += 1

WANT = ('正文', '标题', 'Normal', 'Heading', '题目', 'title', '图', '表', '参考')
print('%-4s %-22s %s' % ('istd', '样式名', '格式'))
for k, (name, sgc, upx) in sorted(styles.items()):
    if not name:
        continue
    info = {}
    for u in upx:
        if len(u) >= 2 and sgc == 1:
            g = u[2:] if len(u) > 2 else b''   # 段落 UPX 前 2 字节是 istd
            s = parse_sprms(g)
        else:
            s = parse_sprms(u)
        if 0x4A43 in s:
            info['字号'] = '%.1f 磅' % (struct.unpack('<H', s[0x4A43][-1][:2])[0] / 2.0)
        if 0x0835 in s and s[0x0835][-1][0] in (1, 128, 129):
            info['加粗'] = '是'
        if 0x2403 in s:
            info['对齐'] = {0: '左', 1: '居中', 2: '右', 3: '两端'}.get(s[0x2403][-1][0], '?')
        if 0x6412 in s and len(s[0x6412][-1]) >= 4:
            dya, mult = struct.unpack('<hH', s[0x6412][-1][:4])
            info['行距'] = ('%.2f 倍' % (dya / 240.0)) if mult else ('固定 %.1f 磅' % (abs(dya) / 20.0))
        if 0x8411 in s:
            info['首行'] = '%.1f 字符' % (struct.unpack('<h', s[0x8411][-1][:2])[0] / 210.0)
    if info and any(w in name for w in WANT):
        print('%-4d %-22s %s' % (k, name, info))
