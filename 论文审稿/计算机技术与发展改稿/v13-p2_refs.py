# -*- coding: utf-8 -*-
"""P2 按新版顺序重排参考文献，并应用三处著录更正。

新版顺序相对旧版：16↔17 对调；旧 22（何立富）后移至 29，旧 23–29 各前移一位。
"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
kids = list(body)

start = next(i for i, c in enumerate(kids)
             if c.tag == W + 'p' and text_of(c).strip() == '参考文献')
end = next(i for i, c in enumerate(kids)
           if c.tag == W + 'p' and '基金项目' in text_of(c))

# 收集现有条目：编号 -> 正文（去掉 [n] 前缀）
items, slots = {}, []
for i in range(start + 1, end):
    p = kids[i]
    if p.tag != W + 'p':
        continue
    m = re.match(r'^\[(\d+)\]\s*(.+)$', text_of(p).strip())
    if not m:
        continue
    items[int(m.group(1))] = m.group(2)
    slots.append(p)
assert len(items) == 30, len(items)

# 三处著录更正
items[9] = items[9].replace('白菁昊, 庄俊玺.', '白菁昊, 庄俊玺, 赖英旭.')
items[15] = items[15].replace('现代信息技术,', '现代信息科技,')
items[17] = items[17].replace('计算机应用与软件, 2026(4):', '计算机应用与软件, 2026, 43(4):')

# 新序 → 旧序
NEW2OLD = {n: n for n in range(1, 31)}
NEW2OLD.update({16: 17, 17: 16, 22: 23, 23: 24, 24: 25,
                25: 26, 26: 27, 27: 28, 28: 29, 29: 22})
assert sorted(NEW2OLD.values()) == list(range(1, 31)), '映射不是双射'

for p, new_no in zip(slots, range(1, 31)):
    rewrite(p, '[%d] %s' % (new_no, items[NEW2OLD[new_no]]))

save(tree, SRC, 'ref.xml')
print('P2 done: 30 条参考文献已按新版顺序重排')
