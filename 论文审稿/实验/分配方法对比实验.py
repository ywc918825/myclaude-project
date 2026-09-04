# -*- coding: utf-8 -*-
"""实验一：本文分段权重法与三种守恒型方法的排名差异分析。

这是把论文从"系统实现"抬到"方法 + 实现"最关键的一组实验，数据全部来自现有积分流水，
不需要重新跑系统。

输入 works.csv（从库里导，一条成果一位作者一行）：

    work_id,author_id,author_rank,is_corresponding,std_points
    W0001,U012,1,0,20
    W0001,U037,2,0,20
    W0001,U105,3,1,20
    W0002,U012,1,0,8
    ...

    author_rank        作者序位，从 1 开始
    is_corresponding   是否通讯作者，1/0（按论文规则通讯作者按第 1 作者计）
    std_points         该成果的标准积分 S_total，同一 work_id 各行相同

对应 SQL 大致是：
    SELECT r.work_id, r.author_id, r.author_rank, r.is_corresponding, i.std_points
    FROM points_record r JOIN points_item i ON r.item_id = i.id
    WHERE r.status = 'approved';

用法：
    python3 分配方法对比实验.py works.csv
    python3 分配方法对比实验.py works.csv --topn 10,30 --out 表5.txt
"""
import argparse, csv, math, sys
from collections import defaultdict


# ── 四种分配方法：给定作者数 n 与序位 i（1-based），返回该作者的分配系数 ──
def w_piecewise(i, n):                       # 本文分段权重法（名义分值制）
    return {1: 1.0, 2: 0.8, 3: 0.5}.get(i, 0.2)


def w_equal(i, n):                           # 均分法
    return 1.0 / n


def w_harmonic(i, n):                        # 调和计数法
    h = sum(1.0 / k for k in range(1, n + 1))
    return (1.0 / i) / h


def w_arith(i, n):                           # 算术递减法
    tot = n * (n + 1) / 2
    return (n - i + 1) / tot


METHODS = [('本文分段权重法', w_piecewise), ('均分法', w_equal),
           ('调和计数法', w_harmonic), ('算术递减法', w_arith)]


def spearman(a, b):
    """两个等长序列的 Spearman 秩相关（含并列秩处理）。"""
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return cov / (va * vb) if va and vb else float('nan')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--topn', default='10,30')
    ap.add_argument('--out', default='')
    a = ap.parse_args()

    works = defaultdict(list)
    with open(a.csv, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            works[r['work_id']].append(
                (r['author_id'], int(r['author_rank']),
                 int(r.get('is_corresponding', 0) or 0), float(r['std_points'])))

    # 每种方法下的个人总积分
    score = {name: defaultdict(float) for name, _ in METHODS}
    multi = defaultdict(float)      # 多作者成果贡献占比
    total = defaultdict(float)
    for wid, rows in works.items():
        n = len(rows)
        for uid, rank, corr, sp in rows:
            eff = 1 if corr else rank        # 通讯作者按第 1 作者计
            for name, fn in METHODS:
                score[name][uid] += sp * fn(eff, n)
            total[uid] += sp
            if n >= 3:
                multi[uid] += sp

    users = sorted(total)
    if len(users) < 5:
        sys.exit('样本太少（%d 人），至少要几十人才有统计意义' % len(users))
    cols = {name: [score[name][u] for u in users] for name, _ in METHODS}

    out = []
    P = out.append
    P('样本：%d 件成果，%d 名科研人员' % (len(works), len(users)))
    P('')
    P('表 5  四种分配方法下人才排名的 Spearman 秩相关')
    names = [n for n, _ in METHODS]
    P('%-14s %s' % ('', ''.join('%-14s' % n for n in names)))
    for x in names:
        P('%-14s %s' % (x, ''.join('%-14.3f' % spearman(cols[x], cols[y]) for y in names)))
    P('')

    base = names[0]
    rank = {n: sorted(range(len(users)), key=lambda i: -cols[n][i]) for n in names}
    P('表 6  以本文方法为基准的 Top-N 人员重合度')
    tops = [int(x) for x in a.topn.split(',')]
    P('%-14s %s' % ('对比方法', ''.join('Top-%-9d' % t for t in tops)))
    for n in names[1:]:
        row = []
        for t in tops:
            s1 = set(rank[base][:t]); s2 = set(rank[n][:t])
            row.append('%-13s' % ('%d/%d' % (len(s1 & s2), t)))
        P('%-14s %s' % (n, ''.join(row)))
    P('')

    # 差异到底出在谁身上——这是本文方法有没有价值的关键
    frac = [multi[u] / total[u] if total[u] else 0 for u in users]
    hi = [i for i, f in enumerate(frac) if f >= 0.5]
    lo = [i for i, f in enumerate(frac) if f < 0.5]
    P('表 7  协作型与独立型科研人员的排名变动（本文方法 相对 均分法）')
    P('%-24s %-10s %-16s %-12s' % ('人员分组', '人数', '平均排名变动', '上升人数占比'))
    pos = {u: i for i, u in enumerate(rank[base])}
    pos_e = {u: i for i, u in enumerate(rank['均分法'])}
    for label, idxs in (('多作者成果占比 ≥ 50%', hi), ('多作者成果占比 < 50%', lo)):
        if not idxs:
            continue
        d = [pos_e[i] - pos[i] for i in idxs]
        up = sum(1 for x in d if x > 0)
        P('%-24s %-10d %-16.1f %-12s'
          % (label, len(idxs), sum(d) / len(d), '%.0f%%' % (100 * up / len(idxs))))
    P('')
    P('读法：秩相关高（> 0.9）说明本文方法没有把排序搞乱；Top-N 重合度中等、')
    P('且协作型人员系统性上升，才说明这个模型真的改变了什么、且改变的方向符合设计意图。')
    P('这两条同时成立，才是论文该报的结论。')

    txt = '\n'.join(out)
    print(txt)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(txt + '\n')
        print('\n已写入 %s' % a.out)


if __name__ == '__main__':
    main()
