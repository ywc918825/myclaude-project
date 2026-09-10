# -*- coding: utf-8 -*-
"""极简 xlsx 写入器：zipfile + 手写 OOXML，不依赖 openpyxl。

本环境无 openpyxl 且 pip 不可用，故自备。只实现填表模板需要的功能：
多工作表、内联字符串、加粗表头、列宽、冻结首行、自动换行。

    from xlsx简易写入器 import Workbook
    wb = Workbook()
    wb.sheet('成果台账', rows, widths=[40, 30, 12, 10], header=True, freeze=True)
    wb.save('台账模板.xlsx')
"""
import zipfile
from xml.sax.saxutils import escape

CT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
%s</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

# 0 常规 / 1 加粗表头(灰底居中) / 2 自动换行 / 3 灰色示例行
STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="4">
<font><sz val="11"/><name val="宋体"/></font>
<font><b/><sz val="11"/><name val="宋体"/></font>
<font><sz val="11"/><name val="宋体"/></font>
<font><sz val="11"/><color rgb="FF999999"/><i/><name val="宋体"/></font>
</fonts>
<fills count="3">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEDEDED"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2"><border/><border>
<left style="thin"><color rgb="FFBBBBBB"/></left><right style="thin"><color rgb="FFBBBBBB"/></right>
<top style="thin"><color rgb="FFBBBBBB"/></top><bottom style="thin"><color rgb="FFBBBBBB"/></bottom>
</border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="4">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
</cellXfs>
</styleSheet>'''


def _cn(i):
    s = ''
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class Workbook:
    def __init__(self):
        self._sheets = []

    def sheet(self, name, rows, widths=None, header=False, freeze=False,
              wrap=False, dim_from=None):
        """rows: 二维列表。header=True 时首行加粗；dim_from: 从该行起用灰斜体。"""
        self._sheets.append((name, rows, widths, header, freeze, wrap, dim_from))

    def _sheet_xml(self, rows, widths, header, freeze, wrap, dim_from):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
        if freeze:
            out.append('<sheetViews><sheetView workbookViewId="0" tabSelected="1">'
                       '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                       '</sheetView></sheetViews>')
        if widths:
            out.append('<cols>' + ''.join(
                '<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i, i, w)
                for i, w in enumerate(widths, 1)) + '</cols>')
        out.append('<sheetData>')
        for ri, row in enumerate(rows, 1):
            cells = []
            for ci, v in enumerate(row, 1):
                if v is None or v == '':
                    continue
                if header and ri == 1:
                    s = 1
                elif dim_from and ri >= dim_from:
                    s = 3
                elif wrap:
                    s = 2
                else:
                    s = 0
                cells.append('<c r="%s%d" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                             % (_cn(ci), ri, s, escape(str(v))))
            out.append('<row r="%d">%s</row>' % (ri, ''.join(cells)))
        out.append('</sheetData></worksheet>')
        return ''.join(out)

    def save(self, path):
        n = len(self._sheets)
        over = ''.join('<Override PartName="/xl/worksheets/sheet%d.xml" '
                       'ContentType="application/vnd.openxmlformats-officedocument.'
                       'spreadsheetml.worksheet+xml"/>' % (i + 1) for i in range(n))
        wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
              '<sheets>' + ''.join(
                  '<sheet name="%s" sheetId="%d" r:id="rId%d"/>'
                  % (escape(s[0]), i + 1, i + 1) for i, s in enumerate(self._sheets))
              + '</sheets></workbook>')
        wbrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  + ''.join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                            'officeDocument/2006/relationships/worksheet" '
                            'Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1)
                            for i in range(n))
                  + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
                    'officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (n + 1)
                  + '</Relationships>')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', CT % over)
            z.writestr('_rels/.rels', RELS)
            z.writestr('xl/workbook.xml', wb)
            z.writestr('xl/_rels/workbook.xml.rels', wbrels)
            z.writestr('xl/styles.xml', STYLES)
            for i, s in enumerate(self._sheets, 1):
                z.writestr('xl/worksheets/sheet%d.xml' % i, self._sheet_xml(*s[1:]))
