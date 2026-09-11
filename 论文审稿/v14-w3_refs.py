# -*- coding: utf-8 -*-
"""W3 删 6 条弱相关文献，正文引用与文后表一并重编号（29 → 23 条）。

删除依据——都属于"看起来在综述、其实撑不起论点"的一类：
  [13] 季甜甜 Vue 前端性能        与前后端分离结构无直接支撑关系，[12] 已够
  [14] Spring Boot 工业物联网编排  边云协同/工业 IoT，与疾控积分系统无关
  [16] Flask 在线考试系统          与本文业务无关，其所在的凑引句已在 W2 删除
  [19] role clustering            RBAC 已有 [18][21] 两条，且本条讲角色聚类
  [20] 魏巍 RBAC 云资源管理        同上，且刊物层次偏低
  [28] 何立富 Spring Security      与 [27] 主题重复

保留 [15]（张岩·基于 Spring Boot 的公共卫生服务平台）与 [21]（隐私增强 RBAC），
前者是全表中与本文场景最近的一条，后者对应 4.6 节的个人信息分级授权。
本刊自引 [10]（计算机技术与发展, 2024）保留。
"""
import re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, save
from rlib import run_replace, para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

DROP = {13, 14, 16, 19, 20, 28}
TOTAL = 29
keep = [n for n in range(1, TOTAL + 1) if n not in DROP]
MAP = {old: new for new, old in enumerate(keep, 1)}
print('编号映射：' + '，'.join('%d→%d' % (o, MAP[o]) for o in keep if o != MAP[o]))

CIT = re.compile(r'\[([0-9]+(?:[,\-][0-9]+)*)\]')


def expand(s):
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-')
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def render(ns):
    """连续段压成 a-b，其余逗号分隔。"""
    ns = sorted(set(ns))
    grp, cur = [], [ns[0]]
    for x in ns[1:]:
        if x == cur[-1] + 1:
            cur.append(x)
        else:
            grp.append(cur)
            cur = [x]
    grp.append(cur)
    return '[%s]' % ','.join(
        '%d-%d' % (g[0], g[-1]) if len(g) > 1 else str(g[0]) for g in grp)


paras = [c for c in body if c.tag == W + 'p']
i_ref = next(i for i, p in enumerate(paras) if para_text(p).strip() == '参考文献')

# ── 正文引用 ──────────────────────────────────────────────────────
nfix = 0
for p in paras[:i_ref]:
    t = para_text(p)
    jobs = []
    for m in CIT.finditer(t):
        ns = expand(m.group(1))
        if not all(1 <= n <= TOTAL for n in ns):
            continue                      # [0, 1]、[20, 100] 之类的区间记号
        new_ns = [MAP[n] for n in ns if n not in DROP]
        if not new_ns:
            raise SystemExit('引用 %s 全部被删，需先处理该句' % m.group(0))
        jobs.append((m.group(0), render(new_ns)))
    if not any(a != b for a, b in jobs):
        continue
    # 两遍替换：先各自换成私用区哨兵，再换成新号，避免"新号撞上后面的旧号"
    for k, (old_tok, _) in enumerate(jobs):
        run_replace(p, old_tok, '%d' % k)
    for k, (old_tok, new_tok) in enumerate(jobs):
        run_replace(p, '%d' % k, new_tok)
        if old_tok != new_tok:
            nfix += 1
            print('  正文 %s → %s   (%s…)' % (old_tok, new_tok, t[:22]))
print('正文引用改写 %d 处' % nfix)

# ── 文后参考文献表 ────────────────────────────────────────────────
ref_ps = {}
for p in paras[i_ref + 1:]:
    m = re.match(r'\s*\[(\d+)\]', para_text(p))
    if m:
        ref_ps[int(m.group(1))] = p
assert set(ref_ps) == set(range(1, TOTAL + 1)), sorted(set(range(1, TOTAL + 1)) - set(ref_ps))

for n in sorted(DROP):
    print('  删除 [%d] %s' % (n, para_text(ref_ps[n])[:52]))
    body.remove(ref_ps[n])
for n in keep:                       # 从小到大改，[13]→[13] 之类不会撞号
    if MAP[n] != n:
        run_replace(ref_ps[n], '[%d]' % n, '[%d]' % MAP[n])

save(tree, SRC, 'ref.xml')
print('W3 done: 参考文献 %d → %d 条' % (TOTAL, len(keep)))
