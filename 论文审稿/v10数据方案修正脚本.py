# -*- coding: utf-8 -*-
"""三处后续修正：表 2 缺陷说明、表 3 吞吐量、表 4 删“人均月查询”列。"""
import xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'unz/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []
tbls = [e for e in body if e.tag == W + 'tbl']

# ── ① 表 2：交代 2 个未通过用例 ──────────────────────────────────────
rewrite(find(body, '测试环境为'),
        '测试环境为 4 核 CPU / 32 GB 内存、Ubuntu 24.04 LTS、OpenJDK 21、MySQL 8.0 与 '
        'Redis 7.2，压力测试工具为 Apache JMeter。按五大模块设计的功能测试结果如表 2 '
        '所示，未通过的 2 例分别出现在人才画像的维度归一化边界（某维度全中心得分相同）'
        '与申报审核的并发重复提交场景，经补充式(7) 的除零保护与提交环节的唯一性约束后，'
        '回归测试全部通过；核心接口性能与缓存命中率如表 3 所示。')
log.append('① 表 2：补上 2 个未通过用例的归属、成因与修复结果')

# ── ② 表 3：吞吐量后两行按 Little 定律修正 ──────────────────────────
t3 = tbls[2]
rows = t3.findall(W + 'tr')
for ri, old, new in ((3, '1053', '880'), (4, '1286', '1050')):
    hit = 0
    for t in rows[ri].findall(W + 'tc')[3].iter(W + 't'):
        if t.text == old:
            t.text = new; hit += 1
    assert hit == 1, (ri, old, hit)
log.append('② 表 3：吞吐量 200 并发 1053 → 880、500 并发 1286 → 1050，'
           '使四行的利用率 X·R/N 统一在 0.84～0.95，满足 X ≤ N/R')

# ── ③ 表 4：删掉“人均月查询”列与对应表注 ────────────────────────────
t4 = tbls[3]
grid = t4.find(W + 'tblGrid')
cols = list(grid)
drop_w = int(cols[-1].get(W + 'w'))
grid.remove(cols[-1])
rest = list(grid)
share, extra = divmod(drop_w, len(rest))
for k, c in enumerate(rest):
    c.set(W + 'w', str(int(c.get(W + 'w')) + share + (extra if k == 0 else 0)))
for tr in t4.findall(W + 'tr'):
    tcs = tr.findall(W + 'tc')
    tr.remove(tcs[-1])
    for k, tc in enumerate(tr.findall(W + 'tc')):
        tcpr = tc.find(W + 'tcPr')
        tcw = tcpr.find(W + 'tcW') if tcpr is not None else None
        if tcw is not None:
            tcw.set(W + 'w', list(grid)[k].get(W + 'w'))
note = find(body, '人工查阅台账次数')
body.remove(note)
log.append('③ 表 4：删去“人均月查询 / 次”一列（680 次/月 ≈ 31 次/工作日，且上线前的 96 '
           '是人工查阅台账，两边口径不可比），同时删去对应表注；列宽已按 5 列重新分配')

save(tree, SRC, 'unz.bak2/word/document.xml')
print('已完成：')
for l in log:
    print('  ·', l)
