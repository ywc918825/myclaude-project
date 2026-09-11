# -*- coding: utf-8 -*-
"""知网 HTML-xls 题录 → works.csv + 中心人员名册。"""
import csv, html, re, sys
from collections import Counter

CDC = re.compile(r'疾病预防控制|疾控')
SPL = re.compile(r'[;；]')

def cells(path):
    raw = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.S | re.I):
        c = [re.sub(r'<[^>]+>', '', x)
             for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S | re.I)]
        c = [html.unescape(x).replace('\xa0', ' ').strip() for x in c]
        if any(c):
            out.append(c)
    return out

rows = cells(sys.argv[1])
hdr, data = rows[0], rows[1:]
ci = {h: i for i, h in enumerate(hdr)}
G = lambda r, k: (r[ci[k]] if ci.get(k) is not None and ci[k] < len(r) else '')
au = lambda s: [x.strip() for x in SPL.split(s) if x.strip()]

# 名册：单位署名仅含疾控的论文，其全部作者必为本中心人员
seed = set()
for r in data:
    orgs = [o.strip() for o in SPL.split(G(r, 'Organ-单位')) if o.strip()]
    if orgs and all(CDC.search(o) for o in orgs):
        seed.update(au(G(r, 'Author-作者')))
extra = set()
if len(sys.argv) > 3:                      # 可选：并入积分评比名册
    extra = {x.strip() for x in open(sys.argv[3], encoding='utf-8') if x.strip()}
roster = seed | extra
open('roster.txt', 'w', encoding='utf-8').write('\n'.join(sorted(roster)))

seen, out, sizes = set(), [], Counter()
for i, r in enumerate(data, 1):
    t = re.sub(r'\s+', '', G(r, 'Title-题名'))
    a = au(G(r, 'Author-作者'))
    if not t or not a or t in seen:
        continue
    seen.add(t)
    sizes[len(a)] += 1
    for rank, name in enumerate(a, 1):
        out.append(['W%04d' % i, name, rank, 0, 1])   # std_points 统一取 1
with open(sys.argv[2], 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['work_id', 'author_id', 'author_rank', 'is_corresponding', 'std_points'])
    w.writerows(out)
print('works.csv：%d 件成果、%d 条署名记录' % (len(seen), len(out)))
print('作者数分布：%s' % '，'.join('%d位%d件' % (k, sizes[k]) for k in sorted(sizes)))
print('roster.txt：%d 名本中心作者' % len(roster))
