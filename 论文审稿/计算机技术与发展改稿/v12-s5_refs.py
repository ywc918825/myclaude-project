# -*- coding: utf-8 -*-
"""S5 参考文献改 GB/T 7714-2015；文末信息规整。"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
kids = list(body)

ref_start = next(i for i, c in enumerate(kids)
                 if c.tag == W + 'p' and text_of(c).strip() == '参考文献')
ref_end = next(i for i, c in enumerate(kids)
               if c.tag == W + 'p' and '基金项目' in text_of(c))

YEAR = re.compile(r',\s*(?:19|20)\d{2}')
n = 0
for i in range(ref_start + 1, ref_end):
    p = kids[i]
    if p.tag != W + 'p':
        continue
    t = text_of(p).strip()
    m = re.match(r'^(\d+)\s+(.*)$', t)
    if not m:
        continue
    num, rest = m.group(1), m.group(2)

    if num == '30':                       # 唯一的会议论文
        rest = rest.replace(
            'a change taxonomy. Proc. of the',
            'a change taxonomy[C]//Proceedings of the')
        rest = rest.replace('(ICSME). IEEE, 2025. 199–210.',
                            '. IEEE, 2025: 199-210.')
    else:                                 # 期刊论文：在刊名前插入 [J]
        ym = YEAR.search(rest)
        assert ym, rest
        cut = rest.rfind('. ', 0, ym.start())
        assert cut > 0, rest
        rest = rest[:cut] + '[J]' + rest[cut:]

    rest = rest.replace('–', '-').replace('—', '-') if num != '23' else \
        re.sub(r'(\d)–(\d)', r'\1-\2', rest)
    rewrite(p, '[%s] %s' % (num, rest))
    n += 1

# ── 文末信息 ────────────────────────────────────────────────────────
p = find(body, '基金项目')
rewrite(p, '{sup|①} 基金项目：南通市社科研究课题（网信专项）（WA25-6）')

p = find(body, '收稿时间')
rewrite(p, '收稿日期：xxxx-xx-xx　　修回日期：xxxx-xx-xx')

p = find(body, '通讯作者')
rewrite(p, text_of(p).replace('通讯作者', '通信作者'))

for who, place in (('杨文超', '江苏如东'), ('张卫兵', '江苏南通'),
                   ('练维', '江苏如皋'), ('徐小卫', '江苏如东'),
                   ('王秦', '江苏如东')):
    p = find(body, '%s（' % who)
    t = text_of(p).replace('，%s，' % place, '，%s人，' % place)
    t = re.sub(r'\.\s*$', '。', t)
    if not t.endswith('。'):
        t += '。'
    rewrite(p, t)

save(tree, SRC, 'ref.xml')
print('S5 done: %d 条参考文献转 GB/T 7714，文末信息已规整' % n)
