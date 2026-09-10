# -*- coding: utf-8 -*-
"""按"字宽当量"重算占版，并逐段列出可压缩空间。

为什么要按字宽当量算
--------------------
排版时一个西文字符只占半个汉字宽。本稿英文摘要 2 223 字符、参考文献含大量西文，
若按字符数等权计算会高估占版。这里以汉字 = 1、半角 = 0.5 折算"字宽当量"，
再按满页当量数估版；期刊说的"字数"仍按字符数报（与 Word 状态栏一致）。
"""
import re, sys, math, zipfile, xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
DOC = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/user/myclaude-project/论文审稿/科研积分系统论文-计算机技术与发展版.docx'

root = ET.fromstring(zipfile.ZipFile(DOC).read('word/document.xml'))
body = root.find(W + 'body')


def txt(el):
    return ''.join(t.text or '' for t in el.iter(W + 't'))


def width(s):
    """字宽当量：CJK 与全角标点按 1，其余按 0.5。"""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if (0x4E00 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F
                or 0xFF00 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6):
            w += 1
        else:
            w += 0.5
    return w


seq = []
for ch in body:
    if ch.tag == W + 'p':
        seq.append(('p', txt(ch), 0))
    elif ch.tag == W + 'tbl':
        seq.append(('tbl', txt(ch), len(ch.findall(W + 'tr'))))


def locate(pat):
    for i, (k, t, _) in enumerate(seq):
        if k == 'p' and re.match(pat, t.strip()):
            return i
    return -1


i_body = locate(r'Key\s*words?\s*[:：]') + 1
i_ref = locate(r'参\s*考\s*文\s*献')
i_end = locate(r'[①\*]?\s*基金项目')

parts = [('前置(题名/作者/中英文摘要/关键词)', 0, i_body),
         ('正文(含表内文字)', i_body, i_ref),
         ('参考文献 29 条', i_ref, i_end),
         ('文末信息(基金/作者简介/通信地址)', i_end, len(seq))]

print('=== 字符数 vs 字宽当量 ===')
print('  %-34s %8s %10s' % ('', '字符数', '字宽当量'))
tc = tw = 0
for name, lo, hi in parts:
    c = sum(len(t) for k, t, _ in seq[lo:hi])
    w = sum(width(t) for k, t, _ in seq[lo:hi])
    tc += c
    tw += w
    print('  %-34s %8d %10.0f' % (name, c, w))
print('  %-34s %8d %10.0f' % ('合计', tc, tw))
print('  西文占比导致的当量缩水：%.0f 当量（%.0f%%）' % (tc - tw, 100 * (tc - tw) / tc))

# ── 非文字 ────────────────────────────────────────────────────────
nfig = len(root.findall('.//' + W + 'drawing'))
tbls = [(i, r) for i, (k, t, r) in enumerate(seq) if k == 'tbl']
nrow = sum(r for _, r in tbls)
neq = len(root.findall('.//' + M + 'oMath'))
FIG, ROW, EQ = 0.28, 0.030, 0.035
extra = nfig * FIG + nrow * ROW + neq * EQ
print('\n=== 非文字占版 ===')
print('  图 %d 张 = %.2f 版；表 %d 张共 %d 行 = %.2f 版；独立公式 %d 个 = %.2f 版；合计 %.2f 版'
      % (nfig, nfig * FIG, len(tbls), nrow, nrow * ROW, neq, neq * EQ, extra))

print('\n=== 占版估算（满页当量数 = 每版可排汉字数）===')
for per in (2200, 2400, 2600):
    t = tw / per
    print('  每版 %d → 文字 %.2f 版 + 非文字 %.2f 版 = %.2f 版 → 取整 %d 版'
          % (per, t, extra, t + extra, math.ceil(t + extra)))


# ── 逐项可压缩空间 ────────────────────────────────────────────────
print('\n\n=== 可压缩项清单（当量 / 折合版数，按每版 2400 计）===')
CUTS = [
    ('A 删表2(功能测试回归表, 全 100% 无信息量), 改写成一句话', 83 * 0.8, 4 * ROW + 0.04),
    ('A 删表7(Top-N 重合度, 6 个数), 并入正文一句话', 62 * 0.8, 4 * ROW + 0.04),
    ('A 删弱引文 [13][14][16][19][21][28] 六条', 217 + 78 + 71 + 127 + 161 + 72, 0),
    ('A 删 P018 "已有文献分别以 SpringBoot 与 Flask 实现…" 凑引句', 86, 0),
    ('B 作者简介由 5 人减为 2 人(第一作者+通信作者)', 68 + 70 + 70, 0),
    ('B P031 名义分值制理由重复表述合并', 80, 0),
    ('B P039 尾句"其合成效果见 3.3 节"(本身即在 3.3, 属笔误)删去', 42, 0),
    ('B P061 表4 口径说明压缩', 60, 0),
    ('C 英文摘要由 2223 字符压到约 1500 字符', (2223 - 1500) * 0.5, 0),
    ('C P016 相关工作段收紧', 90, 0),
    ('C P022 模块罗列收紧', 60, 0),
]
tot_w = tot_p = 0
for name, w, p in CUTS:
    pg = w / 2400 + p
    tot_w += w
    tot_p += pg
    print('  %-52s %6.0f 当量   %.3f 版' % (name, w, pg))
print('  %-52s %6.0f 当量   %.2f 版' % ('合计', tot_w, tot_p))

for per in (2200, 2400, 2600):
    now = tw / per + extra
    aft = (tw - tot_w) / per + extra - (tot_p - tot_w / 2400)
    print('\n  每版 %d：%.2f 版 → %.2f 版（取整 %d → %d）'
          % (per, now, aft, math.ceil(now), math.ceil(aft)))
