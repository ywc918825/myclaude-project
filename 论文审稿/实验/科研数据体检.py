# -*- coding: utf-8 -*-
"""对《2024-2025 人才积分材料汇总表》做实验可行性体检，并导出真实论文题名清单。

结论（2026-09-10 运行）：
  实验一 不可行——按标题归并后 202 件成果，但中心内 ≥3 人合著仅 7 件（门槛 30），
          且仅 10% 的记录带作者位次标记。根因是这份档案是"佐证材料归档"而非
          "成果登记"：每人只提交自己那份，合作者是否也提交纯属偶然，
          181/202 件只出现一次。完整作者列表在论文本身，不在这份档案里。
  实验二 不可行——只有 2024、2025 两个年度，EWMA 递推需 ≥3 期；且 2025 仅 121 条
          （2024 为 779 条），明显是部分年度数据，年际对比会失真。
  可支撑——成果类别分布：80 人、11 类，人均 3.15 类，50.0% 涉及 3 类以上，
          仅 22.5% 单一类别。已作为多维画像的现实依据写入正文第 4 节。

用法：python3 科研数据体检.py 2024-2025人才积分材料汇总表.xlsx [--out 中心论文清单.csv]
"""
import argparse, csv, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx简易读取器 import load

RANKMARK = re.compile(r'^\s*[（(](一作|第一|通讯|参编|第[二三四五六七八九十]|参与)[^）)]*[）)]')
NOISE = {'封面', '目录', '正文', '7.发表论文', '发表论文', '论文'}
SKIP_CAT = {'其他', '积分明细表'}


def norm(s):
    s = RANKMARK.sub('', str(s).strip())
    s = re.sub(r'^\s*\d+[\s._-]+', '', s)
    s = re.sub(r'[（(]\d+[）)]\s*$', '', s)
    s = re.sub(r'_[一-龥]{2,4}\s*$', '', s)
    s = re.sub(r'[-－—–]', '-', s)
    return re.sub(r'[\s，,。.、；;：:_（）()《》“”"\'\[\]]', '', s).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xlsx')
    ap.add_argument('--out', default='中心论文清单.csv')
    a = ap.parse_args()

    sh = dict(load(a.xlsx))
    if '材料明细' not in sh:
        sys.exit('未找到「材料明细」工作表，实际有：' + '、'.join(sh))
    md = sh['材料明细']; hdr = md[0]; rows = md[1:]
    ci = {h: i for i, h in enumerate(hdr)}
    g = lambda r, k: (r[ci[k]] if ci.get(k) is not None and ci[k] < len(r) else '') or ''

    print('材料明细 %d 条，涉及 %d 人' % (len(rows), len({g(r, '姓名') for r in rows if g(r, '姓名')})))
    yc = Counter(g(r, '年度') for r in rows if g(r, '年度'))
    print('年度分布：' + '，'.join('%s 年 %d 条' % kv for kv in sorted(yc.items())))

    # ── 实验一 ────────────────────────────────────────────────────
    ps = [(g(r, '姓名'), g(r, '材料名称')) for r in rows if g(r, '材料类别') == '发表论文']
    bad = {norm(x) for x in NOISE}
    clean = [(n, t) for n, t in ps if norm(t) not in bad and len(norm(t)) >= 8]
    grp, title = defaultdict(set), {}
    for n, t in clean:
        k = norm(t); grp[k].add(n); title.setdefault(k, t)
    sizes = Counter(len(v) for v in grp.values())
    m3 = sum(c for n, c in sizes.items() if n >= 3)
    people = len({n for v in grp.values() for n in v})
    mk = sum(1 for _, t in ps if RANKMARK.match(str(t))
             or re.search(r'第一作者|参与论文|通讯', str(t)))
    print('\n【实验一 分配方法对比】')
    print('  按标题归并 %d 件成果，中心内合著人数：%s'
          % (len(grp), '，'.join('%d人%d件' % (n, sizes[n]) for n in sorted(sizes))))
    for lab, need, act in (('成果件数', 100, len(grp)), ('涉及人员', 30, people),
                           ('≥3 人合著件数', 30, m3)):
        print('  %-16s 需 ≥%-4d 实际 %-5d %s' % (lab, need, act, '✅' if act >= need else '❌'))
    print('  带作者位次标记：%d/%d 条（%.0f%%）' % (mk, len(ps), 100 * mk / len(ps) if ps else 0))
    print('  → %s' % ('可行' if (len(grp) >= 100 and people >= 30 and m3 >= 30)
                      else '不可行。完整作者列表在论文本身，需从知网机构题录取'))

    # ── 实验二 ────────────────────────────────────────────────────
    print('\n【实验二 α/λ 敏感性】')
    print('  年度跨度 %d 年 需 ≥3 年 %s' % (len(yc), '✅' if len(yc) >= 3 else '❌'))
    if len(yc) >= 2 and max(yc.values()) > 3 * min(yc.values()):
        print('  ⚠ 各年度条数相差悬殊，疑为部分年度数据，年际对比会失真')

    # ── 可支撑：成果类别分布 ──────────────────────────────────────
    per = defaultdict(set)
    for r in rows:
        n, c = g(r, '姓名'), g(r, '材料类别')
        if n and c and c not in SKIP_CAT:
            per[n].add(c)
    if per:
        N = len(per); dist = Counter(len(v) for v in per.values())
        avg = sum(len(v) for v in per.values()) / N
        ge3 = sum(c for k, c in dist.items() if k >= 3)
        print('\n【可支撑：成果类别分布】')
        print('  %d 人、%d 类，人均 %.2f 类，≥3 类占 %.1f%%，单一类别占 %.1f%%'
              % (N, len({c for v in per.values() for c in v}), avg,
                 100 * ge3 / N, 100 * dist.get(1, 0) / N))

    with open(a.out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['序号', '论文题名（取自佐证材料名）', '中心内提交人'])
        for i, (k, v) in enumerate(sorted(grp.items(), key=lambda kv: -len(kv[1])), 1):
            w.writerow([i, title[k], '、'.join(sorted(v))])
    print('\n已导出 %s：%d 条真实题名（可用于核对知网检索是否捞全）' % (a.out, len(grp)))


if __name__ == '__main__':
    main()
