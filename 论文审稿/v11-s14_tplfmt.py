# -*- coding: utf-8 -*-
"""按从模板 .doc 中实测出的排版参数，逐类设置段落与字符格式。

实测值（来源：模板 PAPX/CHPX/SEPX，见 tpl2/fmt.py 输出）
    页面      A4，上 30 mm、左 20 mm、右 19 mm，单栏
    正文      10 磅，固定行距 16 磅，首行缩进 2 字符
    摘要/关键词/Abstract/Key words   10 磅，固定行距 16 磅
    单位/通讯作者                     9 磅
    引用格式                         7.5 磅
    图题                             9 磅，居中，固定 16 磅
    表题                             9 磅，居中，固定 16 磅，段前 6 磅
    参考文献标题                     10 磅，居中，段前 12 磅
    参考文献条目                     9 磅，固定行距 14 磅，左缩进 180 twip、悬挂 0.9 字符
    公式行                           1.15 倍行距
"""
import re, xml.etree.ElementTree as ET
from lib import W, register, text_of, save

M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
root = tree.getroot()
body = root.find(W + 'body')
PORDER = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl',
          'numPr', 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens',
          'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE',
          'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid', 'spacing', 'ind',
          'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
          'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr']


def sub_ordered(parent, tag, order):
    el = parent.find(W + tag)
    if el is not None:
        return el
    el = ET.Element(W + tag)
    idx = order.index(tag)
    pos = 0
    for c in list(parent):
        t = c.tag.replace(W, '')
        if t in order and order.index(t) <= idx:
            pos += 1
        else:
            break
    parent.insert(pos, el)
    return el


def fmt(p, sz=None, jc=None, line=None, rule='exact', first=None,
        left=None, hang=None, before=None, after=None):
    ppr = p.find(W + 'pPr')
    if ppr is None:
        ppr = ET.Element(W + 'pPr'); p.insert(0, ppr)
    if jc is not None:
        sub_ordered(ppr, 'jc', PORDER).set(W + 'val', jc)
    if line is not None or before is not None or after is not None:
        sp = sub_ordered(ppr, 'spacing', PORDER)
        if line is not None:
            sp.set(W + 'line', str(line)); sp.set(W + 'lineRule', rule)
        if before is not None:
            sp.set(W + 'before', str(before)); sp.set(W + 'beforeLines', '0')
        if after is not None:
            sp.set(W + 'after', str(after)); sp.set(W + 'afterLines', '0')
    if first is not None or left is not None or hang is not None:
        ind = sub_ordered(ppr, 'ind', PORDER)
        for k in ('firstLine', 'firstLineChars', 'hanging', 'hangingChars'):
            if ind.get(W + k) is not None:
                del ind.attrib[W + k]
        if first is not None:
            ind.set(W + 'firstLineChars', str(int(first * 100)))
            ind.set(W + 'firstLine', str(int(first * 210)))
        if left is not None:
            ind.set(W + 'left', str(left))
        if hang is not None:
            ind.set(W + 'hangingChars', str(int(hang * 100)))
            ind.set(W + 'hanging', str(int(hang * 210)))
    if sz is not None:
        hp = str(int(sz * 2))
        for r in p.iter(W + 'r'):
            rpr = r.find(W + 'rPr')
            if rpr is None:
                rpr = ET.Element(W + 'rPr'); r.insert(0, rpr)
            for tag in ('sz', 'szCs'):
                e = rpr.find(W + tag)
                if e is None:
                    e = ET.SubElement(rpr, W + tag)
                e.set(W + 'val', hp)


BODY = dict(sz=10, line=320, rule='exact', jc='both', first=2)
HEAD2 = dict(sz=10, line=320, rule='exact', jc='left', first=0)
n = {'正文': 0, '标题': 0, '图表题': 0, '文献': 0, '公式': 0, '篇首': 0}
in_ref = False
for p in body.iter(W + 'p'):
    s = text_of(p).strip()
    if not s and not list(p.iter(M + 'oMath')):
        continue
    if list(p.iter(M + 'oMath')):
        fmt(p, line=276, rule='auto'); n['公式'] += 1; continue
    if s == '参考文献':
        fmt(p, sz=10, jc='center', line=320, before=240, first=0); in_ref = True
        n['标题'] += 1; continue
    if in_ref and re.match(r'^\d+\s+\S', s):
        fmt(p, sz=9, line=280, rule='exact', jc='both', left=180, hang=0.9)
        n['文献'] += 1; continue
    if re.match(r'^图\d', s):
        fmt(p, sz=9, jc='center', line=320, first=0); n['图表题'] += 1; continue
    if re.match(r'^表\d', s):
        fmt(p, sz=9, jc='center', line=320, before=120, first=0); n['图表题'] += 1; continue
    if re.match(r'^\d+\.\d+\s+\S', s):
        fmt(p, **HEAD2); n['标题'] += 1; continue
    if re.match(r'^\d+\s{2,}\S', s) and len(s) < 22:
        fmt(p, jc='left', line=320, first=0); n['标题'] += 1; continue
    if s.startswith(('摘　要', '关键词', 'Abstract', 'Key words')):
        fmt(p, sz=10, line=320, jc='both', first=0); n['篇首'] += 1; continue
    if s.startswith('引用格式'):
        fmt(p, sz=7.5, jc='both', first=0); n['篇首'] += 1; continue
    if s.startswith('通讯作者') or s.startswith('(') or s.startswith('（'):
        fmt(p, sz=9, first=0); n['篇首'] += 1; continue
    if s.startswith(('① 基金项目', '收稿时间', '作者简介', '通信地址', '收件人')) or \
       re.match(r'^(张卫兵|练维|徐小卫|王秦)\(', s):
        fmt(p, sz=9, line=280, rule='exact', first=0); n['篇首'] += 1; continue
    if re.match(r'^[A-Z]', s) and not re.search(r'[一-鿿]', s):
        fmt(p, sz=9 if s.startswith('YANG') else None, first=0)
        n['篇首'] += 1; continue
    if s.startswith('杨文超, 张卫兵') or '基于动态积分与标签画像' in s and len(s) < 30:
        n['篇首'] += 1; continue
    fmt(p, **BODY); n['正文'] += 1

# 页面设置
sect = body.find(W + 'sectPr')
if sect is not None:
    pg = sect.find(W + 'pgMar')
    if pg is not None:
        pg.set(W + 'top', '1701'); pg.set(W + 'left', '1134'); pg.set(W + 'right', '1077')

save(tree, SRC, 'work.bak7/word/document.xml')
print('已按模板实测参数排版：')
for k, v in n.items():
    print('   %-6s %3d 段' % (k, v))
print('   页边距：上 30 mm / 左 20 mm / 右 19 mm（模板实测值）')
