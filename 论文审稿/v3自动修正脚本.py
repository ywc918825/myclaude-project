# -*- coding: utf-8 -*-
"""对最新修改稿做 5 处可自动完成的修正。"""
import copy, re, xml.etree.ElementTree as ET

SRC = 'work/word/document.xml'
raw = open(SRC, encoding='utf-8').read()

# 保留原有命名空间前缀（含在 drawing 内部就地声明的 a / pic / a14）
for pfx, uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw)).items():
    if not re.fullmatch(r'ns\d*', pfx):
        ET.register_namespace(pfx, uri)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'

tree = ET.parse(SRC)
root = tree.getroot()
body = root.find(W + 'body')
kids = list(body)
log = []


def text_of(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


def set_single_text(p, s):
    """把段落压成一个 run，沿用原首个 run 的格式。"""
    runs = p.findall(W + 'r')
    keep = None
    for r in runs:
        if r.find(W + 't') is not None:
            keep = r
            break
    if keep is None:
        return False
    rpr = keep.find(W + 'rPr')
    for r in runs:
        p.remove(r)
    nr = ET.SubElement(p, W + 'r')
    if rpr is not None:
        nr.append(copy.deepcopy(rpr))
    t = ET.SubElement(nr, W + 't')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = s
    return True


XS = '{http://www.w3.org/XML/1998/namespace}space'


def patch_runs(marker, pairs):
    """数字与中文常被拆到不同 run，只能逐 run 精确替换。"""
    for p in body.iter(W + 'p'):
        if marker not in ''.join(t.text or '' for t in p.iter(W + 't')):
            continue
        ts = list(p.iter(W + 't'))
        n = 0
        for old, new in pairs:
            for t in ts:
                if t.text == old:
                    t.text = new
                    t.set(XS, 'preserve')
                    n += 1
                    break
        return n
    return 0


# ── A. 摘要漏字 ───────────────────────────────────────────────────────────
if patch_runs('缩短至', [
        ('缩短至 ', ' 天缩短至 '),
        ('天，积分核算人为差错率由 5% 降至 0，核心业务平均响应时间为 ',
         ' 天，积分核算人为差错率由 5% 降至 0，核心业务平均响应时间为 ')]):
    for p in body.iter(W + 'p'):
        for t in p.iter(W + 't'):
            if t.text and t.text.endswith('审核周期由平均'):
                t.text += ' '
                t.set(XS, 'preserve')
    log.append('A 摘要：补上漏掉的“天”，并统一数字前后空格')

# ── B. 引言加编号 ─────────────────────────────────────────────────────────
for p in body.iter(W + 'p'):
    if text_of(p).strip() == '引言':
        set_single_text(p, '1  引言')
        log.append('B 引言标题：加编号 → "1  引言"')
        break

# ── C. 引言正文：恢复研究现状梳理与贡献列举 ───────────────────────────────
INTRO = [
    '在“科教兴卫、人才强卫”战略指引下，各级疾病预防控制机构日益重视科研能力建设，'
    '但基层疾控机构的科研人才评价仍存在方式粗放、“四唯”倾向明显、缺少动态量化手段等'
    '问题[1-2]，难以支撑科研梯队建设与精准激励。',
    '科研评价量化方面，李涛等[1]、沈杨阳[2]与 Amaral 等[3]分别从指标体系、组织机制与'
    '经费分配角度作了探讨，但评价对象均为机构而非个人；Lei[4]面向“破五唯”设计的高校'
    '教师分类绩效指标体系与本文思路接近，但其指标构成与疾控机构以公共卫生服务、现场'
    '流行病学调查为主的产出结构差异较大。人才画像方面，罗仕鉴等[9]与白菁昊等[10]验证了'
    '动态标签刻画能力演进的有效性，但其权重更新机制面向消费与学习行为，未考虑科研成果的'
    '长周期性与时效衰减特征。系统实现方面，刘盛等[6]与张岩[8]验证了 Spring Boot 技术栈在'
    '卫生行业的适用性，但功能定位偏向业务数据管理，未涉及评价的量化建模。',
    '可见，面向公共卫生领域、同时整合积分量化与人才标签画像的专用科研管理系统仍比较少见。'
    '本文的主要工作如下：① 提出面向多作者成果的分段权重积分分配模型，给出其与均分法、'
    '调和计数法的对比及在积分总量口径上的制度性约束；② 构建“指数加权移动平均标签权重 + '
    '指数时间衰减”的动态画像模型，将时间衰减前置于行为积分归一化环节，使标签权重、能力'
    '维度得分与可视化画像构成量纲一致的统一计算链路；③ 实现无第三方框架依赖的状态机'
    '工作流引擎与可配置积分规则引擎，支持审核环节与积分规则的免发布调整。系统面向的'
    '南通市疾控中心设有 15 个业务科室、270 名科研人员，科研成果涵盖论文、专利、技术标准等 '
    '12 个大类，核心业务响应时间要求控制在 3 s 以内。',
]
for idx, p in enumerate(list(body)):
    if p.tag == W + 'p' and '科教兴卫' in text_of(p) and '战略' in text_of(p):
        pos = list(body).index(p)
        set_single_text(p, INTRO[0])
        for k, s in enumerate(INTRO[1:], 1):
            np = copy.deepcopy(p)
            set_single_text(np, s)
            body.insert(pos + k, np)
        log.append('C 引言正文：补首字"在"、修正成对右引号，'
                   '并恢复三类研究现状梳理与三条贡献列举（243 → 约 560 字）')
        break

# ── D. 图 1 改为嵌入式、单独成段；删除其后的空段落 ────────────────────────
kids = list(body)
for i, p in enumerate(kids):
    if p.tag != W + 'p' or not list(p.iter(W + 'drawing')):
        continue
    if not text_of(p).strip():
        continue                      # 已经是单独成段的图（图 2）
    drawing_run = None
    for r in p.findall(W + 'r'):
        if list(r.iter(W + 'drawing')):
            drawing_run = r
            break
    if drawing_run is None:
        continue
    p.remove(drawing_run)

    # anchor（浮动）→ inline（嵌入）
    frag = ET.tostring(drawing_run, encoding='unicode')
    if '<wp:anchor' in frag:
        frag = re.sub(r'<wp:anchor[^>]*>', '<wp:inline distT="0" distB="0" '
                      'distL="0" distR="0">', frag)
        frag = frag.replace('</wp:anchor>', '</wp:inline>')
        for tag in ('wp:simplePos', 'wp:wrapNone'):
            frag = re.sub(rf'<{tag}[^>]*/>', '', frag)
        for tag in ('wp:positionH', 'wp:positionV'):
            frag = re.sub(rf'<{tag}.*?</{tag}>', '', frag, flags=re.S)
        frag = re.sub(r'\s(wp14:anchorId|wp14:editId)="[^"]*"', '', frag)
    new_run = ET.fromstring(frag)

    fig_p = ET.Element(W + 'p')
    ppr = ET.SubElement(fig_p, W + 'pPr')
    ET.SubElement(ppr, W + 'keepNext')
    jc = ET.SubElement(ppr, W + 'jc'); jc.set(W + 'val', 'center')
    fig_p.append(new_run)
    body.insert(list(body).index(p) + 1, fig_p)
    log.append('D 图 1：由浮动(环绕)改为嵌入式并单独居中成段，'
               '移到介绍它的正文之后、图题之前')
    break

# 删除图后到图题之间的空段落
kids = list(body)
removed = 0
for i, p in enumerate(kids):
    if p.tag != W + 'p':
        continue
    if text_of(p).strip() or list(p.iter(W + 'drawing')):
        continue
    nxt = next((q for q in kids[i + 1:] if q.tag == W + 'p'), None)
    if nxt is not None and text_of(nxt).strip().startswith('图 '):
        body.remove(p); removed += 1
    else:
        for q in kids[i + 1:]:
            if q.tag == W + 'p' and (text_of(q).strip() or list(q.iter(W + 'drawing'))):
                if text_of(q).strip().startswith('图 '):
                    body.remove(p); removed += 1
                break
if removed:
    log.append(f'D 删除图 1 与图题之间残留的 {removed} 个空段落')

# ── E. 图编号断号：图 3 → 图 2 ────────────────────────────────────────────
n_fix = 0
for t in body.iter(W + 't'):
    if not t.text:
        continue
    if '如图 3 所示' in t.text:
        t.text = t.text.replace('如图 3 所示', '如图 2 所示'); n_fix += 1
    if t.text.strip().startswith('图 3'):
        t.text = t.text.replace('图 3', '图 2', 1); n_fix += 1
if n_fix:
    log.append(f'E 图编号：图 3 → 图 2（正文引用与图题共 {n_fix} 处），消除断号')

# ── F. 测试环境写法规范化 ─────────────────────────────────────────────────
if patch_runs('测试环境为', [
        ('核 CPU / ', ' 核 CPU / '),
        ('G', 'GB'),
        ('内存、', ' 内存、'),
        ('ubuntu', 'Ubuntu '),
        ('OpenJDK', 'OpenJDK '),
        ('、MySQL 8.0 与 Redis', '、MySQL 8.0 与 Redis ')]):
    log.append('F 测试环境：规范软硬件名称与版本号写法'
               '（4 核 CPU / 500 GB 内存 / Ubuntu 24.04 LTS / OpenJDK 21 / Redis 7.2）')

tree.write(SRC, encoding='UTF-8', xml_declaration=True, method='xml')
print('已完成：')
for l in log:
    print('  ·', l)
