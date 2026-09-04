# -*- coding: utf-8 -*-
"""按作者提供的真实数据修正表 3、表 4 及相关表述。"""
import re, xml.etree.ElementTree as ET

SRC='work/word/document.xml'
raw=open(SRC,encoding='utf-8').read()
for pfx,uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"',raw)).items():
    if not re.fullmatch(r'ns\d*',pfx): ET.register_namespace(pfx,uri)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS='{http://www.w3.org/XML/1998/namespace}space'
tree=ET.parse(SRC); body=tree.getroot().find(W+'body')
log=[]

def cell(tbl,r,c):
    return tbl.findall(W+'tr')[r].findall(W+'tc')[c]

def set_cell(tbl,r,c,val):
    tc=cell(tbl,r,c); ts=list(tc.iter(W+'t'))
    old=''.join(t.text or '' for t in ts)
    for t in ts[1:]: t.text=''
    ts[0].text=val; ts[0].set(XS,'preserve')
    return old

tbls=[e for e in body if e.tag==W+'tbl']
t3=next(t for t in tbls if '并发用户数' in ''.join(x.text or '' for x in t.iter(W+'t')))
t4=next(t for t in tbls if '申报单量' in ''.join(x.text or '' for x in t.iter(W+'t')))

# ① 表 3 第 6 列其实是缓存命中率
old=set_cell(t3,0,5,'缓存命中率 / %')
log.append(f'表 3 列名：「{old}」→「缓存命中率 / %」（数值 96.8/95.6/94.2/92.5 不变）')

# ② 表 4 平均审核周期：与摘要统一为 7 → 2
a=set_cell(t4,1,2,'7'); b=set_cell(t4,2,2,'2')
log.append(f'表 4 平均审核周期：{a} → 7、{b} → 2（与摘要的 7 天→2 天一致）')

# ③ 表 4 申报单量：填入真实台账数
a=set_cell(t4,1,1,'192'); b=set_cell(t4,2,1,'1420')
log.append(f'表 4 申报单量：{a} → 192、{b} → 1420（上线后增至 7.4 倍）')

# ④ 正文表述随之调整
for p in body.iter(W+'p'):
    for t in p.iter(W+'t'):
        if t.text and '（含关闭 Redis 缓存的对照）如表 3 所示' in t.text:
            t.text=t.text.replace('（含关闭 Redis 缓存的对照）如表 3 所示',
                                  '与缓存命中率如表 3 所示')
            t.set(XS,'preserve')
            log.append('第 5 章：「含关闭 Redis 缓存的对照」→「与缓存命中率」')
        if t.text and '防止缓存穿透与击穿[15]' in t.text:
            t.text=t.text.replace('防止缓存穿透与击穿[15]；',
                '防止缓存穿透与击穿[15]，实测缓存命中率在 50～500 并发下保持在 92.5% 以上（表 3）；')
            t.set(XS,'preserve')
            log.append('4.6 节：补入缓存命中率的实测结论，与表 3 呼应')
        if t.text and '审核周期与核算差错显著下降' in t.text:
            t.text=t.text.replace('系统上线后申报与审核实现全流程线上化，审核周期与核算差错显著下降',
                '系统上线后申报与审核实现全流程线上化，申报单量增至上线前的 7.4 倍，'
                '平均审核周期由 7 d 降至 2 d')
            t.set(XS,'preserve')
            log.append('表 4 后的分析句：改为与新数据一致的表述')

tree.write(SRC,encoding='UTF-8',xml_declaration=True)
orig=re.search(r'<w:document\b[^>]*>',open('unz/word/document.xml',encoding='utf-8').read()).group(0)
s=open(SRC,encoding='utf-8').read(); cur=re.search(r'<w:document\b[^>]*>',s).group(0)
have=set(re.findall(r'xmlns:(\w+)=',orig))
add=[f'xmlns:{k}="{v}"' for k,v in re.findall(r'xmlns:(\w+)="([^"]+)"',cur) if k not in have]
open(SRC,'w',encoding='utf-8').write(s.replace(cur, orig[:-1]+(' '+' '.join(add) if add else '')+'>',1))
print('已完成：')
for l in log: print('  ·',l)
