# -*- coding: utf-8 -*-
"""把 JMeter 的 .jtl 结果汇总成论文表 3 的四行，并可直接写回 docx。

用法
    # 1) 只看汇总（先跑完四档压测）
    python3 汇总压测结果.py out/50.jtl out/100.jtl out/200.jtl out/500.jtl

    # 2) 带上 Redis 命中率（四档各一个值，顺序对应）
    python3 汇总压测结果.py out/*.jtl --hit 96.8,95.6,94.2,92.5

    # 3) 直接写进论文
    python3 汇总压测结果.py out/*.jtl --hit ... --docx 科研积分系统论文-计算机系统应用版.docx

去掉爬坡段：默认丢弃每档最初 60 s 的样本（--warmup 可调），只统计稳态。
统计口径与 JMeter 的 Summary Report 一致：
    平均响应  = 所有样本 elapsed 的算术平均
    95% 响应  = elapsed 的 95 百分位（JMeter 用的最近秩法）
    吞吐量    = 样本数 / 稳态时长(s)
    错误率    = 失败样本数 / 样本数
汇总后会用 Little 定律自检：吞吐量 × 平均响应 / 并发数 应在 0~1 之间。
"""
import csv, os, re, sys, zipfile, shutil, argparse
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def pct(sorted_vals, p):
    """JMeter 的百分位算法：最近秩，index = ceil(p/100 * N) - 1。"""
    if not sorted_vals:
        return 0.0
    import math
    i = max(0, math.ceil(p / 100.0 * len(sorted_vals)) - 1)
    return sorted_vals[i]


def load(path, warmup):
    rows = []
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            try:
                rows.append((int(r['timeStamp']), int(r['elapsed']),
                             r['success'].strip().lower() == 'true'))
            except (KeyError, ValueError):
                continue
    if not rows:
        raise SystemExit('%s 里没有可解析的样本，检查 .jtl 是否带表头（fieldNames=true）' % path)
    t0 = min(r[0] for r in rows) + warmup * 1000
    rows = [r for r in rows if r[0] >= t0]
    if not rows:
        raise SystemExit('%s 去掉 %d s 爬坡段后没有样本了，把 --warmup 调小' % (path, warmup))
    span = (max(r[0] for r in rows) - min(r[0] for r in rows)) / 1000.0
    el = sorted(r[1] for r in rows)
    n = len(rows)
    return {
        'n': n,
        'avg': sum(el) / n,
        'p95': pct(el, 95),
        'tps': n / span if span > 0 else 0.0,
        'err': 100.0 * sum(1 for r in rows if not r[2]) / n,
        'span': span,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jtl', nargs='+', help='四档 .jtl，按并发从小到大')
    ap.add_argument('--users', default='50,100,200,500')
    ap.add_argument('--hit', default='', help='各档 Redis 命中率，逗号分隔')
    ap.add_argument('--warmup', type=int, default=60, help='每档丢弃的爬坡秒数')
    ap.add_argument('--docx', default='', help='写回哪个 docx 的表 3')
    a = ap.parse_args()

    users = [int(x) for x in a.users.split(',')]
    hits = [x.strip() for x in a.hit.split(',')] if a.hit else []
    if len(a.jtl) != len(users):
        raise SystemExit('给了 %d 个 jtl 但 --users 有 %d 档' % (len(a.jtl), len(users)))

    out, warn = [], []
    print('%-8s %-10s %-10s %-12s %-9s %-9s %s' %
          ('并发', '平均/ms', '95%/ms', '吞吐/(次·s⁻¹)', '错误率/%', '命中率/%', '利用率'))
    for i, (path, u) in enumerate(zip(a.jtl, users)):
        s = load(path, a.warmup)
        avg, p95 = round(s['avg']), round(s['p95'])
        tps, err = round(s['tps']), round(s['err'], 1)
        util = tps * avg / 1000.0 / u
        hit = hits[i] if i < len(hits) else '—'
        flag = '' if util <= 1.0 else '  ← 超过 1，不可能'
        if util > 1.0:
            warn.append('%d 并发：吞吐 %d × 响应 %d ms / %d = %.2f > 1，'
                        '同一次压测出不来这种组合' % (u, tps, avg, u, util))
        print('%-8d %-10d %-10d %-12d %-9s %-9s %.3f%s' %
              (u, avg, p95, tps, ('%g' % err), hit, util, flag))
        out.append([str(u), str(avg), str(p95), str(tps), '%g' % err, hit])
        print('         样本 %d 个，稳态 %.0f s' % (s['n'], s['span']))

    if warn:
        print('\n⚠️  Little 定律自检没过：')
        for w in warn:
            print('   ·', w)
        print('   多半是 .jtl 混进了别档的样本，或 --warmup 没把爬坡段切干净。')
    else:
        print('\n✅ Little 定律自检通过（吞吐 × 响应 ≤ 并发数）')

    if a.docx:
        write_docx(a.docx, out)


def write_docx(path, rows):
    """把四行数据写进 docx 里表 3 的数据行。"""
    tmp = path + '.unz'
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    with zipfile.ZipFile(path) as z:
        z.extractall(tmp)
    src = os.path.join(tmp, 'word', 'document.xml')
    raw = open(src, encoding='utf-8').read()
    for pfx, uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw)).items():
        if not re.fullmatch(r'ns\d*', pfx):
            ET.register_namespace(pfx, uri)
    tree = ET.parse(src)
    body = tree.getroot().find(W + 'body')

    def txt(el):
        return ''.join(t.text or '' for t in el.iter(W + 't'))

    tbl = None
    for t in body.iter(W + 'tbl'):
        if '并发用户数' in txt(t) and '吞吐量' in txt(t):
            tbl = t
            break
    if tbl is None:
        raise SystemExit('在 %s 里没找到表 3（表头需含"并发用户数"与"吞吐量"）' % path)

    trs = tbl.findall(W + 'tr')[1:]
    if len(trs) != len(rows):
        raise SystemExit('表 3 有 %d 个数据行，但给了 %d 行数据' % (len(trs), len(rows)))
    for tr, vals in zip(trs, rows):
        for tc, v in zip(tr.findall(W + 'tc'), vals):
            ts = list(tc.iter(W + 't'))
            if not ts:
                continue
            ts[0].text = v
            for extra in ts[1:]:
                extra.text = ''

    orig = re.search(r'<w:document\b[^>]*>', raw).group(0)
    tree.write(src, encoding='UTF-8', xml_declaration=True)
    s = open(src, encoding='utf-8').read()
    cur = re.search(r'<w:document\b[^>]*>', s).group(0)
    have = set(re.findall(r'xmlns:(\w+)=', orig))
    add = [f'xmlns:{k}="{v}"' for k, v in re.findall(r'xmlns:(\w+)="([^"]+)"', cur)
           if k not in have]
    open(src, 'w', encoding='utf-8').write(
        s.replace(cur, orig[:-1] + (' ' + ' '.join(add) if add else '') + '>', 1))

    outp = path.replace('.docx', '-实测.docx')
    if os.path.exists(outp):
        os.remove(outp)
    names = []
    for r, _, fs in os.walk(tmp):
        for f in fs:
            p = os.path.join(r, f)
            names.append((p, os.path.relpath(p, tmp).replace(os.sep, '/')))
    names.sort(key=lambda x: (x[1] != '[Content_Types].xml', x[1]))
    with zipfile.ZipFile(outp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p, arc in names:
            z.write(p, arc)
    shutil.rmtree(tmp)
    print('\n已写入 %s' % outp)
    print('别忘了正文里跟表 3 相关的两句话也要对一遍：')
    print('  · 3.6 节"缓存命中率在 50–500 并发下保持在 ××% 以上"')
    print('  · 摘要"500 并发下缓存命中率保持在 ××% 以上"')


if __name__ == '__main__':
    main()
