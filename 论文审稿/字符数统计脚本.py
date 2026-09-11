# -*- coding: utf-8 -*-
"""按 Word 口径统计字符数，并按章节给出分布。"""
import re, sys, xml.etree.ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
SRC = sys.argv[1] if len(sys.argv)>1 else 'work/word/document.xml'

def ptxt(p, math=True):
    out=[]
    def walk(el):
        for c in el:
            if c.tag==M+'oMath':
                if math:
                    out.append(''.join(t.text or '' for t in c.iter(M+'t')))
            elif c.tag==W+'t': out.append(c.text or '')
            elif c.tag==W+'tab': out.append(' ')
            else: walk(c)
    walk(p); return ''.join(out)

root=ET.parse(SRC).getroot(); body=root.find(W+'body')

SEC=[('篇首',None)]
lines=[]
for el in body:
    if el.tag==W+'p':
        lines.append(ptxt(el))
    elif el.tag==W+'tbl':
        for tr in el.findall(W+'tr'):
            for tc in tr.findall(W+'tc'):
                lines.append(' '.join(ptxt(p) for p in tc.findall(W+'p')))

heads=['1  引言','2  系统总体架构','3  核心功能模块设计','4  关键技术实现',
       '4.1','4.2','4.3','4.4','4.5','4.6','5  系统测试','6  结论与展望','参考文献']
cur='篇首'; acc={ '篇首':0 }; order=['篇首']
tot=0
for ln in lines:
    s=ln.strip()
    for h in heads:
        if s.startswith(h):
            cur=s[:14]
            if cur not in acc: acc[cur]=0; order.append(cur)
            break
    n=len(ln)
    acc[cur]=acc.get(cur,0)+n
    tot+=n

allt=''.join(lines)
print('字符数（计空格）: %d' % len(allt))
print('字符数（不计空格）: %d' % len(allt.replace(' ','').replace('　','')))
print('汉字: %d' % len(re.findall(r'[一-鿿]', allt)))
print()
for k in order:
    print('  %-22s %5d' % (k, acc[k]))
print('  %-22s %5d' % ('合计', tot))
