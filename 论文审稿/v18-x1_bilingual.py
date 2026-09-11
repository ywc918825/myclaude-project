# -*- coding: utf-8 -*-
"""X1 中文参考文献补英文对照（须知：「中文文献和学位论文需中英文对照」）。

23 条里 16 条中文，逐条在其下方加一行英文，格式与该刊同类刊物一致：
    [1] 李涛, 关健, 吴沛新. 中文题名[J]. 中文刊名, 2023, 36(4): 259-265.
        LI Tao, GUAN Jian, WU Pei-xin. English title[J]. English Journal, 2023, 36(4): 259-265.
英文行不重复序号，卷期页与中文行逐字相同。

**期刊英文名逐一核过**（来源见审稿意见文档），不是我按字面译的：
    中国科技资源导刊 = China Science & Technology Resources Review
    知识管理论坛     = Knowledge Management Forum
    大众科技         = Popular Science & Technology
    电脑与信息技术   = Computer and Information Technology
    现代信息科技     = Modern Information Technology
    信息系统工程     = Information Systems Engineering
    计算机技术与发展 = Computer Technology and Development（本刊）

**题名是我译的，不是从原文抄的**——知网在本环境访问不到。原文若自带
英文题名，以原文为准；替换时只动题名，作者名与刊名不用动。
"""
import copy, re, sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, save
from rlib import para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
ORDER = lib.RPR_ORDER

EN = {
 1: 'LI Tao, GUAN Jian, WU Pei-xin. Reflections and suggestions on the science and '
    'technology evaluation system in the field of health policy and management '
    'research[J]. Chinese Journal of Medical Science Research Management, 2023, '
    '36(4): 259-265.',
 2: 'HUANG Zhao, YUAN Yuan, TAO Zhen-huan, et al. Design and application of a '
    'digital system for disease control and prevention[J]. China Digital Medicine, '
    '2025, 20(11): 8-13.',
 3: 'LI Shao-qiong, DU Xue-jie, JIN Li-zhu, et al. Construction of evaluation '
    'indicators for the informatization of provincial centers for disease control '
    'and prevention in China based on the Delphi method[J]. China Digital Medicine, '
    '2024, 19(10): 111-114.',
 4: 'YANG Si-luo, ZHOU Zhan-yi, DING Min. Evaluation of university research outputs '
    'under the “breaking the five onlys” orientation: institutional representation '
    'and reform paths[J]. Knowledge Management Forum, 2025, 10(3): 218-231.',
 6: 'SHEN Yang-yang. Practical paths for national research management institutions '
    'to organize disruptive technological innovation[J]. Forum on Science and '
    'Technology in China, 2026(5): 1-11.',
 8: 'LUO Shi-jian, GUO He-rui, ZHONG Su-ping, et al. Agent-driven user profile '
    'generation method for product design[J]. Computer Integrated Manufacturing '
    'Systems, 2025, 31(11): 3919-3931.',
 9: 'BAI Jing-hao, ZHUANG Jun-xi, LAI Ying-xu. Construction and prediction of '
    'temporal dynamic tags for learner profiling[J]. Computer Science, 2026, '
    '53(5): 79-89.',
 10: 'HU Xiao-ying, XUN Ya-ling, LI Yan-feng. Debiased recommendation based on item '
     'popularity and user dynamic interest[J]. Computer Technology and Development, '
     '2024, 34(8): 135-142.',
 12: 'LIU Sheng, WANG Zhan-yun. Design and implementation of a research sample '
     'repository management system based on the SpringBoot+Vue microservice '
     'architecture[J]. Information Systems Engineering, 2025(4): 4-7.',
 13: 'ZHANG Yan. Design of a public health service platform based on Spring Boot[J]. '
     'Modern Information Technology, 2026, 10(1): 105-110, 116.',
 14: 'LIAO Feng-lu, XU Yi, TANG Wei. Design and implementation of a large-screen data '
     'visualization system for libraries[J]. Computer and Information Technology, '
     '2025(3): 79-83, 97.',
 15: 'LAI Tian-ping, WANG Yong-chao, LUO Pan, et al. Design and application of an '
     'access control model based on role-resource levels[J]. Journal on '
     'Communications, 2024, 45(S2): 153-159.',
 17: 'HAN Ying-xiao, ZHANG Jun-sheng, ZHENG Ming, et al. A credit allocation method '
     'covering all authors of a paper: a quantitative anchor for mitigating '
     'authorship disputes[J]. China Science & Technology Resources Review, '
     '2025(6): 48-63.',
 19: 'MENG Li-dong, LIN Nai-bin, WEI Wen-qin, et al. Design and implementation of a '
     'lightweight workflow engine based on JSON[J]. Popular Science & Technology, '
     '2025, 27(2): 20-24.',
 20: 'GUO Sheng-wei, ZHANG Yang. Design and application of a lightweight workflow '
     'system[J]. Computer Knowledge and Technology, 2025(36): 48-51, 55.',
 22: 'LÜ Yu-gui. Authentication and authorization in a microservice architecture '
     'implemented with Spring Security and JWT[J]. Computer Knowledge and '
     'Technology, 2024(22): 60-63.',
}


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


refs = {}
for p in body:
    if p.tag != W + 'p':
        continue
    m = re.match(r'\s*\[(\d+)\]', para_text(p))
    if m:
        refs[int(m.group(1))] = p
assert set(EN) <= set(refs), sorted(set(EN) - set(refs))

# 卷期页必须与中文行逐字相同——写错一个数就是错引
TAIL = re.compile(r'(\d{4}(?:,\s*\d+)?\s*\((?:S?\d+)\)\s*:\s*[\d,\s-]+|\d{4}\(\d+\)\s*:\s*[\d,\s-]+)')
bad = []
for n, en in EN.items():
    cn = para_text(refs[n])
    a = TAIL.findall(cn.replace('，', ','))
    b = TAIL.findall(en)
    if not a or not b or a[-1].replace(' ', '') != b[-1].replace(' ', ''):
        bad.append((n, a[-1] if a else '?', b[-1] if b else '?'))
if bad:
    for n, x, y in bad:
        print('  !! [%d] 中文「%s」 英文「%s」' % (n, x, y))
    raise SystemExit('卷期页对不上，停下检查')
print('卷期页逐条核对：%d 条全部与中文行一致' % len(EN))

for n in sorted(EN, reverse=True):
    cn = refs[n]
    p = copy.deepcopy(cn)
    rewrite(p, EN[n])
    for r in p.findall(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is None:
            rpr = ET.Element(W + 'rPr')
            r.insert(0, rpr)
        set_rpr(rpr, 'rFonts', {'ascii': 'Times New Roman',
                                'hAnsi': 'Times New Roman', 'eastAsia': '宋体'})
        set_rpr(rpr, 'sz', {'val': '18'})
        set_rpr(rpr, 'szCs', {'val': '18'})
    body.insert(list(body).index(cn) + 1, p)

print('16 条中文文献各补一行英文对照')
save(tree, SRC, 'ref.xml')
print('X1 done')
