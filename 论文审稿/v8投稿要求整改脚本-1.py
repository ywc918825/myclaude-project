# -*- coding: utf-8 -*-
"""按《微型电脑应用》编辑部 6 条投稿要求改稿：
   ① 篇幅压缩 ② 邮寄信息 ③ 作者简介格式 ④ 二级单位中英文
   ⑤ 文献标志码 ⑥ 参考文献 16 → 10 并重排文中标注
"""
import copy, re, xml.etree.ElementTree as ET

SRC = 'work/word/document.xml'
raw = open(SRC, encoding='utf-8').read()
for pfx, uri in dict(re.findall(r'xmlns:(\w+)="([^"]+)"', raw)).items():
    if not re.fullmatch(r'ns\d*', pfx):
        ET.register_namespace(pfx, uri)
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XS = '{http://www.w3.org/XML/1998/namespace}space'

tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []

# CT_RPr 中子元素的合法顺序（只列用得到的部分）
RPR_ORDER = ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps',
             'strike', 'dstrike', 'outline', 'shadow', 'emboss', 'imprint',
             'noProof', 'snapToGrid', 'vanish', 'webHidden', 'color', 'spacing',
             'w', 'kern', 'position', 'sz', 'szCs', 'highlight', 'u', 'effect',
             'bdr', 'shd', 'fitText', 'vertAlign', 'rtl', 'cs', 'em', 'lang']


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
    """从段落自身取各种格式的 rPr 模板，缺什么就在纯文本模板上补什么。"""
    plain = None
    got = {}
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
        for k in kinds:
            if len(kinds) == 1 and k not in got:
                got[k] = rpr
    if plain is None:                       # 没有纯文本 run，就从任意 run 剥出来
        any_rpr = next((r.find(W + 'rPr') for r in p.findall(W + 'r')
                        if r.find(W + 'rPr') is not None), None)
        plain = copy.deepcopy(any_rpr) if any_rpr is not None else ET.Element(W + 'rPr')
        for c in list(plain):
            if c.tag.replace(W, '') in ('i', 'b', 'vertAlign', 'highlight'):
                plain.remove(c)
    out = {'-': plain}
    for key, tag, val in (('b', 'b', None), ('i', 'i', None),
                          ('sub', 'vertAlign', 'subscript'),
                          ('sup', 'vertAlign', 'superscript'),
                          ('hl', 'highlight', 'yellow')):
        src = got.get(key if key not in ('sub', 'sup') else
                      ('subscript' if key == 'sub' else 'superscript'))
        if src is None and key == 'hl':
            src = got.get('highlight')
        if src is not None:
            out[key] = src
        else:
            r = copy.deepcopy(plain)
            out[key] = set_prop(r, tag, val)
    return out


TOK = re.compile(r'\{(b|i|sub|sup|hl)\|([^{}]*)\}')


def rewrite(p, markup):
    """用小标记语言重排段落，保留 pPr 与原有字体格式。"""
    tpl = templates(p)
    for r in list(p):
        if r.tag in (W + 'r', W + 'hyperlink', W + 'bookmarkStart', W + 'bookmarkEnd'):
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
    return True


def text_of(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


K = list(body)


def P(i):
    return K[i]


# ══════════════════════════════════════════════════════════════════════
# 一、篇首：署名、二级单位（中英文）、文献标志码
# ══════════════════════════════════════════════════════════════════════
rewrite(P(2), '杨文超，张卫兵，练维，徐小卫，王秦')
rewrite(P(3), '（南通市疾病预防控制中心 {hl|科研与质量管理科}，江苏 南通 226001）')
rewrite(P(6), '({hl|Division of Research and Quality Management}, Nantong Center for '
              'Disease Control and Prevention, Nantong 226001, Jiangsu, China)')
log.append('④ 单位补二级单位（中英文各一处，黄色高亮待你确认）；署名标点改全角')

rewrite(P(9), '{b|中图分类号：}TP311.5　　{b|文献标志码：}A')
log.append('⑤ “文献标识码”改为编辑部用语“文献标志码”')

# ══════════════════════════════════════════════════════════════════════
# 二、中英文摘要压缩
# ══════════════════════════════════════════════════════════════════════
rewrite(P(7),
        '{b|摘要：}针对疾控机构科研人才评价精细化程度不足的问题，设计并实现了基于 '
        'Spring Boot 与 MyBatis 的科研积分管理系统。提出面向多作者成果的分段权重积分'
        '分配模型；构建基于一阶指数加权移动平均（{i|α} = 0.7）的动态标签权重模型，'
        '将半衰期 4.95 年（{i|λ} = 0.14）的指数时间衰减前置嵌入行为积分归一化环节，'
        '使标签权重、能力维度得分与人才画像构成量纲一致的计算链路；基于有限状态机实现'
        '无第三方依赖的四级审批工作流引擎。系统在南通市疾病预防控制中心运行 3 个月，'
        '覆盖 15 个业务科室、270 名科研人员，审核周期由平均 7 天缩短至 2 天，积分核算'
        '差错率由 3.54% 降至 0.08%，可为同类公共卫生机构的科研管理信息化提供参考。')

rewrite(P(10),
        '{b|Abstract: }To improve the granularity of research talent evaluation in '
        'centers for disease control and prevention (CDC), a research points '
        'management system based on Spring Boot and MyBatis is designed and '
        'implemented. A piecewise weighting model allocates points among the multiple '
        'authors of an output. A dynamic tag weight model based on a first-order '
        'exponentially weighted moving average (α = 0.7) embeds an exponential time '
        'decay (half-life 4.95 years, λ = 0.14) ahead of behaviour-score '
        'normalization, so that tag weights, capability dimension scores and the '
        'talent profile form a dimensionally consistent computation chain. A '
        'four-level approval workflow engine is implemented as a finite state machine '
        'without third-party dependency. Over three months at Nantong CDC, covering '
        '15 divisions and 270 researchers, the average approval cycle fell from 7 days '
        'to 2 days and the points-accounting error rate from 3.54% to 0.08%.')
log.append('① 中文摘要 380 → 约 290 字符，英文摘要 1409 → 约 900 字符'
           '（同时删去与表 3 口径不一致的“平均响应时间 68 ms”）')

# ══════════════════════════════════════════════════════════════════════
# 三、正文压缩 + 引用重排
# ══════════════════════════════════════════════════════════════════════
rewrite(P(13),
        '在“科教兴卫、人才强卫”战略指引下，各级疾病预防控制机构日益重视科研能力建设，'
        '但基层疾控机构的科研人才评价仍存在方式粗放、“四唯”倾向明显、缺少动态量化手段'
        '等问题[1-2]，难以支撑科研梯队建设与精准激励。')

rewrite(P(14),
        '李涛等[1]、沈杨阳[2]与 Amaral 等[3]分别从指标体系、组织机制与经费分配角度'
        '探讨了科研评价，但评价对象均为机构而非个人；Lei[4]面向“破五唯”的分类绩效'
        '指标体系与本文思路接近，但其指标构成与疾控机构以公共卫生服务、现场流行病学'
        '调查为主的产出结构差异较大；罗仕鉴等[7]与白菁昊等[8]验证了用户画像与动态标签'
        '方法的有效性，但均未考虑科研成果的长周期性与时效衰减。为此，本文提出面向多作者'
        '成果的分段权重积分分配模型，构建“指数加权移动平均标签权重 + 指数时间衰减”的'
        '动态画像模型，并实现无第三方框架依赖的状态机工作流与可配置积分规则引擎。')

rewrite(P(16),
        '系统采用四层架构：表现层由 Spring Boot 的 @RestController 接收 HTTP 请求并'
        '调用业务服务，实现前后端分离[5]；业务逻辑层封装积分计算、审核流程控制、画像'
        '生成与排行统计等规则并管理事务；数据访问层通过 MyBatis 的 Mapper 接口与 XML '
        '映射文件实现对象关系映射，可在复杂场景下直接优化 SQL；数据层负责持久化与存储'
        '管理。前端采用 Vue.js，通过 RESTful API 与后端交互；数据库选用 MySQL 8.0，'
        '并引入 Redis 缓存提升查询效率[5-6]。分层架构如图 1 所示。')

rewrite(P(20),
        '系统设计了五大功能模块，构成申报、计算、画像、展示、权限的完整闭环。积分管理'
        '模块支持可视化配置 12 大类 46 项积分规则，成果提交后由计算引擎自动校验、核算'
        '分值并生成积分流水；人才画像模块构建涵盖结构化标签（学历、职称、专业）与'
        '非结构化能力标签（科研能力、项目管理、数据分析）的动态标签体系[7-8]；统计分析'
        '模块的“人才晴雨表”仪表盘集成 Apache ECharts，支持多维交叉统计与数据下钻；'
        '申报审核模块内置轻量级工作流引擎驱动四级审批；系统管理模块采用 RBAC 模型构建'
        '用户—角色—权限三层架构[9]，并承担基础数据维护、规则调整与操作日志审计等职能。')

rewrite(P(23),
        '传统实现中调整积分规则需修改代码并重新发布。为此，系统将全部积分规则存入数据库'
        '配置表：points_category 存储 12 个成果大类，points_item 定义分值标准、年度上限、'
        '有效期与适用职称范围，points_record 记录积分变动明细，管理员在后台修改配置即可'
        '实时生效。为确保数据一致性，成果校验、重复申报拦截、年度上限判断、按作者序位'
        '分配、总积分更新与流水生成由 Spring 声明式事务封装在同一事务中，任一步骤出错'
        '即回滚。')

rewrite(P(25),
        '本文采用基于 Kronecker δ 函数的分段权重模型统一刻画作者序位与分配系数的映射'
        '关系，如式(1)、式(2)所示。')

rewrite(P(28),
        '式中：{i|S}{sub|i} 为第 {i|i} 作者获得的积分；{i|S}{sub|total} 为成果标准积分；'
        '{i|n} 为作者总数。第 1、2、3 作者的分配系数分别为 1.0、0.8、0.5，第 4 作者及'
        '以后按 0.2 计；通讯作者按第 1 作者计，共同第一作者按并列第 1 作者计。')

rewrite(P(29),
        '式(1)采用{b|名义分值制}而非总量守恒制，即各作者所得之和可能大于成果标准积分'
        '（4 位作者时为 2.5 倍），以契合疾控机构鼓励多科室协作攻关的导向；其“挂名”风险'
        '由 points_item 表的年度上限封顶与第 4 作者及以后积分不计入职称评审口径两项制度'
        '约束控制。与常见守恒型方法的对比如表 1 所示；对需控制积分总量的场景，系统另'
        '提供可配置的归一化模式（式(3)）。')

rewrite(P(35),
        '系统构建了基础属性、能力维度与专业方向三维标签体系[8]。考虑到科研贡献的时效性，'
        '本文将指数时间衰减因子前置嵌入行为积分归一化环节（式(4)），标签权重在此基础上'
        '按一阶指数加权移动平均更新（式(5)）。')

rewrite(P(38),
        '式中：{i|W}{sup|(k)}{sub|t,u} 为用户 {i|u} 在标签 {i|t} 上第 {i|k} 个周期的'
        '权重；{i|s}{sub|i,u} 为其在行为 {i|i} 上的原始积分；{i|S}{sub|max,t} 为本周期'
        '全中心在标签 {i|t} 下的最高行为积分，用于将行为项归一化至 [0, 1]；{i|w}{sub|i} '
        '为行为 {i|i} 的贡献系数，满足 Σ{i|w}{sub|i} = 1；{i|t}{sub|now} 与 {i|t}{sub|i} '
        '分别为当前时间与成果完成时间。')

rewrite(P(39),
        '式(5)中 {i|α} 取 0.7，对应记忆长度 1/(1 − {i|α}) ≈ 3.3 个周期，即最新一年贡献'
        '约占 70%、历史累积约占 30%，既突出近期活跃度也保留资深人员的积累；时间衰减系数'
        '取 {i|λ} = 0.14，对应半衰期 ln2{i|/λ} ≈ 4.95 年、年衰减约 13.1%，可避免成果'
        '永久有效导致评价僵化，也防止衰减过快挫伤长期积累型科研人员的积极性。')

rewrite(P(40),
        '标签更新采用双策略：积分流水生成后 1 s 内由 Spring Event 触发准实时微调；'
        '每日 2:00 全量重算活跃用户近一年的标签权重，并清理权重低于 0.1 的标签。')

rewrite(P(42),
        '定义标签—能力维度映射矩阵 {i|M} ∈ R{sup|T×D}，{i|T} 为标签总数，{i|D} 为能力'
        '维度数（本系统取 {i|D} = 16，各维度名称如图 2 所示）。矩阵元素 {i|m}{sub|t,d} '
        '∈ [0, 1] 表示标签 {i|t} 对维度 {i|d} 的贡献度，满足 Σ{sub|d}{i|m}{sub|t,d} = 1，'
        '由 3 名科研管理专家按德尔菲法两轮打分确定。用户在各维度上的原始得分为所有标签'
        '权重的加权和（式(6)）。由于式(5)已在行为积分层面完成时间衰减修正，式(6)无需'
        '再次引入衰减因子。')

rewrite(P(46),
        '式中：{i|C}{sub|d,min} 与 {i|C}{sub|d,max} 分别为全中心用户在维度 {i|d} 上的'
        '最低与最高原始得分。结果映射至 [20, 100] 而非 [0, 100]，以避免最低分用户恒为 0、'
        '雷达图退化为尖刺；当 {i|C}{sub|d,max} = {i|C}{sub|d,min} 时取 {i|C}′{sub|d,u} '
        '= 60，避免分母为零。式(7)适用于同一周期内的横向比较，跨年度比较时以上线首年的'
        '分布为固定基准。归一化得分直接对应雷达图半径。')

rewrite(P(50),
        '针对疾控中心审核流程相对固定但存在微调需求的特点，本文实现了无第三方框架依赖的'
        '状态机工作流引擎。引擎定义草稿、待初审、初审驳回、待复核、复核驳回、待终审与'
        '终审通过 7 种状态及 7 种转换事件：草稿经提交进入待初审，初审、复核通过后依次'
        '进入待复核、待终审，任一环节驳回则回退至对应驳回态，修改后重新提交。各状态的'
        '处理人、处理时限与下一状态由 workflow_config 表配置；事件触发时引擎依次校验'
        '权限、更新状态、记录日志并通知下一处理人，终审通过时触发积分计算。管理员修改'
        '配置即可调整审核环节，无需重启系统。')

rewrite(P(52),
        '系统引入 Redis 缓存应对高频积分查询，采用 Cache-Aside 模式并以空值缓存与'
        '分布式锁分别防止缓存穿透与击穿，实测缓存命中率在 50～500 并发下保持在 92.5% '
        '以上（表 3）；数据库层面针对核心查询路径建立联合索引并优化 InnoDB 配置。安全'
        '方面整合 Spring Security 与 JWT 实现无状态认证[10]；系统涉及 270 名科研人员的'
        '学历、职称与成果数据，均按《中华人民共和国个人信息保护法》实施最小必要采集与'
        '分级授权访问，敏感字段脱敏并留存审计日志。')

rewrite(P(54),
        '测试环境为 4 核 CPU / 32 GB 内存、Ubuntu 24.04 LTS、OpenJDK 21、MySQL 8.0 与 '
        'Redis 7.2，压力测试工具为 Apache JMeter。功能测试用例按五大模块设计，覆盖'
        '正常流程、边界条件与异常输入，结果如表 2 所示；核心接口性能与缓存命中率'
        '如表 3 所示。')

rewrite(P(59),
        '为评价标签准确性，从 270 名科研人员中随机抽取 90 名，由 3 名科研管理专家依据其'
        '近三年科研档案独立标注，以三人一致的结果为金标准与系统输出比对。系统共生成 32 '
        '个动态能力标签，准确率 88.0%、召回率 84.1%、{i|F}1 值 0.86，专家标注 Kappa '
        '系数 0.81。上线前后各 3 个月的应用效果对比如表 4 所示。')

rewrite(P(64),
        '由表 4 可见，系统上线后申报与审核实现全流程线上化，申报单量增至上线前的 7.4 倍，'
        '平均审核周期由 7 d 降至 2 d，科研人员的参与度明显提升。')

rewrite(P(66),
        '本文设计并实现了基于 Spring Boot 与 MyBatis 的疾控科研积分管理系统：针对多作者'
        '成果提出分段权重分配模型并与守恒型方法作了对比；将指数时间衰减前置于行为积分'
        '归一化环节，使标签权重、能力维度得分与人才画像形成量纲一致的计算链路；基于'
        '有限状态机实现了无第三方依赖的审批工作流引擎。系统运行期间审核周期与积分核算'
        '差错显著下降。后续将开展 {i|α}、{i|λ} 的敏感性分析，并与人事、财务等系统实现'
        '数据互通。')
log.append('① 正文逐段精简（引言、2～4.6 各节、第 5 章、结论），技术内容与公式、'
           '图表全部保留')

# ══════════════════════════════════════════════════════════════════════
# 四、参考文献 16 → 10
# ══════════════════════════════════════════════════════════════════════
DROP = [5, 7, 12, 13, 15, 16]          # 原编号
KEEP = [1, 2, 3, 4, 6, 8, 9, 10, 11, 14]
refs = {}
for p in list(body):
    if p.tag != W + 'p':
        continue
    m = re.match(r'\[(\d+)\]', text_of(p).strip())
    if m:
        refs[int(m.group(1))] = p
for n in DROP:
    body.remove(refs[n])
for new, old in enumerate(KEEP, 1):
    p = refs[old]
    s = text_of(p)
    rewrite(p, re.sub(r'^\[\d+\]', '[%d]' % new, s.strip()))
log.append('⑥ 参考文献 16 → 10 条（删去原 [5][7][12][13][15][16]，'
           '均为与本文关联较弱或可由其他文献覆盖者），其余顺次重编为 [1]～[10]，'
           '文中标注同步改写，10 条全部在文中出现、无悬空引用')

# ══════════════════════════════════════════════════════════════════════
# 五、作者简介按编辑部模板重排
# ══════════════════════════════════════════════════════════════════════
BIOS = [
    ('杨文超（1988—），男，硕士研究生{hl|（已毕业）}，高级工程师，'
     '主要研究方向为科研管理信息化、公共卫生数据分析。'),
    ('张卫兵（1971—），男，硕士研究生{hl|（已毕业）}，主任医师，'
     '主要研究方向为科研管理、预防医学、食品检测。'),
    ('练维（1980—），男，本科{hl|（已毕业）}，主任技师，'
     '主要研究方向为科研教育、质量管理。'),
    ('徐小卫（1989—），男，本科{hl|（已毕业）}，高级工程师，'
     '主要研究方向为软件开发、数据管理。'),
    ('王秦（1984—），女，本科{hl|（已毕业）}，副主任医师，'
     '主要研究方向为科研教育、数据统计。'),
]
bio_ps = []
for p in list(body):
    if p.tag != W + 'p':
        continue
    s = text_of(p)
    if s.startswith('作者简介') or re.match(r'^[\s　]*(张卫兵|练维|徐小卫|王秦)（', s):
        bio_ps.append(p)
assert len(bio_ps) == 5, len(bio_ps)
rewrite(bio_ps[0], '{b|作者简介}：' + BIOS[0])
for p, s in zip(bio_ps[1:], BIOS[1:]):
    rewrite(p, s)
log.append('③ 5 位作者简介统一为“姓名（出生年—），性别，最高学历学位，职称，研究方向”'
           '模板，并补“（已毕业）”（黄色高亮待你确认在读/已毕业）')

# ══════════════════════════════════════════════════════════════════════
# 六、末尾追加邮寄信息
# ══════════════════════════════════════════════════════════════════════
last = bio_ps[-1]
pos = list(body).index(last) + 1
for s in ['{b|通信地址}：江苏省南通市{hl|××区××路××号} 南通市疾病预防控制中心　'
          '{b|邮编}：226001',
          '{b|收件人}：杨文超　{b|联系电话}：{hl|×××××××××××}　'
          '{b|E-mail}：{hl|××××××@××.com}']:
    np = copy.deepcopy(last)
    rewrite(np, s)
    body.insert(pos, np)
    pos += 1
log.append('② 文末补“通信地址／邮编／收件人／联系电话／E-mail”一栏，'
           '具体内容黄色高亮待你填写')

tree.write(SRC, encoding='UTF-8', xml_declaration=True)

# 还原根标签命名空间
orig = re.search(r'<w:document\b[^>]*>',
                 open('../v8/unz/word/document.xml', encoding='utf-8').read()).group(0)
s = open(SRC, encoding='utf-8').read()
cur = re.search(r'<w:document\b[^>]*>', s).group(0)
have = set(re.findall(r'xmlns:(\w+)=', orig))
add = [f'xmlns:{k}="{v}"' for k, v in re.findall(r'xmlns:(\w+)="([^"]+)"', cur)
       if k not in have]
open(SRC, 'w', encoding='utf-8').write(
    s.replace(cur, orig[:-1] + (' ' + ' '.join(add) if add else '') + '>', 1))

print('已完成：')
for l in log:
    print('  ·', l)
