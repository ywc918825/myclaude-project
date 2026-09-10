# -*- coding: utf-8 -*-
"""改后自检：格式有没有丢、编号有没有断、哨兵有没有残留。

上一轮的教训是格式在批量改写中悄悄丢了而脚本没发现，所以这里逐段比对
斜体/上下标计数，改前改后必须一致（被删掉的段除外）。
"""
import re, sys, xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
PUNC = str.maketrans('，。；：（）“”', ',.;:()""')


def load(path):
    return ET.parse(path).getroot()


def txt(el):
    return ''.join(t.text or '' for t in el.iter(W + 't'))


def key(p):
    """用去标点、去空白的前 24 字做段落身份，避免标点转换导致对不上。"""
    return re.sub(r'\s+', '', txt(p).translate(PUNC))[:24]


def fmt(p):
    return (len(p.findall('.//' + W + 'i')),
            sum(1 for v in p.findall('.//' + W + 'vertAlign')
                if v.get(W + 'val') == 'subscript'),
            sum(1 for v in p.findall('.//' + W + 'vertAlign')
                if v.get(W + 'val') == 'superscript'))


old, new = load('document.orig.xml'), load('unz/word/document.xml')
ob = {key(p): p for p in old.find(W + 'body') if p.tag == W + 'p' and txt(p).strip()}
nb = {key(p): p for p in new.find(W + 'body') if p.tag == W + 'p' and txt(p).strip()}

bad = 0
print('=== 1. 格式比对（斜体/下标/上标）===')
for k, p in ob.items():
    if k not in nb:
        continue
    a, b = fmt(p), fmt(nb[k])
    if a != b:
        bad += 1
        print('  !! %-26s %s → %s' % (k[:26], a, b))
print('  改前有格式的段共 %d 个，%s'
      % (sum(1 for p in ob.values() if any(fmt(p))),
         '全部保持一致' if not bad else '有 %d 段变化' % bad))

print('\n=== 2. 删除的段落 ===')
for k in ob:
    if k not in nb:
        print('  - %s' % txt(ob[k])[:56])

print('\n=== 3. 参考文献编号连续性 ===')
body = new.find(W + 'body')
ps = [p for p in body if p.tag == W + 'p']
i_ref = next(i for i, p in enumerate(ps) if txt(p).strip() == '参考文献')
nums = [int(m.group(1)) for p in ps[i_ref + 1:]
        for m in [re.match(r'\s*\[(\d+)\]', txt(p))] if m]
print('  条目：%d 条，编号 %s' % (len(nums), '连续 1–%d' % nums[-1]
                              if nums == list(range(1, len(nums) + 1)) else nums))

print('\n=== 4. 正文引用是否都能落到条目上 ===')
CIT = re.compile(r'\[([0-9]+(?:[,\-][0-9]+)*)\]')
used = set()
for p in ps[:i_ref]:
    for m in CIT.finditer(txt(p)):
        for part in m.group(1).split(','):
            if '-' in part:
                a, b = part.split('-')
                used |= set(range(int(a), int(b) + 1))
            else:
                used.add(int(part))
over = sorted(x for x in used if x > len(nums))
miss = sorted(set(range(1, len(nums) + 1)) - used)
print('  正文引到 %d 个编号；越界 %s；文后有条目但正文未引 %s'
      % (len(used), over or '无', miss or '无'))

print('\n=== 5. 表号 ===')
alltxt = ''.join(txt(p) for p in new.iter(W + 'p'))
caps = re.findall(r'表(\d+)\s\s', alltxt)
ntbl = len(new.findall('.//' + W + 'tbl'))
print('  表体 %d 张；表题编号 %s' % (ntbl, sorted(set(int(x) for x in caps))))
refs = sorted(set(int(x) for x in re.findall(r'表(\d+)', alltxt)))
print('  正文+表题出现的表号 %s' % refs)

print('\n=== 6. 其他 ===')
print('  公式 oMath 节点：%d' % len(new.findall('.//' + M + 'oMath')))
sent = [c for c in alltxt if 0xE000 <= ord(c) <= 0xF8FF]
print('  哨兵字符残留：%d' % len(sent))
low = re.findall(r'[.;]\s+[a-z]\w+', txt(ps[13]))
print('  英文摘要句首小写：%s' % (low or '无'))
print('  文中是否还有旧刊名占位/半角问题：%s'
      % ('有' if re.search(r'[一-鿿],\s', alltxt) else '无'))
sys.exit(1 if bad or over else 0)
