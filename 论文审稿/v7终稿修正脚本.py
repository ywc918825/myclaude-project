# -*- coding: utf-8 -*-
"""摘要差错率改为 3.54% → 0.08%；表 4 加表注说明上线前查询口径。"""
import copy, re, xml.etree.ElementTree as ET
SRC='work/word/document.xml'
raw=open(SRC,encoding='utf-8').read()
for pfx,uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"',raw)).items():
    if not re.fullmatch(r'ns\d*',pfx): ET.register_namespace(pfx,uri)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS='{http://www.w3.org/XML/1998/namespace}space'
tree=ET.parse(SRC); body=tree.getroot().find(W+'body')
log=[]

def txt(p): return ''.join(t.text or '' for t in p.iter(W+'t'))

# ── 1. 中英文摘要的差错率 ────────────────────────────────────────────────
EDITS=[
 ('积分核算人为差错率由 5% 降至 0，',
  '积分核算差错率由 3.54% 降至 0.08%，',
  '中文摘要：差错率改为 3.54% → 0.08%（与表 4 的 6.8/192 与 1.2/1420 一致）'),
 ('eliminated manual errors in points accounting,',
  'reduced the points-accounting error rate from 3.54% to 0.08%,',
  '英文摘要：同步改为 3.54% → 0.08%（原文 “eliminated” 表示归零，与表 4 不符）'),
]
for old,new,why in EDITS:
    for p in body.iter(W+'p'):
        hit=False
        for t in p.iter(W+'t'):
            if t.text and old in t.text:
                t.text=t.text.replace(old,new); t.set(XS,'preserve'); hit=True; log.append(why); break
        if hit: break

# ── 2. 表 4 加表注 ───────────────────────────────────────────────────────
kids=list(body)
t4=next(i for i,e in enumerate(kids)
        if e.tag==W+'tbl' and '申报单量' in ''.join(x.text or '' for x in e.iter(W+'t')))
# 以表后正文段为模板取字体
tmpl=next(e for e in kids[t4+1:] if e.tag==W+'p' and txt(e).strip())
note=ET.Element(W+'p')
ppr=ET.SubElement(note,W+'pPr')
sp=ET.SubElement(ppr,W+'spacing'); sp.set(W+'beforeLines','20'); sp.set(W+'before','60')
sp.set(W+'afterLines','30'); sp.set(W+'after','90')
jc=ET.SubElement(ppr,W+'jc'); jc.set(W+'val','left')
r=ET.SubElement(note,W+'r')
rpr_src=tmpl.find(W+'r/'+W+'rPr')
if rpr_src is not None:
    rpr=copy.deepcopy(rpr_src)
    for tag in ('sz','szCs'):
        e=rpr.find(W+tag)
        if e is not None: e.set(W+'val','18')      # 小五
    r.append(rpr)
t=ET.SubElement(r,W+'t'); t.set(XS,'preserve')
t.text='注：上线前的人均月查询次数为人工查阅台账次数。'
body.insert(t4+1,note)
log.append('表 4：加表注「注：上线前的人均月查询次数为人工查阅台账次数。」')

tree.write(SRC,encoding='UTF-8',xml_declaration=True)
orig=re.search(r'<w:document\b[^>]*>',open('unz/word/document.xml',encoding='utf-8').read()).group(0)
s=open(SRC,encoding='utf-8').read(); cur=re.search(r'<w:document\b[^>]*>',s).group(0)
have=set(re.findall(r'xmlns:(\w+)=',orig))
add=[f'xmlns:{k}="{v}"' for k,v in re.findall(r'xmlns:(\w+)="([^"]+)"',cur) if k not in have]
open(SRC,'w',encoding='utf-8').write(s.replace(cur, orig[:-1]+(' '+' '.join(add) if add else '')+'>',1))
print('已完成：')
for l in log: print('  ·',l)
