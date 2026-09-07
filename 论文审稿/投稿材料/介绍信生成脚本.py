# -*- coding: utf-8 -*-
"""生成投稿单位介绍信（公文格式，可直接打印盖章）。"""
import os, zipfile

CT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DRELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="仿宋_GB2312" w:cs="Times New Roman"/>
<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:line="560" w:lineRule="exact"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
</w:styles>'''

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def p(runs, jc=None, ind=None, line=560, before=0, after=0, keep=False):
    ppr = '<w:pPr>'
    if keep:
        ppr += '<w:keepNext/>'
    ppr += f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="exact"/>'
    if ind:
        ppr += f'<w:ind w:firstLineChars="{int(ind*100)}" w:firstLine="{int(ind*320)}"/>'
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    ppr += '</w:pPr>'
    return f'<w:p>{ppr}{runs}</w:p>'


def r(t, sz=32, font='仿宋_GB2312', b=False, u=False, space=0):
    rpr = f'<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="{font}"/>'
    if b:
        rpr += '<w:b/><w:bCs/>'
    if space:
        rpr += f'<w:spacing w:val="{space}"/>'
    rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if u:
        rpr += '<w:u w:val="single"/>'
    rpr += '</w:rPr>'
    return f'{{}}<w:r>{rpr}<w:t xml:space="preserve">{t}</w:t></w:r>'.format('')


TITLE = '介　绍　信'
BODY = [
 ('《中国数字医学》编辑部：', None, 0),
 ('兹介绍我单位杨文超、张卫兵、练维、徐小卫、王秦等同志撰写的论文'
  '《基于动态积分与标签画像的疾控科研人才评价系统》，推荐至贵刊审阅并申请发表。'
  '现就有关事项说明如下：', None, 2),
 ('一、该论文系我单位科研人员在本职工作基础上独立完成，数据来源真实可靠，'
  '不存在抄袭、剽窃、伪造、篡改等学术不端行为，文责由作者自负。', None, 2),
 ('二、该论文已经我单位保密审查，内容不涉及国家秘密、工作秘密及个人隐私信息，'
  '可以公开发表。', None, 2),
 ('三、该论文未曾在国内外公开出版物上发表，亦未一稿多投。', None, 2),
 ('四、论文作者署名及排序经全体作者确认，无争议；通讯作者为张卫兵。'
  '所有作者均对本研究有实质性贡献，且不存在利益冲突。', None, 2),
 ('五、该论文为南通市社科研究课题（网信专项）（项目编号：WA25-6）研究成果之一。', None, 2),
 ('特此介绍，请予审阅。', None, 2),
]
SIGN = [
 ('南通市疾病预防控制中心', 'right'),
 ('（盖章）', 'right'),
 ('　　年　　月　　日', 'right'),
]

xml = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {W}><w:body>']
xml.append(p(r(TITLE, sz=44, font='方正小标宋简体', space=60), jc='center', line=700, after=360))
for t, jc, ind in BODY:
    xml.append(p(r(t), jc=jc, ind=ind))
xml.append(p(r('　'), line=400))
for t, jc in SIGN:
    xml.append(p(r(t) + r('　　　　'), jc=jc, line=520))
xml.append('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="2098" w:right="1474" w:bottom="2098" w:left="1587" '
           'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>')
xml.append('</w:body></w:document>')
doc = ''.join(xml)

OUT = '投稿单位介绍信-中国数字医学.docx'
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/_rels/document.xml.rels', DRELS)
    z.writestr('word/styles.xml', STYLES)
    z.writestr('word/document.xml', doc)
print(OUT, os.path.getsize(OUT), 'bytes')
