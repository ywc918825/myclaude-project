# -*- coding: utf-8 -*-
"""S4 半角标点 → 全角。英文块、参考文献、公式号、版本号、邮箱、引文角标一律保护。"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, text_of, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

CJK = r'一-鿿　-〿＀-￯'
PROTECT = [
    r'[\w.+-]+@[\w.-]+\.\w+',        # 邮箱
    r'https?://\S+', r'www\.\S+',    # 网址
    r'E-?mail\s*:',                  # 邮箱标签
    r'\d+\.\d+',                     # 小数 / 版本号 24.04 8.0 3.54
    r'\d+:\d+',                      # 时间 2:00
    r'\[[\d,\s–—-]+\]',    # 引文角标 [12,17] [1-2]
    r'式\(\d+\)',                    # 式(1)
    r'[A-Za-z][A-Za-z0-9]*\.[A-Za-z]{1,4}\b',   # Vue.js Node.js
    r'GB/T\s*[\d.-]+',
    r'et al\.',
]
PAT = re.compile('|'.join('(?:%s)' % p for p in PROTECT))

SKIP_SIG = ('Abstract:', 'Key words:', 'A Dynamic-Points', 'YANG Wen-chao',
            'Division of Research and Quality', '中图分类号')


def mask(s):
    store = []
    def sub(m):
        store.append(m.group(0))
        return '\x00%d\x00' % (len(store) - 1)
    return PAT.sub(sub, s), store


def unmask(s, store):
    return re.sub(r'\x00(\d+)\x00', lambda m: store[int(m.group(1))], s)


def convert(s):
    s, store = mask(s)
    # 逗号 / 分号 / 冒号：前后任一侧为中日韩字符即转全角
    for half, full in ((',', '，'), (';', '；'), (':', '：')):
        s = re.sub(r'(?<=[%s])%s\s*' % (CJK, re.escape(half)), full, s)
        s = re.sub(r'%s\s+(?=[%s])' % (re.escape(half), CJK), full, s)
    # 句号：后接中日韩字符，或位于含中文段落的末尾
    s = re.sub(r'\.\s+(?=[%s])' % CJK, '。', s)
    if re.search(r'[%s]' % CJK, s):
        s = re.sub(r'\.\s*$', '。', s)
    # 括号：内含中文，或紧邻中文
    def par(m):
        inner = m.group(1)
        left = s[:m.start()][-1:] if m.start() else ''
        right = s[m.end():m.end() + 1]
        if re.search(r'[%s]' % CJK, inner) or re.search(r'[%s]' % CJK, left + right):
            return '（%s）' % inner
        return m.group(0)
    s = re.sub(r'\(([^()]*)\)', par, s)
    s = unmask(s, store)
    return re.sub(r'([，；：。（])\s+', r'\1', s)


# 参考文献区间（GB/T 7714 用半角，跳过）
kids = list(body)
ref_start = next(i for i, c in enumerate(kids)
                 if c.tag == W + 'p' and text_of(c).strip() == '参考文献')
ref_end = next(i for i, c in enumerate(kids)
               if c.tag == W + 'p' and '基金项目' in text_of(c))

n = 0
for i, p in enumerate(kids):
    if p.tag != W + 'p':
        continue
    if ref_start < i < ref_end:
        continue
    t = text_of(p)
    if not t.strip() or any(t.lstrip().startswith(x) or x in t[:40] for x in SKIP_SIG):
        continue
    if not re.search(r'[%s]' % CJK, t):
        continue
    for tnode in p.iter(W + 't'):
        old = tnode.text or ''
        if not old:
            continue
        new = convert(old)
        if new != old:
            tnode.text = new
            n += 1

# 表格单元格同样处理（表格不在 body 直接子节点的 p 里）
for tbl in body.iter(W + 'tbl'):
    for tnode in tbl.iter(W + 't'):
        old = tnode.text or ''
        if old and re.search(r'[%s]' % CJK, old):
            new = convert(old)
            if new != old:
                tnode.text = new
                n += 1

save(tree, SRC, 'ref.xml')
print('S4 done: %d 处文本节点标点已转全角' % n)
