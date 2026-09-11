# -*- coding: utf-8 -*-
"""W2 删两处凑数表述。

1) 1 节架构段的"已有文献[12,16]分别以 Spring Boot 与 Flask 实现了科研样本库与
   在线考试系统，表明轻量级 Web 技术栈在此类业务中的适用性"——用一个在线考试
   系统来论证四层架构的可行性，是典型的凑引用，审稿人会当作水分。删句并连带
   删掉只在此处出现的文献[16]。
2) 3.2 节"名义分值制契合协作导向"在同一段里说了三遍，留首尾两处即可。
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, find, save
from rlib import run_replace

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

p = find(body, '系统采用四层架构')
run_replace(p, '，已有文献[12,16]分别以 Spring Boot 与 Flask 实现了科研样本库与'
               '在线考试系统，表明轻量级 Web 技术栈在此类业务中的适用性。', '。')

p = find(body, '式(1)采用名义分值制而非总量守恒制')
run_replace(p, '该增长正是“鼓励多科室协作”这一管理导向的量化形式，'
               '也是本文方法区别于守恒型方法之处。'
               '系统默认采用名义分值制以契合协作导向，需控制年度积分总量的科室',
            '该增长正是上述管理导向的量化形式，也是本文方法区别于守恒型方法之处。'
            '需控制年度积分总量的科室')
run_replace(p, '表1 为 4 位作者时的情形；推广至任意作者数 n，',
            '表1 为 4 位作者时的情形，推广至任意作者数 n 时，')

save(tree, SRC, 'ref.xml')
print('W2 done: 删架构段凑引句；3.2 节去重复表述')
