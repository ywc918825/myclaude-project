# -*- coding: utf-8 -*-
"""S1 把作者提供的真实成果结构统计写入第 4 节。

来源：2024—2025 人才积分材料汇总表（900 份佐证材料、13 个材料类别、85 名人员）。
剔除"其他""积分明细表"两个非成果类别后为 11 类、80 人。

这不是对比实验，而是对评价对象的实证刻画——它给"为什么需要多维画像"提供了
本中心的数据依据，是这批数据唯一能如实支撑的结论。不新增表格：新增会导致
表2—5 重排及交叉引用连改，一句话足够承载该结论。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

anchor = find(body, '为评价标签准确性')
para = copy.deepcopy(anchor)
rewrite(para,
    '为刻画评价对象的产出结构，对本中心 2024—2025 年归档的 900 份成果佐证材料'
    '作了统计：材料覆盖 11 个成果类别、80 名科研人员，人均涉及 3.15 个类别，'
    '涉及 3 个以上类别者占 50.0%，仅 22.5% 集中于单一类别；'
    '发表论文与项目课题的人员覆盖率分别为 78.8% 与 75.0%，其余类别均低于 40%。'
    '该分布表明科研产出结构在人员间差异显著，单一维度的排序难以刻画，'
    '构成了多维画像的现实依据。')
body.insert(list(body).index(anchor), para)

save(tree, SRC, 'ref.xml')
print('S1 done: 真实成果结构统计已写入第 4 节')
