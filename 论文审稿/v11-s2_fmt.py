# -*- coding: utf-8 -*-
"""第二步：按《计算机系统应用》模板重排篇首、参考文献与文末。"""
import copy, re, xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
K = lambda: list(body)
log = []


def para_like(model, markup):
    p = copy.deepcopy(model)
    rewrite(p, markup)
    return p


# ══════════════ 篇首 ══════════════
kids = K()
title = kids[0]
rewrite(title, '基于动态积分与标签画像的疾控科研人才评价系统{sup|①}')
body.remove(kids[1])                                   # 题名后的空段
log.append('题名：补回“科研”二字（正文/摘要通篇讲的是科研人才评价），'
           '并加基金项目脚注标记 ①')

rewrite(find(body, '杨文超，张卫兵'), '杨文超, 张卫兵, 练维, 徐小卫, 王秦')
rewrite(find(body, '南通市疾病预防控制中心 科研与质量管理科'),
        '(南通市疾病预防控制中心 科研与质量管理科, 南通 226001)')
log.append('中文署名与单位改为模板式样：半角逗号 + 空格，单位不写省份、只留城市与邮编')

# 第一作者/通信作者两段 → 模板的单行“通讯作者”
p_first = find(body, '第一作者')
p_corr = find(body, '通信作者')
rewrite(p_first, '通讯作者: 张卫兵, E-mail: yangwecy@gmail.com')
body.remove(p_corr)
log.append('“第一作者/通信作者”两段简介合并为模板要求的单行“通讯作者: 姓名, E-mail”，'
           '详细简介移到文末')

rewrite(find(body, 'YANG Wenchao'),
        'YANG Wen-Chao, ZHANG Wei-Bing, LIAN Wei, XU Xiao-Wei, WANG Qin')
rewrite(find(body, 'Division of Research'),
        '(Division of Research and Quality Management, Nantong Center for Disease '
        'Control and Prevention, Nantong 226001, China)')
log.append('英文作者名改为模板的 XXX Xxx-Xxx 式；英文单位去掉省份')

rewrite(find(body, 'A CDC Talent Evaluation'),
        'A CDC Research Talent Evaluation System Based on Dynamic Points and '
        'Tag Profiling')

# 摘要：去掉“目的/方法/结果/结论”结构，改为模板的连续式
rewrite(find(body, '摘要：'),
        '{b|摘　要}: 针对疾控机构科研人才评价方式粗放、缺少动态量化手段、难以支撑科研'
        '梯队建设与精准激励的问题, 设计并实现了基于 Spring Boot 与 MyBatis 的疾控科研'
        '人才评价系统. 提出面向多作者成果的分段权重积分分配模型; 构建以一阶指数加权移动'
        '平均({i|α} = 0.7)为核心的动态标签权重模型, 并将半衰期 4.95 年({i|λ} = 0.14)的'
        '指数时间衰减前置嵌入行为积分归一化环节, 使标签权重、能力维度得分与人才画像构成'
        '量纲一致的计算链路; 基于有限状态机实现无第三方依赖的三级审批工作流引擎. 系统在'
        '南通市疾病预防控制中心运行 3 个月, 覆盖 15 个业务科室、270 名科研人员, 审核周期'
        '由 7 d 缩短至 2 d, 积分核算差错率由 3.54% 降至 0.08%, 动态能力标签准确率 '
        '88.0%、召回率 84.1%、F1 值 0.86, 500 并发下缓存命中率保持在 92.5% 以上. '
        '该系统可提升疾控机构科研人才评价的精细度与审核效率, 为同类公共卫生机构的人才'
        '评价信息化建设提供参考.')

rewrite(find(body, '关键词：'),
        '{b|关键词}: 积分量化评价; 标签权重模型; 时间衰减算法; 工作流引擎; 人才画像')

rewrite(find(body, 'Abstract:'),
        '{b|Abstract}: To address the problems that research talent evaluation in '
        'centers for disease control and prevention (CDC) remains coarse-grained, '
        'lacks dynamic quantitative means, and can hardly support research echelon '
        'building and targeted incentives, a CDC research talent evaluation system '
        'based on Spring Boot and MyBatis is designed and implemented. A piecewise '
        'weighting model is proposed for multi-author outputs. A dynamic tag weight '
        'model is built on the first-order exponentially weighted moving average '
        '({i|α} = 0.7), with an exponential time decay of a 4.95-year half-life '
        '({i|λ} = 0.14) embedded ahead of behaviour-score normalization, so that tag '
        'weights, capability dimension scores and the talent profile form one '
        'dimensionally consistent computation chain. A three-level approval workflow '
        'engine without third-party dependency is implemented as a finite state '
        'machine. After three months of operation at Nantong CDC, covering 15 '
        'departments and 270 researchers, the approval cycle is shortened from 7 days '
        'to 2 days, the points-accounting error rate drops from 3.54% to 0.08%, the '
        'dynamic capability tagging reaches 88.0% precision, 84.1% recall and 0.86 F1, '
        'and the cache hit ratio stays above 92.5% under 500 concurrent users. The '
        'system improves the granularity of research talent evaluation and the '
        'efficiency of approval in CDC institutions, and provides a reference for the '
        'informatization of talent evaluation in comparable public health '
        'organizations.')

rewrite(find(body, 'Key words:'),
        '{b|Key words}: points-based evaluation; tag weight model; time decay '
        'algorithm; workflow engine; talent profile')
log.append('中英文摘要去掉“目的/方法/结果/结论”分段（模板为连续式），两版内容逐项对齐；'
           '英文关键词删去多出的 architecture，与中文 5 个一一对应；'
           '英文摘要里的 alpha/lambda 改回 α/λ')

# 中图分类号 → 引用格式（模板篇首没有分类号，改放引用格式行）
rewrite(find(body, '中图分类号'),
        '{b|引用格式}: 杨文超,张卫兵,练维,徐小卫,王秦.基于动态积分与标签画像的疾控科研'
        '人才评价系统.计算机系统应用,xxxx,xx(x):x−x. '
        'http://www.c-s-a.org.cn/1003-3254/xxxx.html')
log.append('删去“中图分类号/文献标志码”（模板篇首无此项），替换为模板要求的“引用格式”行')

# 引言标题：模板中引言不设标题，正文接 Key words 之后
body.remove(find(body, '0  引  言'))
log.append('删去“0  引  言”标题——模板中引言不单独设标题，正文承接 Key words，'
           '章节号仍从 1 开始，无需改动')

# ══════════════ 参考文献 ══════════════
rewrite(find(body, '参考文献'), '{b|参考文献}')


def fix_name(nm):
    nm = nm.strip()
    if nm.lower().startswith('et al'):
        return nm
    parts = nm.split()
    sur = [p for p in parts if len(p) > 1]
    ini = [p for p in parts if len(p) == 1]
    s = ' '.join(w[0] + w[1:].lower() for w in sur)
    return (s + ' ' + ''.join(ini)).strip()


nref = 0
for p in K():
    if p.tag != W + 'p':
        continue
    s = text_of(p).strip()
    m = re.match(r'^\[(\d+)\]\s*(.*)$', s, re.S)
    if not m:
        continue
    num, rest = m.group(1), m.group(2)
    rest = rest.replace('[J]. ', '. ').replace('[J].', '.')
    rest = re.sub(r'\[C\]//\s*', '. Proc. of the ', rest)
    rest = rest.replace('[M]. ', '. ').replace('[D]. ', '. ')
    rest = re.sub(r'(:\s*\d+)-(\d+)', r'\1–\2', rest)
    if re.match(r'^[A-Z]', rest):                       # 西文文献
        head, sep, tail = rest.partition('. ')
        rest = ', '.join(fix_name(x) for x in head.split(', ')) + sep + tail
        rest = rest.replace('“', '"').replace('”', '"')
    rest = re.sub(r'\.\s*IEEE,\s*(\d{4}):\s*', '. IEEE, \\1. ', rest)
    rewrite(p, '%s %s' % (num, rest))
    nref += 1
log.append('参考文献 %d 条改为该刊式样：序号去方括号、删去 [J]/[C] 类型标识、'
           '页码连接号改 en dash、西文作者姓名由全大写改为“Surname Initials”' % nref)

# ══════════════ 文末：基金项目与收稿时间 ══════════════
bio = find(body, '作者简介')
pos = list(body).index(bio)
for s in ['{b|①} 基金项目: 南通市社科研究课题(网信专项)(WA25-6)',
          '收稿时间: {hl|xxxx-xx-xx}; 收到修改稿时间: {hl|xxxx-xx-xx}']:
    body.insert(pos, para_like(bio, s))
    pos += 1
log.append('文末补模板要求的脚注内容：“① 基金项目: …”与“收稿时间/收到修改稿时间”'
           '（日期留黄色高亮待填）')

save(tree, SRC, 'work.bak/word/document.xml')
print('已完成：')
for l in log:
    print('  ·', l)
