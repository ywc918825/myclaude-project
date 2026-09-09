# -*- coding: utf-8 -*-
"""S1 元数据层：标题压缩、结构化摘要、关键词、中图分类号、英文块补全、删除他刊引用格式行。"""
import re, sys, copy, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
ps = [p for p in body if p.tag == W + 'p']

def P(i):
    return ps[i]

# ── 1. 标题 22 字 → 19 字 ────────────────────────────────────────────
rewrite(P(0), '疾控科研人才动态积分与标签画像评价系统{sup|①}')

# ── 2. 中文摘要：重组为“目的—方法—结果—结论”四要素 ──────────────
ABS = ('摘　要：针对基层疾控机构科研人才评价长期依赖人工台账与年终汇总、'
       '难以刻画个体能力动态演进的问题，设计并实现疾控科研人才评价系统。'
       '首先，提出面向多作者成果的分段权重积分分配模型，以 Kronecker δ 函数统一刻画'
       '作者序位与分配系数的映射关系，并采用名义分值制以契合疾控机构多科室协作攻关的导向；'
       '其次，构建以一阶指数加权移动平均（α = 0.7）为核心的动态标签权重模型，'
       '将半衰期 4.95 年（λ = 0.14）的指数时间衰减前置嵌入行为积分归一化环节，'
       '使标签权重、能力维度得分与人才画像构成量纲一致的计算链路；'
       '最后，以有限状态机实现无第三方框架依赖的三级审批工作流引擎，'
       '审核环节由配置表驱动，修改配置即可调整而无需重新发布。'
       '系统基于 Spring Boot 与 MyBatis 开发，前端采用 Vue.js，'
       '数据层为 MySQL 8.0 并引入 Redis 缓存。'
       '系统在南通市疾病预防控制中心运行 3 个月，覆盖 15 个业务科室、270 名科研人员，'
       '260 个功能测试用例全部通过；平均审核周期由 7 d 缩短至 2 d，'
       '积分核算差错率由 3.54% 降至 0.08%；动态能力标签相对专家标注的准确率为 88.0%、'
       '召回率为 84.1%、F1 值为 0.86；500 并发下平均响应时间为 452 ms、'
       '缓存命中率保持在 92.5% 以上。结果表明，该系统可提升疾控机构科研人才评价的'
       '精细度与审核效率，为同类公共卫生机构的人才评价信息化建设提供了可复用的'
       '模型与实现路径。')
rewrite(P(7), ABS)

# ── 3. 关键词 5 → 7 ─────────────────────────────────────────────────
rewrite(P(8), '关键词：积分量化评价；标签权重模型；时间衰减算法；工作流引擎；'
              '人才画像；科研管理信息系统；疾病预防控制中心')

# ── 4. 中图分类号 / 文献标识码（占用原“引用格式”段，避免增删段落打乱索引）──
rewrite(P(9), '中图分类号：TP311.5　　文献标识码：A')

# ── 5. 英文题名与作者、单位 ─────────────────────────────────────────
rewrite(P(10), 'A Dynamic-Points and Tag-Profiling Evaluation System '
               'for CDC Research Talent')
rewrite(P(11), 'YANG Wen-chao{sup|1}, ZHANG Wei-bing{sup|2}, LIAN Wei{sup|1}, '
               'XU Xiao-wei{sup|3}, WANG Qin{sup|1}')
rewrite(P(12),
        '({sup|1}Division of Research and Quality Management, Nantong Center for '
        'Disease Control and Prevention, Nantong 226001, China; '
        '{sup|2}Director’s Office, Nantong Center for Disease Control and '
        'Prevention, Nantong 226001, China; '
        '{sup|3}Division of Information Management, Nantong Center for Disease '
        'Control and Prevention, Nantong 226001, China)')

# ── 6. 英文摘要与中文摘要对齐（四要素同序） ─────────────────────────
EN = ('Abstract: Research talent evaluation in grassroots centers for disease control '
      'and prevention (CDC) has long relied on manual ledgers and year-end summaries, '
      'which can hardly capture how individual capability evolves. A CDC research talent '
      'evaluation system is therefore designed and implemented. First, a piecewise '
      'weighting model based on the Kronecker delta function is proposed for multi-author '
      'outputs, adopting a nominal-credit scheme that matches the cross-department '
      'collaboration orientation of CDC institutions. Second, a dynamic tag weight model '
      'is built on the first-order exponentially weighted moving average (alpha = 0.7), '
      'with an exponential time decay of a 4.95-year half-life (lambda = 0.14) embedded '
      'ahead of behaviour-score normalization, so that tag weights, capability dimension '
      'scores and the talent profile form one dimensionally consistent computation chain. '
      'Third, a three-level approval workflow engine without third-party dependency is '
      'implemented as a finite state machine, whose stages are driven by a configuration '
      'table and can be adjusted without redeployment. The system is developed with Spring '
      'Boot and MyBatis, with a Vue.js front end, MySQL 8.0 and a Redis cache. After three '
      'months of operation at Nantong CDC, covering 15 departments and 270 researchers, '
      'all 260 functional test cases pass; the approval cycle is shortened from 7 d to 2 d, '
      'the points-accounting error rate drops from 3.54% to 0.08%, the dynamic capability '
      'tagging reaches 88.0% precision, 84.1% recall and 0.86 F1 against expert annotation, '
      'and under 500 concurrent users the average response time is 452 ms with a cache hit '
      'ratio above 92.5%. The results show that the system improves the granularity and '
      'approval efficiency of research talent evaluation in CDC institutions and provides a '
      'reusable model and implementation path for comparable public health organizations.')
rewrite(P(13), EN)
rewrite(P(14), 'Key words: points-based evaluation; tag weight model; time decay '
               'algorithm; workflow engine; talent profile; research management '
               'information system; center for disease control and prevention')

save(tree, SRC, 'ref.xml')
print('S1 done')
