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
    ap.add_argument('--roster', default='',
                    help='本中心人员名册(每行一个姓名)；给定时全部作者参与 n 的计算，\n'
                         '但只对名册内人员排名——外单位合作者不进入本中心评价')
    a = ap.parse_args()

    works = defaultdict(list)
    with open(a.csv, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            works[r['work_id']].append(
                (r['author_id'], int(r['author_rank']),
                 int(r.get('is_corresponding', 0) or 0), float(r['std_points'])))

    # 每种方法下的个人总积分
    score = {name: defaultdict(float) for name, _ in METHODS}
    teamsum = defaultdict(float)    # 合作规模 n 的累计（按成果分值加权）
    total = defaultdict(float)
    nwork = defaultdict(int)
    for wid, rows in works.items():
        n = len(rows)
        for uid, rank, corr, sp in rows:
            eff = 1 if corr else rank        # 通讯作者按第 1 作者计
            for name, fn in METHODS:
                score[name][uid] += sp * fn(eff, n)
            total[uid] += sp
            teamsum[uid] += n * sp
            nwork[uid] += 1

    users = sorted(total)
    if a.roster:
        keep = {x.strip() for x in open(a.roster, encoding='utf-8') if x.strip()}
        drop = [u for u in users if u not in keep]
        users = [u for u in users if u in keep]
        print('名册过滤：保留 %d 人，剔除 %d 位外单位作者（其署名仍计入作者总数 n）'
              % (len(users), len(drop)))
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

    # 差异到底出在谁身上——这是本文方法有没有价值的关键。
    # 按"人均合作规模"（成果的平均作者数）中位数分组，而不是"多作者成果占比"：
    # 疾控成果绝大多数是 3 人以上合著，占比指标会全员饱和为 1.00、分组失效；
    # 而名义分值制的受益程度本就随团队规模放大，合作规模才是对的自变量。
    frac = [teamsum[u] / total[u] if total[u] else 0 for u in users]
    sf = sorted(frac)
    n = len(sf)
    med = sf[n // 2] if n % 2 else (sf[n // 2 - 1] + sf[n // 2]) / 2
    hi = [i for i, f in enumerate(frac) if f > med]
    lo = [i for i, f in enumerate(frac) if f <= med]
    if not hi or not lo:          # 全员占比相同（如人人都只有合著成果）
        hi, lo = list(range(n)), []
    P('表 7  不同合作规模科研人员的排名变动（本文方法 相对 均分法）')
    P('分组依据：人均合作规模（成果平均作者数）的中位数 = %.2f 人' % med)
    P('%-24s %-10s %-16s %-12s' % ('人员分组', '人数', '平均排名变动', '上升人数占比'))
    pos = {u: i for i, u in enumerate(rank[base])}
    pos_e = {u: i for i, u in enumerate(rank['均分法'])}
    for label, idxs in (('合作规模高于中位数', hi), ('合作规模不高于中位数', lo)):
        if not idxs:
            P('%-24s %-10s %s' % (label, 0, '（无此分组，全员合作占比一致）'))
            continue
        d = [pos_e[i] - pos[i] for i in idxs]
        up = sum(1 for x in d if x > 0)
        P('%-24s %-10d %-16.1f %-12s'
          % (label, len(idxs), sum(d) / len(d), '%.0f%%' % (100 * up / len(idxs))))
    P('')
    P('注：排名变动为正表示在本文方法下名次上升（数值越大上升越多）。')
    P('')
    P('读法：秩相关高（> 0.9）说明本文方法没有把排序搞乱；Top-N 重合度中等、')
    P('且大团队协作者系统性上升，才说明这个模型真的改变了什么、且方向符合设计意图。')
    P('这两条同时成立，才是论文该报的结论。')

    txt = '\n'.join(out)
    print(txt)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(txt + '\n')
        print('\n已写入 %s' % a.out)


if __name__ == '__main__':
    main()
