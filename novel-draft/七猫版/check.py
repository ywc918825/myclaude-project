import re, sys, glob, collections
def cjk(x): return len(re.findall(r'[一-鿿]', x))
tot = 0; bad = []
for f in sorted(glob.glob('卷一-*.md')):
    t = open(f, encoding='utf-8').read()
    parts = re.split(r'\n# (第\d+章｜[^\n]*)\n', '\n' + t)
    for i in range(1, len(parts), 2):
        ti, b = parts[i], parts[i+1]
        n = cjk(b); tot += n
        d = sum(cjk(m) for m in re.findall(r'\u201c(.*?)\u201d', b, re.S)) \
          + sum(cjk(m) for m in re.findall(r'「(.*?)」', b, re.S))
        ps = [x.strip() for x in b.split('\n') if x.strip()]
        c = collections.Counter([x for x in ps if len(x) >= 12])
        dup = sum(1 for x, k in c.items() if k > 1)
        dr = round(100 * d / max(n, 1))
        mx = max(cjk(x) for x in ps)
        flag = []
        if not (1800 <= n <= 2300): flag.append('字数')
        if dr < 40: flag.append('对白')
        if mx > 70: flag.append('长段')
        if dup: flag.append('重复')
        if flag: bad.append((ti, flag))
        print(f'{ti[:14]:<18}{n:>5} 对白{dr:>3}% 最长段{mx:>3} 重复{dup}  {"⚠ "+"/".join(flag) if flag else "✓"}')
print(f'\n合计 {tot} 字')
if bad:
    print('不达标：', ', '.join(f'{t[:6]}({"/".join(f_)})' for t, f_ in bad))
