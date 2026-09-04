# -*- coding: utf-8 -*-
"""重排引用位置，使每处引用落在它真正支撑的论述上。"""
import re, xml.etree.ElementTree as ET
SRC='work/word/document.xml'
raw=open(SRC,encoding='utf-8').read()
for pfx,uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"',raw)).items():
    if not re.fullmatch(r'ns\d*',pfx): ET.register_namespace(pfx,uri)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS='{http://www.w3.org/XML/1998/namespace}space'
tree=ET.parse(SRC); body=tree.getroot().find(W+'body')

EDITS=[
 # (原文, 新文, 说明)
 ('等问题[1-2]，难以支撑', '等问题[1]，难以支撑',
  '引言首句：去掉[2]。[2]讲颠覆性技术创新的组织路径，不支撑“评价方式粗放”；它在下一句已按“组织机制”角度引用'),
 ('罗仕鉴等[9]与白菁昊等[10]验证了动态标签刻画能力演进的有效性，但未考虑科研成果的长周期性与时效衰减特征。',
  '罗仕鉴等[9]与白菁昊等[10]分别在产品设计与学习者场景验证了用户画像与动态标签方法的有效性，但均未考虑科研成果的长周期性与时效衰减特征。',
  '引言：[9]是产品设计用户画像、[10]是学习者画像，原句“刻画能力演进”与二者实际内容不符，改为如实表述'),
 ('实现前后端分离；业务逻辑层', '实现前后端分离[5]；业务逻辑层',
  '2 章：[5]是 Spring Boot 轻量级编排框架，移到 Spring Boot 架构处（原挂在 4.5 工作流配置，关联很弱）'),
 ('可在复杂场景下直接优化 SQL[8]；数据层', '可在复杂场景下直接优化 SQL；数据层',
  '2 章：删[8]。[8]是公共卫生服务平台设计，不讲 MyBatis 对象关系映射'),
 ('前端采用 Vue.js，通过 RESTful API', '前端采用 Vue.js[7]，通过 RESTful API',
  '2 章：[7]是 Vue 前端性能研究，给它一个真正对口的位置（原来只被 [5-8] 区间捎带覆盖）'),
 ('并引入 Redis 缓存提升查询效率[5-8]。', '并引入 Redis 缓存提升查询效率[6,8]。',
  '2 章：[5-8]收窄为[6,8]。这两篇是 Spring Boot 行业系统实践，支撑技术栈选型；[5][7]已各自归位'),
 ('自动校验并核算分值、生成积分流水[8-9]；', '自动校验并核算分值、生成积分流水；',
  '3 章：删[8-9]。积分核算是本文自身设计，且[8]公共卫生平台、[9]产品设计画像均不支撑该论述'),
 ('共同第一作者按并列第 1 作者计[9]。', '共同第一作者按并列第 1 作者计。',
  '4.2：删[9]。多作者积分分配规则与“产品设计用户画像生成方法”无关'),
 ('系统构建了基础属性、能力维度与专业方向三维标签体系。',
  '系统构建了基础属性、能力维度与专业方向三维标签体系[10]。',
  '4.3：[10]“时序动态标签构建及预测”移到标签体系处，这才是它真正对口的论述'),
 ('团队贡献矩阵与标签云图[10]。', '团队贡献矩阵与标签云图。',
  '4.4：删[10]。该句讲的是前端图表组件，[10]不涉及可视化'),
 ('调整审核环节或处理人，无需重启系统[5]。', '调整审核环节或处理人，无需重启系统。',
  '4.5：删[5]，已移至 2 章'),
 ('系统引入 Redis 缓存应对高频积分查询', '系统引入 Redis 缓存[15]应对高频积分查询',
  '4.6：[15]kRedis 是 Redis 缓存机制研究，移到“引入 Redis 缓存”处'),
 ('分别防止缓存穿透与击穿[15]，实测', '分别防止缓存穿透与击穿，实测',
  '4.6：删原位置的[15]。kRedis 讲多租户缓存分区与 LRU，不讲穿透/击穿防护'),
]

log=[]; miss=[]
for old,new,why in EDITS:
    hit=False
    for p in body.iter(W+'p'):
        for t in p.iter(W+'t'):
            if t.text and old in t.text:
                t.text=t.text.replace(old,new); t.set(XS,'preserve'); hit=True; break
        if hit: break
    (log if hit else miss).append(why if hit else f'未匹配：{old[:34]}')

tree.write(SRC,encoding='UTF-8',xml_declaration=True)
orig=re.search(r'<w:document\b[^>]*>',open('unz/word/document.xml',encoding='utf-8').read()).group(0)
s=open(SRC,encoding='utf-8').read(); cur=re.search(r'<w:document\b[^>]*>',s).group(0)
have=set(re.findall(r'xmlns:(\w+)=',orig))
add=[f'xmlns:{k}="{v}"' for k,v in re.findall(r'xmlns:(\w+)="([^"]+)"',cur) if k not in have]
open(SRC,'w',encoding='utf-8').write(s.replace(cur, orig[:-1]+(' '+' '.join(add) if add else '')+'>',1))
print(f'已调整 {len(log)} 处：')
for l in log: print('  ·',l)
if miss:
    print('\n⚠ 未匹配:')
    for m in miss: print('  ·',m)
