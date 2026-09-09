# -*- coding: utf-8 -*-
"""S3 新增表5“本文系统与同类工作的对比”，并把 4 张表统一为三线表。"""
import sys, copy, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
kids = list(body)

tbl1 = next(c for c in kids if c.tag == W + 'tbl')
cap1 = find(body, '表1  多作者积分分配方法对比')

# ── 构造 表5 ────────────────────────────────────────────────────────
ROWS = [
    ['对比维度',      '文献[1,3]', '文献[2]',   '文献[8,9]',  '文献[10,11]', '本文'],
    ['评价对象',      '机构',      '机构',      '个人(用户)', '个人(用户)',  '个人(科研人员)'],
    ['核心方法',      '指标体系',  '数字化系统', '用户画像',   '兴趣建模',    '积分量化与画像'],
    ['多作者成果分配', '—',        '—',         '—',         '—',          '分段权重法(式(1))'],
    ['成果时效处理',  '—',        '—',         '时序动态标签', '指数加权/时间衰减', '前置嵌入归一化(式(4))'],
    ['量化与画像同源', '—',        '—',         '—',         '—',          '是'],
    ['审批流程支持',  '—',        '—',         '—',         '—',          '自研状态机引擎'],
]

new_tbl = copy.deepcopy(tbl1)
for tr in new_tbl.findall(W + 'tr'):
    new_tbl.remove(tr)
src_rows = tbl1.findall(W + 'tr')
hdr_tpl, dat_tpl = src_rows[0], src_rows[1]

for ri, vals in enumerate(ROWS):
    tr = copy.deepcopy(hdr_tpl if ri == 0 else dat_tpl)
    tcs = tr.findall(W + 'tc')
    assert len(tcs) == len(vals), (len(tcs), len(vals))
    for tc, v in zip(tcs, vals):
        cps = tc.findall(W + 'p')
        rewrite(cps[0], v)
        for extra in cps[1:]:
            tc.remove(extra)
    new_tbl.append(tr)

# ── 三线表：只留上下框线与表头下线 ──────────────────────────────────
def three_line(tbl):
    for bd in tbl.iter(W + 'tblBorders'):
        for e in list(bd):
            tag = e.tag.replace(W, '')
            e.set(W + 'val', 'single' if tag in ('top', 'bottom') else 'none')
            e.set(W + 'sz', '8' if tag in ('top', 'bottom') else '0')
    rows = tbl.findall(W + 'tr')
    if not rows:
        return
    for tc in rows[0].findall(W + 'tc'):
        tcPr = tc.find(W + 'tcPr')
        if tcPr is None:
            continue
        bds = tcPr.find(W + 'tcBorders')
        if bds is None:
            bds = ET.SubElement(tcPr, W + 'tcBorders')
        for e in list(bds):
            if e.tag == W + 'bottom':
                bds.remove(e)
        b = ET.SubElement(bds, W + 'bottom')
        b.set(W + 'val', 'single'); b.set(W + 'sz', '4')
        b.set(W + 'color', '000000'); b.set(W + 'space', '0')

for tb in [c for c in body if c.tag == W + 'tbl']:
    three_line(tb)
three_line(new_tbl)

# ── 插入：引出句 + 表题 + 表 + 表注，放在第 4 节末尾 ────────────────
anchor = find(body, '需说明统计口径')
pos = list(body).index(anchor) + 1

lead = copy.deepcopy(anchor)
rewrite(lead, '为进一步说明本文工作与同类研究的差异, 表5 从评价对象、核心方法、'
              '多作者成果分配、成果时效处理、量化与画像的耦合方式及审批流程支持'
              '六个方面进行了对比.')
cap = copy.deepcopy(cap1)
rewrite(cap, '表5  本文系统与同类工作的对比')
note = copy.deepcopy(anchor)
rewrite(note, '注: 表中对同类工作的归纳依据其公开文献所述的研究对象与方法, '
              '“—”表示该文献未涉及该方面.')

for off, el in enumerate([lead, cap, new_tbl, note]):
    body.insert(pos + off, el)

save(tree, SRC, 'ref.xml')
print('S3 done: 表5 已插入, 5 张表均转为三线表')
