# -*- coding: utf-8 -*-
"""生成用于 α/λ 敏感性分析的**仿真**积分流水。

════════════════════════════════════════════════════════════════════════
  ⚠ 这个脚本产出的是仿真数据，不是实测数据。
  ⚠ 写进论文时必须明确标注为"仿真实验"，并写清本文件记录的生成规则。
  ⚠ 绝对不能与表 2/表 3/表 4 的实测结果混排，也不能说成是系统运行数据。
════════════════════════════════════════════════════════════════════════

为什么这件事是允许的
--------------------
参数敏感性分析回答的是**模型自身的数学性质**——"排名结果对 α、λ 取值有多敏感"，
而不是"本中心的科研人员实际排名如何"。这类问题在计算机类论文里用仿真数据回答是
标准做法，只要满足三个条件：

  1. 明确标注数据为仿真生成，不冒充实测；
  2. 完整交代生成规则与随机种子，使他人可复现；
  3. 在局限性中说明结论待实际数据积累后验证。

反过来说：把仿真数字填进表 3（标着"实测"的性能表）就是造假。区别在于**是否冒充
对真实世界的测量**，不在于数据是不是算出来的。

生成规则（写进论文时照抄这一段）
--------------------------------
  · 270 名科研人员、32 个能力标签、7 个年度（2019—2025），与系统实际规模一致
  · 人员分三类活动模式，比例 6:2:2
      稳定型  年均产出恒定
      上升型  年产出按 1.25^t 递增（模拟成长期科研人员）
      衰退型  年产出按 0.75^t 递减（模拟早期活跃、近年沉寂）
    —— 若全部为稳定型，任何 α、λ 都给出同一排名，敏感性分析将失去意义
  · 每人每年成果数 ~ Poisson(λ=3.2×模式系数)，与 192 件/3 月的线下申报量同量级
  · 单项成果积分 ~ LogNormal(μ=2.6, σ=0.7) 后截断至 [2, 60]，对应 46 项积分规则的
    分值跨度
  · 每人主攻 2—4 个标签（Zipf 分布抽取），其余标签偶发
  · 成果完成月份在 1—12 内均匀抽取
    —— 必须精确到月，否则式(4) 的周期内龄期恒为常数，λ 退化为常数缩放、
       对排名毫无影响，敏感性分析会得到"秩相关恒为 1"的空结论
  · 随机种子固定为 20250101，结果完全可复现

用法
----
    python3 参数敏感性仿真数据生成.py --out records_sim.csv
    python3 参数敏感性分析.py records_sim.csv --now 2025 --out 表7-仿真.txt

    # 一步到位（自动接着跑分析）
    python3 参数敏感性仿真数据生成.py --out records_sim.csv --run
"""
import argparse, csv, math, os, random, subprocess, sys

SEED = 20250101
N_USER = 270
N_TAG = 32
YEARS = list(range(2019, 2026))
PATTERNS = [('stable', 0.6, 1.00), ('rising', 0.2, 1.25), ('fading', 0.2, 0.75)]
BASE_RATE = 3.2

TAGS = ['论文发表', '课题主持', '课题参与', '专利授权', '标准制定', '专著编写',
        '成果转化', '学术任职', '科技奖励', '人才计划', '学术会议', '继续教育',
        '现场流调', '实验室检测', '数据分析', '统计建模', '监测预警', '应急处置',
        '健康教育', '疫苗接种', '慢病管理', '传染病防控', '职业卫生', '环境卫生',
        '食品安全', '营养评估', '消毒杀虫', '质量控制', '生物安全', '信息化建设',
        '教学带教', '科普宣传']


def poisson(rng, lam):
    """Knuth 采样，避免依赖 numpy。"""
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='records_sim.csv')
    ap.add_argument('--users', type=int, default=N_USER)
    ap.add_argument('--seed', type=int, default=SEED)
    ap.add_argument('--run', action='store_true', help='生成后直接跑敏感性分析')
    a = ap.parse_args()

    rng = random.Random(a.seed)

    # 为每人分配活动模式与主攻标签
    profile = []
    for u in range(a.users):
        r, acc = rng.random(), 0.0
        for name, share, coef in PATTERNS:
            acc += share
            if r <= acc:
                mode, coef_ = name, coef
                break
        n_main = rng.randint(2, 4)
        main_tags = rng.sample(TAGS, n_main)
        profile.append((('U%03d' % (u + 1)), mode, coef_, main_tags))

    rows = []
    for uid, mode, coef, main_tags in profile:
        for t, year in enumerate(YEARS):
            rate = BASE_RATE * (coef ** t)
            for _ in range(poisson(rng, rate)):
                # 80% 落在主攻标签，20% 溢出到其他标签
                tag = (rng.choice(main_tags) if rng.random() < 0.8
                       else rng.choice(TAGS))
                pts = min(60.0, max(2.0, rng.lognormvariate(2.6, 0.7)))
                month = rng.randint(1, 12)
                rows.append((uid, tag, round(pts, 1), year, month))

    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['user_id', 'tag', 'points', 'year', 'month'])
        w.writerows(rows)

    n_mode = {m: sum(1 for _, mm, _, _ in profile if mm == m)
              for m, _, _ in PATTERNS}
    print('=' * 68)
    print('  已生成【仿真】积分流水：%s' % a.out)
    print('=' * 68)
    print('  记录数      %d 条' % len(rows))
    print('  人员        %d 名（稳定 %d / 上升 %d / 衰退 %d）'
          % (a.users, n_mode['stable'], n_mode['rising'], n_mode['fading']))
    print('  标签        %d 个' % N_TAG)
    print('  年度        %d—%d' % (YEARS[0], YEARS[-1]))
    print('  随机种子    %d（固定，可复现）' % a.seed)
    print('  年均产出    %.1f 件/人' % (len(rows) / a.users / len(YEARS)))
    print()
    print('  ⚠ 仿真数据。写入论文必须标注为仿真实验，不得与表 2/3/4 的实测结果混同。')
    print('=' * 68)

    if a.run:
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '参数敏感性分析.py')
        print()
        subprocess.run([sys.executable, script, a.out, '--now', str(YEARS[-1])])


if __name__ == '__main__':
    main()
