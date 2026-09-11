# -*- coding: utf-8 -*-
"""第六步：篇首块序按模板归位——中文摘要/关键词/引用格式在前，英文题名块在后。"""
import xml.etree.ElementTree as ET
from lib import W, register, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

en_title = find(body, 'A CDC Research Talent Evaluation')
en_auth = find(body, 'YANG Wen-Chao')
en_aff = find(body, 'Division of Research and Quality Management')
cite = find(body, '引用格式')

for p in (en_title, en_auth, en_aff):
    body.remove(p)
pos = list(body).index(cite) + 1
for p in (en_title, en_auth, en_aff):
    body.insert(pos, p)
    pos += 1

save(tree, SRC, 'work.bak/word/document.xml')
order = [text_of(p)[:34] for p in list(body)[:13] if p.tag == W + 'p']
print('篇首现序：')
for i, s in enumerate(order, 1):
    print('  %2d  %s' % (i, s))
