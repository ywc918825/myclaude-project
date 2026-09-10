# -*- coding: utf-8 -*-
"""Z1 按《计算机技术与发展》投稿须知与模板调整版式。

对表结果（须知①②③ + 模板页）：
  缺 "0 引言" 一级标题                      —— 模板明确有这一节，补
  单位署名分成三段、且南通非省会未标省份        —— 模板要求合并成一个括号、逗号前带省份
  中文作者应四号仿宋，现四号宋体
  英文题名应四号(sz28)，现小四(sz24)；英文作者应小四(sz24)，现五号(sz21)
  二级标题应五号黑体，现五号宋体加粗
  5、6 节一级标题漏了加粗，与 1—4 节不一致
  图表题应小五号黑体，现小五号宋体
  表内文字应六号(sz15)，现小五(sz18)
  参考文献字号 sz18/sz21 混排

已符合、不动的：A4 页面、正文宋体五号(sz21)、一级标题四号宋体、三线表
（表头行确有下框线）、中文题名二号宋体、中文摘要 614 字（须知要求 350 字以上）、
关键词 7 个（要求 5～8）、参考文献 23 条含外文 7 条（要求 ≥15 含 ≥5 外文）。
"""
import copy, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, rewrite, save
from rlib import run_replace, para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
ORDER = lib.RPR_ORDER


def set_rpr(rpr, tag, attrs=None):
    for c in list(rpr):
        if c.tag == W + tag:
            rpr.remove(c)
    el = ET.Element(W + tag)
    for k, v in (attrs or {}).items():
        el.set(W + k, v)
    idx = ORDER.index(tag) if tag in ORDER else len(ORDER)
    pos = 0
    for c in list(rpr):
        t = c.tag.replace(W, '')
        if (ORDER.index(t) if t in ORDER else len(ORDER)) <= idx:
            pos += 1
        else:
            break
    rpr.insert(pos, el)


def style(p, ea=None, ascii_=None, sz=None, bold=None):
    """把整段所有 run 设成给定字体/字号/粗体。"""
    for r in p.findall(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is None:
            rpr = ET.Element(W + 'rPr')
            r.insert(0, rpr)
        if ea or ascii_:
            f = rpr.find(W + 'rFonts')
            a = dict(f.attrib) if f is not None else {}
            a = {k.replace(W, ''): v for k, v in a.items()}
            if ea:
                a['eastAsia'] = ea
            if ascii_:
                a['ascii'] = ascii_
                a['hAnsi'] = ascii_
            set_rpr(rpr, 'rFonts', a)
        if sz:
            set_rpr(rpr, 'sz', {'val': sz})
            set_rpr(rpr, 'szCs', {'val': sz})
        if bold is True:
            set_rpr(rpr, 'b', {})
        elif bold is False:
            for c in list(rpr):
                if c.tag == W + 'b':
                    rpr.remove(c)


# ── 1. 补 "0  引言" 一级标题 ─────────────────────────────────────
h1 = find(body, '1  系统总体架构')
intro = find(body, '在“科教兴卫')
p0 = copy.deepcopy(h1)
rewrite(p0, '0  引言')
body.insert(list(body).index(intro), p0)
print('补 0  引言 标题')

# ── 2. 一级标题：5、6 节补粗，与 1—4 节一致 ──────────────────────
for t in ('5  分配方法对比实验', '6  结论与展望'):
    style(find(body, t), bold=True)
print('5、6 节一级标题补粗体')

# ── 3. 二级标题：五号黑体 ────────────────────────────────────────
for t in ('3.1  可配置积分规则引擎', '3.2  多作者积分权重分配模型',
          '3.3  动态标签权重模型', '3.4  多维能力得分与画像渲染',
          '3.5  轻量级状态机工作流引擎', '3.6  性能优化与安全设计'):
    style(find(body, t), ea='黑体', ascii_='黑体', sz='21', bold=False)
print('二级标题 6 个改五号黑体')

# ── 4. 单位署名合并为模板格式，并补省份 ─────────────────────────
UNIT = '南通市疾病预防控制中心'
p2 = find(body, '1（南通市疾病预防控制中心科研与质量管理科')
p3 = find(body, '2（南通市疾病预防控制中心主任室')
p4 = find(body, '3（南通市疾病预防控制中心信息管理科')
rewrite(p2, '（1. %s 科研与质量管理科，江苏 南通 226001；'
            '2. %s 主任室，江苏 南通 226001；'
            '3. %s 信息管理科，江苏 南通 226001）' % (UNIT, UNIT, UNIT))
body.remove(p3)
body.remove(p4)
print('三条单位署名合并为一段，补省份「江苏」')

# ── 5. 英文单位同步为 1. 2. 3. 体例并补 Jiangsu ─────────────────
EN = 'Nantong Center for Disease Control and Prevention, Nantong 226001, Jiangsu, China'
pe = find(body, 'Division of Research and Quality Management')
rewrite(pe, '(1. Division of Research and Quality Management, %s; '
            '2. Director’s Office, %s; '
            '3. Division of Information Management, %s)' % (EN, EN, EN))
print('英文单位同步体例并补 Jiangsu')

# ── 6. 题名、作者字号字体 ────────────────────────────────────────
style(find(body, '杨文超'), ea='仿宋', sz='28')                 # 中文作者 四号仿宋
style(find(body, 'A Dynamic-Points'), ascii_='Times New Roman', sz='28')   # 英文题名 四号
style(find(body, 'YANG Wen-chao'), ascii_='Times New Roman', sz='24')      # 英文作者 小四
print('中文作者→四号仿宋；英文题名→四号；英文作者→小四')

# ── 7. 表内文字六号 ─────────────────────────────────────────────
n = 0
for tb in [c for c in body if c.tag == W + 'tbl']:
    for tc in tb.iter(W + 'tc'):
        for p in tc.findall(W + 'p'):
            style(p, sz='15')
            n += 1
print('表内 %d 个单元格段落改六号(sz15)' % n)

# ── 8. 参考文献字号统一小五 ─────────────────────────────────────
ps = [p for p in body if p.tag == W + 'p']
i = next(i for i, p in enumerate(ps) if para_text(p).strip() == '参考文献')
for p in ps[i + 1:]:
    if para_text(p).strip().startswith('['):
        style(p, sz='18')
print('参考文献字号统一为小五(sz18)')

save(tree, SRC, 'ref.xml')
print('Z1 done')
