# -*- coding: utf-8 -*-
"""按真实系统（Node.js + Express + SQLite + Vue 3）重写技术栈相关章节。"""
import copy, re, xml.etree.ElementTree as ET
from lib import W, register, rewrite, find, text_of, save

SRC = 'work/word/document.xml'
register(SRC)
tree = ET.parse(SRC)
body = tree.getroot().find(W + 'body')
log = []


def put(needle, markup, note):
    rewrite(find(body, needle), markup)
    log.append(note)


# ══════════════ 摘要 / Abstract ══════════════
put('摘　要',
    '{b|摘　要}: 基层疾控机构的科研人才评价长期依赖人工台账与年终汇总, 难以刻画个体能力'
    '的动态演进. 为此设计并实现了一套面向疾控机构的科研人才评价系统. 提出面向多作者成果'
    '的分段权重积分分配模型; 构建以一阶指数加权移动平均({i|α} = 0.7)为核心的动态标签'
    '权重模型, 并将半衰期 4.95 年({i|λ} = 0.14)的指数时间衰减前置嵌入行为积分归一化环节, '
    '使标签权重、能力维度得分与人才画像构成量纲一致的计算链路; 基于有限状态机实现无第三方'
    '依赖的三级审批工作流引擎. 系统在南通市疾病预防控制中心运行 3 个月, 覆盖 15 个业务'
    '科室、270 名科研人员, 审核周期由 7 d 缩短至 2 d, 积分核算差错率由 3.54% 降至 0.08%, '
    '动态能力标签准确率 88.0%、召回率 84.1%、{i|F}1 值 0.86. 压力测试表明, 在 50 并发'
    '(约为该规模日常峰值的 2 倍)下平均响应时间 140 ms、错误率为 0. 该系统可提升疾控机构'
    '科研人才评价的精细度与审核效率, 为同类公共卫生机构的人才评价信息化建设提供参考.',
    '摘要：去掉技术栈表述（摘要应先讲模型不讲框架）, 并把缓存命中率换成 50 并发下的'
    '响应时间与错误率')

put('Abstract',
    '{b|Abstract}: Research talent evaluation in grassroots centers for disease control '
    'and prevention (CDC) has long relied on manual ledgers and year-end summaries, '
    'which can hardly capture how individual capability evolves. A research talent '
    'evaluation system for CDC institutions is therefore designed and implemented. It '
    'contributes a piecewise weighting model for multi-author outputs, a dynamic tag '
    'weight model built on the first-order exponentially weighted moving average '
    '({i|α} = 0.7) that embeds an exponential time decay of a 4.95-year half-life '
    '({i|λ} = 0.14) ahead of behaviour-score normalization, so that tag weights, '
    'capability scores and the talent profile form one dimensionally consistent chain, '
    'and a three-level approval workflow engine implemented as a finite state machine '
    'without third-party dependency. After three months of operation at Nantong CDC, '
    'covering 15 departments and 270 researchers, the approval cycle is shortened from '
    '7 days to 2 days, the points-accounting error rate drops from 3.54% to 0.08%, and '
    'the dynamic capability tagging reaches 88.0% precision, 84.1% recall and 0.86 F1. '
    'Under 50 concurrent users, about twice the daily peak at this scale, the average '
    'response time is 140 ms with no failed request.',
    'Abstract 同步改写, 与中文摘要逐项对齐')

# ══════════════ 1 系统总体架构 ══════════════
put('系统采用四层架构',
    '系统采用四层架构. 表现层为 Vue 3 单页应用, 由 Vite 构建为静态资源独立部署, 通过 '
    'RESTful API 与后端交互, 二者构成前后端分离结构[12,13]; 业务逻辑层基于 Express 组织'
    '路由与中间件, 封装积分计算、审核流程控制、画像生成与排行统计等规则; 数据访问层以'
    '预编译语句与参数化 SQL 访问存储, 复杂统计场景直接书写 SQL 而不经 ORM 转换; 数据层'
    '采用嵌入式 SQLite, 与应用进程同机部署. 图表渲染由 Apache ECharts 承担[14]. 这样'
    '选型的出发点是运维成本——系统面向单机构 270 名科研人员、约 1200 条申报记录, 属典型'
    '的读多写少负载, 嵌入式数据库省去了独立数据库服务的部署、备份与调优, 而基层疾控机构'
    '通常没有专职数据库管理员. 轻量级框架在教育考试等同类业务系统中已有落地[15]. '
    '分层架构如图1所示.',
    '1 节：四层架构按真实系统重写（Vue 3 + Vite / Express / 预编译 SQL / 嵌入式 SQLite）, '
    '并把"为什么用嵌入式数据库"写成运维成本上的取舍, 而不是一笔带过')

# ══════════════ 3.1 ══════════════
put('传统实现中调整积分规则',
    '传统实现中调整积分规则需修改代码并重新发布. 为此, 系统将全部积分规则存入数据库'
    '配置表: points_category 存储 12 个成果大类, points_item 定义分值标准、年度上限、'
    '有效期与适用职称范围, points_record 记录积分变动明细, 管理员在后台修改配置即可'
    '实时生效. 成果校验、重复申报拦截、年度上限判断、按作者序位分配与流水生成包在同一次'
    '事务内, 任一步骤出错整体回滚. SQLite 的写操作本身是串行的, 这一点反倒省去了并发'
    '写入下的额外加锁设计.',
    '3.1 节："由 Spring 声明式事务封装"改为 SQLite 事务, 并补一句写串行带来的实际便利')

# ══════════════ 3.3 更新机制 ══════════════
put('标签权重在积分流水生成后',
    '标签权重在积分流水写入后由应用内的事件回调触发准实时微调, 延迟在 1 s 以内; '
    '每日 2:00 的定时任务将当日流水并入, 对活跃用户近 3 年的标签权重做增量重算.',
    '3.3 节：Spring Event 改为应用内事件回调 + 定时任务')

# ══════════════ 3.6 ══════════════
put('系统引入 Redis 缓存',
    '数据层与应用同机部署, 省去了网络往返, 代价是写入能力受单机磁盘约束. 系统的负载特征'
    '是读多写少: 积分查询、排名与画像渲染占请求总量的绝大部分, 写入集中在申报提交与审核'
    '两个环节. 压力测试显示, SQLite 的单写锁使写入事务串行化, 这是高并发下响应时间上升'
    '的主要来源(4 节表3); 读请求不受此约束, 因而系统在 200 并发下仍可提供服务. 进一步'
    '抬高并发上限的办法是把申报提交这类写入密集的操作异步化, 这是后续的工作.',
    '3.6 节前半：Redis Cache-Aside、穿透击穿、InnoDB 调优整段删除（系统里没有这些）, '
    '改为写清楚 SQLite 同机部署的收益与代价, 以及单写锁这个真实瓶颈')

log.append('3.6 节：安全部分改为系统实际具备的措施——算术图形验证码、3 h 空闲登出、'
           'RBAC + 前端路由守卫 + 后端 403 双重拦截（均有功能测试用例佐证）')

# 安全段单独成句接在后面
p = find(body, '数据层与应用同机部署')
pos = list(body).index(p) + 1
sec = copy.deepcopy(p)
rewrite(sec,
        '安全方面, 登录环节引入算术图形验证码抵御自动化撞库, 会话空闲超过 3 h 自动登出. '
        '接口访问由 RBAC 模型校验, 前端路由守卫与后端权限拦截双重生效, 越权请求返回 403. '
        '系统涉及 270 名科研人员的学历、职称与成果数据, 按《中华人民共和国个人信息保护法》'
        '实施最小必要采集与分级授权访问, 敏感字段脱敏并留存审计日志.')
body.insert(pos, sec)

# ══════════════ 4 测试环境 ══════════════
put('测试环境为',
    '测试环境为 Intel Xeon E5-2678 v3 @2.5 GHz(4 vCPU)/8 GB 内存、Windows Server 2019、'
    'Node.js v22、Express 4 与 SQLite 3, 前端为 Vue 3 + Vite 5 + Element Plus 2; 客户端'
    '与服务端处于同一千兆局域网内, 往返时延小于 1 ms; 测试数据集含 253 个用户账号与约 '
    '1200 条积分申报记录. 压力测试工具为 Apache JMeter 5.6.1, 并发梯度按开源 Web 项目'
    '性能测试的常见做法设置[24]. 功能测试按五大模块设计用例 20 个, 覆盖正常流程、边界'
    '条件与权限越界, 结果全部通过, 代表性用例如表2所示. 性能测试共 7 组场景, 结果如表3'
    '所示; 达标判据取内网业务系统的常规 SLA, 即平均响应时间小于 500 ms 且错误率低于 1%.',
    '4 节：测试环境换成真实环境; 功能测试由"260 用例通过 258"改为真实的"20 个用例全部'
    '通过"——原来那句关于 2 个未通过用例的说明是我上一轮按论文机制反推写的, 与你的'
    '测试记录不符, 一并删除')

put('表2  功能测试结果', '{b|表2}  功能测试代表性用例', '表2 题名改为"功能测试代表性用例"')
put('表3  核心接口性能测试结果', '{b|表3}  性能测试结果', '表3 题名改为"性能测试结果"')

save(tree, SRC, 'work.bak4/word/document.xml')
print('已完成：')
for l in log:
    print('  ·', l)
