# -*- coding: utf-8 -*-
"""W1 按模板正文文件（e08e073c）对齐字面体例。

模板里能确定的写法（repr 取自 .doc 原文，均为半角空格）：
    '0 引言'  '1 一级标题'  '1.1 二级标题'  '1.2.1 三级标题'   ← 编号后一个空格
    '图1 图的题目' / 'Fig.1 Pic title'                      ← Fig. 后不空格
    '表1 表的题目' / 'Table 1 Table title'                  ← Table 后空一格
    '摘要：'                                               ← 不是"摘　要："
    '(1.上标为1的作者的工作单位 二级单位，所在城市 邮编；2.…)'   ← 半角括号，序号后不空格

现稿这些位置一律用的是两个空格、'Fig. 1'、'摘　要：'、全角括号，逐项改齐。

**不跟的两处**，模板自身在这里前后矛盾，判断是输入法没切换：
  英文单位行写成 '…author2；2. Communication address of author2、author3…'
  —— 英文里出现全角分号和顿号，同一模板的 'Abstract: ' 却是半角冒号。
  照抄会把明显的排版错误抄进稿子，故英文行仍用半角 '; '，
  'Key words: ' 也维持半角冒号（与 'Abstract: ' 一致）。
"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, save
from rlib import run_replace, para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
n = 0


def fix(p, old, new, tag):
    global n
    run_replace(p, old, new)
    n += 1
    print('  %-10s %-34r → %r' % (tag, old[:34], new[:34]))


# ── 1. 各级标题：编号后两空格 → 一空格 ──────────────────────────
HEAD = re.compile(r'^(\d+(?:\.\d+)*)  (\S)')
for p in [c for c in body if c.tag == W + 'p']:
    t = para_text(p).strip()
    m = HEAD.match(t)
    if m and len(t) < 30:
        fix(p, '%s  %s' % (m.group(1), m.group(2)),
            '%s %s' % (m.group(1), m.group(2)), '标题')

# ── 2. 图表题：中文两空格 → 一空格；Fig. N → Fig.N；Table N 保留空格 ──
for p in [c for c in body if c.tag == W + 'p']:
    t = para_text(p).strip()
    m = re.match(r'^([图表])(\d+)  (\S)', t)
    if m:
        fix(p, '%s%s  %s' % m.groups(), '%s%s %s' % m.groups(), '中文题')
        continue
    m = re.match(r'^Fig\. (\d+)  (\S)', t)
    if m:
        fix(p, 'Fig. %s  %s' % m.groups(), 'Fig.%s %s' % m.groups(), '英文图题')
        continue
    m = re.match(r'^Table (\d+)  (\S)', t)
    if m:
        fix(p, 'Table %s  %s' % m.groups(), 'Table %s %s' % m.groups(), '英文表题')

# ── 3. 摘要标签 ─────────────────────────────────────────────────
fix(find(body, '摘　要：'), '摘　要：', '摘要：', '摘要')

# ── 4. 单位行：全角括号 → 半角，序号后不空格（模板体例）──────────
p = find(body, '南通市疾病预防控制中心 科研与质量管理科')
t = para_text(p)
new = ('(' + t.strip()[1:-1].replace('1. ', '1.').replace('2. ', '2.')
       .replace('3. ', '3.') + ')')
fix(p, t.strip(), new, '中文单位')

save(tree, SRC, 'ref.xml')
print('W1 done：按模板改 %d 处' % n)
