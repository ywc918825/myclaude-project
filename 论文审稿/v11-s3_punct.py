# -*- coding: utf-8 -*-
"""第三步：全文标点改为《计算机系统应用》的半角式样（顿号、引号、书名号保留全角）。"""
import re, xml.etree.ElementTree as ET
from lib import W, register, text_of, save

XS = '{http://www.w3.org/XML/1998/namespace}space'
SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

MAP = {'，': ', ', '。': '. ', '；': '; ', '：': ': ',
       '（': '(', '）': ')', '？': '? ', '！': '! ',
       '～': '–', '％': '%', '　 ': '　'}
SKIP = ('引用格式',)          # 该行模板用紧排标点，不加空格

n_par = n_chr = 0
for p in body.iter(W + 'p'):
    whole = text_of(p)
    if any(k in whole[:6] for k in SKIP):
        continue
    ts = [t for t in p.iter(W + 't')]
    if not ts:
        continue
    hit = 0
    for t in ts:
        if not t.text:
            continue
        s = t.text
        for a, b in MAP.items():
            if a in s:
                hit += s.count(a)
                s = s.replace(a, b)
        t.text = s
    if not hit:
        continue
    # 跨 run 的重复空格清理
    prev = None
    for t in ts:
        if t.text is None:
            continue
        if prev is not None and prev.text and prev.text.endswith(' '):
            t.text = t.text.lstrip(' ')
        if t.text:
            prev = t
    # 段末不留空格
    for t in reversed(ts):
        if t.text and t.text.strip():
            t.text = t.text.rstrip()
            break
    for t in ts:
        if t.text and (t.text[:1] == ' ' or t.text[-1:] == ' '):
            t.set(XS, 'preserve')
    n_par += 1
    n_chr += hit

save(tree, SRC, 'work.bak/word/document.xml')
print('已把 %d 个段落中的 %d 个全角标点改为半角式样（，。；：（）→ , . ; : ( )）；'
      '顿号、引号、书名号按模板保留全角。' % (n_par, n_chr))
