# -*- coding: utf-8 -*-
"""S8 按系统真实实现修正 τ_now 与时效衰减的表述。

系统中 τ_now 取评价时刻（非本周期期末），故式(4) 按成果绝对年龄衰减，
与式(5) 的 EWMA 对同一段时间各折算一次，合成年度保持率 (1−α)e^(−λ) ≈ 0.261，
等效半衰期约 0.52 年。S7 曾按“周期期末”改写，与代码不符，此处推翻重写。
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

# ── 式中符号说明：τ_now 定义 + 删除“不重复计算”的错误论断 ──────────
p = find(body, '为用户 u 在标签 t 上第 k 个周期')
t = text_of(p)
old_tail = ('τnow 为本周期期末时刻，τi 为成果完成时间。需要指出的是，'
            '式(4) 的衰减因子只处理周期内部的时效差异，跨周期的时效由式(5) 的'
            '指数加权承担，两级衰减各司其职，不重复计算同一段时间。')
assert old_tail in t, '锚点未命中:\n' + t[-200:]
new_tail = ('τnow 为评价时刻，τi 为成果完成时间，'
            '故式(4) 按成果相对评价时刻的绝对年龄衰减。'
            '式(4) 作用于归一化之前，刻画成果完成先后的连续差异；'
            '式(5) 作用于周期之间，提供跨周期的指数平滑。'
            '两式共同决定成果的时效权重，其合成效果见 3.3 节参数取值的说明。')
rewrite(p, t.replace(old_tail, new_tail))

# ── 3.3 节参数取值：给出合成衰减率与实际记忆特性 ────────────────────
p = find(body, '式(5)中 α 取 0.7')
rewrite(p,
    '式(5)中 α 取 0.7，即最新周期贡献占 70%、历史累积占 30%，各期权重按 '
    'α(1 − α){sup|j} 衰减；式(4)中的时间衰减系数取 λ = 0.14。'
    '两式合成后，j 个周期前的成果相对当期的权重为 '
    '[(1 − α)e{sup|−λ}]{sup|j} ≈ 0.261{sup|j}，'
    '最近 3 个年度周期累计贡献约 98%，与事业单位近三年考核口径相吻合。'
    '该权重序列由 α 主导（1 − α = 0.30 远小于 '
    'e{sup|−λ} = 0.87），λ 的作用是在此基础上按成果完成时间'
    '做连续修正，使同一周期内早完成与晚完成的成果不致等权，避免年末集中申报。'
    '需要明确的是，上述取值使模型度量的是{b|当前科研活跃度}——'
    '对近期成果显著加权，而非对多年积累作等权累计；'
    '若评价目的转向长周期积累，需相应下调 α，仅调整 λ 无法改变该特性。')

# ── 摘要：去掉 S7 引入的“周期内”限定 ───────────────────────────────
p = find(body, '摘　要：')
t = text_of(p).replace('并将周期内指数时间衰减（λ = 0.14）前置嵌入行为积分归一化环节',
                       '并将指数时间衰减（λ = 0.14）前置嵌入行为积分归一化环节')
rewrite(p, t)

p = find(body, 'Abstract: Research talent evaluation')
t = text_of(p).replace('with a within-period exponential time decay (lambda = 0.14) '
                       'embedded ahead of behaviour-score normalization',
                       'with an exponential time decay (lambda = 0.14) embedded '
                       'ahead of behaviour-score normalization')
rewrite(p, t)

# ── 结论局限性：λ 的定位同步 ───────────────────────────────────
p = find(body, '本文工作尚存三点局限')
t = text_of(p).replace(
    'α 依据事业单位近三年考核口径设定，λ 用于区分年度内成果的完成先后，'
    '两者制度依据明确，但其取值区间对人才排名的影响程度仍有待'
    '更大样本的敏感性分析验证',
    'α 与 λ 合成的年度保持率约为 0.26，最近三个周期累计贡献约 98%，'
    '与近三年考核口径相符，但这也意味着模型偏重当前活跃度、'
    '对多年积累的刻画有限；两参数取值对排名的影响程度仍有待'
    '更大样本的敏感性分析验证')
rewrite(p, t)

save(tree, SRC, 'ref.xml')
print('S8 done')
