# -*- coding: utf-8 -*-
import re, sys, zipfile
import xml.etree.ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'

def ptext(p):
    out=[]
    for el in p.iter():
        if el.tag==W+'t': out.append(el.text or '')
        elif el.tag==W+'tab': out.append('\t')
        elif el.tag==W+'br': out.append('\n')
        elif el.tag==M+'oMath': pass
    return ''.join(out)

def mathtext(el):
    return ''.join(t.text or '' for t in el.iter(M+'t'))

z=zipfile.ZipFile(sys.argv[1])
root=ET.fromstring(z.read('word/document.xml'))
body=root.find(W+'body')
i=0
for child in body:
    tag=child.tag.split('}')[1]
    if tag=='p':
        t=ptext(child)
        maths=[mathtext(m) for m in child.iter(M+'oMath')]
        style=''
        pPr=child.find(W+'pPr')
        if pPr is not None:
            ps=pPr.find(W+'pStyle')
            if ps is not None: style='['+ps.get(W+'val')+']'
        drawing = 'IMG' if child.find('.//'+W+'drawing') is not None else ''
        line=t
        if maths: line += '  ⟨EQ: ' + ' | '.join(maths) + '⟩'
        if drawing: line += ' ⟨'+drawing+'⟩'
        print('%3d P%s %s' % (i, style, line))
    elif tag=='tbl':
        print('%3d ===TABLE===' % i)
        for r,tr in enumerate(child.findall(W+'tr')):
            cells=[]
            for tc in tr.findall(W+'tc'):
                cells.append(' '.join(ptext(p) for p in tc.findall(W+'p')).strip())
            print('      | ' + ' | '.join(cells))
        print('    ===END TABLE===')
    else:
        print('%3d <%s>' % (i,tag))
    i+=1
