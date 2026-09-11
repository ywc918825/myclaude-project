# -*- coding: utf-8 -*-
"""删掉表 3 的吞吐量列——该列 200/500 两档为反推值，非实测。"""
import xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

tbl = None
for t in body.iter(W + 'tbl'):
    if '并发用户数' in ''.join(x.text or '' for x in t.iter(W + 't')):
        tbl = t
        break
assert tbl is not None

rows = tbl.findall(W + 'tr')
hdr = [' '.join(''.join(x.text or '' for x in p.iter(W + 't')) for p in tc.findall(W + 'p'))
       for tc in rows[0].findall(W + 'tc')]
col = next(i for i, h in enumerate(hdr) if '吞吐' in h)

grid = tbl.find(W + 'tblGrid')
cols = list(grid)
drop_w = int(cols[col].get(W + 'w'))
grid.remove(cols[col])
rest = list(grid)
share, extra = divmod(drop_w, len(rest))
for k, c in enumerate(rest):
    c.set(W + 'w', str(int(c.get(W + 'w')) + share + (extra if k == 0 else 0)))
for tr in rows:
    tcs = tr.findall(W + 'tc')
    tr.remove(tcs[col])
    for k, tc in enumerate(tr.findall(W + 'tc')):
        tcpr = tc.find(W + 'tcPr')
        tcw = tcpr.find(W + 'tcW') if tcpr is not None else None
        if tcw is not None:
            tcw.set(W + 'w', list(grid)[k].get(W + 'w'))

# 4 节那句“核心接口性能”不必改，但把并发范围写法与表头统一
p = find(body, '测试环境为')
s = text_of(p)
rewrite(p, s)

save(tree, SRC, 'work.bak3/word/document.xml')
print('表 3 已删去“吞吐量 / (次·s⁻¹)”列，剩余 5 列全部为实测：')
print('   并发用户数 | 平均响应/ms | 95%响应/ms | 错误率/% | 缓存命中率/%')
