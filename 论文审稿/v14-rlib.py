# -*- coding: utf-8 -*-
"""run 级文本替换：只动命中的那几个 w:t，段内其余 run 的斜体/上下标原样保留。

之前用 rewrite(p, text_of(p).replace(...)) 改过带公式变量的段落，
text_of() 只返回纯文本，重排后整段格式全丢（式(4)(5) 式中段丢了 9 斜体 18 上标）。
凡是段内有格式的，一律走这里。
"""
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS = '{http://www.w3.org/XML/1998/namespace}space'


def _cells(p):
    """段内 w:r/w:t 的有序列表（跳过 oMath 内部，公式不碰）。"""
    out = []
    for r in p.findall(W + 'r'):
        for t in r.findall(W + 't'):
            out.append((r, t))
    return out


def run_replace(p, old, new, count=1):
    """把段落纯文本里的 old 换成 new，只重写被覆盖到的 w:t。"""
    done = 0
    while done < count:
        cells = _cells(p)
        flat = ''.join(t.text or '' for _, t in cells)
        at = flat.find(old)
        if at < 0:
            if done == 0:
                raise KeyError('段内未找到：%r\n段落：%s' % (old[:60], flat[:200]))
            break
        end = at + len(old)
        pos = 0
        for r, t in cells:
            s = t.text or ''
            lo, hi = pos, pos + len(s)
            pos = hi
            if hi <= at or lo >= end:
                continue
            a = max(at, lo) - lo
            b = min(end, hi) - lo
            t.text = s[:a] + (new if lo <= at < hi else '') + s[b:]
            if t.text:
                t.set(XS, 'preserve')
        done += 1
    # 清掉被掏空的 run
    for r in list(p.findall(W + 'r')):
        ts = r.findall(W + 't')
        if ts and all(not (t.text or '') for t in ts) and r.find(W + 'drawing') is None:
            p.remove(r)
    return done


def drop_para(body, p):
    body.remove(p)


def para_text(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))
