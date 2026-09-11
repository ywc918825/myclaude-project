# -*- coding: utf-8 -*-
"""W2 图表与上下文之间留一行（模板：「图表与上下文有一行的行距」）。

现稿 9 个图表块前后一行空行都没有，正文段直接贴着图或表题。按模板补：

    正文                          正文
    (空行)                        (空行)
    [图]            表题（中文）
    图题（中文）      表题（英文）
    图题（英文）      [表体]
    (空行)           [表注，如有]
    正文                          (空行)
                                  正文

表 4 与表 7 下面各有一条「注：…」，空行放在表注之后，不把表和它的注隔开。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, save
from rlib import para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')


def is_p(c):
    return c.tag == W + 'p'


def blank_like(src):
    """照着正文段做一个空段，保留段落属性（字号行距随之一致）。"""
    p = ET.Element(W + 'p')
    ppr = src.find(W + 'pPr')
    if ppr is not None:
        p.append(copy.deepcopy(ppr))
    r = ET.SubElement(p, W + 'r')
    rpr = next((x.find(W + 'rPr') for x in src.findall(W + 'r')
                if x.find(W + 'rPr') is not None), None)
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    return p


body_p = next(c for c in body if is_p(c) and len(para_text(c)) > 120)

# ── 找出 9 个图表块的起止下标 ───────────────────────────────────
blocks = []
kids = list(body)
for i, c in enumerate(kids):
    if is_p(c) and c.findall('.//' + W + 'drawing'):          # 图：图体在最前
        j = i
        while j + 1 < len(kids) and is_p(kids[j + 1]) and \
                para_text(kids[j + 1]).strip()[:3] in ('图1 ', '图2 ') or \
                (j + 1 < len(kids) and is_p(kids[j + 1])
                 and para_text(kids[j + 1]).strip().startswith('Fig.')):
            j += 1
        blocks.append(('图', i, j))
    elif c.tag == W + 'tbl':                                   # 表：表题在表体之前
        s = i
        while s - 1 >= 0 and is_p(kids[s - 1]) and (
                para_text(kids[s - 1]).strip().startswith('Table ')
                or para_text(kids[s - 1]).strip()[:1] == '表'):
            s -= 1
        e = i
        if e + 1 < len(kids) and is_p(kids[e + 1]) and \
                para_text(kids[e + 1]).strip().startswith('注：'):
            e += 1
        blocks.append(('表', s, e))

print('识别到 %d 个图表块：' % len(blocks))
for k, s, e in blocks:
    print('  %s  「%s」…「%s」' % (k, para_text(kids[s])[:22] or '[图体]',
                                  para_text(kids[e])[:22] or '[表体]'))

# ── 从后往前插，避免下标漂移 ────────────────────────────────────
added = 0
for k, s, e in sorted(blocks, key=lambda x: -x[1]):
    cur = list(body)
    after, before = cur[e], cur[s]
    if not (e + 1 < len(cur) and is_p(cur[e + 1]) and not para_text(cur[e + 1]).strip()):
        body.insert(cur.index(after) + 1, blank_like(body_p))
        added += 1
    cur = list(body)
    if not (s - 1 >= 0 and is_p(cur[cur.index(before) - 1])
            and not para_text(cur[cur.index(before) - 1]).strip()):
        body.insert(cur.index(before), blank_like(body_p))
        added += 1

print('补空行 %d 处' % added)
save(tree, SRC, 'ref.xml')
print('W2 done')
