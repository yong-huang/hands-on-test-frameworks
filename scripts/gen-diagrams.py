#!/usr/bin/env python3
"""生成 29 份架构图图源 IR（labs 01-30，00 工具类实验不配图；调 Archify 技能校验并渲染）。

类型映射：workflow=过程流、sequence=交互时序、architecture=组件拓扑。
中文标注、showcase 质量档、节点 ≤ 12、一条主路径。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "labs"

META = {
    "quality_profile": "showcase",
    "locale": "zh-CN",
    "animation": "trace",
    "visual_preset": "signal-flow",
}


def wf(title, output, lanes, phases, nodes, edges, cards, main_path, views=None):
    return {
        "schema_version": 2, "diagram_type": "workflow",
        "meta": {**META, "title": title, "output": output},
        "lanes": lanes, "phases": phases, "mainPath": main_path,
        "nodes": nodes, "edges": edges, "cards": cards,
    }


def seq(title, output, participants, messages, cards, segments=None, activations=None, views=None):
    return {
        "schema_version": 1, "diagram_type": "sequence",
        "meta": {**META, "title": title, "output": output, "viewBox": [900, 900]},
        "participants": participants, "segments": segments or [],
        "messages": messages, "activations": activations or [], "cards": cards,
    }


def arch(title, output, components, connections, cards, boundaries=None, views=None):
    return {
        "schema_version": 1, "diagram_type": "architecture",
        "meta": {**META, "title": title, "output": output},
        "components": components, "boundaries": boundaries or [],
        "connections": connections, "cards": cards,
    }


def n(id_, lane, col, label, sub="", type_="backend", tag="", width=132):
    d = {"id": id_, "lane": lane, "col": col, "type": type_, "label": label, "width": width}
    if sub: d["sublabel"] = sub
    if tag: d["tag"] = tag
    return d


def e(id_, a, b, label="", variant="default"):
    d = {"id": id_, "from": a, "to": b, "variant": variant}
    if label: d["label"] = label
    return d


def c(id_, label, sub, type_, pos, size=(132, 60), tag=""):
    d = {"id": id_, "type": type_, "label": label, "sublabel": sub,
         "pos": list(pos), "size": list(size)}
    if tag: d["tag"] = tag
    return d


def m(a, b, y, label, variant="default"):
    return {"from": a, "to": b, "y": y, "label": label, "variant": variant}


def card(dot, title, items):
    return {"dot": dot, "title": title, "items": items}


SPECS = {}

# ---------------- 01 pytest 运行生命周期 ----------------
SPECS["01_pytest_basics"] = wf(
    "pytest 一次运行的生命周期", "01_pytest_basics/images/pytest_basics.html",
    [{"id": "cli", "label": "命令行"}, {"id": "collect", "label": "收集期"},
     {"id": "run", "label": "执行期"}, {"id": "report", "label": "报告期"}],
    [{"id": "find", "label": "发现用例", "fromCol": 0, "toCol": 1},
     {"id": "exec", "label": "逐条执行", "fromCol": 2, "toCol": 2, "variant": "emphasis"},
     {"id": "sum", "label": "汇总退出", "fromCol": 3, "toCol": 3}],
    [n("cli", "cli", 0, "pytest 命令", "-k / -x / -v", "external"),
     n("ini", "cli", 1, "pytest.ini", "rootdir + addopts", "frontend"),
     n("disc", "collect", 2, "用例发现", "test_*.py::test_*", "backend"),
     n("assert", "run", 3, "断言重写", "失败展开中间值", "backend", "教学点"),
     n("mark", "run", 2, "参数化展开", "一函数多实例", "backend"),
     n("sum", "report", 3, "汇总报告", "退出码 0/1", "messagebus")],
    [e("a", "cli", "ini"), e("b", "ini", "disc", "按配置收集", "emphasis"),
     e("c", "disc", "mark"), e("d", "mark", "assert", "逐条执行"),
     e("f", "assert", "sum", "结果汇总")],
    [card("cyan", "运行规则", ["-k 圈选 / -x 早停", "testpaths 限定收集范围"]),
     card("emerald", "断言重写", ["assert 表达式两侧被求值", "失败输出可直接读"]),
     card("rose", "预期失败", ["regression_demo 故意红", "教学脚本显式标注"])],
    ["cli", "ini", "disc", "mark", "assert", "sum"],
)

# ---------------- 02 fixture 作用域 ----------------
SPECS["02_fixtures"] = wf(
    "fixture 的装配：作用域入栈出栈", "02_fixtures/images/fixtures.html",
    [{"id": "test", "label": "测试用例"}, {"id": "session", "label": "session 级"},
     {"id": "func", "label": "function 级"}, {"id": "teardown", "label": "清理"}],
    [{"id": "setup", "label": "setup 自底向上", "fromCol": 0, "toCol": 2},
     {"id": "tear", "label": "teardown 逆序出栈", "fromCol": 3, "toCol": 3, "variant": "dashed"}],
    [n("t1", "test", 0, "用例 A", "参数声明 db", "external"),
     n("db", "session", 1, "FakeDB 连接", "0.2s 只建一次", "database", "session"),
     n("clean", "func", 2, "clean_db 表", "每用例清空", "database", "function"),
     n("factory", "func", 3, "user_factory", "造 N 个用户", "backend"),
     n("t2", "test", 3, "用例结束", "断言完成", "external"),
     n("close", "teardown", 3, "连接关闭", "会话末尾", "messagebus")],
    [e("a", "t1", "db", "首次请求创建", "emphasis"),
     e("b", "db", "clean", "复用连接"), e("c", "clean", "factory"),
     e("d", "factory", "t2", "注入数据", "emphasis"),
     e("f", "t2", "close", "yield 之后", "dashed")],
    [card("cyan", "作用域", ["session 贵资源共享", "function 脏数据换新"]),
     card("emerald", "conftest", ["同目录用例自动可见", "子目录可覆盖"]),
     card("rose", "teardown", ["yield 之后即清理", "用例失败也执行"])],
    ["t1", "db", "clean", "factory", "t2", "close"],
)

# ---------------- 03 参数化展开 ----------------
SPECS["03_parametrize"] = wf(
    "参数化：一条函数展开成用例矩阵", "03_parametrize/images/parametrize.html",
    [{"id": "src", "label": "数据来源"}, {"id": "expand", "label": "展开期"},
     {"id": "run", "label": "执行期"}, {"id": "out", "label": "报告"}],
    [{"id": "decl", "label": "声明矩阵", "fromCol": 0, "toCol": 1},
     {"id": "exec", "label": "24 条独立执行", "fromCol": 2, "toCol": 2, "variant": "emphasis"}],
    [n("func", "src", 0, "11 个测试函数", "被测：配置解析器", "external"),
     n("vals", "src", 1, "argvalues", "值列表", "database"),
     n("ids", "expand", 2, "ids 命名", "报告可读", "backend", "可读性"),
     n("cart", "expand", 3, "笛卡尔积", "2×3=6 组合", "backend"),
     n("ind", "expand", 4, "indirect", "参数走 fixture", "backend"),
     n("cases", "run", 4, "24 条用例", "独立失败", "messagebus")],
    [e("a", "func", "vals"), e("b", "vals", "ids", "命名展开", "emphasis"),
     e("c", "ids", "cart", "叠加组合"), e("d", "cart", "ind"),
     e("f", "ind", "cases", "矩阵执行", "emphasis")],
    [card("cyan", "ids", ["没有 ids 就是 param0", "可读名让 -k 精确制导"]),
     card("emerald", "异常断言", ["raises + match 双重锁", "消息内容也是契约"]),
     card("rose", "indirect", ["参数先进 fixture 再进用例", "预处理管道"])],
    ["func", "vals", "ids", "cart", "ind", "cases"],
)

# ---------------- 04 mock 架构 ----------------
SPECS["04_mock"] = arch(
    "通知服务与测试替身", "04_mock/images/mock.html",
    [c("svc", "NotificationService", "被测业务层", "backend", (420, 260)),
     c("smtp", "SmtpClient", "真实外部依赖", "cloud", (720, 260), tag="测试中禁用"),
     c("mock", "MagicMock", "记录调用+断言", "security", (720, 140), tag="契约"),
     c("fake", "InMemoryMailer", "能跑的迷你实现", "database", (720, 380), tag="状态"),
     c("mp", "monkeypatch", "环境变量注入", "security", (160, 140)),
     c("fz", "freezegun", "冻结 datetime.now", "messagebus", (160, 380), tag="时间")],
    [{"id": "a", "from": "svc", "to": "smtp", "variant": "dashed", "fromSide": "top", "toSide": "top"},
     {"id": "b", "from": "svc", "to": "mock", "label": "断言调用形状"},
     {"id": "c", "from": "svc", "to": "fake", "label": "查询 outbox"},
     {"id": "d", "from": "mp", "to": "svc", "label": "setenv/delenv"},
     {"id": "f", "from": "fz", "to": "svc", "label": "@freeze_time"}],
    [card("cyan", "mock", ["assert_called_once_with", "耦合实现：重构易误红"]),
     card("emerald", "fake", ["outbox 可查询", "故障注入 fail_for 集合"]),
     card("rose", "时间", ["freezegun 定格日期", "截止逻辑天天可测"])],
    [{"kind": "region", "label": "测试进程（无真实网络）", "wraps": ["svc", "mock", "fake", "mp", "fz"]}],
)

# ---------------- 05 覆盖率数据流 ----------------
SPECS["05_coverage"] = wf(
    "覆盖率与质量门禁的数据流", "05_coverage/images/coverage.html",
    [{"id": "src", "label": "被测代码"}, {"id": "inst", "label": "插桩执行"},
     {"id": "rpt", "label": "报告"}, {"id": "gate", "label": "门禁"}],
    [{"id": "run", "label": "字节码插桩", "fromCol": 0, "toCol": 1},
     {"id": "decide", "label": "阈值判定", "fromCol": 3, "toCol": 3, "variant": "emphasis"}],
    [n("code", "src", 0, "discount.py", "分支密集", "external"),
     n("tests", "src", 1, "基础+补漏用例", "13 条", "backend"),
     n("trace", "inst", 1, "coverage.py", "branch=True", "backend"),
     n("html", "rpt", 2, "HTML/XML 报告", "逐行着色", "messagebus"),
     n("thr", "gate", 3, "--cov-fail-under 90", "低于即拦", "security", "门禁"),
     n("exit", "gate", 4, "退出码", "非 0 拦截提交", "messagebus")],
    [e("a", "code", "tests"), e("b", "tests", "trace", "度量覆盖", "emphasis"),
     e("c", "trace", "html", "生成报告"), e("d", "html", "thr"),
     e("f", "thr", "exit", "通过放行 / 不达标拦截", "security")],
    [card("cyan", "分支覆盖", ["行覆盖 100% 也会漏分支", "if 只走真分支=半盲"]),
     card("emerald", "排除规则", ["TYPE_CHECKING 不计", "门禁衡量业务逻辑"]),
     card("rose", "实测", ["基础集 78% 被拦", "补漏后 100% 放行"])],
    ["code", "tests", "trace", "html", "thr", "exit"],
)

# ---------------- 06 hypothesis 收缩循环 ----------------
SPECS["06_hypothesis"] = wf(
    "property-based：生成-断言-收缩-入库", "06_hypothesis/images/hypothesis.html",
    [{"id": "decl", "label": "声明"}, {"id": "gen", "label": "生成期"},
     {"id": "fix", "label": "失败处置"}, {"id": "store", "label": "沉淀"}],
    [{"id": "loop", "label": "N 组随机输入", "fromCol": 1, "toCol": 2},
     {"id": "shrink", "label": "收缩到最小", "fromCol": 3, "toCol": 4, "variant": "emphasis"}],
    [n("given", "decl", 0, "@given 策略", "st.lists/floats", "external"),
     n("ex", "decl", 1, "@example 锚点", "固定回归", "security"),
     n("gen", "gen", 1, "随机输入", "200 例", "backend"),
     n("prop", "gen", 2, "性质断言", "往返/不变量", "backend"),
     n("shr", "fix", 3, "Falsifying example", "最小复现", "security", "收缩"),
     n("db", "store", 4, ".hypothesis 库", "失败永久重放", "database")],
    [e("a", "given", "gen"), e("b", "ex", "gen", "锚点必跑", "security"),
     e("c", "gen", "prop", "执行性质", "emphasis"),
     e("d", "prop", "shr", "失败即收缩", "security"),
     e("f", "shr", "db", "入库重放", "dashed")],
    [card("cyan", "性质", ["往返/不变量/对拍", '覆盖「想不到」的输入']),
     card("emerald", "收缩", ["大乱数→[1e300,1,-1e300]", "调试两小时→看一行"]),
     card("rose", "真战果", ["decode('') 边界 bug", "编解码格式限制"])],
    ["given", "gen", "prop", "shr", "db"],
)

# ---------------- 07 快照审查流（sequence） ----------------
SPECS["07_snapshot"] = seq(
    "快照测试：比对-红-审查-更新的循环", "07_snapshot/images/snapshot.html",
    [{"id": "test", "type": "external", "label": "快照用例", "sublabel": "assert == snapshot"},
     {"id": "rend", "type": "backend", "label": "被测输出", "sublabel": "JSON/HTML"},
     {"id": "snap", "type": "database", "label": ".ambr 基线", "sublabel": "上次认可版本"},
     {"id": "human", "type": "external", "label": "人工审查", "sublabel": "看 diff 决策"}],
    [m("test", "rend", 180, "构造输出", "emphasis"),
     m("test", "snap", 222, "读取基线", "emphasis"),
     m("rend", "snap", 264, "逐行比对", "default"),
     {"from": "snap", "to": "test", "y": 306, "label": "不一致 → 红 + diff", "variant": "return"},
     m("test", "human", 368, "呈现 diff", "dashed"),
     {"from": "human", "to": "snap", "y": 410, "label": "合法变更 → --snapshot-update", "variant": "emphasis"},
     {"from": "snap", "to": "test", "y": 452, "label": "新基线 → 绿", "variant": "return"}],
    [card("cyan", "基线", [".ambr 提交进版本库", "快照=上一次认可的输出"]),
     card("rose", "纪律", ["禁止无脑 -u", "diff 是审查界面不是噪音"])],
    segments=[{"from": 150, "to": 320, "label": "自动比对"},
              {"from": 340, "to": 470, "label": "人工决策"}],
    activations=[{"participant": "test", "from": 160, "to": 330, "type": "external"},
                 {"participant": "snap", "from": 200, "to": 470, "type": "database"}],
)

# ---------------- 08 异步重试时序 ----------------
SPECS["08_async"] = seq(
    "异步重试客户端：退避时序与注入点", "08_async/images/async.html",
    [{"id": "test", "type": "external", "label": "测试", "sublabel": "注入 sleeper"},
     {"id": "cli", "type": "backend", "label": "RetryClient", "sublabel": "指数退避"},
     {"id": "tp", "type": "cloud", "label": "transport", "sublabel": "注入的替身"},
     {"id": "sl", "type": "messagebus", "label": "sleeper", "sublabel": "记账不真睡"}],
    [m("test", "cli", 170, "get(url)", "emphasis"),
     m("cli", "tp", 210, "尝试 #1", "emphasis"),
     {"from": "tp", "to": "cli", "y": 250, "label": "TransientError", "variant": "return"},
     m("cli", "sl", 290, "sleep(0.5) 名义", "emphasis"),
     m("cli", "tp", 350, "尝试 #2", "default"),
     {"from": "tp", "to": "cli", "y": 390, "label": "又失败", "variant": "return"},
     m("cli", "sl", 430, "sleep(1.0) 名义", "emphasis"),
     m("cli", "tp", 490, "尝试 #3 → 200", "emphasis"),
     {"from": "cli", "to": "test", "y": 530, "label": "Response（fetched_at 冻结时间）", "variant": "return"}],
    [card("cyan", "注入三件套", ["transport=网络替身", "sleeper=时间替身", "clock=时钟替身"]),
     card("emerald", "实测", ["名义退避 3.5s", "真实耗时 <1s"]),
     card("rose", "坑", ["time-machine 加速不了事件循环等待", "OS 级 select 不认时钟补丁"])],
    segments=[{"from": 150, "to": 320, "label": "首次尝试"},
              {"from": 330, "to": 470, "label": "指数退避"},
              {"from": 480, "to": 560, "label": "成功返回"}],
    activations=[{"participant": "cli", "from": 160, "to": 560, "type": "backend"},
                 {"participant": "sl", "from": 280, "to": 450, "type": "messagebus"}],
)

# ---------------- 09 xdist 架构 ----------------
SPECS["09_xdist"] = arch(
    "pytest-xdist：主进程分派与 worker 各自为政", "09_xdist/images/xdist.html",
    [c("main", "pytest 主进程", "收集+分发+汇总", "backend", (160, 240)),
     c("w1", "Worker 1", "独立进程", "backend", (440, 120)),
     c("w2", "Worker 2", "独立进程", "backend", (440, 240)),
     c("w3", "Worker N", "按核心数", "backend", (440, 360)),
     c("db", "module 全局", "每 worker 独立副本", "database", (720, 240), tag="污染现场")],
    [{"id": "a", "from": "main", "to": "w1", "label": "分发用例"},
     {"id": "b", "from": "main", "to": "w2"},
     {"id": "c", "from": "main", "to": "w3"},
     {"id": "d", "from": "w1", "to": "db", "label": "计数器从 0 起", "variant": "dashed"},
     {"id": "f", "from": "w3", "to": "main", "variant": "dashed", "fromSide": "left", "toSide": "left"}],
    [card("cyan", "实测加速", ["串行 11.8s → 并行 1.9s", "200 条 50ms 用例"]),
     card("rose", "独立性", ["共享计数器并行必翻车", "fixture 化修复后全绿"]),
     card("emerald", "分层", ["-m smoke 0.3s 秒回", "CI push 只跑冒烟"])],
)

# ---------------- 10 插件钩子 ----------------
SPECS["10_plugin"] = wf(
    "pytest 插件的四个介入时机", "10_plugin/images/plugin.html",
    [{"id": "coll", "label": "收集期"}, {"id": "run", "label": "执行期"},
     {"id": "finish", "label": "收尾期"}, {"id": "out", "label": "产物"}],
    [{"id": "entry", "label": "pytest11 入口点", "fromCol": 0, "toCol": 1, "variant": "emphasis"},
     {"id": "gate", "label": "配置早失败", "fromCol": 2, "toCol": 3, "variant": "security"}],
    [n("ep", "coll", 0, "pyproject 入口点", "pip install 即加载", "external"),
     n("mark", "coll", 1, "marker 校验", "tier 非法即 UsageError", "security"),
     n("hook", "run", 2, "runtest_makereport", "失败落上下文 JSON", "backend", "核心钩子"),
     n("slow", "run", 3, "慢用例打标", "duration > 阈值", "backend"),
     n("fin", "finish", 3, "sessionfinish", "写报告 JSON", "messagebus"),
     n("sum", "out", 3, "terminal_summary", "官方钩子打印摘要", "messagebus")],
    [e("a", "ep", "mark", "发现插件", "emphasis"),
     e("b", "mark", "hook", "通过收集", "emphasis"),
     e("c", "hook", "slow", "逐用例记账"),
     e("d", "slow", "fin", "会话结束"),
     e("f", "fin", "sum", "产出报告")],
    [card("cyan", "礼貌插件", ["--ministore 开关才生效", "不碰私有 API"]),
     card("rose", "踩坑实录", ["pytest9 移除 _terminalreporter", "平铺包要显式 packages"]),
     card("emerald", "复用", ["同 venv 两个项目即插即用", "conftest 做不到"])],
    ["ep", "mark", "hook", "slow", "fin", "sum"],
)

# ---------------- 11 SUT 架构 ----------------
SPECS["11_sut_app"] = arch(
    "SUT：FastAPI 订单管理应用", "11_sut_app/images/sut.html",
    [c("ui", "静态页", "下单/慢加载/登录/admin", "frontend", (160, 240)),
     c("api", "FastAPI 路由", "契约冻结 :8899", "backend", (420, 240)),
     c("store", "store.py", "SQLite 数据层", "database", (680, 240)),
     c("slow", "/api/slow-config", "故意 1.5s（lab 17 靶子）", "cloud", (420, 100), tag="等待训练"),
     c("login", "/api/login", "admin/user 双角色", "security", (420, 380)),
     c("db", "orders.db", "幂等种子数据", "database", (680, 380))],
    [{"id": "a", "from": "ui", "to": "api", "label": "fetch JSON"},
     {"id": "b", "from": "api", "to": "store", "label": "SQL"},
     {"id": "c", "from": "api", "to": "slow", "variant": "dashed"},
     {"id": "d", "from": "api", "to": "login", "label": "token", "labelDy": 24},
     {"id": "f", "from": "store", "to": "db", "label": "读写", "labelDy": 24}],
    [card("cyan", "契约", ["CRUD + 登录 + 慢接口", "后续 19 个实验都测它"]),
     card("emerald", "可测性设计", ["DB 路径环境变量可注入", "种子幂等可重跑"]),
     card("rose", "教学事故现场", ["慢接口/4xx 分支", "都是故意留的靶子"])],
    [{"kind": "region", "label": "SUT 进程", "wraps": ["api", "store", "slow", "login", "db"]}],
)

# ---------------- 12 API 用例生命周期（sequence） ----------------
SPECS["12_api_tests"] = seq(
    "一条 API 用例的完整生命周期", "12_api_tests/images/api_tests.html",
    [{"id": "case", "type": "external", "label": "用例", "sublabel": "30 条之一"},
     {"id": "fac", "type": "backend", "label": "order_factory", "sublabel": "自造自清"},
     {"id": "cli", "type": "frontend", "label": "httpx client", "sublabel": "session 级复用"},
     {"id": "sut", "type": "backend", "label": "SUT :8901", "sublabel": "独立空库"}],
    [m("case", "fac", 170, "造 3 条订单", "emphasis"),
     m("fac", "sut", 210, "POST /api/orders ×3", "emphasis"),
     m("case", "cli", 260, "GET /api/orders?limit=2", "default"),
     m("cli", "sut", 300, "HTTP", "default"),
     {"from": "sut", "to": "cli", "y": 340, "label": "200 + X-Total-Count", "variant": "return"},
     {"from": "cli", "to": "case", "y": 380, "label": "pydantic 校验 + 断言", "variant": "return"},
     {"from": "case", "to": "fac", "y": 440, "label": "teardown", "variant": "dashed"},
     {"from": "fac", "to": "sut", "y": 480, "label": "DELETE ×3 清场", "variant": "dashed"}],
    [card("cyan", "独立可乱序", ["-k 圈一半/另一半都绿", "-n 4 并行也绿"]),
     card("emerald", "负向占半壁", ["422/400/404/403", "健壮性藏在 4xx"]),
     card("rose", "踩坑", ["conftest 放错层级不生效", "响应头被小写化"])],
    segments=[{"from": 150, "to": 240, "label": "造数"},
              {"from": 250, "to": 400, "label": "请求与断言"},
              {"from": 430, "to": 500, "label": "清场"}],
    activations=[{"participant": "fac", "from": 160, "to": 500, "type": "backend"},
                 {"participant": "cli", "from": 250, "to": 400, "type": "frontend"}],
)

# ---------------- 13 两种隔离策略 ----------------
SPECS["13_db_tests"] = wf(
    "数据层集成测试：两种隔离策略", "13_db_tests/images/db_tests.html",
    [{"id": "case", "label": "数据层用例"}, {"id": "fresh", "label": "fresh 策略"},
     {"id": "trunc", "label": "truncate 策略"}, {"id": "conc", "label": "并发实测"}],
    [{"id": "mark", "label": "mark.isolation 切换", "fromCol": 0, "toCol": 1},
     {"id": "lock", "label": "database is locked", "fromCol": 3, "toCol": 3, "variant": "security"}],
    [n("case", "case", 0, "10 条用例", "直打 store.py", "external"),
     n("f", "fresh", 1, "全新库文件", "每用例一个", "database", "最干净"),
     n("t", "trunc", 2, "共享库+截表", "DELETE FROM", "database", "最快"),
     n("raw", "conc", 3, "裸 SQLite 写者", "BEGIN IMMEDIATE", "backend"),
     n("lock", "conc", 4, "写锁冲突", "必现 locked", "security", "实测"),
     n("ok", "conc", 5, "应用层串行化", "20 线程全成功", "messagebus")],
    [e("a", "case", "f", "策略 A", "emphasis"),
     e("b", "case", "t", "策略 B", "emphasis"),
     e("g", "f", "t", "策略对账"), e("h", "t", "raw", "并发实测"),
     e("c", "raw", "lock", "不串行化", "security"),
     e("i", "lock", "ok", "锁退让后成功"),
     e("d", "case", "ok", "store 写锁")],
    [card("cyan", "策略对账", ["同组用例两策略结果一致", "差异只在速度与成本"]),
     card("emerald", "迁移三板斧", ["空库可执行/旧库重跑/数据完好"]),
     card("rose", "诚实记录", ["回滚隔离缺席：数据层一操作一连接", "拿不到事务控制权"])],
    ["case", "f", "t", "raw", "lock", "ok"],
)

# ---------------- 14 testcontainers 架构 ----------------
SPECS["14_testcontainers"] = arch(
    "testcontainers：容器随会话起停", "14_testcontainers/images/testcontainers.html",
    [c("py", "pytest 会话", "session 级 fixture", "backend", (140, 240)),
     c("tc", "testcontainers", "拉起/等待/销毁", "backend", (380, 240)),
     c("dk", "Docker daemon", "已运行的引擎", "cloud", (620, 240)),
     c("pg", "postgres:16-alpine", "动态端口", "database", (860, 240), tag="自动销毁"),
     c("store", "pg_store.py", "方言适配层", "database", (380, 400))],
    [{"id": "a", "from": "py", "to": "tc", "label": "with 块生命周期"},
     {"id": "b", "from": "tc", "to": "dk", "label": "API 调用"},
     {"id": "c", "from": "dk", "to": "pg", "label": "run/stop"},
     {"id": "d", "from": "py", "to": "store", "label": "CRUD"},
     {"id": "f", "from": "store", "to": "pg", "label": "%s 占位符 + RETURNING"}],
    [card("cyan", "生命周期", ["会话开始拉起", "结束自动销毁零残留"]),
     card("emerald", "实测差异", ["类型强约束/MVCC 并发", "NUMERIC 定点/RETURNING"]),
     card("rose", "方言适配", ["psycopg2 无 conn.execute", "必须经 cursor"])],
    [{"kind": "region", "label": "本机 Docker", "wraps": ["dk", "pg"]}],
)

# ---------------- 15 pact 闭环（sequence） ----------------
SPECS["15_pact"] = seq(
    "Pact 契约闭环：consumer 定义，provider 对账", "15_pact/images/pact.html",
    [{"id": "consumer", "type": "external", "label": "前端 consumer", "sublabel": "frontend_client"},
     {"id": "mock", "type": "backend", "label": "mock server", "sublabel": "FFI 拉起"},
     {"id": "pact", "type": "database", "label": "pacts/*.json", "sublabel": "本地文件交换"},
     {"id": "provider", "type": "backend", "label": "SUT provider", "sublabel": ":8902 真服务"},
     {"id": "verifier", "type": "security", "label": "Verifier", "sublabel": "退出码即门禁"}],
    [m("consumer", "mock", 170, "按契约发请求", "emphasis"),
     {"from": "mock", "to": "consumer", "y": 210, "label": "按期望返回", "variant": "return"},
     m("consumer", "pact", 250, "write_file 合并", "emphasis"),
     m("verifier", "pact", 310, "读取契约", "default"),
     m("verifier", "provider", 350, "重放请求", "emphasis"),
     {"from": "provider", "to": "verifier", "y": 390, "label": "真实响应", "variant": "return"},
     {"from": "verifier", "to": "consumer", "y": 440, "label": "改字段 → verify 红", "variant": "return"}],
    [card("cyan", "匹配器", ["like 只锁类型不锁值", "契约测结构不测数据"]),
     card("rose", "provider 状态", ["items 至少 1 条", "种子数据 = 最小 state handler"]),
     card("emerald", "实测踩坑", ["系统代理吃掉 mock 请求", "query 是字符串不是整数"])],
    segments=[{"from": 150, "to": 280, "label": "consumer 侧"},
              {"from": 290, "to": 420, "label": "provider 侧"},
              {"from": 430, "to": 470, "label": "破坏演练"}],
    activations=[{"participant": "mock", "from": 160, "to": 270, "type": "backend"},
                 {"participant": "verifier", "from": 300, "to": 460, "type": "security"}],
)

# ---------------- 16 Playwright 执行链路 ----------------
SPECS["16_pw_basics"] = wf(
    "Playwright 一次 E2E 的执行链路", "16_pw_basics/images/pw_basics.html",
    [{"id": "pytest", "label": "pytest"}, {"id": "pw", "label": "Playwright"},
     {"id": "browser", "label": "浏览器"}, {"id": "evidence", "label": "取证"}],
    [{"id": "fix", "label": "page fixture", "fromCol": 0, "toCol": 1},
     {"id": "act", "label": "动作+断言", "fromCol": 2, "toCol": 2, "variant": "emphasis"}],
    [n("pt", "pytest", 0, "pytest-playwright", "page fixture", "external"),
     n("pw", "pw", 1, "定位器", "get_by_role 优先", "backend"),
     n("wait", "pw", 2, "自动等待", "可交互即动作", "backend", "零 sleep"),
     n("br", "browser", 2, "Chromium", "真实页面", "frontend"),
     n("expect", "browser", 3, "web-first 断言", "expect 重试", "backend"),
     n("trace", "evidence", 3, "trace.zip", "时间旅行回放", "database")],
    [e("a", "pt", "pw", "注入", "emphasis"), e("b", "pw", "wait"),
     e("c", "wait", "br", "驱动", "emphasis"), e("d", "br", "expect"),
     e("f", "expect", "trace", "失败/全程留痕", "dashed")],
    [card("cyan", "定位器优先级", ["role > placeholder > css", "语义定位抗重构"]),
     card("rose", "踩坑", ["is_visible() 不等待", "断言必须用 expect"]),
     card("emerald", "codegen", ["操作即生成代码", "录制是起点整理是终点"])],
    ["pt", "pw", "wait", "br", "expect", "trace"],
)

# ---------------- 17 等待时序 ----------------
SPECS["17_pw_locators"] = seq(
    "竞态按钮的三阶段与 expect 轮询", "17_pw_locators/images/pw_locators.html",
    [{"id": "user", "type": "external", "label": "用例", "sublabel": "click + expect"},
     {"id": "btn", "type": "frontend", "label": "竞态按钮", "sublabel": "三态变化"},
     {"id": "js", "type": "backend", "label": "页面 JS", "sublabel": "1s 后才变终态"},
     {"id": "expect", "type": "security", "label": "expect 轮询", "sublabel": "到终态为止"}],
    [m("user", "btn", 170, "click", "emphasis"),
     m("btn", "js", 210, "触发处理", "default"),
     {"from": "js", "to": "btn", "y": 250, "label": "文字变 处理中…", "variant": "return"},
     {"from": "expect", "to": "btn", "y": 310, "label": "轮询：终态到了吗", "variant": "dashed"},
     {"from": "btn", "to": "expect", "y": 350, "label": "还没有（继续等）", "variant": "return"},
     {"from": "js", "to": "btn", "y": 410, "label": "1s 后：竞态完成 ✅", "variant": "emphasis"},
     {"from": "btn", "to": "expect", "y": 450, "label": "匹配成功 → 绿", "variant": "return"}],
    [card("cyan", "三原则", ["断言终态不断言时刻", "慢 UI 显式给足超时", "role 定位优先"]),
     card("rose", "反模式实测", ["sleep(0.5)+count 必挂", "sleep(3) 稳但全浪费"])],
    segments=[{"from": 150, "to": 280, "label": "触发"},
              {"from": 290, "to": 400, "label": "轮询等待"},
              {"from": 400, "to": 480, "label": "终态"}],
    activations=[{"participant": "expect", "from": 290, "to": 470, "type": "security"}],
)

# ---------------- 18 POM 分层 ----------------
SPECS["18_pw_pom"] = arch(
    "POM 分层：选择器只活在 pages/", "18_pw_pom/images/pw_pom.html",
    [c("test", "test_orders_pom", "业务语言用例", "external", (150, 240)),
     c("fix", "conftest fixture", "index_page/slow_page", "backend", (400, 240)),
     c("page", "IndexPage/SlowPage", "选择器唯一居所", "backend", (650, 240), tag="收口"),
     c("br", "Playwright page", "浏览器抽象", "frontend", (880, 240)),
     c("new", "test_new_feature", "12 行新增用例", "external", (400, 400), tag="低成本")],
    [{"id": "a", "from": "test", "to": "fix", "label": "注入"},
     {"id": "b", "from": "fix", "to": "page", "label": "构造"},
     {"id": "c", "from": "page", "to": "br", "label": "驱动"},
     {"id": "d", "from": "new", "to": "fix", "label": "复用即写", "variant": "dashed"}],
    [card("cyan", "纪律检查", ["grep 泄漏检查进脚本", "tests/ 出现选择器即失败"]),
     card("emerald", "等价重构", ["用例数与断言语义不变", "页面细节全部下沉"]),
     card("rose", "真实竞态", ["连续下单踩中刷新竞态", "按真实用户节奏写用例"])],
)

# ---------------- 19 route 拦截时序 ----------------
SPECS["19_pw_network"] = seq(
    "route 拦截：请求永远到不了真后端", "19_pw_network/images/pw_network.html",
    [{"id": "page", "type": "frontend", "label": "页面 JS", "sublabel": "fetch /api/*"},
     {"id": "route", "type": "security", "label": "page.route", "sublabel": "中间人"},
     {"id": "be", "type": "backend", "label": "真后端", "sublabel": "可挂可不开"},
     {"id": "state", "type": "database", "label": "storageState", "sublabel": "admin/user 双会话"}],
    [m("page", "route", 170, "fetch /api/slow-config", "emphasis"),
     {"from": "route", "to": "page", "y": 210, "label": "fulfill 5ms mock", "variant": "return"},
     m("page", "route", 260, "fetch /api/**", "default"),
     {"from": "route", "to": "page", "y": 300, "label": "abort → 优雅降级", "variant": "return"},
     m("page", "route", 360, "POST /api/orders", "emphasis"),
     {"from": "route", "to": "page", "y": 400, "label": "500 → 下单失败 alert", "variant": "return"},
     {"from": "state", "to": "page", "y": 460, "label": "注入 token/role，双角色不串号", "variant": "dashed"}],
    [card("cyan", "三种注入", ["fulfill 假响应提速 300 倍", "abort 模拟断网", "500 验证报错路径"]),
     card("emerald", "登录复用", ["UI 登录一次存档", "新 context 零登录成本"]),
     card("rose", "踩坑", ["expect_event('dialog') 等弹窗", "localStorage 要先有 origin"])],
    segments=[{"from": 150, "to": 330, "label": "桩与降级"},
              {"from": 340, "to": 430, "label": "故障注入"},
              {"from": 440, "to": 480, "label": "会话"}],
    activations=[{"participant": "route", "from": 160, "to": 430, "type": "security"}],
)

# ---------------- 20 三核矩阵 ----------------
SPECS["20_pw_quality"] = arch(
    "三核矩阵与失败取证管线", "20_pw_quality/images/pw_quality.html",
    [c("suite", "冒烟套件 ×3", "同语义用例", "backend", (150, 240)),
     c("cr", "Chromium", "主力内核", "frontend", (420, 100)),
     c("ff", "Firefox", "独立引擎", "frontend", (420, 240)),
     c("wk", "WebKit", "Safari 同源", "frontend", (420, 380)),
     c("res", "test-results/", "按用例×内核归档", "database", (700, 240)),
     c("ev", "png+webm+trace", "失败三件套", "messagebus", (700, 400), tag="only-on-failure")],
    [{"id": "a", "from": "suite", "to": "cr", "label": "--browser ×3"},
     {"id": "b", "from": "suite", "to": "ff"},
     {"id": "c", "from": "suite", "to": "wk"},
     {"id": "d", "from": "wk", "to": "res", "label": "失败落盘", "variant": "dashed"},
     {"id": "f", "from": "res", "to": "ev"}],
    [card("cyan", "矩阵语义", ["9 用例 = 3×3 全绿", "WebKit 无需特殊处理（诚实记录）"]),
     card("emerald", "取证", ["retain-on-failure", "show-trace 时间旅行"]),
     card("rose", "边界意识", ["引擎差异靠 expect 等待吸收", "skipif + issue 才是迁就之道"])],
)

# ---------------- 21 Cypress 架构 ----------------
SPECS["21_cypress_basics"] = arch(
    "Cypress 架构：测试活在浏览器里", "21_cypress_basics/images/cypress_basics.html",
    [c("spec", "orders.cy.js", "describe/it", "backend", (140, 240)),
     c("proxy", "Cypress 代理层", "命令注入/流量接管", "security", (390, 240)),
     c("br", "Electron 浏览器", "测试与页面同进程", "frontend", (640, 240), tag="原生体验"),
     c("auto", "自动等待", "should 自带重试", "backend", (390, 100)),
     c("runner", "运行器", "cypress open / run", "messagebus", (390, 380), tag="调试利器"),
     c("sut", "SUT :8921", "被测应用", "cloud", (640, 380))],
    [{"id": "a", "from": "spec", "to": "proxy", "label": "cy.* 命令链"},
     {"id": "b", "from": "proxy", "to": "br"},
     {"id": "c", "from": "auto", "to": "br", "variant": "dashed"},
     {"id": "d", "from": "runner", "to": "spec", "label": "headless/open"},
     {"id": "f", "from": "br", "to": "sut", "label": "HTTP", "labelDy": 24}],
    [card("cyan", "第一印象", ["测试跑在浏览器内", "链式命令+内置重试"]),
     card("emerald", "对比 Playwright", ["同 SUT 同 3 用例", "调试体验是招牌"]),
     card("rose", "取舍", ["单域/同源限制", "Electron 单内核"])],
)

# ---------------- 22 intercept/session 时序 ----------------
SPECS["22_cypress_advanced"] = seq(
    "cy.intercept 与 cy.session 的协作", "22_cypress_advanced/images/cypress_advanced.html",
    [{"id": "spec", "type": "external", "label": "spec", "sublabel": "桩+会话+命令"},
     {"id": "int", "type": "security", "label": "cy.intercept", "sublabel": "桩/断网/500"},
     {"id": "page", "type": "frontend", "label": "页面", "sublabel": "banner/表单/alert"},
     {"id": "sess", "type": "database", "label": "cy.session", "sublabel": "登录态缓存"}],
    [m("spec", "int", 160, "注册桩", "emphasis"),
     m("spec", "page", 192, "visit /", "default"),
     {"from": "int", "to": "page", "y": 228, "label": "MOCKED banner / 断网降级", "variant": "return"},
     m("spec", "int", 288, "POST 桩 500", "emphasis"),
     {"from": "page", "to": "spec", "y": 326, "label": "window:alert 下单失败", "variant": "return"},
     m("spec", "sess", 392, "cy.login('admin')", "emphasis"),
     {"from": "sess", "to": "spec", "y": 428, "label": "同角色只登录一次", "variant": "return"},
     {"from": "spec", "to": "page", "y": 460, "label": "cy.createOrder 复用", "variant": "dashed"}],
    [card("cyan", "intercept", ["forceNetworkError 断网", "statusCode 500 注入"]),
     card("emerald", "session", ["cacheAcrossSpecs 跨文件", "validate 校验 token"]),
     card("rose", "命令封装", ["cy.createOrder 三处复用", "业务语言进 cy.*"])],
    segments=[{"from": 150, "to": 290, "label": "网络桩"},
              {"from": 300, "to": 380, "label": "故障注入"},
              {"from": 400, "to": 540, "label": "会话与命令"}],
    activations=[{"participant": "int", "from": 160, "to": 380, "type": "security"},
                 {"participant": "sess", "from": 410, "to": 480, "type": "database"}],
)

# ---------------- 23 WebDriver 协议时序 ----------------
SPECS["23_selenium_basics"] = seq(
    "WebDriver 协议：每步都是一次 HTTP", "23_selenium_basics/images/selenium_basics.html",
    [{"id": "py", "type": "external", "label": "pytest 用例", "sublabel": "selenium 绑定"},
     {"id": "drv", "type": "backend", "label": "chromedriver", "sublabel": "驱动自动下载"},
     {"id": "br", "type": "frontend", "label": "Chrome", "sublabel": "headless"},
     {"id": "sut", "type": "cloud", "label": "SUT", "sublabel": ":8923"}],
    [m("py", "drv", 170, "POST /session", "emphasis"),
     m("drv", "br", 210, "启动浏览器", "emphasis"),
     m("py", "drv", 272, "find_element", "default"),
     m("drv", "br", 300, "协议命令（同步阻塞）", "default"),
     m("br", "sut", 340, "页面加载 2s 延迟", "dashed"),
     {"from": "py", "to": "drv", "y": 400, "label": "无等待 find → NoSuchElementException", "variant": "return"},
     {"from": "py", "to": "drv", "y": 460, "label": "WebDriverWait(10) 轮询 → 稳定", "variant": "emphasis"}],
    [card("cyan", "协议直感", ["每个动作一次 HTTP 往返", "没有内置自动等待"]),
     card("rose", "必挂 vs 稳定", ["裸 find 当场抛错", "显式等待是纪律"]),
     card("emerald", "Safari", ["safaridriver 需手动启用", "诚实标注不装会跑"])],
    segments=[{"from": 150, "to": 250, "label": "会话建立"},
              {"from": 260, "to": 380, "label": "元素定位"},
              {"from": 390, "to": 490, "label": "等待策略对决"}],
    activations=[{"participant": "drv", "from": 160, "to": 490, "type": "backend"}],
)

# ---------------- 24 Grid 架构 ----------------
SPECS["24_selenium_advanced"] = arch(
    "Selenium Grid：单节点双会话并行", "24_selenium_advanced/images/selenium_grid.html",
    [c("pytest", "pytest -n 2", "xdist 双进程", "backend", (140, 240)),
     c("grid", "Grid :4444", "standalone-chrome", "backend", (400, 240), tag="docker"),
     c("c1", "Chrome 会话 1", "容器内", "frontend", (660, 120)),
     c("c2", "Chrome 会话 2", "容器内", "frontend", (660, 360)),
     c("sut", "SUT :8924", "宿主机", "cloud", (880, 240))],
    [{"id": "a", "from": "pytest", "to": "grid", "label": "SELENIUM_REMOTE_URL"},
     {"id": "b", "from": "grid", "to": "c1", "label": "maxSession=2"},
     {"id": "c", "from": "grid", "to": "c2"},
     {"id": "d", "from": "c1", "to": "sut", "label": "host.docker.internal", "variant": "emphasis"},
     {"id": "f", "from": "c2", "to": "sut", "label": "同左"}],
    [card("cyan", "实测", ["串行 12.2s → ×2 并行 6.8s", "加速比 1.8x"]),
     card("rose", "经典坑", ["容器内 127.0.0.1 是容器自己", "SUT 地址必须 host.docker.internal"]),
     card("emerald", "其他", ["data: URL 的 # 要编码", "ActionChains 走原生鼠标事件"])],
    [{"kind": "region", "label": "Docker 容器", "wraps": ["grid", "c1", "c2"]}],
)

# ---------------- 25 对比执行流 ----------------
SPECS["25_comparison"] = wf(
    "三框架统一矩阵的执行与统计", "25_comparison/images/comparison.html",
    [{"id": "drive", "label": "编排"}, {"id": "pw", "label": "Playwright"},
     {"id": "cy", "label": "Cypress"}, {"id": "se", "label": "Selenium"}],
    [{"id": "loop", "label": "同一 SUT 同语义 5 用例", "fromCol": 0, "toCol": 1, "variant": "emphasis"},
     {"id": "stat", "label": "统计落盘", "fromCol": 3, "toCol": 3}],
    [n("run", "drive", 0, "run_all.sh", "ROUNDS 轮", "external"),
     n("a", "pw", 1, "pytest 套件", "Chromium", "backend"),
     n("b", "cy", 1, "cypress run", "Electron", "backend"),
     n("c", "se", 1, "pytest 套件", "Chrome", "backend"),
     n("csv", "drive", 2, "results.csv", "耗时/通过/失败", "database"),
     n("rpt", "drive", 3, "comparison.md", "场景选型结论", "messagebus")],
    [e("a", "run", "a", "轮 1..N", "emphasis"), e("b", "run", "b"), e("c", "run", "c"),
     e("d", "a", "csv"), e("f", "b", "csv"), e("g", "c", "csv"),
     e("h", "csv", "rpt", "数据说话")],
    [card("cyan", "实测均值", ["PW 2.7s < CY 3.0s < SE 5.6s", "启动模型不同，量级参考"]),
     card("emerald", "稳定性", ["15 执行 0 失败", "重试机制 CY 内置/PW expect/SE 自建"]),
     card("rose", "选型", ["新项目 PW / 前端团队 CY", "多语言团队 SE"])],
    ["run", "a", "csv", "rpt"],
)

# ---------------- 26 Locust 压测 ----------------
SPECS["26_locust"] = arch(
    "Locust 虚拟用户群与拐点观测", "26_locust/images/locust.html",
    [c("users", "虚拟用户 ×100", "读写混合 3:1（阶梯加压）", "external", (120, 200)),
     c("loc", "Locust 引擎", "headless + CSV", "backend", (380, 200)),
     c("sut", "SUT :8926", "uvicorn + SQLite", "backend", (640, 200)),
     c("lock", "SQLite 单写者", "写请求排队（瓶颈根源）", "database", (880, 200), tag="拐点"),
     c("rpt", "报告", "locust.html + bottleneck.md", "messagebus", (880, 360))],
    [{"id": "a", "from": "users", "to": "loc", "label": "spawn 10/s"},
     {"id": "b", "from": "loc", "to": "sut", "label": "HTTP 压力", "variant": "emphasis"},
     {"id": "c", "from": "sut", "to": "lock", "label": "下单写串行", "variant": "dashed", "labelDy": 24},
     {"id": "d", "from": "loc", "to": "rpt", "label": "逐档统计", "variant": "dashed"}],
    [card("cyan", "场景设计", ["浏览:下单:慢接口 = 3:1:1", "唯一客户名避免冲突"]),
     card("emerald", "实测", ["10→100 并发阶梯", "P95 1500ms 被慢接口定锚"]),
     card("rose", "拐点解释", ["写排队=SQLite 锁", "解法见 lab 14 的 MVCC"])],
)

# ---------------- 27 k6 阈值门禁 ----------------
SPECS["27_k6"] = wf(
    "k6 场景与 thresholds 门禁", "27_k6/images/k6.html",
    [{"id": "scn", "label": "场景"}, {"id": "exec", "label": "执行"},
     {"id": "metric", "label": "指标"}, {"id": "gate", "label": "门禁"}],
    [{"id": "sel", "label": "SCENARIO 选择", "fromCol": 0, "toCol": 0},
     {"id": "judge", "label": "阈值判定", "fromCol": 3, "toCol": 3, "variant": "security"}],
    [n("smoke", "scn", 0, "smoke", "1 VU 15s 验活", "external"),
     n("ramp", "scn", 1, "ramping", "0→20→0 VU", "backend"),
     n("spike", "exec", 1, "spike", "5→60 到达率突刺", "backend", "突刺"),
     n("tags", "metric", 2, "endpoint:fast 标签", "阈值只管快接口", "messagebus"),
     n("thr", "gate", 3, "p95<500ms & 错误<1%", "不达标退出非 0", "security", "CI 门禁"),
     n("exit", "gate", 4, "退出码", "直接当闸门", "messagebus")],
    [e("a", "smoke", "ramp"), e("b", "ramp", "spike", "同脚本三形态", "emphasis"),
     e("c", "spike", "tags"), e("d", "tags", "thr"),
     e("f", "thr", "exit", "不达标拦下提交", "security")],
    [card("cyan", "三场景", ["部署验活/爬坡稳态/突发流量", "一份脚本 env 切换"]),
     card("emerald", "阈值", ["标签过滤慢接口", "失败演示真实触发非 0"]),
     card("rose", "vs Locust", ["k6=JS+门禁语义", "Locust=Python+灵活场景"])],
    ["smoke", "ramp", "spike", "tags", "thr", "exit"],
)

# ---------------- 28 移动端双路径 ----------------
SPECS["28_appium"] = arch(
    "移动端测试：Appium 链路与 fallback 双路径", "28_appium/images/appium.html",
    [c("ap", "Appium server", "npm -g appium", "backend", (150, 120), tag="本机未装"),
     c("xc", "Xcode Simulator", "simctl 不可用", "cloud", (150, 280), tag="环境受阻"),
     c("ref", "appium_reference.py", "补齐环境即可跑", "database", (400, 200)),
     c("fb", "fallback 移动视口", "iPhone 14 描述符+触屏（本机实跑）", "frontend", (400, 400)),
     c("case", "3 条触屏用例", "tap 下单/布局/竞态", "backend", (680, 400)),
     c("sut", "SUT :8928", "同一被测应用", "cloud", (680, 240))],
    [{"id": "a", "from": "ap", "to": "ref", "label": "理想路径", "variant": "dashed"},
     {"id": "b", "from": "xc", "to": "ref", "variant": "dashed"},
     {"id": "c", "from": "ref", "to": "fb", "label": "受阻则切换", "variant": "emphasis", "labelDy": 24},
     {"id": "d", "from": "fb", "to": "case"},
     {"id": "f", "from": "case", "to": "sut", "label": "tap 交互"}],
    [card("cyan", "诚实探测", ["simctl 不可用如实打印", "fallback 按清单约定计入完成"]),
     card("emerald", "fallback 等价性", ["tap=触屏不是鼠标", "视口+UA=真机描述符"]),
     card("rose", "Appium 要点", ["accessibility id 定位首选", "链路长，预留 2 倍时间"])],
)

# ---------------- 29 双基线 ----------------
SPECS["29_a11y_security"] = wf(
    "a11y 与安全双基线扫描", "29_a11y_security/images/a11y_security.html",
    [{"id": "sut", "label": "SUT"}, {"id": "axe", "label": "axe 无障碍"},
     {"id": "zap", "label": "ZAP 安全"}, {"id": "docs", "label": "产出"}],
    [{"id": "scan", "label": "双扫描器并行", "fromCol": 0, "toCol": 2},
     {"id": "fix", "label": "修复与记录", "fromCol": 3, "toCol": 4, "variant": "emphasis"}],
    [n("page", "sut", 0, "三个页面", "index/login/slow", "external"),
     n("axe", "axe", 1, "axe-core 规则", "critical/serious=0 门禁", "security"),
     n("found", "axe", 2, "实测违例", "label 缺失（critical）", "database", "已修复"),
     n("zap", "zap", 2, "ZAP baseline", "docker 被动扫+爬虫", "security"),
     n("warn", "zap", 3, "7 条 WARN", "安全头缺失，不阻断", "messagebus"),
     n("rpt", "docs", 4, "报告入 docs", "zap_report.html + 前后对比", "messagebus")],
    [e("a", "page", "axe", "注入规则", "emphasis"),
     e("b", "axe", "found", "扫出真问题", "emphasis"),
     e("h", "axe", "zap", "互不替代", "dashed"),
     e("c", "zap", "warn", "基线扫描", "default"),
     e("f", "warn", "rpt", "清单入 docs", "dashed"),
     e("g", "found", "rpt", "修复前后对比", "dashed")],
    [card("cyan", "axe 闭环", ["扫出 critical → 修 SUT", "复扫变绿，历史入 docs"]),
     card("emerald", "ZAP 语义", ["WARN 不阻断/FAIL 才拦", "-I 让警告不灭门"]),
     card("rose", "一键回归", ["本脚本即门禁", "CI 里接 lab 30"])],
    ["page", "axe", "zap", "warn", "rpt"],
)

# ---------------- 30 CI 流水线 ----------------
SPECS["30_local_ci"] = wf(
    "分层流水线：本地 make 与 GitHub Actions 同源", "30_local_ci/images/local_ci.html",
    [{"id": "push", "label": "触发"}, {"id": "early", "label": "快速层"},
     {"id": "heavy", "label": "重型层"}, {"id": "gate", "label": "门禁"}],
    [{"id": "chain", "label": "needs 链式依赖，失败即阻断", "fromCol": 0, "toCol": 4, "variant": "emphasis"}],
    [n("push", "push", 0, "push / act / make", "三种入口同一语义", "external"),
     n("unit", "early", 1, "unit-core + advanced", "纯 pytest 秒级", "backend"),
     n("api", "early", 2, "api-tests", "30 条真 HTTP", "backend"),
     n("e2e", "heavy", 2, "e2e-playwright", "Chromium 三部曲", "backend"),
     n("perf", "heavy", 3, "perf-smoke", "k6 thresholds", "backend"),
     n("a11y", "heavy", 4, "a11y-security", "axe+ZAP", "security"),
     n("art", "gate", 4, "报告 artifact", "ZAP/trace 上传", "database")],
    [e("a", "push", "unit", "第 0 层", "emphasis"), e("b", "unit", "api", "needs"),
     e("c", "api", "e2e", "needs"), e("d", "e2e", "perf", "needs"),
     e("f", "perf", "a11y", "needs"), e("g", "a11y", "art", "always()")],
    # mainPath 顺序 = 列单调：push0 unit1 api2 e2e2 perf3 a11y4 art4
    [card("cyan", "同源语义", ["make quality = 本地等价", "act push -j unit-core 本地复跑"]),
     card("emerald", "分层", ["秒级反馈在前", "重依赖在后"]),
     card("rose", "act 实测", ["Docker 内跑通 unit-core", "镜像 catthehacker/ubuntu"])],
    ["push", "unit", "api", "e2e", "perf", "a11y", "art"],
)


def main():
    count = 0
    for spec in SPECS.values():
        # workflow/sequence 画布压到一屏内（卡片信息已在各 lab README 的"怎么看"里）
        if spec["diagram_type"] == "workflow":
            spec["meta"]["viewBox"] = [1100, 660]
        if spec["diagram_type"] == "sequence":
            max_y = max(m.get("y", 0) for m in spec["messages"])
            if max_y > 460:  # 纵向压缩，保证画布纵横比在 viewer 一屏内
                k = 460 / max_y
                for msg in spec["messages"]:
                    msg["y"] = max(160, int(msg["y"] * k))  # 时间线最低从 160 起
                for seg in spec.get("segments", []):
                    if "from" in seg: seg["from"] = int(seg["from"] * k) + 20
                    if "to" in seg: seg["to"] = int(seg["to"] * k) + 20
                for act in spec.get("activations", []):
                    act["from"] = int(act["from"] * k)
                    act["to"] = int(act["to"] * k)
                max_y = 460
            spec["meta"]["viewBox"] = [1050, int(max_y + 145)]
            spec["meta"]["column_fit"] = "spread"
        if spec["diagram_type"] in ("workflow", "sequence"):
            spec.pop("cards", None)
        out_html = ROOT / spec["meta"]["output"]           # deliver 的输出
        ir_path = out_html.with_suffix(f".{spec['diagram_type']}.json")  # 图源 IR
        ir_path.parent.mkdir(parents=True, exist_ok=True)
        spec["meta"]["output"] = str(out_html)
        ir_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        if out_html.exists() and out_html.read_text(encoding="utf-8").startswith("{"):
            out_html.unlink()
        count += 1
    print(f"generated {count} IR files")


if __name__ == "__main__":
    main()
