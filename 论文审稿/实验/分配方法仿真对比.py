# -*- coding: utf-8 -*-
"""四种分配方法的**仿真**对比：以本中心真实规模为锚，对合著结构做假设扫描。

════════════════════════════════════════════════════════════════════════
  ⚠ 本脚本产出的是仿真结果，不是实测。写入论文必须标注为仿真/模型行为分析，
  ⚠ 不得与表 2/3/4 的实测结果混排，不得说成"系统运行数据"。
════════════════════════════════════════════════════════════════════════

哪些是真的，哪些是假设的
------------------------
**真实锚点**（取自《2024—2025 人才积分材料汇总表》佐证材料，可核验）：
  · 成果件数 202
  · 涉及人员 61
  · 每人成果数分布（1 篇 11 人 … 13 篇 1 人），高度不均，直接用作抽样权重

**必须假设**（档案未记录，而这恰恰是本实验要测的量）：
  · 每件成果的**作者总数**——档案只记录中心内提交人，外单位合作者不可见
  · 每位作者的**署名序位**——仅 10% 的记录带位次标记

正因为假设的部分就是被测量的部分，本脚本**不给单点结论**，而是把假设铺成
网格全部跑一遍，只报告**结论在假设区间内是否稳定**。稳定，则该结论是分配
方法自身的性质；不稳定，则说明它依赖于假设，不能写进论文。

假设网格（3 × 2 × 2 = 12 组，每组 5 个随机种子，共 60 次运行）
  中心内合著密度  sparse(均值≈1.6) / medium(≈2.4) / dense(≈3.2)
  外单位作者数    none(0) / some(~Poisson 1.5)
  序位分配        random(随机) / seniority(高产者更可能靠前)

用法：
    python3 分配方法仿真对比.py anchors.json
    python3 分配方法仿真对比.py anchors.json --out 仿真结果.txt
"""
import argparse, json, math, random, sys
from collections import defaultdict


# ── 四种分配方法：给定序位 i（1-based）与作者总数 n，返回分配系数 ──
def w_piecewise(i, n):
    return {1: 1.0, 2: 0.8, 3: 0.5}.get(i, 0.2)


def w_equal(i, n):
    return 1.0 / n


def w_harmonic(i, n):
    h = sum(1.0 / k for k in range(1, n + 1))
    return (1.0 / i) / h


def w_arith(i, n):
    return (n - i + 1) / (n * (n + 1) / 2)


METHODS = [('本文分段权重法', w_piecewise), ('均分法', w_equal),
           ('调和计数法', w_harmonic), ('算术递减法', w_arith)]

DENSITY = {                       # 中心内合著人数的分布
    'sparse': [(1, .55), (2, .30), (3, .10), (4, .05)],
    'medium': [(1, .25), (2, .35), (3, .25), (4, .15)],
    'dense':  [(1, .10), (2, .25), (3, .35), (4, .30)],
}
EXTERNAL = {'none': 0.0, 'some': 1.5}      # 外单位作者数的 Poisson 均值
ORDERING = ('random', 'seniority')


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


def draw(rng, pairs):
    r, acc = rng.random(), 0.0
    for v, p in pairs:
        acc += p
        if r <= acc:
            return v
    return pairs[-1][0]


def poisson(rng, lam):
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def one_run(users, weights, n_works, density, external, ordering, seed):
    rng = random.Random(seed)
    score = {m: defaultdict(float) for m, _ in METHODS}
    multi = defaultdict(float)
    total = defaultdict(float)

    for _ in range(n_works):
        k = min(draw(rng, DENSITY[density]), len(users))
        # 按真实产出量加权抽取中心内作者（高产者更常出现）
        inside = []
        pool, w = list(users), list(weights)
        for _ in range(k):
            tot = sum(w)
            r, acc = rng.random() * tot, 0.0
            for idx, ww in enumerate(w):
                acc += ww
                if r <= acc:
                    break
            inside.append(pool.pop(idx))
            w.pop(idx)
        ext = poisson(rng, EXTERNAL[external])
        n = k + ext
        # 序位：随机，或按产出量降序（高产者靠前）
        if ordering == 'seniority':
            inside.sort(key=lambda u: -weights[users.index(u)])
        else:
            rng.shuffle(inside)
        # 外单位作者随机插入到序列中
        slots = list(range(n))
        rng.shuffle(slots)
        pos = dict(zip(inside, sorted(slots[:k])))
        sp = min(60.0, max(4.0, rng.lognormvariate(2.7, 0.6)))   # 成果标准积分
        for u in inside:
            i = pos[u] + 1
            for m, fn in METHODS:
                score[m][u] += sp * fn(i, n)
            total[u] += sp
            if n >= 3:
                multi[u] += sp

    cols = {m: [score[m][u] for u in users] for m, _ in METHODS}
    base = cols['本文分段权重法']
    rank = {m: sorted(range(len(users)), key=lambda i: -cols[m][i]) for m, _ in METHODS}
    res = {'sp_equal': spearman(base, cols['均分法']),
           'sp_harm': spearman(base, cols['调和计数法']),
           'sp_arith': spearman(base, cols['算术递减法'])}
    for t in (10, 30):
        s1 = set(rank['本文分段权重法'][:t])
        res['top%d_equal' % t] = len(s1 & set(rank['均分法'][:t]))
    # 协作型 vs 独立型：按多作者成果积分占比的中位数分组
    frac = [multi[u] / total[u] if total[u] else 0 for u in users]
    sf = sorted(frac)
    n2 = len(sf)
    med = sf[n2 // 2] if n2 % 2 else (sf[n2 // 2 - 1] + sf[n2 // 2]) / 2
    pos_b = {u: i for i, u in enumerate(rank['本文分段权重法'])}
    pos_e = {u: i for i, u in enumerate(rank['均分法'])}
    hi = [i for i, f in enumerate(frac) if f > med]
    lo = [i for i, f in enumerate(frac) if f <= med]
    res['d_hi'] = sum(pos_e[i] - pos_b[i] for i in hi) / len(hi) if hi else 0.0
    res['d_lo'] = sum(pos_e[i] - pos_b[i] for i in lo) / len(lo) if lo else 0.0
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('anchors', help='由 科研数据体检.py 产生的 anchors.json')
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--out', default='')
    a = ap.parse_args()

    A = json.load(open(a.anchors, encoding='utf-8'))
    per = A['per_person']
    users = sorted(per)
    weights = [per[u] for u in users]
    n_works = A['works']

    out = []
    P = out.append
    P('=' * 72)
    P('  四种分配方法的仿真对比 —— 假设扫描')
    P('=' * 72)
    P('  真实锚点：%d 件成果、%d 名人员、人均 %.2f 篇（取自佐证材料）'
      % (n_works, len(users), sum(weights) / len(users)))
    P('  假设网格：合著密度 3 × 外单位作者 2 × 序位分配 2 = 12 组，每组 %d 个种子'
      % a.seeds)
    P('')
    P('  ⚠ 仿真结果。作者总数与署名序位为假设值——档案未记录，而这正是本实验')
    P('     要测的量。故只看结论在假设区间内是否稳定，不取单点数值。')
    P('')

    rows = []
    P('%-9s %-6s %-10s %-9s %-9s %-9s %-8s' %
      ('合著密度', '外单位', '序位', 'ρ(均分)', 'ρ(调和)', 'Top-10', '排名变动 高/低'))
    P('-' * 72)
    for dens in DENSITY:
        for ext in EXTERNAL:
            for order in ORDERING:
                rs = [one_run(users, weights, n_works, dens, ext, order, 1000 + s)
                      for s in range(a.seeds)]
                avg = lambda k: sum(r[k] for r in rs) / len(rs)
                rows.append((dens, ext, order, avg('sp_equal'), avg('sp_harm'),
                             avg('top10_equal'), avg('d_hi'), avg('d_lo')))
                P('%-9s %-6s %-10s %-9.3f %-9.3f %-9.1f %+.1f / %+.1f'
                  % (dens, ext, order, avg('sp_equal'), avg('sp_harm'),
                     avg('top10_equal'), avg('d_hi'), avg('d_lo')))

    P('')
    P('=' * 72)
    P('  结论稳定性')
    P('=' * 72)
    sp = [r[3] for r in rows]
    t10 = [r[5] for r in rows]
    dhi = [r[6] for r in rows]
    dlo = [r[7] for r in rows]
    P('  与均分法的秩相关 ρ    %.3f ~ %.3f' % (min(sp), max(sp)))
    P('  Top-10 重合          %.1f ~ %.1f / 10' % (min(t10), max(t10)))
    P('  合作占比高组 排名变动  %+.1f ~ %+.1f' % (min(dhi), max(dhi)))
    P('  合作占比低组 排名变动  %+.1f ~ %+.1f' % (min(dlo), max(dlo)))
    P('')
    stable_dir = all(h > 0 for h in dhi) and all(l < 0 for l in dlo)
    stable_rho = min(sp) > 0.80
    P('  判定：')
    P('    · 秩相关始终 %s 0.80 —— %s'
      % ('>' if stable_rho else '未能保持 >', '本文方法没有把排序整体搞乱'
         if stable_rho else '排序稳定性依赖假设，不能作结论'))
    P('    · 合作占比高的一组在全部 %d 组假设下%s上升 —— %s'
      % (len(rows), '' if stable_dir else '并非一致',
         '方向性结论稳健，是分段权重法的固有性质' if stable_dir
         else '方向性结论依赖假设，不能写进论文'))
    P('')
    P('  能写进论文的只有"在假设区间内稳定"的那部分；随假设摆动的数值不能报。')

    txt = '\n'.join(out)
    print(txt)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(txt + '\n')
        print('\n已写入 %s' % a.out)


if __name__ == '__main__':
    main()
