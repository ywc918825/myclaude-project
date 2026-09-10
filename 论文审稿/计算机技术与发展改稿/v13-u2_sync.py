# -*- coding: utf-8 -*-
"""U2 摘要、英文摘要、结论同步纳入第 5 节的对比实验，并修一处措辞。"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')


def swap(anchor, old, new):
    p = find(body, anchor)
    t = text_of(p)
    assert old in t, '未命中【%s】:\n%s' % (old[:44], t[:300])
    rewrite(p, t.replace(old, new))


# ── 措辞：“结果显示三点。其中……”读着断裂 ─────────────────────────
swap('结果显示三点',
     '结果显示三点。其中与均分法的秩相关为 0.864，',
     '与均分法的秩相关为 0.864，')

# ── 中文摘要 ──────────────────────────────────────────────────────
swap('摘　要：',
     '260 个功能测试用例全部通过；',
     '260 个功能测试用例全部通过；'
     '以本中心 2024—2025 年公开发表的 183 篇论文为样本的对比实验表明，'
     '本文分配方法与均分法的人才排名 Spearman 秩相关为 0.864、Top-30 重合 21/30，'
     '合作规模高于中位数的人员平均上升 9.8 个名次，'
     '与名义分值制鼓励协作的设计意图一致；')

# ── 英文摘要 ──────────────────────────────────────────────────────
swap('Abstract: Research talent evaluation',
     'all 260 functional test cases pass;',
     'all 260 functional test cases pass. A comparative experiment on 183 papers '
     'published by the centre in 2024-2025, retrieved from CNKI, shows a Spearman '
     'rank correlation of 0.864 between the proposed allocation method and equal '
     'sharing, a Top-30 overlap of 21/30, and an average rise of 9.8 places for '
     'researchers whose mean team size is above the median, which matches the '
     'collaboration-oriented intent of the nominal-credit scheme.')

# ── 结论 ──────────────────────────────────────────────────────────
swap('把时间衰减放在行为积分层',
     '多作者分配采用名义分值制则是管理导向下的取舍，',
     '以本中心 183 篇公开发表论文为样本的对比实验表明，'
     '该方法与均分法的排名秩相关为 0.864、Top-30 重合 21/30，'
     '合作规模高于中位数的人员平均上升 9.8 个名次，'
     '排名变化的方向与设计意图一致。'
     '多作者分配采用名义分值制则是管理导向下的取舍，')

save(tree, SRC, 'ref.xml')
print('U2 done')
