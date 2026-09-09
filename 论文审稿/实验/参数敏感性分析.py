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

**两种 τ_now 口径**（`--tau-now`），结论差别很大：

  current（默认，**系统实际实现**）
      τ_now 取评价时刻，式(4) 按成果的**绝对年龄**衰减。此时同一段时间被折算两次：
      式(4) 给 e^(−λj)，式(5) 的 EWMA 再给 (1−α)^j。合成后 j 年前成果的相对权重为
          ((1−α)·e^(−λ))^j = 0.2608^j        (α=0.7, λ=0.14)
      等效半衰期 ln0.5/ln0.2608 ≈ **0.52 年**，5 年前成果仅剩 0.12%。
      注意：这与"λ=0.14 对应半衰期 4.95 年"完全不是一回事——后者只描述式(4)
      单独的行为，而模型的实际衰减由 EWMA 主导。

  period
      τ_now 取本周期期末，式(4) 只处理周期内部的龄期差异（≤1 年，最大衰减 13%），
      跨周期时效全部由 EWMA 承担，等效半衰期 ln0.5/ln(1−α) ≈ 0.58 年。

  两者相差不大（0.52 vs 0.58 年），因为 (1−α)=0.3 完全压过了 e^(−λ)=0.87。
  **想让整体半衰期真正等于 5 年，需要 (1−α)e^(−λ) = 0.871，固定 λ=0.14 则要求
  α ≈ −0.001——α=0.7 与多年记忆在数学上不可能同时成立。**

**month 这一列**：成果完成时间本就是日期，只精确到年会损失年内先后信息。
在 period 口径下缺 month 更致命——龄期退化为常数，λ 完全失效、秩相关恒为 1。
缺失时脚本按年中（第 6.5 月）处理并给出警告。

用法：
    python3 参数敏感性分析.py records.csv --now 2025
    python3 参数敏感性分析.py records.csv --now 2025 --tau-now period
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


def total_weight(rec, users, tags, alpha, lam, now, ymin, tau_now='current'):
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
            # τ_now: current=评价时刻(系统实际实现) / period=本周期期末
            ref = (now + 1.0) if tau_now == 'current' else (y + 1.0)
            age = max(0.0, ref - (yy + frac))
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
    ap.add_argument('--tau-now', choices=['current','period'], default='current',
                    help="current=评价时刻(系统实际实现); period=本周期期末")
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
    TN = a.tau_now

    out = []
    P = out.append
    P('样本：%d 名科研人员，%d 个标签，%d 条行为积分，年度 %d–%d'
      % (len(users), len(tags), len(rec), ymin, a.now))
    P('τ_now 口径：%s' % ('评价时刻（系统实际实现，式(4) 按成果绝对年龄衰减）'
                         if TN == 'current' else '本周期期末（仅周期内衰减）'))
    if TN == 'current':
        q = (1 - A0) * math.exp(-L0)
        P('注意：此口径下式(4) 与式(5) 对同一段时间各折算一次，合成后 j 年前成果')
        P('      相对权重为 ((1−α)e^(−λ))^j = %.4f^j，等效半衰期 %.2f 年。'
          % (q, math.log(0.5) / math.log(q)))
    if not has_month:
        P('')
        P('⚠ 数据无 month 列，全部按年中处理 → 周期内成果龄期恒为 0.5 年，')
        P('  λ 对排名的影响将退化为常数缩放，表 9 的秩相关必然恒为 1.0000，')
        P('  该结果不能作为“λ 不敏感”的证据。请补 month 列后重跑。')
    P('')

    base = total_weight(rec, users, tags, A0, L0, a.now, ymin, TN)
    P('表 8  α 的敏感性（λ = 0.14 固定，与 α = 0.7 的排名比较）')
    P('%-10s %-16s %-14s' % ('α', 'Spearman 秩相关', 'Top-10 重合'))
    r0 = sorted(range(len(users)), key=lambda i: -base[i])
    for al in alphas:
        v = total_weight(rec, users, tags, al, L0, a.now, ymin, TN)
        rk = sorted(range(len(users)), key=lambda i: -v[i])
        ov = len(set(r0[:10]) & set(rk[:10]))
        P('%-10.2f %-16.4f %-14s' % (al, spearman(base, v), '%d/10' % ov))
    P('')
    P('表 9  λ 的敏感性（α = 0.7 固定，与 λ = 0.14 的排名比较）')
    P('%-10s %-16s %-14s %-12s' % ('λ', 'Spearman 秩相关', 'Top-10 重合', '半衰期/年'))
    for lm in lams:
        v = total_weight(rec, users, tags, A0, lm, a.now, ymin, TN)
        rk = sorted(range(len(users)), key=lambda i: -v[i])
        ov = len(set(r0[:10]) & set(rk[:10]))
        P('%-10.2f %-16.4f %-14s %-12.2f'
          % (lm, spearman(base, v), '%d/10' % ov, math.log(2) / lm))
    P('')
    P('该怎么写这一节：')
    P('  · α 在 0.6~0.8 区间秩相关若都 > 0.95，说明排名对 α 不敏感，取 0.7 是稳健的；')
    P('  · 表 9 的“半衰期”一列只是 ln2/λ，即式(4) 单独的半衰期，**不是模型的实际')
    P('    记忆长度**。实际记忆由 EWMA 主导，正文切勿把这一列当作系统的时效跨度；')
    P('  · λ 若在整个扫描区间秩相关都很高，说明它对排名是二阶影响，其价值在于')
    P('    刻画成果新旧的连续性而非调节排名，正文应据此定位，不要反过来当卖点；')
    P('  · 两张表合成一张折线图（横轴参数值、纵轴秩相关）比表格更直观。')

    txt = '\n'.join(out)
    print(txt)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(txt + '\n')
        print('\n已写入 %s' % a.out)


if __name__ == '__main__':
    main()
