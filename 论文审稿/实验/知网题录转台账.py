# -*- coding: utf-8 -*-
"""把知网/万方的机构题录导出转成《成果台账》，供实验一使用。

为什么这条路可行
----------------
实验一只需要"每件成果的全部作者及各自位次"。这些信息**不在系统里，而在公开发表记录里**：
本中心发表的每一篇论文，其题名与作者署名顺序都是公开事实，可从知网按作者单位检索得到。
不依赖系统是否上线、库里有没有数据，且他人可复核——比任何仿真都硬。

怎么拿到题录
------------
知网高级检索 → 作者单位 = 南通市疾病预防控制中心 → 时间范围 2020-2025
→ 全选 → 导出与分析 → 自定义 → 勾选【题名】【作者】【文献来源】【发表时间】
→ 导出 Excel。普通账号单次上限 50 条，分批导完拼到一起即可。
万方、维普同理，本脚本按列名识别，三家的导出都能读。

标准积分怎么填
--------------
脚本不猜分值。它会把**去重后的期刊名按出现频次排序**打印出来——通常 200 篇论文集中在
30~60 种期刊上——你按本中心积分办法给每种期刊定一次级别分值，在 Excel 里批量填入
"标准积分"列即可，约 20 分钟。

用法：
    python3 知网题录转台账.py 知网导出.xlsx --out 台账.csv
    python3 知网题录转台账.py 知网导出.csv  --out 台账.csv --score-map 期刊分值.csv

    期刊分值.csv（可选，两列）：
        期刊,标准积分
        中国公共卫生,20
        江苏预防医学,12
"""
import argparse, csv, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ALIAS = {
    'title': ('题名', 'title', '篇名', '文献题名', '论文题目', '标题'),
    'authors': ('作者', 'author', '作者姓名', '责任者', 'authors'),
    'source': ('文献来源', '来源', '期刊名称', '刊名', 'source', '来源期刊'),
    'year': ('发表时间', '年', '出版年', '发表年份', 'year', '年份'),
}
CN = {'title': '题名', 'authors': '作者', 'source': '文献来源', 'year': '发表时间'}
SEP = re.compile(r'[;；,，、/／]+')


def pick(header):
    """列名包含匹配，精确优先、别名越长越优先，贪心指派。"""
    low = {h: (h or '').strip().lower() for h in header}
    cand = []
    for key, names in ALIAS.items():
        for nm in names:
            n = nm.lower()
            for h in header:
                if low[h] == n:
                    cand.append((0, -len(n), key, h))
                elif n and n in low[h]:
                    cand.append((1, -len(n), key, h))
    cand.sort()
    got, used = {}, set()
    for _, _, key, h in cand:
        if key not in got and h not in used:
            got[key] = h
            used.add(h)
    miss = [CN[k] for k in ('title', 'authors') if k not in got]
    if miss:
        sys.exit('题录缺少必需列：%s\n实际列名：%s\n'
                 '（导出时请勾选【题名】与【作者】）' % ('、'.join(miss), '、'.join(header)))
    print('列名识别：' + '，'.join('%s ← %s' % (CN[k], got[k]) for k in
                                  ('title', 'authors', 'source', 'year') if k in got))
    return got


def read_html_table(path):
    """知网导出的 .xls 实为 HTML 表格，这里直接解析。"""
    import html as _h
    raw = open(path, encoding='utf-8', errors='replace').read()
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.S | re.I):
        cells = [re.sub(r'<[^>]+>', '', c)
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S | re.I)]
        cells = [_h.unescape(c).replace('\xa0', ' ').strip() for c in cells]
        if any(cells):
            rows.append(cells)
    return rows


def read_table(path):
    """读 xlsx / csv / 知网 HTML-xls，返回 (表头, 数据行)。"""
    low = path.lower()
    if low.endswith(('.xls', '.htm', '.html')):
        head = open(path, 'rb').read(8)
        if head[:2] not in (b'PK',) and head != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            rows = read_html_table(path)
            if not rows:
                sys.exit('%s 既不是 xlsx/csv，按 HTML 表格解析也没读到内容' % path)
            print('（按知网 HTML-xls 格式解析，共 %d 行）' % len(rows))
            return rows[0], rows[1:]
        sys.exit('%s 是老式二进制 .xls，本环境无法读取。\n'
                 '请在 Excel 里另存为 .xlsx 或 CSV（UTF-8）后重试。' % path)
    if low.endswith(('.xlsx', '.xlsm')):
        from xlsx简易读取器 import load
        sheets = load(path)
        name, rows = sheets[0]
        if len(sheets) > 1:
            print('（工作簿有 %d 个表，取第一个：%s）' % (len(sheets), name))
        return rows[0], rows[1:]
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def clean_author(s):
    """去掉知网作者字段里的角标、机构序号与空白。"""
    s = re.sub(r'[\d①-⑳\*\#\s]+$', '', (s or '').strip())
    return re.sub(r'^\s+', '', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', help='知网/万方导出的 xlsx 或 csv')
    ap.add_argument('--out', default='台账.csv')
    ap.add_argument('--score-map', default='', help='期刊,标准积分 两列的 csv')
    ap.add_argument('--min-authors', type=int, default=1,
                    help='少于该作者数的记录跳过（默认 1，即全留）')
    a = ap.parse_args()

    header, data = read_table(a.src)
    col = pick(header)
    idx = {k: header.index(v) for k, v in col.items()}

    smap = {}
    if a.score_map:
        with open(a.score_map, newline='', encoding='utf-8-sig') as f:
            for r in csv.reader(f):
                if len(r) >= 2 and r[1].strip():
                    try:
                        smap[r[0].strip()] = float(r[1])
                    except ValueError:
                        pass
        print('已载入期刊分值 %d 条' % len(smap))

    out, journals, sizes, skipped = [], Counter(), Counter(), 0
    seen = set()
    for row in data:
        def cell(k):
            i = idx.get(k)
            return (row[i] if i is not None and i < len(row) else '') or ''
        title = cell('title').strip()
        authors = [clean_author(x) for x in SEP.split(cell('authors')) if clean_author(x)]
        if not title or len(authors) < a.min_authors:
            skipped += 1
            continue
        key = re.sub(r'\s+', '', title)
        if key in seen:            # 分批导出常有重复
            continue
        seen.add(key)
        src = cell('source').strip()
        yr = re.search(r'(19|20)\d{2}', cell('year'))
        journals[src] += 1
        sizes[len(authors)] += 1
        out.append([title, '、'.join(authors), '', smap.get(src, ''), src,
                    yr.group(0) if yr else ''])

    if not out:
        sys.exit('没有可用记录，检查导出文件是否含【题名】【作者】两列。')

    with open(a.out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['成果名称', '作者（按署名顺序，用、分隔）', '通讯作者',
                    '标准积分', '文献来源（选填）', '完成年份（选填）'])
        w.writerows(out)

    people = len({x for r in out for x in r[1].split('、')})
    multi = sum(c for n, c in sizes.items() if n >= 3)
    print('\n已写入 %s' % a.out)
    print('  成果 %d 件（跳过 %d 条），涉及署名 %d 人次' % (len(out), skipped, people))
    print('  作者数分布：%s'
          % '，'.join('%d人 %d件' % (n, sizes[n]) for n in sorted(sizes)))
    print('  3 人及以上合著 %d 件（占 %.0f%%）——实验一的差异全部来自这部分'
          % (multi, 100 * multi / len(out)))

    blank = sum(1 for r in out if r[3] == '')
    if blank:
        print('\n还差"标准积分"列（%d 件为空）。下面是按频次排序的期刊清单，'
              '按本中心积分办法给每种定一次分值，在 Excel 里批量填入即可：' % blank)
        for j, c in journals.most_common(40):
            print('    %-34s %3d 篇' % ((j or '（来源为空）')[:34], c))
        if len(journals) > 40:
            print('    …… 另有 %d 种' % (len(journals) - 40))
        print('  （也可做成两列的 期刊分值.csv，用 --score-map 自动套入）')

    print('\n下一步：')
    print('  1) 补齐"标准积分"列；"通讯作者"列可留空，留空则全部按署名顺序计')
    print('  2) python3 台账转实验数据.py %s --out works.csv --run' % a.out)


if __name__ == '__main__':
    main()
