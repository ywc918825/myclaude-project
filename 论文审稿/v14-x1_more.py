# -*- coding: utf-8 -*-
"""X1 第二轮精简：摘要收到本刊常规长度，正文去掉"把表读一遍"和重复表述。

上一轮我把"压缩英文摘要"划为高风险，理由是中英文摘要不对应。那个理由只针对
单压英文——中英一起等比例压缩就不存在这个问题，而本稿中文摘要 756 字，
比该刊常规长度长出近一倍，压到 520 字是往规范靠，不是往外走。

四处正文改动都是"同一件事说了两遍"：
  P016  "机构层面"说了三遍，末句的小结重复前两句
  P016  三个问题先列一遍、再"针对这三个问题"列一遍
  P074  126/+9.8/58%/131/−9.5 五个数把上方表格整个读了一遍
  P078  "两个参数……有待敏感性分析"与末句"后续将……开展参数敏感性分析"同义
  P051  8 种状态列完，紧接着又把同一条路径走了一遍
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, save
from rlib import run_replace, para_text

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')


def wid(s):
    return sum(1 if (0x4E00 <= ord(c) <= 0x9FFF or 0x3000 <= ord(c) <= 0x303F
                     or 0xFF00 <= ord(c) <= 0xFF60) else 0.5 for c in s)


saved = 0.0


def cut(anchor, old, new, label):
    global saved
    p = find(body, anchor)
    run_replace(p, old, new)
    d = wid(old) - wid(new)
    saved += d
    print('  %-16s −%4.0f 当量   （%d → %d 字符）' % (label, d, len(old), len(new)))


# ── 中文摘要：删 260 用例、准确率/召回率、并发与命中率、Top-30 与 9.8 名次 ──
cut('摘　要：',
    '系统基于 Spring Boot 与 MyBatis 开发，前端采用 Vue.js，数据层为 MySQL 8.0 '
    '并引入 Redis 缓存。系统在南通市疾病预防控制中心运行 3 个月，覆盖 270 名科研人员，'
    '260 个功能测试用例全部通过；以本中心 2024—2025 年公开发表的 183 篇论文为样本的'
    '对比实验表明，本文分配方法与均分法的人才排名 Spearman 秩相关为 0.864、'
    'Top-30 重合 21/30，合作规模高于中位数的人员平均上升 9.8 个名次，'
    '与名义分值制鼓励协作的设计意图一致；平均审核周期由 7 d 缩短至 2 d，'
    '积分核算差错率由 3.54% 降至 0.08%；动态能力标签相对专家标注的准确率为 88.0%、'
    '召回率为 84.1%、F1 值为 0.86；500 并发下平均响应时间为 452 ms、'
    '缓存命中率保持在 92.5% 以上。结果表明，该系统可提升疾控机构科研人才评价的'
    '精细度与审核效率，为同类公共卫生机构的人才评价信息化建设提供了可复用的模型与实现路径。',
    '系统基于 Spring Boot、Vue.js 与 MySQL 8.0 实现，在南通市疾病预防控制中心'
    '运行 3 个月，覆盖 270 名科研人员：平均审核周期由 7 d 缩短至 2 d，'
    '积分核算差错率由 3.54% 降至 0.08%，动态能力标签相对专家标注的 F1 值为 0.86。'
    '以本中心 2024—2025 年公开发表的 183 篇论文为样本的对比实验表明，'
    '本文分配方法与均分法的人才排名 Spearman 秩相关为 0.864，'
    '合作规模高于中位数的人员名次系统性上升，与名义分值制鼓励协作的设计意图一致。'
    '结果表明，该系统可提升疾控机构科研人才评价的精细度与审核效率，'
    '为同类公共卫生机构提供可复用的模型与实现路径。',
    '中文摘要')

# ── 英文摘要：与中文同步删同样几项 ──────────────────────────────
cut('Abstract: Research talent evaluation',
    'The system is developed with Spring Boot and MyBatis, with a Vue.js front '
    'end, MySQL 8.0 and a Redis cache. After three months of operation at Nantong '
    'CDC, covering 270 researchers, all 260 functional test cases pass. '
    'A comparative experiment on 183 papers published by the centre in 2024-2025, '
    'retrieved from CNKI, shows a Spearman rank correlation of 0.864 between the '
    'proposed allocation method and equal sharing, a Top-30 overlap of 21/30, and '
    'an average rise of 9.8 places for researchers whose mean team size is above '
    'the median, which matches the collaboration-oriented intent of the '
    'nominal-credit scheme. The approval cycle is shortened from 7 d to 2 d, the '
    'points-accounting error rate drops from 3.54% to 0.08%, the dynamic '
    'capability tagging reaches 88.0% precision, 84.1% recall and 0.86 F1 against '
    'expert annotation, and under 500 concurrent users the average response time '
    'is 452 ms with a cache hit ratio above 92.5%.',
    'Implemented with Spring Boot, Vue.js and MySQL 8.0, the system has run for '
    'three months at Nantong CDC covering 270 researchers: the approval cycle is '
    'shortened from 7 d to 2 d, the points-accounting error rate drops from 3.54% '
    'to 0.08%, and the dynamic capability tagging reaches an F1 of 0.86 against '
    'expert annotation. A comparative experiment on 183 papers published by the '
    'centre in 2024-2025, retrieved from CNKI, shows a Spearman rank correlation '
    'of 0.864 between the proposed allocation method and equal sharing, with '
    'researchers of above-median team size rising systematically in rank, which '
    'matches the collaboration-oriented intent of the nominal-credit scheme.',
    '英文摘要')

# ── 引言：三处重复 ───────────────────────────────────────────────
A = '现有研究多从指标体系视角探讨科研评价'
cut(A, '两类研究尚缺乏贯通：评价指标研究停留在机构层面，动态标签研究面向的是消费与学习行为。',
    '两类研究尚缺乏贯通。', '引言·小结重复')
cut(A, '，是须先解决的三个具体问题。针对这三个问题，本文做了三方面工作。',
    '，是须先解决的三个问题，本文对应做了三方面工作。', '引言·问题重列')
cut(A, '使标签权重、能力维度得分与人才画像共用一条量纲一致的计算通路。三是',
    '使上述通路在量纲上保持一致。三是', '引言·通路重述')

# ── 3.5 节：状态列完又走一遍 ─────────────────────────────────────
cut('针对疾控中心审核流程相对固定',
    '：草稿经提交进入待初审，初审、复核通过后依次进入待复核、待终审，'
    '任一环节驳回则回退至对应驳回态。',
    '：草稿提交后依次经初审、复核进入待终审，任一环节驳回则回退至对应驳回态。',
    '3.5·路径重走')

# ── 5 节结果：把表7 整个读了一遍 ─────────────────────────────────
cut('与均分法的秩相关为 0.864',
    '合作规模高于中位数的 126 人平均上升 9.8 个名次、58% 的人名次上升，'
    '合作规模不高于中位数的 131 人平均下降 9.5 个名次，',
    '合作规模高于中位数与不高于中位数的两组，平均名次分别上升 9.8 与下降 9.5，',
    '5 节·读表')

# ── 结论：与摘要同步 + 删与末句同义的一句 ────────────────────────
B = '把时间衰减放在行为积分层'
cut(B, '该方法与均分法的排名秩相关为 0.864、Top-30 重合 21/30，'
       '合作规模高于中位数的人员平均上升 9.8 个名次，排名变化的方向与设计意图一致。',
    '该方法与均分法的排名秩相关为 0.864，合作规模高于中位数的人员名次系统性上升，'
    '方向与设计意图一致。', '结论·与摘要同步')
cut(B, '本文工作也有局限。式(4)(5) 合成的年度保持率约为 0.26，',
    '本文工作也有局限：式(4)(5) 合成的年度保持率约为 0.26，', '结论·标点')
cut(B, '宜与同行评议互补使用；两个参数的取值对排名影响多大，仍有待更大样本的敏感性分析。'
       '标签—能力维度映射矩阵由本中心专家标定，跨机构推广时需要重新标定。'
       '式(4) 采用极值归一化，对周期内出现的异常高分较为敏感。',
    '宜与同行评议互补使用；标签—能力维度映射矩阵由本中心专家标定，跨机构推广需重新标定；'
    '式(4) 采用极值归一化，对异常高分较敏感。', '结论·同义重复')

print('\n合计省 %.0f 当量 = %.3f 版（每版 2400）' % (saved, saved / 2400))
save(tree, SRC, 'ref.xml')
print('X1 done')
