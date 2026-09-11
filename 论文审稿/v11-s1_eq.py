# -*- coding: utf-8 -*-
"""第一步：修复式(3)(5)(7) 被打乱的 sSubSup（基/下标/上标 整体错位一格）。"""
import copy, xml.etree.ElementTree as ET
from lib import W, register, save
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
root = tree.getroot()

# 期望：sSubSup 的 e/sub/sup 应为 (基, 下标, 上标)
WANT = {3: [('S', 'i', 'norm')],
        5: [('W', 't,u', '(k)'), ('W', 't,u', '(k - 1)')],
        7: [('C', 'd,u', "'")]}
n = 0
for i, om in enumerate(list(root.iter(M + 'oMath')), 1):
    if i not in WANT:
        continue
    for ss in om.iter(M + 'sSubSup'):
        e, sub, sup = (ss.find(M + 'e'), ss.find(M + 'sub'), ss.find(M + 'sup'))
        cur = [''.join(t.text or '' for t in x.iter(M + 't')) for x in (e, sub, sup)]
        # 现状是 (下标, 上标, 基) 的轮转 → 把三个容器的内容轮转回去
        ce, cs, cp = [list(x) for x in (e, sub, sup)]
        for x in (e, sub, sup):
            for c in list(x):
                x.remove(c)
        for c in cp:                      # 原 sup 里装的是“基”
            e.append(c)
        for c in ce:                      # 原 e 里装的是“下标”
            sub.append(c)
        for c in cs:                      # 原 sub 里装的是“上标”
            sup.append(c)
        new = [''.join(t.text or '' for t in x.iter(M + 't')) for x in (e, sub, sup)]
        print('  式(%d) %s → 基=%r 下标=%r 上标=%r' % (i, cur, *new))
        n += 1
save(tree, SRC, 'work.bak/word/document.xml')
print('共修复 %d 处上下标错位。' % n)
