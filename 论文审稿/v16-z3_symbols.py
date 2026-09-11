# -*- coding: utf-8 -*-
"""Z3 上下标的正斜体，按须知区分；矩阵改黑斜体。

须知原文：「变量用斜体表示，矩阵、向量用黑斜体表示；下标字母若为说明性的
(如英文缩写)则用白正体表示，若为代表量和变动性数字及坐标轴的符号则用斜体表示」

原稿的做法是**下标一律不斜体**，于是 S_total 的 total（说明性，该正体）
和 S_i 的 i（变量，该斜体）排成了一样。按规则拆开：

  单个拉丁字母    → 变量  → 斜体      i, u, t, d, k, T, D
  多字母词        → 说明性 → 正体      total, max, min, now
  数字、逗号、括号 → 正体               (0), (k) 的括号、','、'×'

同段主符号（S、W、m、C…）本来就是斜体，不动；3.4 节的映射矩阵 M
按"矩阵用黑斜体"改为粗斜体。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, save
from rlib import para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
XS = '{http://www.w3.org/XML/1998/namespace}space'


def has(rpr, tag):
    return rpr is not None and rpr.find(W + tag) is not None


def set_i(rpr, on):
    for c in list(rpr):
        if c.tag == W + 'i':
            rpr.remove(c)
    if on:
        lib.set_prop(rpr, 'i')


def tokens(s):
    """切成 (文本, 是否变量) 段：单个拉丁字母算变量，其余算说明性/符号。"""
    out, buf = [], ''
    for ch in s:
        if ch.isascii() and ch.isalpha():
            buf += ch
        else:
            if buf:
                out.append((buf, len(buf) == 1))
                buf = ''
            if out and not out[-1][1]:
                out[-1] = (out[-1][0] + ch, False)
            else:
                out.append((ch, False))
    if buf:
        out.append((buf, len(buf) == 1))
    return out


changed = []
for p in body.iter(W + 'p'):
    for r in list(p.findall(W + 'r')):
        rpr = r.find(W + 'rPr')
        va = rpr.find(W + 'vertAlign') if rpr is not None else None
        if va is None:
            continue
        txt = ''.join(t.text or '' for t in r.findall(W + 't'))
        segs = tokens(txt)
        if not segs or all(v is False for _, v in segs):
            set_i(rpr, False)          # 全说明性：确保正体
            continue
        if len(segs) == 1 and segs[0][1]:
            set_i(rpr, True)           # 整段就是一个变量字母
            changed.append((va.get(W + 'val'), txt, '斜'))
            continue
        at = list(p).index(r)
        p.remove(r)
        for k, (seg, is_var) in enumerate(segs):
            nr = copy.deepcopy(r)
            for t in nr.findall(W + 't'):
                nr.remove(t)
            set_i(nr.find(W + 'rPr'), is_var)
            t = ET.SubElement(nr, W + 't')
            t.set(XS, 'preserve')
            t.text = seg
            p.insert(at + k, nr)
        changed.append((va.get(W + 'val'), txt,
                        '/'.join('%s%s' % (s, '斜' if v else '正') for s, v in segs)))

for kind, txt, how in changed:
    print('  %-11s %-10s → %s' % (kind, txt, how))

# ── 矩阵 M 用黑斜体 ─────────────────────────────────────────────
p = find(body, '定义标签—能力维度映射矩阵')
done = 0
for r in p.findall(W + 'r'):
    if ''.join(t.text or '' for t in r.findall(W + 't')) == 'M':
        lib.set_prop(r.find(W + 'rPr'), 'b')
        done += 1
print('映射矩阵 M 改黑斜体（%d 处）' % done)
assert done == 1

save(tree, SRC, 'ref.xml')
print('Z3 done：上下标改写 %d 处' % len(changed))
