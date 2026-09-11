# -*- coding: utf-8 -*-
"""U1 新增第 5 节「分配方法对比实验」，含表6/7/8；原第 5 节顺延为第 6 节。

数据来自中国知网机构题录（本中心 2024—2025 年发表期刊论文 183 篇、署名 939 人次），
公开可核验。这是回应"只有理论对比、没有实验"这条拒稿意见的正面答案。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

h5 = find(body, '5  结论与展望')
cap = find(body, '表5  本文系统与同类工作的对比')
note = find(body, '注：前两列为同类研究的方法类别归纳')
tbl5 = [c for c in body if c.tag == W + 'tbl'][-1]
para = find(body, '为进一步说明本文工作与同类研究的差异')


def mk_table(rows, widths):
    t = copy.deepcopy(tbl5)
    for tr in t.findall(W + 'tr'):
        t.remove(tr)
    grid = t.find(W + 'tblGrid')
    for g in grid.findall(W + 'gridCol'):
        grid.remove(g)
    for wd in widths:
        g = ET.SubElement(grid, W + 'gridCol')
        g.set(W + 'w', str(wd))
    src = tbl5.findall(W + 'tr')
    hdr_tpl, dat_tpl = src[0], src[1]
    for ri, vals in enumerate(rows):
        tr = copy.deepcopy(hdr_tpl if ri == 0 else dat_tpl)
        tcs = tr.findall(W + 'tc')
        for extra in tcs[len(vals):]:
            tr.remove(extra)
        cur = tr.findall(W + 'tc')
        while len(cur) < len(vals):
            tr.append(copy.deepcopy(cur[-1]))
            cur = tr.findall(W + 'tc')
        for tc, v in zip(tr.findall(W + 'tc'), vals):
            cps = tc.findall(W + 'p')
            rewrite(cps[0], v)
            for e in cps[1:]:
                tc.remove(e)
        t.append(tr)
    return t


T6 = [['分配方法', '本文分段权重法', '均分法', '调和计数法', '算术递减法'],
      ['本文分段权重法', '1.000', '0.864', '0.956', '0.952'],
      ['均分法', '0.864', '1.000', '0.897', '0.926'],
      ['调和计数法', '0.956', '0.897', '1.000', '0.981'],
      ['算术递减法', '0.952', '0.926', '0.981', '1.000']]
T7 = [['对比方法', 'Top-10 重合', 'Top-30 重合'],
      ['均分法', '8/10', '21/30'],
      ['调和计数法', '8/10', '26/30'],
      ['算术递减法', '8/10', '26/30']]
T8 = [['人员分组', '人数', '平均排名变动', '名次上升人数占比'],
      ['合作规模高于中位数', '126', '+9.8', '58%'],
      ['合作规模不高于中位数', '131', '−9.5', '39%']]

blocks = []


def add_p(src, markup):
    p = copy.deepcopy(src)
    rewrite(p, markup)
    blocks.append(p)


# ── 节标题 ────────────────────────────────────────────────────────
sec = copy.deepcopy(h5)
rewrite(sec, '5  分配方法对比实验')
blocks.append(sec)

add_p(para,
      '式(1) 与三种守恒型方法的系数差异见表1，但系数不同是否真会改变人才排名，'
      '需以实际成果数据检验。为此以本中心公开发表的论文为样本开展对比实验。')

add_p(para,
      '数据取自中国知网机构题录：按作者单位检索本中心 2024—2025 年发表的期刊论文，'
      '得 183 篇，署名 939 人次，篇均作者 5.13 人，其中 3 人及以上合著 163 篇。'
      '以单位署名仅含本中心的 130 篇论文所涉作者为种子，并与本中心积分评比名册取并集，'
      '确定 257 名本中心作者；外单位合作者计入作者总数 {i|n}，但不进入本中心排名。'
      '知网题录不含通讯作者信息，故全部按署名顺序计算，实验未覆盖'
      '“通讯作者按第 1 作者计”这一规则；各成果取等权（{i|S}{sub|total} = 1），'
      '以隔离分配规则本身的影响。')

add_p(para,
      '按式(1) 与均分法、调和计数法、算术递减法分别累计各作者积分并排序，'
      '四种方法两两之间的 Spearman 秩相关如表6所示。')
c6 = copy.deepcopy(cap); rewrite(c6, '表6  四种分配方法下人才排名的 Spearman 秩相关')
blocks += [c6, mk_table(T6, [1900, 1700, 1500, 1600, 1600])]

add_p(para,
      '秩相关反映整体一致性，头部名次的差异则更直接影响职称评审与激励分配，'
      '以本文方法为基准的 Top-N 人员重合度如表7所示。')
c7 = copy.deepcopy(cap); rewrite(c7, '表7  以本文方法为基准的 Top-N 人员重合度')
blocks += [c7, mk_table(T7, [2600, 2000, 2000])]

add_p(para,
      '排名变化落在谁身上，是判断该方法是否符合设计意图的关键。'
      '按人均合作规模（个人成果的平均作者数，中位数 5.50 人）将人员分为两组，'
      '其相对均分法的名次变动如表8所示。'
      '此处不以“多作者成果占比”分组：本中心 183 篇论文中 163 篇为 3 人以上合著，'
      '该指标全员饱和，无法区分。')
c8 = copy.deepcopy(cap); rewrite(c8, '表8  不同合作规模科研人员的排名变动（本文方法相对均分法）')
blocks += [c8, mk_table(T8, [2400, 1200, 1800, 2000])]
n8 = copy.deepcopy(note)
rewrite(n8, '注：排名变动为正表示在本文方法下名次上升。')
blocks.append(n8)

add_p(para,
      '结果显示三点。其中与均分法的秩相关为 0.864，为四种方法两两比较中的最低值，'
      '而与调和计数法、算术递减法分别为 0.956 与 0.952，说明本文方法'
      '在整体排序上更接近按序位递减的守恒型方法，与均分法差异最大。'
      'Top-30 重合度上，均分法为 21/30，即前 30 名中有 9 人不同，'
      '而调和计数法与算术递减法均为 26/30，差异集中在均分法一侧。'
      '合作规模高于中位数的 126 人平均上升 9.8 个名次、58% 的人名次上升，'
      '合作规模不高于中位数的 131 人平均下降 9.5 个名次，'
      '方向与名义分值制“鼓励多科室协作”的设计意图一致。')

add_p(para,
      '为检验结论对成果分值方案的敏感性，另以对数正态分布随机赋予各成果标准积分'
      '重复 5 次：与均分法的秩相关稳定在 0.864—0.883，Top-30 重合度为 21—24，'
      '高合作规模组始终上升、低合作规模组始终下降。'
      '可见上述结论不随成果分值方案改变。')

add_p(para,
      '本实验的样本仅含公开发表论文，不含课题、专利等其他成果类型，'
      '故所得排名不等同于系统内的完整积分排名，'
      '其作用是在真实合作结构下检验分配规则本身的行为差异。')

pos = list(body).index(h5)
for off, el in enumerate(blocks):
    body.insert(pos + off, el)

rewrite(find(body, '5  结论与展望'), '6  结论与展望')

save(tree, SRC, 'ref.xml')
print('U1 done: 新增第 5 节与表6/7/8，原结论节顺延为第 6 节')
