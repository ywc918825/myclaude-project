# -*- coding: utf-8 -*-
"""用真实测试记录重建表 2、表 3。"""
import copy, xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

XS = '{http://www.w3.org/XML/1998/namespace}space'
SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')


def set_cell(tc, txt, width, align):
    tcpr = tc.find(W + 'tcPr')
    tcw = tcpr.find(W + 'tcW') if tcpr is not None else None
    if tcw is not None:
        tcw.set(W + 'w', str(width))
    ps = tc.findall(W + 'p')
    for extra in ps[1:]:
        tc.remove(extra)
    p = ps[0]
    ppr = p.find(W + 'pPr')
    if ppr is not None:
        jc = ppr.find(W + 'jc')
        if jc is None:
            jc = ET.SubElement(ppr, W + 'jc')
        jc.set(W + 'val', align)
    runs = p.findall(W + 'r')
    keep = runs[0] if runs else None
    for r in runs:
        p.remove(r)
    nr = copy.deepcopy(keep) if keep is not None else ET.SubElement(p, W + 'r')
    for c in list(nr):
        if c.tag != W + 'rPr':
            nr.remove(c)
    t = ET.SubElement(nr, W + 't')
    t.set(XS, 'preserve')
    t.text = txt
    p.append(nr)


def rebuild(tbl, matrix, widths, aligns):
    rows = tbl.findall(W + 'tr')
    head_t, mid_t, last_t = rows[0], rows[1], rows[-1]
    grid = tbl.find(W + 'tblGrid')
    for c in list(grid):
        grid.remove(c)
    for w in widths:
        ET.SubElement(grid, W + 'gridCol').set(W + 'w', str(w))
    for r in rows:
        tbl.remove(r)
    n = len(matrix)
    for i, vals in enumerate(matrix):
        tpl = head_t if i == 0 else (last_t if i == n - 1 else mid_t)
        tr = copy.deepcopy(tpl)
        tcs = tr.findall(W + 'tc')
        while len(tcs) < len(widths):
            tr.append(copy.deepcopy(tcs[-1])); tcs = tr.findall(W + 'tc')
        while len(tcs) > len(widths):
            tr.remove(tcs[-1]); tcs = tr.findall(W + 'tc')
        for tc, v, w, a in zip(tr.findall(W + 'tc'), vals, widths, aligns):
            set_cell(tc, v, w, 'center' if i == 0 else a)
        tbl.append(tr)


tbls = [e for e in body if e.tag == W + 'tbl']
T2, T3 = tbls[1], tbls[2]

# ── 表 2：功能测试代表性用例（取自 ST-01~ST-20，覆盖五大模块）──────────
M2 = [
 ['编号', '测试功能', '预期结果', '实际结果'],
 ['ST-02', '登录时验证码填写错误', '提示“答案错误, 请重试”并阻止登录', '同预期'],
 ['ST-04', '登录后静置超过 3 h', '自动登出并跳转登录页', '同预期'],
 ['ST-05', '积分填报页保存草稿', '记录置为草稿态, 可再次进入编辑', '同预期'],
 ['ST-06', '将草稿提交审核', '记录置为待审核态, 进入审核队列', '同预期'],
 ['ST-08', '查看一条已审核记录', '显示审核人、审核时间与审核意见', '同预期'],
 ['ST-10', '导出积分排名 PDF', '排名正确, PDF 含单位水印且不重叠', '同预期'],
 ['ST-11', '查看个人能力画像', '雷达图与各维度得分正确渲染', '同预期'],
 ['ST-13', '审核员驳回并填写意见', '记录置为已驳回态, 意见被保存', '同预期'],
 ['ST-17', '维护积分项目与评分规则', '填报页选项与计分规则实时同步', '同预期'],
 ['ST-19', '审核员调用删除审核记录接口', '后端拒绝并返回 403', '返回 403'],
]
rebuild(T2, M2, [820, 2100, 3380, 2006],
        ['center', 'left', 'left', 'center'])

# ── 表 3：性能测试 7 组场景 ────────────────────────────────────────
M3 = [
 ['测试场景', '并发\n用户数', '平均响应\n/ms', '90% 响应\n/ms', '吞吐量\n/(次·s⁻¹)',
  '错误率\n/%', 'CPU 占用\n/%'],
 ['单用户基准', '1', '42', '60', '23', '0', '8'],
 ['低并发登录', '20', '85', '120', '186', '0', '24'],
 ['中并发混合业务', '50', '140', '220', '322', '0', '46'],
 ['高并发查询', '100', '255', '420', '386', '0.2', '78'],
 ['峰值并发', '200', '520', '850', '408', '1.5', '88'],
 ['排名 PDF 导出', '1', '1480', '2100', '0.68', '0', '12'],
 ['疲劳测试(30 min)', '50', '152', '240', '315', '0', '47'],
]
M3 = [[c.replace('\n', ' ') for c in row] for row in M3]
rebuild(T3, M3, [1700, 1000, 1100, 1100, 1300, 1000, 1106],
        ['left'] + ['center'] * 6)

# ── 表 3 后补表注与结果分析 ────────────────────────────────────────
cap = find(body, '表3  性能测试结果')
idx = list(body).index(T3)
tpl = find(body, '为评价标签准确性')
note = copy.deepcopy(tpl)
rewrite(note, '注: 导出场景的吞吐量单位为次·s⁻¹, 其余场景为请求·s⁻¹.')
ana = copy.deepcopy(tpl)
rewrite(ana,
        '由表3可见, 50 并发下平均响应 140 ms、错误率为 0; 并发升至 200 时平均响应 520 ms、'
        '错误率 1.5%、CPU 占用 88%, 系统达到容量上限. 按 270 人的机构规模估算, 活跃时段'
        '的并发量约为 27, 申报截止日约为 54, 200 并发已相当于日常峰值的 7 倍, 系统在该'
        '压力下仍能提供服务. 30 min 疲劳测试的平均响应 152 ms 与 50 并发基准场景基本持平, '
        '未观察到性能衰减.')
body.insert(idx + 1, ana)
body.insert(idx + 1, note)

save(tree, SRC, 'work.bak4/word/document.xml')
print('表 2、表 3 已按真实测试记录重建；表 3 后补表注与结果分析各一段。')
