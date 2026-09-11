# -*- coding: utf-8 -*-
"""删掉 6 条随 Java 技术栈失去落点的文献, 30 → 24 条, 并重排正文标注。"""
import re, xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

DROP = [14, 15, 22, 27, 28, 29]      # Spring Boot 微服务编排 / Spring Boot 公卫平台 /
                                     # Spring Security / kRedis / B+树索引 / Spring Security+JWT
KEEP = [n for n in range(1, 31) if n not in DROP]
MAP = {old: new for new, old in enumerate(KEEP, 1)}

# 1) 正文标注重排（只动仍带旧号的段落；1 节与 4 节我改写时已用新号）
FIX = [
    ('系统设计了五大功能模块', [('[16]', '[14]'), ('[18-21]', '[16-19]')]),
    ('多作者成果的积分分配是量化评价的难点', [('[23]', '[20]'), ('[24]', '[21]')]),
    ('式(1)采用名义分值制', [('[23,24]', '[20,21]')]),
    ('针对疾控中心审核流程相对固定', [('[25-26]', '[22-23]')]),
]
for needle, pairs in FIX:
    p = find(body, needle)
    s = text_of(p)
    for a, b in pairs:
        assert a in s, (needle, a)
        s = s.replace(a, b, 1)
    rewrite(p, s)

# 2) 删条目并重编号
refs = {}
started = False
for p in list(body):
    if p.tag != W + 'p':
        continue
    s = text_of(p).strip()
    if s == '参考文献':
        started = True
        continue
    m = re.match(r'^(\d+)\s+(.*)$', s, re.S)
    if started and m:
        refs[int(m.group(1))] = p
for n in DROP:
    body.remove(refs[n])
for old in KEEP:
    p = refs[old]
    s = text_of(p).strip()
    rewrite(p, re.sub(r'^\d+', str(MAP[old]), s, count=1))

save(tree, SRC, 'work.bak4/word/document.xml')
print('参考文献 30 → %d 条；删去原 %s。' % (len(KEEP), DROP))
