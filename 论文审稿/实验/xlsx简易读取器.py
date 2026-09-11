# -*- coding: utf-8 -*-
"""极简 xlsx 读取器：zipfile + ElementTree，不依赖 openpyxl。"""
import re, sys, zipfile
import xml.etree.ElementTree as ET
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def load(path):
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    rels = {r.get('Id'): r.get('Target')
            for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    out = []
    for sh in ET.fromstring(z.read('xl/workbook.xml')).find(NS + 'sheets'):
        tgt = rels[sh.get(REL + 'id')].lstrip('/')
        if not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt
        rows = []
        for row in ET.fromstring(z.read(tgt)).iter(NS + 'row'):
            cells = {}
            for c in row.findall(NS + 'c'):
                col = re.match(r'([A-Z]+)', c.get('r') or 'A').group(1)
                v = c.find(NS + 'v')
                isv = c.find(NS + 'is')
                if c.get('t') == 's' and v is not None:
                    val = shared[int(v.text)]
                elif isv is not None:
                    val = ''.join(t.text or '' for t in isv.iter(NS + 't'))
                elif v is not None:
                    val = v.text
                else:
                    val = ''
                cells[col] = val
            if cells:
                n = max(_ci(k) for k in cells)
                rows.append([cells.get(_cn(i), '') for i in range(1, n + 1)])
        out.append((sh.get('name'), rows))
    return out


def _ci(s):
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 64
    return n


def _cn(i):
    s = ''
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


if __name__ == '__main__':
    for name, rows in load(sys.argv[1]):
        print('=' * 70)
        print('工作表：%s   （%d 行）' % (name, len(rows)))
        print('=' * 70)
        for r in rows[:int(sys.argv[2]) if len(sys.argv) > 2 else 12]:
            print(' | '.join((x or '')[:26] for x in r))
        if len(rows) > 12:
            print('   …… 共 %d 行' % len(rows))
