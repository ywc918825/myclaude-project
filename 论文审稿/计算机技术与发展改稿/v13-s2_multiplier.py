# -*- coding: utf-8 -*-
"""S2 在 3.2 节补出本文方法"合计倍率随作者数增长"的精确序列。

表1 只给了 n = 4 这一列，读者看不出本文方法与三种守恒型方法的本质差别：
守恒型方法的合计恒为 1.00，而本文方法随作者数单调增长。这正是"名义分值制
契合多科室协作导向"的量化形式，且**精确可算、零假设**——比任何仿真都硬。

不新增表格：一句话即可承载该序列，新增会导致表2—5 重排及交叉引用连改。
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, '.')
import lib
from lib import W, rewrite, text_of, find, save

SRC = 'unz/word/document.xml'
lib.register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')

p = find(body, '式(1)采用名义分值制而非总量守恒制')
t = text_of(p)
old = ('与常见守恒型方法的对比如表1所示，其中调和计数法与算术递减法'
       '取自文献[22,23]的归类。')
assert old in t, t[:300]
new = ('与常见守恒型方法的对比如表1所示，其中调和计数法与算术递减法'
       '取自文献[22,23]的归类。表1 为 4 位作者时的情形；'
       '推广至任意作者数 n，三种守恒型方法的分配系数之和恒为 1.00，'
       '而本文方法在 n = 2、3、4、6 时分别为 1.80、2.30、2.50、2.90，'
       '随合作规模单调增长——这一增长正是"鼓励多科室协作"这一管理导向的'
       '量化形式，也是本文方法区别于守恒型方法的根本所在。')
rewrite(p, t.replace(old, new))

save(tree, SRC, 'ref.xml')
print('S2 done')
