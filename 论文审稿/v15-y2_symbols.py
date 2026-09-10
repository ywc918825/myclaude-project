# -*- coding: utf-8 -*-
"""Y2 补 3.4 节的变量符号格式，并修同段的半角逗号。

这是本轮翻出来的旧账，不是精简造成的：3 节里 5 个含变量的段落
（式(1)(3)(4)(5)(7) 的"式中"段）都有斜体与上下标，唯独 3.4 节
"定义标签—能力维度映射矩阵…"这段是纯文本——M、R^{T×D}、m_{t,d}、
W^{(k)}_{t,u} 全部平排。同一篇里两种排法，编辑一眼能看出来。

格式沿用 3.3 节既有约定（见 P039）：主符号斜体，上下标不斜体。
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, rewrite, text_of, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

p = find(body, '定义标签—能力维度映射矩阵')
before = text_of(p)

MARKUP = (
    '定义标签—能力维度映射矩阵 {i|M} ∈ {i|R}{sup|T×D}，{i|T} 为标签总数，'
    '{i|D} 为能力维度数（本系统取 {i|D} = 16，各维度名称如图2所示）。'
    '元素 {i|m}{sub|t,d} ∈ [0, 1] 表示标签 {i|t} 对维度 {i|d} 的贡献度，'
    '满足 Σ{sub|d}{i|m}{sub|t,d} = 1，由本中心 3 名具有高级职称的科研管理专家'
    '经两轮独立打分与组间反馈修正确定，打分流程参照省级疾控信息化评价指标的构建方式[3]；'
    '受机构规模限制，参与标定的专家人数偏少，该矩阵反映的是本中心的评价导向，'
    '跨机构应用时需重新标定。各维度原始得分为当前周期标签权重'
    '（式(5) 中的 {i|W}{sup|(k)}{sub|t,u}）的加权和（式(6)）；'
    '由于式(4)已在行为积分层面完成时间衰减修正，式(6)无需再次引入衰减因子。'
)

rewrite(p, MARKUP)
after = text_of(p)

# 纯文本只应差一个字符：半角逗号 → 全角逗号
def norm(s):
    return s.replace('，', ',').replace(' ', '')


if norm(after) != norm(before):
    import difflib
    for d in difflib.unified_diff([norm(before)], [norm(after)], lineterm='', n=0):
        print(d[:400])
    raise SystemExit('文字被改动了，停下检查')
print('纯文本一致（仅 RT×D 后的半角逗号改为全角，随之去掉多余空格）')
print('  斜体 %d、下标 %d、上标 %d'
      % (len(p.findall('.//' + W + 'i')),
         sum(1 for v in p.findall('.//' + W + 'vertAlign')
             if v.get(W + 'val') == 'subscript'),
         sum(1 for v in p.findall('.//' + W + 'vertAlign')
             if v.get(W + 'val') == 'superscript')))

save(tree, SRC, 'ref.xml')
print('Y2 done')
