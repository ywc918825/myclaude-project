# -*- coding: utf-8 -*-
"""按期刊排版口径估算本稿占版数，用于推算版面费。

口径说明：
  - 中文期刊说的"字数"通常指**全文字符数（计空格）**，与 Word 状态栏的
    「字符数（计空格）」一致，含题名、摘要、正文、图表文字、参考文献。
  - 《计算机技术与发展》为 A4（大 16 开）双栏、五号宋体排版，
    满页纯文字约 2 200~2 600 字，这里取三档分别算。
  - 图、表、独立公式占版但字数少，要单独折算。
"""
import re, sys, zipfile, xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
DOC = sys.argv[1] if len(sys.argv) > 1 else \
    '/home/user/myclaude-project/论文审稿/科研积分系统论文-计算机技术与发展版.docx'

z = zipfile.ZipFile(DOC)
root = ET.fromstring(z.read('word/document.xml'))
body = root.find(W + 'body')


def txt(el):
    return ''.join(t.text or '' for t in el.iter(W + 't'))


# ── 按块顺序取文本，表格单独计 ────────────────────────────────────
seq = []          # (kind, text)
for ch in body:
    if ch.tag == W + 'p':
        seq.append(('p', txt(ch)))
    elif ch.tag == W + 'tbl':
        rows = ch.findall(W + 'tr')
        seq.append(('tbl', txt(ch)))
        seq.append(('#rows', str(len(rows))))

full = ''.join(t for k, t in seq if k in ('p', 'tbl'))

# ── 分段：前置 / 正文 / 参考文献 / 文末 ───────────────────────────
def locate(pat):
    for i, (k, t) in enumerate(seq):
        if k == 'p' and re.match(pat, t.strip()):
            return i
    return -1


i_kw = locate(r'Key\s*words?\s*[:：]')          # 英文关键词，前置部分的最后一段
i_body = i_kw + 1 if i_kw >= 0 else locate(r'1\s+系统总体架构')
i_ref = locate(r'参\s*考\s*文\s*献')
i_end = locate(r'[①\*]?\s*基金项目')             # 文末信息起点
if i_end < 0:
    i_end = len(seq)


def count(lo, hi):
    return sum(len(t) for k, t in seq[lo:hi] if k in ('p', 'tbl'))


parts = [('前置(题名/作者/摘要/关键词/英文摘要)', 0, i_body),
         ('正文(含表内文字)', i_body, i_ref),
         ('参考文献', i_ref, i_end),
         ('文末信息', i_end, len(seq))]

print('文件：%s\n' % DOC)
print('=== 各部分字符数（计空格）===')
for name, lo, hi in parts:
    print('  %-36s %6d' % (name, count(lo, hi)))
print('  %-36s %6d' % ('合计（期刊口径"全文字数"）', len(full)))

# ── 非文字元素 ────────────────────────────────────────────────────
nfig = len(root.findall('.//' + W + 'drawing')) + \
       len(root.findall('.//{urn:schemas-microsoft-com:vml}imagedata'))
ntbl = len([c for c in body if c.tag == W + 'tbl'])
nrow = sum(int(t) for k, t in seq if k == '#rows')
nomml = len(root.findall('.//' + M + 'oMathPara')) or len(root.findall('.//' + M + 'oMath'))
neq = len(re.findall(r'式\s*\(\s*\d+\s*\)', full))
print('\n=== 非文字占版 ===')
print('  图 %d 张、表 %d 张(共 %d 行)、独立公式约 %d 个（oMath 节点 %d）'
      % (nfig, ntbl, nrow, 7, nomml))

# ── 折版 ──────────────────────────────────────────────────────────
FIG = 0.28      # 一张双栏图约占 1/4 版多
ROW = 0.030     # 三线表每行约占 3% 版（含表题、表注、行距）
EQ  = 0.035     # 一个独立公式约占 3.5% 版
extra = nfig * FIG + nrow * ROW + 7 * EQ
print('\n=== 版面估算 ===')
print('  非文字折算：图 %.2f 版 + 表 %.2f 版 + 公式 %.2f 版 = %.2f 版'
      % (nfig * FIG, nrow * ROW, 7 * EQ, extra))
print('  %-12s %-10s %-10s %-10s' % ('每版字数', '纯文字版', '合计版', '排版取整'))
for per in (2200, 2400, 2600):
    t = len(full) / per
    tot = t + extra
    import math
    print('  %-12d %-10.2f %-10.2f %d 版' % (per, t, tot, math.ceil(tot)))

# ── 若按用户口径 9000 字 ──────────────────────────────────────────
import math
print('\n=== 若按"全文 9000 字"计（需先删减约 %d 字）===' % (len(full) - 9000))
for per in (2200, 2400, 2600):
    tot = 9000 / per + extra
    print('  每版 %d 字 → %.2f 版 → 取整 %d 版' % (per, tot, math.ceil(tot)))
