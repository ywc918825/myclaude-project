# -*- coding: utf-8 -*-
"""W1 修两处硬伤（与精简无关，但审稿人一眼能看见）。

1) 英文摘要 "…nominal-credit scheme. the approval cycle…" 句首小写。
   这是上一轮把对比实验并入英文摘要时留下的接缝。
2) 3.3 节段末"其合成效果见 3.3 节参数取值的说明"——本段就在 3.3 节内，
   属自指笔误；且紧接的下一段就是那段说明，删去不损失信息。
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

run_replace(find(body, 'Abstract: Research talent evaluation'),
            'scheme. the approval cycle', 'scheme. The approval cycle')

run_replace(find(body, '为行为 i 经时间衰减与归一化后的积分'),
            '两式共同决定成果的时效权重，其合成效果见 3.3 节参数取值的说明。', '')

save(tree, SRC, 'ref.xml')
print('W1 done: 英文摘要句首大写；删自指句')
