# -*- coding: utf-8 -*-
"""直接从 talent.db 导出实验数据，并先做一次"数据够不够"的体检。

按实际库结构（SQLite，7 表 64 字段）编写：
    points_items(user_id, year, category 1~17, title, level, role_rank, role_type,
                 amount, extras JSON, self_score, status, obtain_date, ...)
    users(id, name, department, title, ...)

用法：
    python3 db导出实验数据.py server/data/talent.db            # 只体检，不导出
    python3 db导出实验数据.py server/data/talent.db --export   # 体检并导出 CSV

两个实验在这套表结构下的可行性完全不同，先看清楚再动手：

实验二（α/λ 敏感性）——**结构上完全支持**
    需要 user_id, tag, points, year, month
    · tag    ← category 的 17 个大项名称
    · points ← self_score
    · year/month ← obtain_date（YYYY-MM-DD），月份可得，λ 才有意义
    唯一门槛是记录条数。

实验一（分配方法对比）——**结构上不支持，只能近似**
    需要"每件成果的全部作者及各自位次"，而 points_items 一行只记录申报人自己：
    · 无 work_id，同一成果的合作者之间没有任何关联字段
    · 无作者列表，不记录"这篇还有谁"
    · 无成果标准积分，只有 self_score（自评）
    本脚本按标题归并近似重建成果，并如实报告有多少成果凑到了 ≥2 名申报人。
    若绝大多数成果只有 1 名申报人，说明这条路走不通——改用历史科研台账，
    见 台账转实验数据.py。
"""
import argparse, csv, os, re, sqlite3, sys
from collections import Counter, defaultdict

CATEGORY = {
    1: '项目课题', 2: '成果奖励', 3: '专利发明', 4: '技术标准', 5: '成果转化',
    6: '科普项目', 7: '发表论文', 8: '出版著作', 9: '继续教育', 10: '工作文章',
    11: '荣誉表彰', 12: '学科团队', 13: '学科人才', 14: '技能竞赛',
    15: '学术比赛', 16: '学术交流', 17: '学术地位',
}

# role_rank 是自由文本，这里给出常见取值到数字位次的映射
RANK = {
    '第一': 1, '第1': 1, '主持': 1, '第一作者': 1, '负责人': 1, '主要完成人': 1,
    '第二': 2, '第2': 2, '第二作者': 2,
    '第三': 3, '第3': 3, '第三作者': 3,
    '第四': 4, '第4': 4, '参与': 4, '成员': 4, '参加': 4, '其他': 4,
}
CORR = ('通讯', '通信')


def norm_title(s):
    """标题归一化：去空白与全角标点，用于把同一成果的多份申报归到一起。"""
    s = re.sub(r'\s+', '', s or '')
    return re.sub(r'[，。、；：（）()《》“”"\'\-—_]', '', s).lower()


def rank_of(txt):
    t = re.sub(r'\s+', '', txt or '')
    for k, v in RANK.items():
        if k in t:
            return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('db')
    ap.add_argument('--export', action='store_true', help='通过体检后导出 CSV')
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--status', default='approved',
                    help="纳入统计的状态，逗号分隔；填 all 表示不筛（默认 approved）")
    a = ap.parse_args()

    if not os.path.exists(a.db):
        sys.exit('找不到数据库：%s' % a.db)
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row

    have = {r['name'] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ('points_items', 'users'):
        if t not in have:
            sys.exit('库里没有 %s 表，表清单：%s' % (t, '、'.join(sorted(have))))

    print('=' * 68)
    print('  数据体检：%s' % a.db)
    print('=' * 68)
    for t in sorted(have):
        n = con.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
        print('  %-20s %6d 行' % (t, n))

    st = con.execute('SELECT status, COUNT(*) c FROM points_items '
                     'GROUP BY status ORDER BY c DESC').fetchall()
    print('\n  points_items 状态分布：'
          + ('，'.join('%s %d' % (r['status'], r['c']) for r in st) or '（空表）'))

    where = '' if a.status == 'all' else \
        'WHERE status IN (%s)' % ','.join('?' * len(a.status.split(',')))
    args = [] if a.status == 'all' else a.status.split(',')
    rows = con.execute('SELECT user_id, year, category, title, role_rank, '
                       'self_score, obtain_date FROM points_items ' + where,
                       args).fetchall()
    print('  纳入统计（status=%s）：%d 条' % (a.status, len(rows)))

    if not rows:
        print('\n  ⛔ 没有可用记录，两个实验都无法进行。')
        return

    yrs = Counter()
    for r in rows:
        y = None
        if r['obtain_date']:
            m = re.match(r'(\d{4})', str(r['obtain_date']))
            if m:
                y = int(m.group(1))
        y = y or r['year']
        if y:
            yrs[y] += 1
    nomonth = sum(1 for r in rows if not (r['obtain_date'] and
                  re.match(r'\d{4}-\d{2}', str(r['obtain_date']))))
    print('  年度分布：' + '，'.join('%d年 %d条' % (y, yrs[y]) for y in sorted(yrs)))
    print('  缺 obtain_date 月份的记录：%d 条' % nomonth)
    print('  涉及人员：%d 名' % len({r['user_id'] for r in rows}))

    # ── 实验二 可行性 ──────────────────────────────────────────────
    print('\n' + '-' * 68)
    print('  实验二（α/λ 敏感性）')
    print('-' * 68)
    ok2 = True
    if len({r['user_id'] for r in rows}) < 30:
        print('  ⛔ 人员 %d 名 < 30，Spearman 秩相关不稳'
              % len({r['user_id'] for r in rows})); ok2 = False
    if len(yrs) < 3:
        print('  ⛔ 年度跨度 %d 年 < 3，EWMA 递推无从体现跨周期差异' % len(yrs)); ok2 = False
    if len(rows) < 300:
        print('  ⛔ 记录 %d 条 < 300，结论不具统计意义' % len(rows)); ok2 = False
    if nomonth > len(rows) * 0.3:
        print('  ⚠ 超过 30%% 的记录缺月份，λ 的敏感性结论会被削弱')
    print('  ✅ 可行' if ok2 else '  → 不可行，改用 参数敏感性仿真数据生成.py')

    # ── 实验一 可行性：按标题归并 ──────────────────────────────────
    print('\n' + '-' * 68)
    print('  实验一（分配方法对比）—— 按标题近似重建成果')
    print('-' * 68)
    works = defaultdict(list)
    for r in rows:
        works[norm_title(r['title'])].append(r)
    sizes = Counter(len(v) for v in works.values())
    multi = sum(c for n, c in sizes.items() if n >= 2)
    unknown_rank = sum(1 for r in rows if rank_of(r['role_rank']) is None)
    print('  归并后成果 %d 件，申报人数分布：%s'
          % (len(works), '，'.join('%d人 %d件' % (n, sizes[n]) for n in sorted(sizes))))
    print('  ≥2 名申报人的成果：%d 件（占 %.0f%%）'
          % (multi, 100 * multi / len(works) if works else 0))
    print('  role_rank 无法映射为数字位次的记录：%d 条' % unknown_rank)
    ok1 = multi >= 30 and len(works) >= 100
    if not ok1:
        print('\n  ⛔ 不可行。实验一的差异全部来自多作者成果，'
              '而这里只有 %d 件成果凑到 ≥2 名申报人。' % multi)
        print('     根因是表结构：points_items 一行只记录申报人自己，'
              '无 work_id、无作者列表。')
        print('     → 改走历史科研台账：台账转实验数据.py')
    else:
        print('  ✅ 可行（仍需注意：按标题归并可能漏配，且 self_score 是自评'
              '而非成果标准积分）')

    if not a.export:
        print('\n（本次只体检。加 --export 导出 CSV）')
        return

    os.makedirs(a.outdir, exist_ok=True)
    p2 = os.path.join(a.outdir, 'records.csv')
    with open(p2, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['user_id', 'tag', 'points', 'year', 'month'])
        for r in rows:
            y, mo = r['year'], ''
            if r['obtain_date']:
                m = re.match(r'(\d{4})-(\d{2})', str(r['obtain_date']))
                if m:
                    y, mo = int(m.group(1)), int(m.group(2))
            if not y or not r['self_score']:
                continue
            w.writerow(['U%s' % r['user_id'], CATEGORY.get(r['category'], '其他'),
                        r['self_score'], y, mo])
    print('\n已写入 %s' % p2)

    p1 = os.path.join(a.outdir, 'works.csv')
    with open(p1, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['work_id', 'author_id', 'author_rank',
                    'is_corresponding', 'std_points'])
        for i, (_, rs) in enumerate(sorted(works.items()), 1):
            pts = max((x['self_score'] or 0) for x in rs)
            for r in rs:
                rk = rank_of(r['role_rank'])
                if rk is None:
                    continue
                corr = 1 if any(c in (r['role_rank'] or '') for c in CORR) else 0
                w.writerow(['W%04d' % i, 'U%s' % r['user_id'], rk, corr, pts])
    print('已写入 %s' % p1)
    print('\n⚠ works.csv 由标题归并近似重建，std_points 取同一成果各申报人自评分的最大值，'
          '均为替代口径。若实验一体检未通过，请勿用于论文。')


if __name__ == '__main__':
    main()
