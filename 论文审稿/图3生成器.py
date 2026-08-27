# -*- coding: utf-8 -*-
"""图 3 生成器 —— 16 维能力维度雷达图。

SERIES 为空  -> 输出「维度体系图」（只有坐标系与维度名，不含任何数据）
SERIES 有值  -> 输出带数据的能力雷达图

要生成带数据的版本：把下面 SERIES 里的 None 换成你系统导出的 16 个得分
（式(7)归一化后的值，范围 20–100，顺序必须与 DIMS 一致），然后重新运行本脚本。
"""
import math, os, subprocess, sys

# ─────────────────────────────────────────────────────────────────────────
# 维度定义：顺序即雷达图上的顺序，从正上方开始顺时针
DIMS = [
    ('发表论文', 0), ('出版著作', 0), ('项目课题', 0), ('成果奖励', 0),
    ('专利发明', 1), ('技术标准', 1), ('成果转化', 1), ('工作文章', 1),
    ('学术交流', 2), ('学术地位', 2), ('学术团队', 2), ('科普作品', 2),
    ('技能资质', 3), ('继续教育', 3), ('学术比赛', 3), ('荣誉表彰', 3),
]
GROUPS = ['学术产出', '技术贡献', '学术影响', '专业成长']
GCOLOR = ['#2a78d6', '#eb6834', '#1baf7a', '#4a3aa7']

# ── 数据区：填入真实得分即可生成带数据的雷达图 ──────────────────────────
SERIES = {
    # '个人得分':   [None] * 16,
    # '科室平均':   [None] * 16,
    # '全中心优秀': [None] * 16,
}
DASH = ['none', '7 5', '2 5']
# ─────────────────────────────────────────────────────────────────────────

VB = 930
CX = CY = VB / 2
RINGS = [100, 165, 230, 295]          # 对应 20 / 40 / 60 / 80 ... 见 TICKS
TICKS = ['20', '40', '60', '80', '100']
R_MAX = 295
R_TINT = 320
R_LABEL = 350
R_GROUP = 432
INK, INK2, GRID = '#1b1b1b', '#555555', '#c9cdd4'
FONT = "'WenQuanYi Zen Hei','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
N = len(DIMS)
STEP = 360 / N


def pt(ang, r):
    a = math.radians(ang)
    return CX + r * math.sin(a), CY - r * math.cos(a)


def poly(r, ang0=0.0):
    return ' '.join('%.2f,%.2f' % pt(ang0 + i * STEP, r) for i in range(N))


def sector(i0, i1, r):
    """扇形背景：覆盖第 i0..i1 条轴，向两侧各外扩半格"""
    a0, a1 = (i0 - 0.5) * STEP, (i1 + 0.5) * STEP
    x0, y0 = pt(a0, r)
    x1, y1 = pt(a1, r)
    large = 1 if (a1 - a0) > 180 else 0
    return (f'M {CX:.2f},{CY:.2f} L {x0:.2f},{y0:.2f} '
            f'A {r:.2f},{r:.2f} 0 {large} 1 {x1:.2f},{y1:.2f} Z')


def arc_path(r, a0, a1, pid):
    """下半圆的弧反向绘制，使 textPath 上的中文正立。"""
    flip = 90 < ((a0 + a1) / 2) % 360 < 270
    if flip:
        a0, a1 = a1, a0
        r += 46                      # 反向后文字落在弧内侧，半径外推补偿
    x0, y0 = pt(a0, r)
    x1, y1 = pt(a1, r)
    large = 1 if abs(a1 - a0) > 180 else 0
    sweep = 0 if flip else 1
    return (f'<path id="{pid}" d="M {x0:.2f},{y0:.2f} '
            f'A {r:.2f},{r:.2f} 0 {large} {sweep} {x1:.2f},{y1:.2f}" fill="none"/>')


s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" '
     f'width="{VB}" height="{VB}" font-family="{FONT}">',
     f'<rect width="{VB}" height="{VB}" fill="#ffffff"/>', '<defs>']
for g in range(4):
    a0, a1 = (g * 4 - 0.5) * STEP, (g * 4 + 3.5) * STEP
    s.append(arc_path(R_GROUP, a0, a1, f'garc{g}'))
s.append('</defs>')

# 分组扇形底色
for g in range(4):
    s.append(f'<path d="{sector(g*4, g*4+3, R_TINT)}" fill="{GCOLOR[g]}" '
             f'fill-opacity="0.055"/>')

# 网格环与轴
for r in RINGS:
    s.append(f'<polygon points="{poly(r)}" fill="none" stroke="{GRID}" stroke-width="1.1"/>')
s.append(f'<polygon points="{poly(R_MAX)}" fill="none" stroke="{GRID}" stroke-width="1.6"/>')
for i in range(N):
    x, y = pt(i * STEP, R_MAX)
    s.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.2f}" y2="{y:.2f}" '
             f'stroke="{GRID}" stroke-width="1.1"/>')

# 刻度（对应式(7)归一化区间 20–100）
s.append(f'<circle cx="{CX}" cy="{CY}" r="3.4" fill="{INK2}"/>')
for r, t in zip([0] + RINGS, TICKS):
    s.append(f'<text x="{CX-7}" y="{CY-r+4}" text-anchor="end" font-size="22" '
             f'fill="{INK2}">{t}</text>')

# 数据系列
legend = []
for k, (name, vals) in enumerate(SERIES.items()):
    if not vals or any(v is None for v in vals):
        continue
    pts = []
    for i, v in enumerate(vals):
        r = RINGS[0] + (max(20.0, min(100.0, float(v))) - 20) / 80 * (R_MAX - RINGS[0])
        pts.append('%.2f,%.2f' % pt(i * STEP, r))
    c = GCOLOR[k % 4]
    s.append(f'<polygon points="{" ".join(pts)}" fill="{c}" fill-opacity="0.10" '
             f'stroke="{c}" stroke-width="2.6" stroke-dasharray="{DASH[k % 3]}" '
             f'stroke-linejoin="round"/>')
    for p in pts:
        x, y = p.split(',')
        s.append(f'<circle cx="{x}" cy="{y}" r="4.6" fill="{c}" '
                 f'stroke="#ffffff" stroke-width="1.6"/>')
    legend.append((name, c, DASH[k % 3]))

# 维度标签：每个 4 字标签排成 2×2 字块
for i, (name, g) in enumerate(DIMS):
    x, y = pt(i * STEP, R_LABEL)
    s.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" font-size="30" '
             f'fill="{INK}">'
             f'<tspan x="{x:.2f}" dy="-4">{name[:2]}</tspan>'
             f'<tspan x="{x:.2f}" dy="32">{name[2:]}</tspan></text>')

# 分组弧标签
for g in range(4):
    s.append(f'<text font-size="31" font-weight="bold" fill="{GCOLOR[g]}" '
             f'letter-spacing="3">'
             f'<textPath href="#garc{g}" startOffset="50%" text-anchor="middle">'
             f'{GROUPS[g]}</textPath></text>')

# 图例（仅在有数据时）
if legend:
    y = VB - 26
    total = len(legend) * 210
    x = CX - total / 2 + 20
    for name, c, dash in legend:
        s.append(f'<line x1="{x}" y1="{y-6}" x2="{x+44}" y2="{y-6}" stroke="{c}" '
                 f'stroke-width="2.6" stroke-dasharray="{dash}"/>')
        s.append(f'<circle cx="{x+22}" cy="{y-6}" r="4.6" fill="{c}" '
                 f'stroke="#ffffff" stroke-width="1.6"/>')
        s.append(f'<text x="{x+54}" y="{y}" font-size="26" fill="{INK}">{name}</text>')
        x += 210
s.append('</svg>')

svg = '\n'.join(s)
open('fig3.svg', 'w', encoding='utf-8').write(svg)

# 渲染为高分辨率 PNG（82 mm 宽 @ ~600 dpi）
PX = 1940
open('fig3.html', 'w', encoding='utf-8').write(
    '<!doctype html><meta charset="utf-8">'
    '<style>html,body{margin:0;padding:0;background:#fff}'
    f'svg{{width:{PX}px;height:{PX}px;display:block}}</style>' + svg)
chrome = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-sandbox',
                '--hide-scrollbars', '--force-device-scale-factor=1',
                f'--window-size={PX},{PX}', '--virtual-time-budget=6000',
                '--screenshot=fig3.png', f'file://{os.path.abspath("fig3.html")}'],
               check=True, capture_output=True)
mode = '带数据雷达图' if legend else '维度体系图（无数据）'
print(f'已生成 fig3.png / fig3.svg —— {mode}，{PX}×{PX} px')
