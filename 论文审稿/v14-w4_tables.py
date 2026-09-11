# -*- coding: utf-8 -*-
"""W4 删表2（功能测试回归结果），其余表顺次前移。

表2 五个模块的通过率全是 100%，整张表只承载"260 个用例全部通过"一条信息，
而这条信息在摘要、4 节正文与结论里各出现一次。改为正文一句话，模块用例数
照录不丢。4 节仍保留性能测试表与上线前后对比表两张。

表7（Top-N 重合度）不动：它的 6 个数里 Top-10 那一行别处没有，
且删实验节的表会削弱"有实验"的观感，省下的半版不值这个险。
"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, save
from rlib import run_replace, para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
root = tree.getroot()
body = root.find(W + 'body')

# ── 1. 表2 的内容并入正文 ────────────────────────────────────────
run_replace(find(body, '测试环境为 4 核 CPU'),
            '缺陷修复后的回归测试结果如表2所示，260 个用例全部通过；',
            '积分管理、人才画像、统计分析、申报审核与系统管理五个模块的用例数'
            '分别为 68、56、47、52 与 37，缺陷修复后的回归测试中 260 个用例'
            '全部通过；')

# ── 2. 删表题与表体 ──────────────────────────────────────────────
cap = find(body, '表2  功能测试回归结果')
kids = list(body)
tbl = next(c for c in kids[kids.index(cap):] if c.tag == W + 'tbl')
print('删除：%s（%d 行）' % (para_text(cap), len(tbl.findall(W + 'tr'))))
body.remove(tbl)
body.remove(cap)

# ── 3. 表号前移 3→2, 4→3, 5→4, 6→5, 7→6, 8→7 ────────────────────
MAP = {3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7}
NUM = re.compile(r'表([1-8])')
SENT = '%d'
n = 0
for p in root.iter(W + 'p'):
    t = para_text(p)
    hits = [m.group(0) for m in NUM.finditer(t) if int(m.group(1)) in MAP]
    if not hits:
        continue
    for k, tok in enumerate(hits):
        run_replace(p, tok, SENT % k)
    for k, tok in enumerate(hits):
        run_replace(p, SENT % k, '表%d' % MAP[int(tok[1])])
        n += 1
    print('  %s → %s' % (t[:30], para_text(p)[:30]))
print('表号改写 %d 处' % n)

save(tree, SRC, 'ref.xml')
print('W4 done: 表 8 张 → 7 张')
