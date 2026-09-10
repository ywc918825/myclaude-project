# -*- coding: utf-8 -*-
"""Z2 图表题补英文，并按模板设字体。

模板原文：「图、表需同时编排中英文图题、表题…图题置于图下方，表题置于表上方，
字号比正文字号小一号，居中。图题、表题的中文用小五号黑体，英文用小五号
Times New Roman，加粗。」

原稿 9 个图表题只有中文，且用的是小五号宋体。这里逐个补英文题并改字体：
表题在表上方（中文题、英文题、表体），图题在图下方（图、中文题、英文题）。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, rewrite, save
from rlib import para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
ORDER = lib.RPR_ORDER

EN = {
    '图1': 'Fig. 1  Layered architecture of the system',
    '图2': 'Fig. 2  Capability radar chart of a talent profile',
    '表1': 'Table 1  Comparison of credit allocation methods for multi-author outputs',
    '表2': 'Table 2  Performance test results of core interfaces',
    '表3': 'Table 3  Application effects before and after system deployment',
    '表4': 'Table 4  Comparison between the proposed system and related work',
    '表5': 'Table 5  Spearman rank correlations of talent rankings under '
           'four allocation methods',
    '表6': 'Table 6  Top-N overlap of researchers with the proposed method '
           'as the baseline',
    '表7': 'Table 7  Rank changes of researchers with different collaboration '
           'scales (proposed method vs. equal sharing)',
}


def set_rpr(rpr, tag, attrs=None):
    for c in list(rpr):
        if c.tag == W + tag:
            rpr.remove(c)
    el = ET.Element(W + tag)
    for k, v in (attrs or {}).items():
        el.set(W + k, v)
    idx = ORDER.index(tag) if tag in ORDER else len(ORDER)
    pos = 0
    for c in list(rpr):
        t = c.tag.replace(W, '')
        if (ORDER.index(t) if t in ORDER else len(ORDER)) <= idx:
            pos += 1
        else:
            break
    rpr.insert(pos, el)


def style(p, ea, ascii_, sz, bold):
    for r in p.findall(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is None:
            rpr = ET.Element(W + 'rPr')
            r.insert(0, rpr)
        set_rpr(rpr, 'rFonts', {'ascii': ascii_, 'hAnsi': ascii_, 'eastAsia': ea})
        set_rpr(rpr, 'sz', {'val': sz})
        set_rpr(rpr, 'szCs', {'val': sz})
        for c in list(rpr):
            if c.tag == W + 'b':
                rpr.remove(c)
        if bold:
            set_rpr(rpr, 'b', {})


caps = [p for p in body if p.tag == W + 'p'
        and para_text(p).strip()[:2] in EN
        and para_text(p).strip()[2:3] == ' ']
assert len(caps) == 9, [para_text(p)[:16] for p in caps]

for cap in caps:
    key = para_text(cap).strip()[:2]
    style(cap, '黑体', '黑体', '18', False)          # 中文题 小五号黑体
    en = copy.deepcopy(cap)
    rewrite(en, EN[key])
    style(en, 'Times New Roman', 'Times New Roman', '18', True)   # 英文题 小五 TNR 粗
    body.insert(list(body).index(cap) + 1, en)
    print('  %-6s + %s' % (key, EN[key][:52]))

print('9 个图表题补英文题，中文改小五号黑体')
save(tree, SRC, 'ref.xml')
print('Z2 done')
