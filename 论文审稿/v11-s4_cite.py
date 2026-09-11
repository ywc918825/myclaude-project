# -*- coding: utf-8 -*-
"""第四步：修正 3 处张冠李戴的引用。"""
import xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []


def sub(needle, pairs, note):
    p = find(body, needle)
    s = text_of(p)
    for a, b in pairs:
        assert a in s, (needle, a)
        s = s.replace(a, b, 1)
    rewrite(p, s)
    log.append(note)


sub('多作者成果的积分分配是量化评价的难点',
    [('抹杀普通合著者的贡献[22]', '抹杀普通合著者的贡献[23]'),
     ('调和计数法等经典方案[23]', '调和计数法等经典方案[24]')],
    '3.2 节开头：“抹杀普通合著者的贡献”原引[22]——那是何立富的 Spring Security 论文, '
    '与作者贡献分配毫无关系, 改引[23]（韩颖霄等《一种覆盖所有作者的论文荣誉分配方法》）; '
    '“分数分配法、调和计数法等经典方案”改引[24]（Xu 等 authorship credit allocation schemes）')

sub('式(1)采用名义分值制',
    [('取自文献[23]', '取自文献[23,24]')],
    '3.2 节表1 出处：调和计数法与算术递减法的系数同时出自[23]与[24]两篇分配方法研究')

sub('针对疾控中心审核流程相对固定',
    [('规则引擎的方案[24-26]', '规则引擎的方案[25-26]')],
    '3.5 节：工作流引擎对比原引[24-26], 其中[24]是作者贡献分配的论文, 与工作流无关, '
    '收窄为[25-26]（两篇轻量级工作流引擎研究）')

sub('系统引入 Redis 缓存应对高频积分查询',
    [('实现无状态认证[29]', '实现无状态认证[22,29]')],
    '3.6 节：把[22]（何立富, 前后端分离下的 Spring Security 权限系统）挪到它真正对应的'
    '无状态认证处, 与[29]并列')

sub('系统采用四层架构',
    [('并引入 Redis 缓存提升查询效率[14].', '并引入 Redis 缓存提升查询效率.')],
    '1 节：“引入 Redis 缓存提升查询效率”原引[14]（边云协同微服务编排）与缓存无关, '
    '去掉该处标注——缓存策略在 3.6 节有[27]支撑, [14]在“服务端框架选型[14-15]”处仍保留')

save(tree, SRC, 'work.bak/word/document.xml')
print('已完成：')
for l in log:
    print('  ·', l)
