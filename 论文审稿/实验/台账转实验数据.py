# -*- coding: utf-8 -*-
"""把科研成果台账转成实验一所需的 works.csv。

为什么这一步不需要系统运营过
----------------------------
实验一（四种分配方法的排名对比）只需要三样东西：**哪些成果、每个成果有哪些作者、
各自排第几**。这是你中心的历史科研台账，纸质时代就在，跟系统上没上线无关。
论文表 4 写着上线前 3 个月线下申报 192 件，按年折算七百余件，
三到五年的台账足够跑出统计意义。

输入 台账.csv（用 Excel 另存为 CSV，UTF-8）：

    成果名称,作者,通讯作者,标准积分
    某某地区手足口病流行特征分析,张三、李四、王五,王五,20
    某某市饮用水监测能力建设研究,李四、赵六,李四,35
    一种病原微生物快速检测方法,王五、张三、孙七、周八,,12
    ...

    作者      按署名顺序排列，用顿号、分号、逗号或斜杠分隔均可
    通讯作者  姓名；无通讯作者留空；多个通讯作者用同样的分隔符
    标准积分  该成果的 S_total（论文式(1) 里的成果标准积分）

    表头可用中文或英文（title/authors/corresponding/points），大小写不敏感。
    重名作者请在台账里就区分开（如"张三(检验科)"），本脚本按姓名字符串归并。

输出 works.csv：work_id,author_id,author_rank,is_corresponding,std_points

用法：
    python3 台账转实验数据.py 台账.csv --out works.csv
    python3 台账转实验数据.py 台账.csv --out works.csv --run   # 直接接着跑实验一
"""
import argparse, csv, os, re, subprocess, sys
from collections import Counter

SEP = re.compile(r'[、;；,，/／\s]+')
ALIAS = {
    'title': ('成果名称', '题名', '名称', 'work_name', 'title', 'work'),
    'authors': ('作者列表', '署名顺序', '作者', '署名', 'authors', 'author'),
    'corr': ('通讯作者', '通信作者', 'corresponding', 'corr'),
    'points': ('标准积分', 'std_points', '积分', '分值', 'points', 'score'),
}
CN = {'title': '成果名称', 'authors': '作者', 'corr': '通讯作者', 'points': '标准积分'}


def pick(header):
    """把台账表头映射到四个逻辑字段。

    表头常带补充说明（如"作者（按署名顺序，用、分隔）"），故用包含匹配而非全等。
    按"精确优先、别名越长越优先"排序后贪心指派，避免"通讯作者"被 authors 的
    别名"作者"抢走、"成果类型"被 title 抢走这类串台。
    """
    low = {h: (h or '').strip().lower() for h in header}
    cand = []
    for key, names in ALIAS.items():
        for nm in names:
            n = nm.lower()
            for h in header:
                if low[h] == n:
                    cand.append((0, -len(n), key, h))
                elif n in low[h]:
                    cand.append((1, -len(n), key, h))
    cand.sort()
    got, used = {}, set()
    for _, _, key, h in cand:
        if key not in got and h not in used:
            got[key], _ = h, used.add(h)

    missing = [CN[k] for k in ('title', 'authors', 'points') if k not in got]
    if missing:
        sys.exit('台账缺少必需列：%s\n实际表头：%s\n'
                 '（表头可带括号说明，只要含"成果名称""作者""标准积分"字样即可）'
                 % ('、'.join(missing), '、'.join(header)))
    print('表头识别：' + '，'.join('%s ← %s' % (CN[k], got[k])
                                  for k in ('title', 'authors', 'corr', 'points')
                                  if k in got))
    return got


def split_names(s):
    return [x for x in SEP.split((s or '').strip()) if x]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--out', default='works.csv')
    ap.add_argument('--run', action='store_true', help='生成后直接跑实验一')
    a = ap.parse_args()

    with open(a.csv, newline='', encoding='utf-8-sig') as f:
        rd = csv.DictReader(f)
        col = pick(rd.fieldnames or [])
        src = list(rd)
    if not src:
        sys.exit('台账里没有数据行')

    out, skipped, n_author = [], [], Counter()
    for i, r in enumerate(src, 1):
        authors = split_names(r.get(col['authors']))
        corr = set(split_names(r.get(col.get('corr'), '') if col.get('corr') else ''))
        raw = (r.get(col['points']) or '').strip()
        try:
            pts = float(re.sub(r'[^\d.]', '', raw))
        except ValueError:
            pts = 0.0
        if not authors or pts <= 0:
            skipped.append((i, r.get(col['title'], ''), '作者为空' if not authors
                            else '积分缺失或为 0'))
            continue
        unknown = corr - set(authors)
        if unknown:
            skipped.append((i, r.get(col['title'], ''),
                            '通讯作者不在作者列表中：' + '、'.join(sorted(unknown))))
        wid = 'W%04d' % i
        n_author[len(authors)] += 1
        for rank, name in enumerate(authors, 1):
            out.append([wid, name, rank, 1 if name in corr else 0, '%g' % pts])

    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work_id', 'author_id', 'author_rank',
                    'is_corresponding', 'std_points'])
        w.writerows(out)

    people = len({r[1] for r in out})
    works = len({r[0] for r in out})
    multi = sum(c for n, c in n_author.items() if n >= 3)
    print('已写入 %s' % a.out)
    print('  成果 %d 件，作者 %d 人，署名记录 %d 条' % (works, people, len(out)))
    print('  作者数分布：%s'
          % '，'.join('%d 人成果 %d 件' % (k, n_author[k]) for k in sorted(n_author)))
    print('  3 人及以上合著成果 %d 件（占 %.0f%%）——实验一的差异主要来自这部分'
          % (multi, 100 * multi / works if works else 0))

    if skipped:
        print('\n⚠ %d 行有问题，请回台账核对：' % len(skipped))
        for i, t, why in skipped[:15]:
            print('   第 %d 行  %s  → %s' % (i, (t or '')[:24], why))
        if len(skipped) > 15:
            print('   ……另有 %d 行' % (len(skipped) - 15))

    if works < 30 or people < 5:
        print('\n⚠ 样本偏少（成果 %d 件 / %d 人）。实验一要出统计意义，'
              '建议成果 ≥100 件、人员 ≥30 人；否则 Spearman 秩相关会不稳。'
              % (works, people))

    if a.run:
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '分配方法对比实验.py')
        print()
        subprocess.run([sys.executable, script, a.out])


if __name__ == '__main__':
    main()
