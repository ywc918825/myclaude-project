# -*- coding: utf-8 -*-
"""定稿复审的机械核查部分：交叉引用、数字一致性、标点、残余重复、句长。

两轮精简动了摘要、引言、3.5、5 节与结论，最可能的伤是"删了 A 处的数，
B 处还在引它"或"删了解释句，结论句失去支撑"。这里把能自动查的先查掉。
"""
import re, sys, zipfile, xml.etree.ElementTree as ET
from collections import Counter

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
DOC = ('/home/user/myclaude-project/论文审稿/'
       '科研积分系统论文-计算机技术与发展版.docx')
root = ET.fromstring(zipfile.ZipFile(DOC).read('word/document.xml'))
body = root.find(W + 'body')


def txt(el):
    return ''.join(t.text or '' for t in el.iter(W + 't'))


blocks = [('p', txt(c)) if c.tag == W + 'p' else ('tbl', txt(c))
          for c in body if c.tag in (W + 'p', W + 'tbl')]
ps = [t for k, t in blocks if k == 'p']
ALL = '\n'.join(t for _, t in blocks)


def seg(a, b=None):
    i = next(i for i, t in enumerate(ps) if re.match(a, t.strip()))
    j = next((j for j, t in enumerate(ps) if b and re.match(b, t.strip())), len(ps))
    return '\n'.join(ps[i:j])


CN_ABS = next(t for t in ps if t.startswith('摘　要'))
EN_ABS = next(t for t in ps if t.startswith('Abstract'))
CONCL = seg(r'6\s+结论与展望', r'参考文献')
MAIN = seg(r'在“科教兴卫', r'参考文献')

print('=' * 62)
print('一、交叉引用完整性')
print('=' * 62)
for kind, pat, cite in (('图', r'图(\d+)\s\s', r'图(\d+)'),
                        ('表', r'表(\d+)\s\s', r'表(\d+)'),
                        ('式', None, r'式\s*\(\s*(\d+)\s*\)')):
    if pat:
        defined = sorted({int(x) for x in re.findall(pat, ALL)})
    else:
        defined = list(range(1, len(root.findall('.//' + M + 'oMath')) + 1))
    used = sorted({int(x) for x in re.findall(cite, ALL)})
    print('  %s：定义 %s' % (kind, defined))
    print('     引用 %s   未被引用 %s   引了但没定义 %s'
          % (used, sorted(set(defined) - set(used)) or '无',
             sorted(set(used) - set(defined)) or '无'))

print('\n' + '=' * 62)
print('二、摘要 / 正文 / 结论 的数字一致性')
print('=' * 62)
NUM = re.compile(r'\d+(?:\.\d+)?%?|\d+/\d+')
STOP = {'1', '2', '3', '4', '5', '6', '7', '8', '0', '16', '12', '46', '8.0',
        '7.2', '21', '24.04', '2024', '2025', '2026', '32', '500', '0.7',
        '0.14', '226001'}


def nums(s):
    return {x for x in NUM.findall(s) if x not in STOP}


ca, co, mn = nums(CN_ABS), nums(CONCL), nums(MAIN)
print('  摘要出现但正文没有：%s' % (sorted(ca - mn) or '无'))
print('  结论出现但正文没有：%s' % (sorted(co - mn) or '无'))
print('  摘要数字：%s' % sorted(ca))
print('  结论数字：%s' % sorted(co))

print('\n  中英文摘要要点对照：')
PAIRS = [('7 d', '7 d'), ('2 d', '2 d'), ('3.54', '3.54'), ('0.08', '0.08'),
         ('0.86', '0.86'), ('0.864', '0.864'), ('183', '183'), ('270', '270'),
         ('0.7', '0.7'), ('0.14', '0.14')]
for cn, en in PAIRS:
    a, b = cn in CN_ABS, en in EN_ABS
    if a != b:
        print('    !! %s 中文%s 英文%s' % (cn, '有' if a else '无', '有' if b else '无'))
else:
    print('    十项关键量中英文摘要均对应')

print('\n' + '=' * 62)
print('三、标点与字符')
print('=' * 62)
i_ref = next(i for i, t in enumerate(ps) if t.strip() == '参考文献')
front = '\n'.join(ps[:i_ref]) + '\n' + '\n'.join(t for k, t in blocks if k == 'tbl')
bad = []
for pat, name in ((r'[一-鿿],\s', 'CJK+半角逗号'), (r'[一-鿿];', 'CJK+半角分号'),
                  (r'[一-鿿]:', 'CJK+半角冒号'), (r'"', 'ASCII 直引号'),
                  (r'[0-9A-Za-z]\.\s+[一-鿿]', '数字/字母+半角句点+中文'),
                  (r'\(\s*[一-鿿]', '半角括号包中文'),
                  # 标题与图表题的"编号+两空格+题名"是该刊体例，不算问题
                  (r'(?<![\d.])(?<!表\d)(?<!图\d)  +', '正文内连续空格')):
    src = re.sub(r'^(?:\d+(?:\.\d+)?|[图表]\s*\d+)  +', '', front, flags=re.M)
    src = re.sub(r'[（;；]\s*\d+\.\s', '；', src)      # 单位署名 1. 2. 3. 体例
    hit = re.findall(pat, src)
    if hit:
        bad.append('%s ×%d' % (name, len(hit)))
        for m in list(re.finditer(pat, src))[:6]:
            print('    %-16s …%s…' % (name, src[max(0, m.start() - 20):m.start() + 14]))
print('  ' + ('、'.join(bad) if bad else '未发现问题'))

print('\n' + '=' * 62)
print('四、残余重复（正文内重复出现的 12 字片段）')
print('=' * 62)
body_txt = re.sub(r'\s+', '', MAIN)
c = Counter(body_txt[i:i + 12] for i in range(len(body_txt) - 12))
dup = [(k, v) for k, v in c.items() if v > 1]
seen = set()
out = []
for k, v in sorted(dup, key=lambda x: -x[1]):
    if any(k[:6] in s for s in seen):
        continue
    seen.add(k)
    out.append('    ×%d  %s' % (v, k))
print('\n'.join(out[:14]) if out else '    无')

print('\n' + '=' * 62)
print('五、句长与文风')
print('=' * 62)
sents = [s for s in re.split(r'[。？！]', re.sub(r'\s+', '', MAIN)) if len(s) > 4]
L = [len(s) for s in sents]
print('  正文 %d 句，平均 %.1f 字，≥50 字 %.0f%%，≥100 字 %d 句'
      % (len(L), sum(L) / len(L), 100 * sum(1 for x in L if x >= 50) / len(L),
         sum(1 for x in L if x >= 100)))
for pat, name in ((r'其一|其二|其三', '其一/其二/其三'), (r'——', '破折号'),
                  (r'值得注意的是|需要指出的是|众所周知|综上所述', '套话'),
                  (r'首先.{0,80}其次.{0,80}最后', '首先/其次/最后串')):
    n = len(re.findall(pat, MAIN))
    print('  %-16s 正文 %d 处' % (name, n))
print('  最长三句：')
for s in sorted(sents, key=len, reverse=True)[:3]:
    print('    %3d 字  %s…' % (len(s), s[:38]))
