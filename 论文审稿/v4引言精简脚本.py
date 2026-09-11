# -*- coding: utf-8 -*-
"""精简引言（595 → 约 355 字），并顺带统一内存写法。"""
import copy, re, xml.etree.ElementTree as ET

SRC = 'work/word/document.xml'
raw = open(SRC, encoding='utf-8').read()
for pfx, uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw)).items():
    if not re.fullmatch(r'ns\d*', pfx):
        ET.register_namespace(pfx, uri)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS = '{http://www.w3.org/XML/1998/namespace}space'

tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []


def text_of(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def set_single_text(p, s):
    runs = p.findall(W + 'r')
    keep = next((r for r in runs if r.find(W + 't') is not None), None)
    if keep is None:
        return False
    rpr = keep.find(W + 'rPr')
    for r in runs:
        p.remove(r)
    nr = ET.SubElement(p, W + 'r')
    if rpr is not None:
        nr.append(copy.deepcopy(rpr))
    t = ET.SubElement(nr, W + 't')
    t.set(XS, 'preserve')
    t.text = s
    return True


# ── 精简后的引言：两段 ────────────────────────────────────────────────────
NEW = [
    '在“科教兴卫、人才强卫”战略指引下，各级疾病预防控制机构日益重视科研能力建设，'
    '但基层疾控机构的科研人才评价仍存在方式粗放、“四唯”倾向明显、缺少动态量化手段等'
    '问题[1-2]，难以支撑科研梯队建设与精准激励。',

    '李涛等[1]、沈杨阳[2]与 Amaral 等[3]分别从指标体系、组织机制与经费分配角度探讨了'
    '科研评价，但评价对象均为机构而非个人；Lei[4]面向“破五唯”设计的分类绩效指标体系与'
    '本文思路接近，但其指标构成与疾控机构以公共卫生服务、现场流行病学调查为主的产出结构'
    '差异较大；罗仕鉴等[9]与白菁昊等[10]验证了动态标签刻画能力演进的有效性，但未考虑'
    '科研成果的长周期性与时效衰减特征。可见，面向公共卫生领域、同时整合积分量化与人才'
    '标签画像的专用系统仍比较少见。为此，本文提出面向多作者成果的分段权重积分分配模型，'
    '构建“指数加权移动平均标签权重 + 指数时间衰减”的动态画像模型，并实现无第三方框架'
    '依赖的状态机工作流与可配置积分规则引擎。系统面向的南通市疾控中心设有 15 个业务科室、'
    '270 名科研人员，科研成果涵盖 12 个大类，核心业务响应时间要求控制在 3 s 以内。',
]

# 定位现有引言的三段（从"科教兴卫"那段起，到"2  系统总体架构"之前）
kids = list(body)
start = next(i for i, p in enumerate(kids)
             if p.tag == W + 'p' and '科教兴卫' in text_of(p))
end = next(i for i, p in enumerate(kids)
           if p.tag == W + 'p' and text_of(p).strip().startswith('2') and '系统总体架构' in text_of(p))
old_paras = [p for p in kids[start:end] if p.tag == W + 'p']
old_len = sum(len(re.findall(r'[一-鿿]', text_of(p))) for p in old_paras)

template = old_paras[0]
set_single_text(template, NEW[0])
for p in old_paras[1:]:
    body.remove(p)
np = copy.deepcopy(template)
set_single_text(np, NEW[1])
body.insert(list(body).index(template) + 1, np)

new_len = sum(len(re.findall(r'[一-鿿]', s)) for s in NEW)
log.append(f'引言：{len(old_paras)} 段 {old_len} 字 → 2 段 {new_len} 字（减 {old_len - new_len} 字）')

# ── 内存写法统一：32G内存 → 32 GB 内存 ───────────────────────────────────
for p in body.iter(W + 'p'):
    if '测试环境为' not in text_of(p):
        continue
    ts = list(p.iter(W + 't'))
    for t in ts:
        if t.text and re.search(r'\dG(?=内|$)', t.text):
            t.text = re.sub(r'(\d)G', r'\1 GB ', t.text)
            t.set(XS, 'preserve')
            log.append('测试环境：32G内存 → 32 GB 内存')
    break

tree.write(SRC, encoding='UTF-8', xml_declaration=True)

# 还原根标签的命名空间声明
orig_root = re.search(r'<w:document\b[^>]*>',
                      open('unz/word/document.xml', encoding='utf-8').read()).group(0)
s = open(SRC, encoding='utf-8').read()
cur = re.search(r'<w:document\b[^>]*>', s).group(0)
have = set(re.findall(r'xmlns:(\w+)=', orig_root))
add = [f'xmlns:{k}="{v}"' for k, v in re.findall(r'xmlns:(\w+)="([^"]+)"', cur)
       if k not in have]
merged = orig_root[:-1] + (' ' + ' '.join(add) if add else '') + '>'
open(SRC, 'w', encoding='utf-8').write(s.replace(cur, merged, 1))

print('已完成：')
for l in log:
    print('  ·', l)
