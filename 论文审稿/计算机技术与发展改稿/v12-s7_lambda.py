# -*- coding: utf-8 -*-
"""S7 修正 λ 的表述：其作用范围是周期内部，不应再声称 4.95 年半衰期 / 5 年聘期。"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

# ── 3.3 节参数取值段 ────────────────────────────────────────────────
p = find(body, '式(5)中 α 取 0.7')
rewrite(p,
    '式(5)中 α 取 0.7，即最新周期贡献占 70%、历史累积占 30%，各期权重按 '
    'α(1 − α){sup|j} 衰减，最近 3 个年度周期累计贡献约 97.3%，'
    '与事业单位近三年考核口径相吻合——{b|跨年度的成果时效完全由式(5) 承担}，'
    '兼顾近期活跃度与资深人员的积累。式(4)中的时间衰减系数取 λ = 0.14，'
    '其作用范围限于周期内部：由于 τ{sub|now} 取本周期期末，成果龄期不超过 1 年，'
    '年内最大衰减为 1 − e{sup|−0.14} ≈ 13.1%，用于区分同一考核年度内'
    '早完成与晚完成的成果，避免年末集中申报与年初申报获得同等权重。'
    '两式分工明确，不重复计算同一段时间。')

# ── 摘要：不再声称 4.95 年半衰期 ────────────────────────────────────
p = find(body, '摘　要：')
t = text_of(p).replace(
    '将半衰期 4.95 年（λ = 0.14）的指数时间衰减前置嵌入行为积分归一化环节',
    '并将周期内指数时间衰减（λ = 0.14）前置嵌入行为积分归一化环节')
rewrite(p, t)

# ── 英文摘要同步 ────────────────────────────────────────────────────
p = find(body, 'Abstract: Research talent evaluation')
t = text_of(p).replace(
    'with an exponential time decay of a 4.95-year half-life (lambda = 0.14) '
    'embedded ahead of behaviour-score normalization',
    'with a within-period exponential time decay (lambda = 0.14) embedded '
    'ahead of behaviour-score normalization')
rewrite(p, t)

# ── 结论：局限性表述同步 ────────────────────────────────────────────
p = find(body, '本文工作尚存三点局限')
t = text_of(p).replace(
    'α 与 λ 依据事业单位近三年考核口径与 5 年聘期设定，制度依据明确，'
    '但其取值区间对人才排名的影响程度仍有待更大样本的敏感性分析验证',
    'α 依据事业单位近三年考核口径设定，λ 用于区分年度内成果的完成先后，'
    '两者制度依据明确，但其取值区间对人才排名的影响程度仍有待'
    '更大样本的敏感性分析验证')
rewrite(p, t)

save(tree, SRC, 'ref.xml')
print('S7 done')
