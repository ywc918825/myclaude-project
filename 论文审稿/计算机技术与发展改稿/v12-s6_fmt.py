# -*- coding: utf-8 -*-
"""S6 版式：A4 + Word 默认页边距；正文宋体五号 / 西文 Times New Roman。"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

# ── 页面：A4，上下 2.54 cm、左右 3.17 cm（Word 默认） ─────────────────
sec = body.find(W + 'sectPr')
pg = sec.find(W + 'pgSz')
pg.set(W + 'w', '11906'); pg.set(W + 'h', '16838')
mar = sec.find(W + 'pgMar')
for k, v in (('top', '1440'), ('bottom', '1440'), ('left', '1800'),
             ('right', '1800'), ('header', '851'), ('footer', '992')):
    mar.set(W + k, v)

# ── 正文字体：中文宋体 / 西文 Times New Roman（不动公式的 Cambria Math）──
n = 0
for r in body.iter(W + 'r'):
    rpr = r.find(W + 'rPr')
    if rpr is None:
        rpr = ET.Element(W + 'rPr')
        r.insert(0, rpr)
    f = rpr.find(W + 'rFonts')
    if f is not None and f.get(W + 'ascii') == 'Cambria Math':
        continue
    if f is None:
        f = ET.Element(W + 'rFonts')
        rpr.insert(0, f)
    for a in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        f.attrib.pop(W + a, None)
    f.set(W + 'ascii', 'Times New Roman')
    f.set(W + 'hAnsi', 'Times New Roman')
    f.set(W + 'eastAsia', '宋体')
    n += 1
save(tree, SRC, 'ref.xml')

# ── docDefaults 同步 ────────────────────────────────────────────────
sp = 'unz/word/styles.xml'
s = open(sp, encoding='utf-8').read()
s = s.replace(
    '<w:rFonts w:asciiTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi" '
    'w:eastAsiaTheme="minorEastAsia" w:cstheme="minorBidi"/>',
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
    'w:eastAsia="宋体" w:cs="Times New Roman"/><w:sz w:val="21"/>'
    '<w:szCs w:val="21"/>')
open(sp, 'w', encoding='utf-8').write(s)
print('S6 done: 页面 A4 / 上下 2.54cm 左右 3.17cm；%d 个 run 字体已绑定宋体+Times' % n)
