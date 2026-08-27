# -*- coding: utf-8 -*-
"""图 3 生成器 —— 16 维能力雷达图（高清重绘版）

维度顺序与名称、三条系列的取值均取自原系统界面截图，按原图几何反解得到。
要换成别的数据，直接改下面 SERIES 里的 16 个数（0–100），顺序对应 DIMS。
"""
import math, os, subprocess

# 维度顺序：正上方起顺时针，与原系统界面一致
DIMS = ['专利发明', '成果奖励', '成果转换', '出版著作',
        '工作文章', '技能资质', '技术标准', '继续教育',
        '荣誉表彰', '科普作品', '学科团队', '学术比赛',
        '学术地位', '学术交流', '项目课题', '发表论文']

# 三条系列（0–100）
SERIES = [
    ('个人得分',   [99, 34, 34, 34, 34, 34, 91, 42,
                    100, 35, 44, 99, 35, 34, 97, 99],
     '#2d3282', 'none', 2.8),
    ('科室平均',   [58, 59, 49, 43, 59, 54, 47, 66,
                    63, 53, 58, 44, 49, 56, 53, 64],
     '#3a8f3a', '9 6', 2.4),
    ('全中心优秀', [93, 90, 81, 74, 86, 80, 81, 85,
                    93, 77, 85, 79, 82, 85, 88, 94],
     '#ef8a30', '2 6', 2.4),
]

VB = 930
CX = CY = VB / 2
R_MAX = 300
RINGS = [60, 120, 180, 240, 300]          # 20 / 40 / 60 / 80 / 100
TICKS = ['20', '40', '60', '80', '100']
R_LABEL = 352
INK, INK2, GRID, GRID2 = '#1b1b1b', '#5b6270', '#d3d7de', '#e8eaef'
FONT = "'WenQuanYi Zen Hei','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
N = len(DIMS)
STEP = 360 / N


def pt(ang, r):
    a = math.radians(ang)
    return CX + r * math.sin(a), CY - r * math.cos(a)


def poly(r):
    return ' '.join('%.2f,%.2f' % pt(i * STEP, r) for i in range(N))


s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB} {VB}" '
     f'width="{VB}" height="{VB}" font-family="{FONT}">',
     f'<rect width="{VB}" height="{VB}" fill="#ffffff"/>']

# 交替环带底色，便于读半径
for i in range(len(RINGS) - 1, 0, -1):
    if i % 2:
        s.append(f'<polygon points="{poly(RINGS[i])}" fill="{GRID2}" fill-opacity="0.45"/>')
        s.append(f'<polygon points="{poly(RINGS[i-1])}" fill="#ffffff"/>')

# 网格与轴
for r in RINGS:
    s.append(f'<polygon points="{poly(r)}" fill="none" stroke="{GRID}" stroke-width="1.2"/>')
for i in range(N):
    x, y = pt(i * STEP, R_MAX)
    s.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.2f}" y2="{y:.2f}" '
             f'stroke="{GRID}" stroke-width="1.1"/>')

# 数据系列
for name, vals, color, dash, wid in SERIES:
    pts = ['%.2f,%.2f' % pt(i * STEP, max(0.0, min(100.0, v)) / 100 * R_MAX)
           for i, v in enumerate(vals)]
    s.append(f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.09" '
             f'stroke="{color}" stroke-width="{wid}" stroke-dasharray="{dash}" '
             f'stroke-linejoin="round"/>')
for name, vals, color, dash, wid in SERIES:
    for i, v in enumerate(vals):
        x, y = pt(i * STEP, max(0.0, min(100.0, v)) / 100 * R_MAX)
        s.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.4" fill="{color}" '
                 f'stroke="#ffffff" stroke-width="1.5"/>')

# 半径刻度
for r, t in zip(RINGS, TICKS):
    s.append(f'<text x="{CX-8}" y="{CY-r+8}" text-anchor="end" font-size="21" '
             f'fill="{INK2}">{t}</text>')

# 维度标签：4 字排成 2×2 字块
for i, name in enumerate(DIMS):
    x, y = pt(i * STEP, R_LABEL)
    s.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" font-size="31" '
             f'fill="{INK}">'
             f'<tspan x="{x:.2f}" dy="-4">{name[:2]}</tspan>'
             f'<tspan x="{x:.2f}" dy="34">{name[2:]}</tspan></text>')

# 图例
y = VB - 14
w = 232
x = CX - (len(SERIES) * w) / 2 + 24
for name, vals, color, dash, wid in SERIES:
    s.append(f'<line x1="{x}" y1="{y-8}" x2="{x+48}" y2="{y-8}" stroke="{color}" '
             f'stroke-width="{wid}" stroke-dasharray="{dash}"/>')
    s.append(f'<circle cx="{x+24}" cy="{y-8}" r="4.4" fill="{color}" '
             f'stroke="#ffffff" stroke-width="1.5"/>')
    s.append(f'<text x="{x+60}" y="{y}" font-size="28" fill="{INK}">{name}</text>')
    x += w
s.append('</svg>')

svg = '\n'.join(s)
open('fig3.svg', 'w', encoding='utf-8').write(svg)

PX = 1940
open('fig3.html', 'w', encoding='utf-8').write(
    '<!doctype html><meta charset="utf-8">'
    '<style>html,body{margin:0;padding:0;background:#fff;overflow:hidden}'
    f'html,body{{height:{PX}px}}'
    f'svg{{width:{PX}px;height:{PX}px;display:block}}</style>' + svg)
subprocess.run(['/opt/pw-browsers/chromium-1194/chrome-linux/chrome', '--headless=new',
                '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                '--force-device-scale-factor=1', f'--window-size={PX},{PX + 300}',
                '--virtual-time-budget=6000', '--screenshot=fig3.png',
                f'file://{os.path.abspath("fig3.html")}'], check=True, capture_output=True)
# 无头截图的视口比窗口矮约 160 px，故窗口开高后再把底部空白裁掉
from pngcrop import crop_height
crop_height('fig3.png', 'fig3.png', PX)
print(f'已生成 fig3.png / fig3.svg —— {PX}×{PX} px')
