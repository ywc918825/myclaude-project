# -*- coding: utf-8 -*-
"""全文自洽性 + 公式核查后的修正。"""
import re, xml.etree.ElementTree as ET
from lib import W, TOK, register, rewrite, find, text_of, save

M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
SRC = 'unz/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []

TILDE = 's̃'          # s + 组合波浪号，与式(4)(5) 的 m:acc 一致

# ══════════════════════════════════════════════════════════════════
# A. 公式与符号
# ══════════════════════════════════════════════════════════════════

# A1  式(4)：时间变量 t 与标签下标 t 同名，改用 τ
om = list(tree.getroot().iter(M + 'oMath'))[3]
n = 0
for d in om.iter(M + 'd'):
    for ss in d.iter(M + 'sSub'):
        sub = ss.find(M + 'sub')
        e = ss.find(M + 'e')
        if sub is None or e is None:
            continue
        subtxt = ''.join(t.text or '' for t in sub.iter(M + 't'))
        if subtxt in ('now', 'i'):
            for t in e.iter(M + 't'):
                if t.text == 't':
                    t.text = 'τ'; n += 1
assert n == 2, n
log.append('A1 式(4)：时间变量 t_now、t_i 改为 τ_now、τ_i——原来 t 既当标签下标'
           '（W_t,u、m_t,d、S_max,t）又当时间，同符两义')

# A2  式(4)(5) 的“式中”：补 s̃ 与 m 的定义，时间符号同步改 τ
rewrite(find(body, '为本周期全中心在标签'),
        '式中：{i|' + TILDE + '}{sub|i,u} 为行为 {i|i} 经时间衰减与归一化后的积分；'
        '{i|W}{sup|(k)}{sub|t,u} 为用户 {i|u} 在标签 {i|t} 上第 {i|k} 个周期的权重；'
        '{i|s}{sub|i,u} 为其在行为 {i|i} 上的原始积分；{i|m} 为标签 {i|t} 下的行为总数；'
        '{i|S}{sub|max,t} 为本周期全中心在标签 {i|t} 下的最高行为积分，用于将行为项'
        '归一化至 [0, 1]；{i|w}{sub|i} 为行为 {i|i} 的贡献系数，满足 Σ{i|w}{sub|i} = 1；'
        '{i|τ}{sub|now} 与 {i|τ}{sub|i} 分别为当前时间与成果完成时间。')
log.append('A2 式(4)(5) 的“式中”：补上原来没定义的 ' + TILDE + '_i,u 与 m（求和上限），'
           '时间符号同步改 τ')

# A3  α 的“记忆长度”公式用错了
rewrite(find(body, '式(5)中'),
        '式(5)中 {i|α} 取 0.7，即最新周期贡献占 70%、历史累积占 30%，各期权重按 '
        '{i|α}(1 − {i|α})^{sup|j} 衰减，最近 3 个周期累计贡献约 97%，可兼顾近期活跃度'
        '与资深人员的积累；时间衰减系数取 {i|λ} = 0.14，对应半衰期 ln2{i|/λ} ≈ 4.95 年、'
        '年衰减约 13.1%，既避免成果永久有效导致评价僵化，也防止衰减过快挫伤长期积累型'
        '科研人员的积极性。')
log.append('A3 式(5)：删去“记忆长度 1/(1−α) ≈ 3.3 个周期”——该式对应的是 α 作“保留系数”'
           '的写法，本文 α 是新息系数，等效窗口只有 (2−α)/α ≈ 1.9 期，与同句“最新一年占 70%”'
           '自相矛盾。改为直接给权重衰减律与“最近 3 期累计约 97%”（1 − 0.3³ = 0.973），结论'
           '不变而推导站得住')

# A4  式(3) 的 v_i 表述
rewrite(find(body, '原始分配系数'),
        '式中：{i|v}{sub|i} 为式(1)括号中第 {i|i} 作者的分配系数。')
log.append('A4 式(3)：v_i 说成“按式(1)得到的原始分配系数”不准确——式(1)给出的是积分 S_i，'
           'v_i 是括号内的系数')

# A5  4.4 节：衰减修正出自式(4) 而非式(5)；式(6) 用的是当期权重
p = find(body, '定义标签')
s = text_of(p)
rewrite(p,
        '定义标签—能力维度映射矩阵 {i|M} ∈ R{sup|T×D}，{i|T} 为标签总数，{i|D} 为能力'
        '维度数（本系统取 {i|D} = 16，各维度名称如图 2 所示）。元素 {i|m}{sub|t,d} ∈ '
        '[0, 1] 表示标签 {i|t} 对维度 {i|d} 的贡献度，满足 Σ{sub|d}{i|m}{sub|t,d} = 1，'
        '由 3 名科研管理专家按德尔菲法两轮打分确定。各维度原始得分为当前周期标签权重'
        '（式(5)中的 {i|W}{sup|(k)}{sub|t,u}）的加权和（式(6)）；由于式(4)已在行为积分'
        '层面完成时间衰减修正，式(6)无需再次引入衰减因子。')
log.append('A5 4.4 节：“由于式(5)已完成时间衰减修正”改为式(4)——衰减因子 e^(−λΔτ) 在式(4)；'
           '并说明式(6) 的 W_t,u 就是式(5) 的当期权重 W^(k)_t,u（原来少了周期上标）')

# ══════════════════════════════════════════════════════════════════
# B. 全文自洽
# ══════════════════════════════════════════════════════════════════

# B1  四级审批 → 三级（4.5 节只有初审、复核、终审三个审批节点）
for needle, old, new in [
        ('摘要：', '四级审批', '三级审批'),
        ('申报审核模块内置', '四级审批', '三级审批'),
        ('Abstract:', 'four-level', 'three-level')]:
    p = find(body, needle)
    hit = 0
    for t in p.iter(W + 't'):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new); hit += 1
    assert hit, (needle, old)
log.append('B1 “四级审批”改为“三级审批”——4.5 节的状态机只有初审、复核、终审 3 个审批'
           '节点（摘要、英文摘要、第 3 章各 1 处）')

# B2  7 种状态 → 8 种（“任一环节驳回”要求终审也有驳回态）
p = find(body, '针对疾控中心审核流程')
s2 = text_of(p)
assert '待终审与终审通过 7 种状态' in s2, s2
rewrite(p, s2.replace('待终审与终审通过 7 种状态', '待终审、终审驳回与终审通过 8 种状态'))
log.append('B2 4.5 节：状态由 7 种改为 8 种，补“终审驳回”——7 种转换事件里有“终审驳回”，'
           '而原来的 7 个状态没有它的落点，与“任一环节驳回则回退至对应驳回态”矛盾')

# B3  第 3 章标签体系表述对齐 4.3 节的“三维”
p = find(body, '系统设计了五大功能模块')
old = text_of(p)
new = old.replace(
    '人才画像模块构建涵盖结构化标签（学历、职称、专业）与能力标签（科研能力、项目管理、数据分析）的动态标签体系',
    '人才画像模块构建由基础属性（学历、职称）、专业方向与能力维度（科研能力、项目管理、数据分析）构成的三维动态标签体系')
assert new != old
rewrite(p, new)
log.append('B3 第 3 章：标签体系由“结构化 + 能力”两类改为“基础属性 / 专业方向 / 能力维度”，'
           '与 4.3 节的“三维标签体系”对齐')

# B4  表 4：核算差错“件”出现小数 → 改为差错率 / %，与摘要口径完全一致
tbl = [e for e in body if e.tag == W + 'tbl'][3]
rows = tbl.findall(W + 'tr')
for t in rows[0].findall(W + 'tc')[4].iter(W + 't'):
    if t.text == '核算差错':
        t.text = '核算差错率'
    elif t.text == '件':
        t.text = '%'
for t in rows[1].findall(W + 'tc')[4].iter(W + 't'):
    if t.text == '6.8':
        t.text = '3.54'
for t in rows[2].findall(W + 'tc')[4].iter(W + 't'):
    if t.text == '1.2':
        t.text = '0.08'
log.append('B4 表 4：“核算差错 / 件”出现 6.8、1.2 这样的小数（件数不可能是小数），改为'
           '“核算差错率 / %”，取 3.54 与 0.08——恰好就是 6.8/192 与 1.2/1420，与摘要'
           '“由 3.54% 降至 0.08%”完全对上')

# B5  结论补回应用效果
p = find(body, '本文设计并实现了基于')
s = text_of(p)
assert '审批工作流引擎。' in s
rewrite(p, s.replace(
    '审批工作流引擎。后续',
    '审批工作流引擎。系统在南通市疾控中心运行 3 个月，平均审核周期由 7 d 降至 2 d、'
    '积分核算差错率由 3.54% 降至 0.08%。后续').replace('α', '{i|α}').replace('λ', '{i|λ}'))
log.append('B5 结论：补回应用效果一句——压缩时被删掉了，结论只剩三条技术贡献和展望，'
           '没有回扣第 5 章的结果')

# B6  通信地址笔误
p = find(body, '工农南')
for t in list(p.iter(W + 't')):
    if t.text == '路':
        t.text = '路 '        # “工农南路路 189 号” → “工农南路 189 号”
        break
for t in p.iter(W + 't'):
    if t.text == '路':
        t.text = ''
log.append('B6 通信地址：“工农南路路189号”→“工农南路 189 号”（多了一个“路”）')

save(tree, SRC, 'unz.bak/word/document.xml')
print('已完成：')
for l in log:
    print('  ·', l)
