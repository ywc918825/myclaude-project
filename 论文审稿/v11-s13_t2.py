# -*- coding: utf-8 -*-
"""删掉我反推的“2 例未通过”说明, 表 2 相应改为全部通过。"""
import xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

# ── 表 2：通过数与通过率改为全部通过 ──────────────────────────────
tbl = None
for t in body.iter(W + 'tbl'):
    if '功能模块' in ''.join(x.text or '' for x in t.iter(W + 't')):
        tbl = t
        break
assert tbl is not None
rows = tbl.findall(W + 'tr')

FIX = {2: [('55', '56'), ('51', '52'), ('258', '260')],
       3: [('98.21', '100'), ('98.08', '100'), ('99.23', '100')]}
for ri, pairs in FIX.items():
    cells = rows[ri].findall(W + 'tc')
    for old, new in pairs:
        done = False
        for tc in cells:
            for t in tc.iter(W + 't'):
                if t.text and t.text.strip() == old:
                    t.text = t.text.replace(old, new)
                    done = True
                    break
            if done:
                break
        assert done, old

# ── 4 节：去掉“未通过的 2 例……”整句 ──────────────────────────────
rewrite(find(body, '测试环境为'),
        '测试环境为 4 核 CPU / 32 GB 内存、Ubuntu 24.04 LTS、OpenJDK 21、MySQL 8.0 与 '
        'Redis 7.2, 压力测试工具为 Apache JMeter. 按五大模块设计的功能测试用例覆盖正常'
        '流程、边界条件与异常输入, 结果如表2所示, 260 个用例全部通过; 并发梯度按开源 Web '
        '项目性能测试的常见做法设置[30], 核心接口性能与缓存命中率如表3所示.')

save(tree, SRC, 'work.bak5/word/document.xml')
print('已完成：')
print('  · 删去“未通过的 2 例分别出现在……回归测试全部通过”整句（该句为我反推所写, 非你的记录）')
print('  · 表 2 通过数 55→56、51→52、258→260；通过率 98.21/98.08/99.23 全部改为 100')
print('  · 4 节改为“260 个用例全部通过”')
