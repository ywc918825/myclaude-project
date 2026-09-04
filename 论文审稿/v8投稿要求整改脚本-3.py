# -*- coding: utf-8 -*-
"""第三轮：摘要收口（英文摘要压到约 95 词，中文摘要略收）。"""
import re, xml.etree.ElementTree as ET
from lib import W, TOK, register, rewrite, find, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

R = [
    ('摘要：',
     '{b|摘要：}针对疾控机构科研人才评价精细化不足的问题，设计并实现了基于 Spring Boot '
     '与 MyBatis 的科研积分管理系统。提出面向多作者成果的分段权重积分分配模型；构建'
     '基于一阶指数加权移动平均（{i|α} = 0.7）的动态标签权重模型，将半衰期 4.95 年'
     '（{i|λ} = 0.14）的指数时间衰减前置嵌入行为积分归一化环节，使标签权重、能力维度'
     '得分与人才画像构成量纲一致的计算链路；基于有限状态机实现无第三方依赖的四级审批'
     '工作流引擎。系统在南通市疾控中心运行 3 个月，覆盖 15 个业务科室、270 名科研人员，'
     '审核周期由平均 7 天缩短至 2 天，积分核算差错率由 3.54% 降至 0.08%，可为同类'
     '公共卫生机构提供参考。'),

    ('Abstract:',
     '{b|Abstract: }To improve the granularity of research talent evaluation in '
     'centers for disease control and prevention (CDC), a research points management '
     'system based on Spring Boot and MyBatis is designed. It contributes a piecewise '
     'weighting model for multi-author outputs, a dynamic tag weight model embedding '
     'exponential time decay ahead of behaviour-score normalization so that tag '
     'weights, capability scores and the talent profile form one dimensionally '
     'consistent chain, and a lightweight four-level approval workflow engine built '
     'as a finite state machine. Over three months at Nantong CDC, the approval cycle '
     'fell from 7 days to 2 days and the points-accounting error rate from 3.54% to '
     '0.08%.'),
]
for needle, new in R:
    rewrite(find(body, TOK.sub(lambda m: m.group(2), needle)), new)

save(tree, SRC, '../v8/unz/word/document.xml')
print('第三轮完成。')
