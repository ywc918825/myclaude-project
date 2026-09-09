# -*- coding: utf-8 -*-
"""实验二：α 与 λ 的敏感性分析。

论文里 α = 0.7、λ = 0.14 目前是经验取值，没有实验支撑——这是计算机类期刊必问的一条。
本脚本用现有积分流水扫参数，给出排名稳定性曲线。

**为什么只用标签权重就够了**：由式(6) 与 Σ_d m(t,d) = 1 可得
    Σ_d C(d,u) = Σ_d Σ_t W(t,u)·m(t,d) = Σ_t W(t,u)·Σ_d m(t,d) = Σ_t W(t,u)
即个人能力总分恒等于其标签权重之和，与映射矩阵 M 无关。所以做排名敏感性分析不需要 M，
直接用 Σ_t W(t,u) 排序即可，结论完全等价。

输入 records.csv（一条行为积分一行）：

    user_id,tag,points,year,month
    U012,论文发表,20,2024,3
    U012,课题主持,35,2022,11
    ...

    year    成果完成年度
    month   成果完成月份，1—12，**可省略**

**month 这一列为什么要紧**：式(4) 的 τ_now 取本周期期末、τ_i 取成果完成时间，
而周期就是自然年度。若只精确到年，同一周期内 τ_now − τ_i 恒为 0，
exp(−λ·0) ≡ 1，λ 取任何值都得到同一排名——λ 在模型中根本不起作用。
只有精确到月，λ 才真正作用于"年内早发表 vs 晚发表"的差异（年内最大衰减
1 − e^(−λ) ≈ 13%）。缺 month 时脚本按年中（第 6.5 月）统一处理，
并会明确警告 λ 的敏感性结论不成立。

跨年度的时效由式(5) 的 EWMA 承担，与 λ 无关：α = 0.7 时 j 年前的成果权重为
α(1−α)^j，相对当年为 (1−α)^j，等效半衰期 ln0.5/ln(1−α) ≈ 0.58 年。

用法：
    python3 参数敏感性分析.py records.csv --now 2025
    python3 参数敏感性分析.py records.csv --now 2025 --out 表8.txt
"""
import argparse, csv, math, sys
from collections import defaultdict


def spearman(a, b):
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


def total_weight(rec, users, tags, alpha, lam, now, ymin):
    """按式(4)(5) 逐年度递推，返回每人的 Σ_t W(t,u)。"""
    # 每年度、每标签的全中心最高衰减后积分 S_max,t（式(4) 分母）
    W = defaultdict(float)                    # (tag, user) -> 当前权重，初值 0
    for y in range(ymin, now + 1):
        cur = defaultdict(float)              # (tag,user) -> 本年度衰减后积分之和
        smax = defaultdict(float)             # tag -> 本年度全中心最高原始积分
        for (u, t, p, yy, frac) in rec:
            if yy != y:
                continue
            smax[t] = max(smax[t], p)
        for (u, t, p, yy, frac) in rec:
            if yy != y:
                continue
            if smax[t] <= 0:
                continue
            # τ_now 取本周期期末(y+1)，τ_i 取成果完成时刻(yy+frac) → 周期内衰减
            age = max(0.0, (y + 1.0) - (yy + frac))
            decayed = p * math.exp(-lam * age)
            cur[(t, u)] += decayed / smax[t]
        # 本年度行为项归一化到 [0,1]（Σw_i = 1，按人-标签内部等权）
        for key in set(list(cur.keys()) + list(W.keys())):
            new = min(1.0, cur.get(key, 0.0))
            W[key] = alpha * new + (1 - alpha) * W.get(key, 0.0)
        # 跨年度的时效由 EWMA 承担，此处不再额外衰减
    tot = defaultdict(float)
    for (t, u), w in W.items():
        tot[u] += w
    return [tot[u] for u in users]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--now', type=int, required=True, help='当前评价年度，如 2025')
    ap.add_argument('--alphas', default='0.5,0.6,0.7,0.8,0.9')
    ap.add_argument('--lambdas', default='0.07,0.14,0.21,0.28')
    ap.add_argument('--out', default='')
    a = ap.parse_args()

    rec, has_month = [], False
    with open(a.csv, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            m = (r.get('month') or '').strip()
            if m:
                has_month = True
                frac = (int(m) - 0.5) / 12.0     # 该月中点
            else:
                frac = 0.5                       # 缺失时按年中处理
            rec.append((r['user_id'], r['tag'], float(r['points']),
                        int(r['year']), frac))
    if not rec:
        sys.exit('没读到数据')
    users = sorted({u for u, *_ in rec})
    tags = sorted({t for _, t, *_ in rec})
    ymin = min(x[3] for x in rec)
    if len(users) < 5:
        sys.exit('样本太少（%d 人）' % len(users))

    alphas = [float(x) for x in a.alphas.split(',')]
    lams = [float(x) for x in a.lambdas.split(',')]
    A0, L0 = 0.7, 0.14

    out = []
    P = out.append
    P('样本：%d 名科研人员，%d 个标签，%d 条行为积分，年度 %d–%d'
      % (len(users), len(tags), len(rec), ymin, a.now))
    if not has_month:
        P('')
        P('⚠ 数据无 month 列，全部按年中处理 → 周期内成果龄期恒为 0.5 年，')
        P('  λ 对排名的影响将退化为常数缩放，表 9 的秩相关必然恒为 1.0000，')
        P('  该结果不能作为“λ 不敏感”的证据。请补 month 列后重跑。')
    P('')

    base = total_weight(rec, users, tags, A0, L0, a.now, ymin)
    P('表 8  α 的敏感性（λ = 0.14 固定，与 α = 0.7 的排名比较）')
    P('%-10s %-16s %-14s' % ('α', 'Spearman 秩相关', 'Top-10 重合'))
    r0 = sorted(range(len(users)), key=lambda i: -base[i])
    for al in alphas:
        v = total_weight(rec, users, tags, al, L0, a.now, ymin)
        rk = sorted(range(len(users)), key=lambda i: -v[i])
        ov = len(set(r0[:10]) & set(rk[:10]))
        P('%-10.2f %-16.4f %-14s' % (al, spearman(base, v), '%d/10' % ov))
    P('')
    P('表 9  λ 的敏感性（α = 0.7 固定，与 λ = 0.14 的排名比较）')
    P('%-10s %-16s %-14s %-12s' % ('λ', 'Spearman 秩相关', 'Top-10 重合', '半衰期/年'))
    for lm in lams:
        v = total_weight(rec, users, tags, A0, lm, a.now, ymin)
        rk = sorted(range(len(users)), key=lambda i: -v[i])
        ov = len(set(r0[:10]) & set(rk[:10]))
        P('%-10.2f %-16.4f %-14s %-12.2f'
          % (lm, spearman(base, v), '%d/10' % ov, math.log(2) / lm))
    P('')
    P('该怎么写这一节：')
    P('  · 若 α 在 0.6~0.8 区间秩相关都 > 0.95，说明排名对 α 不敏感，取 0.7 是稳健的；')
    P('  · 若 λ 的秩相关随取值明显下降，说明 λ 是真正起作用的参数，那么正文里')
    P('    “λ = 0.14 对应半衰期 4.95 年、与事业单位 5 年聘期一致”这条制度依据就成了')
    P('    选参的正当理由，而不是事后凑的说法。')
    P('  · 两张表合成一张折线图（横轴参数值、纵轴秩相关）比表格更直观。')

    txt = '\n'.join(out)
    print(txt)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(txt + '\n')
        print('\n已写入 %s' % a.out)


if __name__ == '__main__':
    main()
