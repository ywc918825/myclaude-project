# -*- coding: utf-8 -*-
"""段落重排工具：保留 pPr 与斜体/上下标/加粗/高亮格式的小标记语言。"""
import copy, re, xml.etree.ElementTree as ET
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS = '{http://www.w3.org/XML/1998/namespace}space'
RPR_ORDER = ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps',
             'strike', 'dstrike', 'outline', 'shadow', 'emboss', 'imprint',
             'noProof', 'snapToGrid', 'vanish', 'webHidden', 'color', 'spacing',
             'w', 'kern', 'position', 'sz', 'szCs', 'highlight', 'u', 'effect',
             'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs', 'em', 'lang']
TOK = re.compile(r'\{(b|i|sub|sup|hl)\|([^{}]*)\}')


def register(path):
    raw = open(path, encoding='utf-8').read()
    for pfx, uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw)).items():
        if not re.fullmatch(r'ns\d*', pfx):
            ET.register_namespace(pfx, uri)


def set_prop(rpr, tag, val=None):
    for c in list(rpr):
        if c.tag == W + tag:
            rpr.remove(c)
    el = ET.Element(W + tag)
    if val is not None:
        el.set(W + 'val', val)
    idx = RPR_ORDER.index(tag) if tag in RPR_ORDER else len(RPR_ORDER)
    pos = 0
    for c in list(rpr):
        t = c.tag.replace(W, '')
        ci = RPR_ORDER.index(t) if t in RPR_ORDER else len(RPR_ORDER)
        if ci <= idx:
            pos += 1
        else:
            break
    rpr.insert(pos, el)
    return rpr


def templates(p):
    plain, got = None, {}
    for r in p.findall(W + 'r'):
        rpr = r.find(W + 'rPr')
        if rpr is None:
            continue
        kinds = set()
        for c in rpr:
            t = c.tag.replace(W, '')
            if t == 'vertAlign':
                kinds.add(c.get(W + 'val'))
            elif t in ('i', 'b', 'highlight'):
                kinds.add(t)
        if not kinds and plain is None:
            plain = rpr
        if len(kinds) == 1:
            got.setdefault(next(iter(kinds)), rpr)
    if plain is None:
        any_rpr = next((r.find(W + 'rPr') for r in p.findall(W + 'r')
                        if r.find(W + 'rPr') is not None), None)
        plain = copy.deepcopy(any_rpr) if any_rpr is not None else ET.Element(W + 'rPr')
        for c in list(plain):
            if c.tag.replace(W, '') in ('i', 'b', 'vertAlign', 'highlight'):
                plain.remove(c)
    out = {'-': plain}
    for key, src_key, tag, val in (('b', 'b', 'b', None), ('i', 'i', 'i', None),
                                   ('sub', 'subscript', 'vertAlign', 'subscript'),
                                   ('sup', 'superscript', 'vertAlign', 'superscript'),
                                   ('hl', 'highlight', 'highlight', 'yellow')):
        src = got.get(src_key)
        out[key] = src if src is not None else set_prop(copy.deepcopy(plain), tag, val)
    return out


def rewrite(p, markup):
    tpl = templates(p)
    for r in list(p):
        if r.tag == W + 'r':
            p.remove(r)
    segs, pos = [], 0
    for m in TOK.finditer(markup):
        if m.start() > pos:
            segs.append(('-', markup[pos:m.start()]))
        segs.append((m.group(1), m.group(2)))
        pos = m.end()
    if pos < len(markup):
        segs.append(('-', markup[pos:]))
    for kind, txt in segs:
        if not txt:
            continue
        r = ET.SubElement(p, W + 'r')
        r.append(copy.deepcopy(tpl[kind]))
        t = ET.SubElement(r, W + 't')
        t.set(XS, 'preserve')
        t.text = txt


def text_of(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def find(body, needle, start=0):
    """返回首个正文含 needle 的段落。"""
    for p in list(body)[start:]:
        if p.tag == W + 'p' and needle in text_of(p):
            return p
    raise KeyError(needle)


def save(tree, src, ref):
    tree.write(src, encoding='UTF-8', xml_declaration=True)
    orig = re.search(r'<w:document\b[^>]*>',
                     open(ref, encoding='utf-8').read()).group(0)
    s = open(src, encoding='utf-8').read()
    cur = re.search(r'<w:document\b[^>]*>', s).group(0)
    have = set(re.findall(r'xmlns:(\w+)=', orig))
    add = [f'xmlns:{k}="{v}"' for k, v in re.findall(r'xmlns:(\w+)="([^"]+)"', cur)
           if k not in have]
    open(src, 'w', encoding='utf-8').write(
        s.replace(cur, orig[:-1] + (' ' + ' '.join(add) if add else '') + '>', 1))
