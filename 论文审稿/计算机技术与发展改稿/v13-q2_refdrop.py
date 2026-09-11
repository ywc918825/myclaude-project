# -*- coding: utf-8 -*-
"""Q2 删除文献[27]（持久内存 B+ 树索引优化综述），28–30 依次前移。

3.6 节原以该文献支撑"索引列顺序与选择性"的做法，而其主题是持久内存上的
B+ 树结构优化，两者不对题；弱引文比不引更伤。删引文后该条成为悬挂条目，
故一并删除。剩余 29 条仍远超该刊 ≥15 条的要求，外文 9 条不受影响。
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

slots, items = [], {}
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
assert '持久内存' in items[27], items[27]

keep = [n for n in range(1, 31) if n != 27]
for p, (new_no, old_no) in zip(slots, enumerate(keep, 1)):
    rewrite(p, '[%d] %s' % (new_no, items[old_no]))
body.remove(slots[-1])          # 少一条，移除末尾空出的段落

save(tree, SRC, 'ref.xml')
print('Q2 done: 已删除[27], 现 %d 条' % len(keep))
