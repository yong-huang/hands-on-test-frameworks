# 🧪 现有测试框架 30 小项目学习清单 · Todo List（pytest / Playwright / Cypress / Selenium）

> 通过 30 个小项目系统掌握**业界现成**的测试框架与工具链，全部**免费**、全部在 **MacBook 本地跑通**
> 覆盖：pytest 生态（单测/参数化/property-based）→ API/集成测试（testcontainers/Pact）→
> Web E2E 三巨头（Playwright / Cypress / Selenium）→ 性能（Locust/k6）→ 移动（Appium）→ 本地 CI 流水线
> **共享被测应用**：项目 11 造一个带前端的 FastAPI 小应用（SUT），后续所有框架都测它——同目标才好对比
> 每项目 80-300 行；不用任何付费 SaaS（Percy / BrowserStack / Sauce / TestRail 全部不碰）
> 预计周期：8-10 周（每天有效学习 2-3 小时）

## 🧭 学习路线图

```
 阶段一/二 (1-10)          阶段三 (11-15)         阶段四 (16-20)
 pytest 单测基本功    →    API/集成/契约      →   Playwright E2E
 ─────────────────────────────────────────────────────────────
 阶段五 (21-25)                              阶段六 (26-30)
 Cypress + Selenium + 三框架对比      →   性能/移动/a11y/本地CI 终极串联
        ↑ 全程共用同一个被测应用 SUT（项目 11 造）↑
```

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始测试框架学习项目「[名称]」，被测对象是 [SUT/函数]。请给我完整代码约 [行数] 行（[pytest/Playwright/Cypress/Selenium]），macOS 可运行，包含断言和运行命令。只输出代码。` |
| **选型/对比** | `对比 [框架A] 和 [框架B] 在 [场景] 下的差异：API 风格、等待机制、调试体验、并行能力、生态，给出选型建议。` |
| **用例失败排查** | `我的 [框架] 测试在 [操作] 时 [失败现象]，报错：[粘贴]。请分析根因（选择器/等待/异步/环境）并给修复。` |
| **重构为可维护** | `把这份测试代码重构为 [POM/fixture/分层] 结构：[粘贴代码]。要求可读性与复用性，不改变断言语义。` |

## 📊 总进度

进度：██░░░░░░░░░░░░░░░░░░ 0/30 (0%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：pytest 单测基本功 | 5 | 0 |
| 第二阶段：高级单测技术 | 5 | 0 |
| 第三阶段：API、集成与契约测试 | 5 | 0 |
| 第四阶段：Playwright 现代 E2E | 5 | 0 |
| 第五阶段：Cypress 与 Selenium 三国杀 | 5 | 0 |
| 第六阶段：性能、移动与流水线交付 | 5 | 0 |
| **合计** | **30** | **0** |

---

## 🗂️ 第一阶段：pytest 单测基本功（项目 1-5）

> **目标**：把 pytest 用成母语：fixture、参数化、mock、覆盖率——一切测试的地基

### [ ] 项目 1：pytest 起步与运行规则

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~120 行 |
| **核心知识点** | venv + 安装、断言重写、测试发现规则、`-v/-s/-k/-x`、`pytest.ini` 配置 |
| **产出物** | `pytest-lab/01_basics`：对一个温度换算模块写 15 条用例 |
| **验收标准** | 会用 `-k` 圈选用例、`-x` 早停；故意写一条失败用例看懂断言回溯输出 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 1「起步」。请给我一个温度换算模块 + 15 条 pytest 用例（含故意失败的 1 条），约 120 行，附 pytest.ini 与常用运行命令说明。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 2：fixture 与 conftest

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | fixture 作用域（function/module/session）、yield 式 setup/teardown、conftest.py 共享、fixture 工厂模式 |
| **产出物** | `02_fixtures`：临时目录 + 数据库连接 + 工厂 fixture 三件套 |
| **验收标准** | 用 session 级 fixture 证明昂贵资源只建一次；工厂 fixture 支持一条用例造 N 份不同数据 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 2「fixture」。请给我约 180 行代码：演示 function/module/session 作用域计数、yield teardown、conftest 共享、工厂 fixture（可造 N 个用户），附运行与断言。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 3：参数化与异常断言

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | `@pytest.mark.parametrize`（ids/笛卡尔积）、`pytest.raises` 匹配异常、`parametrize` + `indirect` 组合 |
| **产出物** | `03_parametrize`：一个解析器的正常/边界/异常用例矩阵 |
| **验收标准** | 一条用例覆盖 20+ 输入组合且报告可读（ids 命名）；异常断言能校验消息内容 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 3「参数化」。请给我约 150 行代码：对一个配置解析器做参数化矩阵（含 ids 可读命名、笛卡尔积、indirect 传 fixture）、pytest.raises 校验异常消息。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 4：mock 与测试替身

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `monkeypatch`、`unittest.mock`（patch/MagicMock/call 断言）、fake 实现 vs mock 对比、`freezegun` 冻结时间 |
| **产出物** | `04_mock`：给一个"邮件通知服务"写替身测试（不发真邮件）|
| **验收标准** | 同一场景分别用 mock 和 fake 各写一遍，注释说明两者取舍；冻结时间测试"当天截止"逻辑 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 4「mock 与替身」。请给我约 200 行代码：邮件通知服务的 mock 版（patch+call 断言）与 fake 版（内存实现）各一套，monkeypatch 环境变量、freezegun 冻结时间测截止逻辑，附取舍注释。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 5：覆盖率与质量门禁

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~100 行 + 配置 |
| **核心知识点** | pytest-cov、行/分支覆盖率、`--cov-fail-under` 门禁、coverage.xml/HTML 报告、排除规则 |
| **产出物** | `05_coverage`：给前 4 项的代码配门禁 + HTML 报告 |
| **验收标准** | 分支覆盖率从 70% 提到 ≥90%（补漏用例）；门禁低于阈值时 CI 退出码非 0 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 5「覆盖率」。请给我约 100 行代码+配置：pytest-cov 分支覆盖率、--cov-fail-under 门禁、HTML 报告、.coveragerc 排除规则，附一个故意不达标就失败的演示。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第二阶段：高级单测技术（项目 6-10）

> **目标**：用高级武器从"测得对"到"测得深"：property-based、快照、异步、并行、自定义插件

### [ ] 项目 6：property-based 测试（Hypothesis）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | `@given` 策略、自动收缩（shrink）、不变量思维、`@example` 固定回归案例、状态ful 测试（RuleBasedStateMachine）|
| **产出物** | `06_hypothesis`：对序列/编解码/JSON 解析器做性质测试 |
| **验收标准** | 至少挖出 1 个手写用例想不到的边界 bug（记录进报告）；失败用例被收缩成最小样例 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 6「Hypothesis」。请给我约 180 行代码：对 编解码往返/排序不变量/JSON解析器 用 @given 做性质测试，含 @example 回归、收缩演示，附一个 RuleBasedStateMachine 有状态测试。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 7：快照测试（syrupy）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | snapshot 文件管理、`--snapshot-update`、API 响应/大对象回归、审查流程（防"无脑更新快照"）|
| **产出物** | `07_snapshot`：对一段 API JSON 与渲染 HTML 做快照回归 |
| **验收标准** | 改一处输出后测试变红 → 有意更新快照变绿；快照 diff 能在报告里看清变化点 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 7「快照测试」。请给我约 150 行代码：syrupy 对 API JSON 与 HTML 片段做快照，演示 破坏→红→更新→绿 流程与 diff 查看。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 8：异步与时间测试

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | pytest-asyncio、async fixture、`freezegun`/`time-machine`、重试/超时逻辑的确定性测试 |
| **产出物** | `08_async`：测一个带重试+退避的异步客户端 |
| **验收标准** | 重试 3 次的用例总耗时 <1s（时间被冻结/加速）；asyncio 报错能被 pytest 正确归因 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 8「异步与时间」。请给我约 200 行代码：pytest-asyncio + async fixture，测一个指数退避重试客户端，用 time-machine 加速时间流逝（重试用例 <1s 跑完），附超时与取消用例。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 9：并行与测试选择策略

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | pytest-xdist 并行、用例独立性改造（共享状态坑）、`-m` marker 分层（smoke/e2e）、durations 找慢用例 |
| **产出物** | `09_xdist`：把一个 200 用例套件从 60s 并行到 <15s |
| **验收标准** | `-n auto` 结果与串行一致（无互相污染）；marker 分层跑 smoke 只需 5s |

**🤖 开始提示词**：
> `我要开始 pytest 项目 9「并行与分层」。请给我约 150 行代码：pytest-xdist 并行改造（修掉 3 处共享状态污染）、-m marker 分层 smoke/e2e、--durations 找慢用例，输出前后耗时对比。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 10：写一个自己的 pytest 插件

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | 钩子体系（`pytest_collection_modifyitems`/`pytest_runtest_makereport`）、自定义 marker、失败自动截图/落日志的雏形 |
| **产出物** | `10_plugin`：`pytest-ministore-report` 小插件（本地安装）|
| **验收标准** | 插件能：自动给 slow 用例打标、失败用例自动落一份上下文 JSON；在两个不同项目里 pip install 复用 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 10「自定义插件」。请给我约 200 行代码：一个可 pip 安装的插件，实现 自定义 marker 校验、失败用例自动写上下文 JSON（用 runtest_makereport 钩子），附 pyproject 与两个项目的复用示例。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第三阶段：API、集成与契约测试（项目 11-15）

> **目标**：越过单测边界：真 HTTP、真数据库、真依赖容器；同时造出全程共用的被测应用 SUT

### [ ] 项目 11：造被测应用 SUT（FastAPI + 前端）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | FastAPI CRUD + SQLite、静态页（HTML/JS 表单）、OpenAPI 文档、种子数据脚本 |
| **产出物** | `sut-app/`：订单管理小应用（后续 19 个项目都测它）|
| **验收标准** | `uvicorn` 起服务后：API 增查删可用；浏览器页面可下单；一条 `make seed` 造演示数据 |

**🤖 开始提示词**：
> `我要开始测试项目 11「被测应用 SUT」。请给我约 250 行代码：FastAPI 订单管理（SQLite + /orders CRUD + 静态 HTML 表单页 + 种子数据脚本），附 uvicorn 启动与自测命令。这是后续所有测试项目的被测对象，接口要稳定。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 12：API 测试套件（requests/httpx + pytest）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | session 级 client fixture、测试数据生命周期（自造自清）、jsonschema/pydantic 响应校验、负向用例（4xx）|
| **产出物** | `12_api_tests`：对 SUT 的 30 条 API 用例 |
| **验收标准** | 用例互相独立可乱序执行；响应 schema 校验覆盖全部端点；负向用例（缺字段/不存在 id）全过 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 12「API 测试」。请给我约 250 行代码：httpx client fixture 对 SUT 写 30 条用例（CRUD+分页+4 个负向），pydantic 响应模型校验，测试数据自造自清保证乱序可跑。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 13：数据库集成测试（真库 + 隔离）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | 事务回滚隔离 vs 截表隔离、迁移测试（建表脚本可重复执行）、并发写冲突用例 |
| **产出物** | `13_db_tests`：SUT 数据层的集成测试 |
| **验收标准** | 两种隔离策略各跑一遍并对比速度/干净度；迁移脚本在空库和旧库上都能执行成功 |

**🤖 开始提示词**：
> `我要开始 pytest 项目 13「数据库集成」。请给我约 200 行代码：对 SUT 的 SQLite 数据层写集成测试，实现 事务回滚 与 截表 两种隔离（fixture 切换）、迁移可重复执行验证、一条并发写冲突用例。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 14：Testcontainers 真依赖容器化

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | testcontainers-python、Postgres/Redis 容器随测试起停、session 级容器复用、Docker 依赖说明 |
| **产出物** | `14_testcontainers`：把 SUT 数据层切换到真 Postgres 测试 |
| **验收标准** | 测试运行时自动起 Postgres 容器、结束自动销毁；对比 SQLite 版发现的差异问题 ≥1 条（记录）|

**🤖 开始提示词**：
> `我要开始 pytest 项目 14「Testcontainers」。请给我约 200 行代码：testcontainers-python 起 Postgres（session 级复用），SUT 数据层切到 Postgres 跑集成测试，输出与 SQLite 行为差异记录。附 Docker 前置说明。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 15：契约测试（Pact）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Consumer-Driven Contracts、pact-python（无 JVM）、pact 文件本地交换、provider verify |
| **产出物** | `15_pact`：前端 JS 作为 consumer + SUT 作为 provider 的契约闭环 |
| **验收标准** | consumer 生成的 pact 文件 → provider 端 verify 通过；故意改字段名后 verify 变红 |

**🤖 开始提示词**：
> `我要开始测试项目 15「Pact 契约」。请给我约 250 行代码：pact-python 写 consumer（对 SUT /orders 的期望）生成 pact 文件，provider 端 verify 脚本，演示 字段改名→verify 失败→修复。不用付费 broker，本地文件交换。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第四阶段：Playwright 现代 E2E（项目 16-20）

> **目标**：掌握当前最强的开源 E2E 框架：自动等待、网络拦截、多浏览器、trace 调试

### [ ] 项目 16：Playwright 入门（pytest-playwright）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | 安装浏览器、`pytest-playwright` fixture（page）、codegen 录制、首个 SUT 端到端用例 |
| **产出物** | `16_pw_basics`：SUT 页面 下单→查询→删 3 条用例 |
| **验收标准** | codegen 录制转手写；3 条用例对 Chromium 跑绿；会打开 trace 查看执行过程 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 16「入门」。请给我约 150 行代码：pytest-playwright 对 SUT 页面写 下单/查询/删除 3 条用例（Chromium），附安装（pip+playwright install）、codegen 用法、trace 打开命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 17：定位器与等待哲学

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | role/text/CSS 定位器优先级、auto-wait vs 显式 `expect`、网络空闲、避免 sleep 的反模式清单 |
| **产出物** | `17_pw_locators`：SUT 加一个"慢加载"页面专治等待问题 |
| **验收标准** | 5 条用例覆盖 竞态/延迟渲染/轮询刷新 场景全部稳定（连续跑 10 次不红）|

**🤖 开始提示词**：
> `我要开始 Playwright 项目 17「定位与等待」。请给我约 200 行代码：SUT 增加慢加载演示页（延迟渲染/轮询/竞态按钮），测试用 role 定位+web first 断言稳定处理，附 10 连跑脚本与反模式（sleep）对照注释。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 18：页面对象模型（POM）与 fixture 分层

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Page Object 封装、fixture 注入 page 对象、业务断言与交互分离、目录结构规范 |
| **产出物** | `18_pw_pom`：把 16-17 的用例重构为 POM 架构 |
| **验收标准** | 页面选择器只存在于 page object；重构前后用例数量与断言语义不变；新增一条用例只需 10 行 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 18「POM」。请给我约 250 行代码：把 SUT 测试重构为 pages/ 页面对象 + conftest fixture 注入，选择器收口到 page object，演示新增一条用例只需 10 行。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 19：网络拦截与登录态复用

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `page.route` mock 后端、错误注入（超时/500）、storageState 保存登录、多角色会话（admin/user）|
| **产出物** | `19_pw_network`：mock 场景套件 + 登录态复用 |
| **验收标准** | 不启动后端也能跑前端交互用例；注入 500 验证页面报错提示；admin/user 双角色用例切换会话无串号 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 19「网络拦截」。请给我约 200 行代码：page.route mock SUT 后端（含 500/超时注入）、storageState 登录复用 fixture、admin/user 双角色会话用例。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 20：多浏览器、视觉回归与 trace 报告

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | Chromium/Firefox/WebKit 三核跑批、`--screenshot` 视觉对比、trace viewer、失败自动留痕（截图+trace+video）|
| **产出物** | `20_pw_quality`：全浏览器回归 + 失败留痕配置 |
| **验收标准** | 三核全绿（WebKit 兼容问题至少记录 1 条）；人为失败用例自动产出 截图+trace 可回放 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 20「多核与留痕」。请给我约 200 行代码：pytest 参数化三浏览器跑 SUT 回归、失败自动 截图+trace+video 配置（pytest_playwright hook 或 playwright.config）、截图基线对比脚本。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第五阶段：Cypress 与 Selenium 三国杀（项目 21-25）

> **目标**：补齐另外两大主流框架，最后用同一组用例做硬核对比，形成自己的选型判断

### [ ] 项目 21：Cypress 入门

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行（JS spec）|
| **核心知识点** | npm 工程、Cypress 目录约定、运行器 UI vs headless、SUT 前 3 条用例移植 |
| **产出物** | `cypress-lab/`：对 SUT 复刻项目 16 的 3 条用例 |
| **验收标准** | `cypress open` 调试体验走通；headless 模式跑绿；对比 Playwright 写出 3 条第一印象差异 |

**🤖 开始提示词**：
> `我要开始 Cypress 项目 21「入门」。请给我约 150 行代码：npm 初始化 Cypress、对 SUT 写 下单/查询/删除 3 条 spec，附 open/headless 运行命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 22：Cypress 进阶（intercept/session/自定义命令）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `cy.intercept` 网络桩、`cy.session` 登录复用、自定义命令、失败重试机制与 flaky 治理 |
| **产出物** | `cypress-lab/advanced`：复刻项目 19 的 mock+会话场景 |
| **验收标准** | intercept 模拟 500 验证 UI 报错；cy.session 复用登录；自定义命令 `cy.createOrder()` 被多条 spec 复用 |

**🤖 开始提示词**：
> `我要开始 Cypress 项目 22「进阶」。请给我约 200 行代码：cy.intercept mock SUT 后端（500 注入）、cy.session 登录复用、自定义命令封装 createOrder，对应 Playwright 项目 19 的场景。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 23：Selenium 基础（WebDriver 协议直感）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | Selenium Manager 自动驱动、三大浏览器 session、显式等待（WebDriverWait/expected_conditions）、与自动等待框架的差异 |
| **产出物** | `selenium-lab/`：SUT 基础用例 + 一个"没有等待就必挂"的演示 |
| **验收标准** | 同一脚本跑 Chrome/Safari（macOS 原生）双浏览器；无等待版必挂、显式等待版稳定（亲手体会差距）|

**🤖 开始提示词**：
> `我要开始 Selenium 项目 23「基础」。请给我约 200 行代码（Python selenium）：Selenium Manager 起 Chrome+Safari，对 SUT 写基础用例；同一页面写 无等待（必挂）与 WebDriverWait（稳定）两版对比，附运行命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 24：Selenium 进阶（POM + Actions + 本地 Grid）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | POM 在 Selenium 的实现、ActionChains（拖拽/悬停）、JS 执行器、Docker 起本地 Selenium Grid 并行 |
| **产出物** | `selenium-lab/advanced` + `docker-compose.grid.yml` |
| **验收标准** | Grid 上 Chrome×2 并行跑套件耗时≈串行一半；拖拽用例稳定；截图能力接进失败钩子 |

**🤖 开始提示词**：
> `我要开始 Selenium 项目 24「进阶」。请给我约 250 行代码：Selenium POM、ActionChains 拖拽/悬停用例、失败自动截图钩子、docker-compose 起本地 Grid 并 2 个 Chrome 并行跑批的脚本。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 25：三框架硬对比（同一 SUT 同样用例）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行（报告 + 复测脚本）|
| **核心知识点** | 统一 10 条用例矩阵：速度（并行/串行耗时）、稳定性（连跑 20 次）、调试体验（trace/Timeline/日志）、API 风格、生态 |
| **产出物** | `25_comparison/docs/comparison.md` 对比报告 + `run_all.sh` |
| **验收标准** | 报告含实测数据表（不是抄官网）；给出"什么场景选谁"的结论（如：新项目 Web E2E 首选、遗留 JS 项目、多语言团队）|

**🤖 开始提示词**：
> `我要开始测试项目 25「三框架对比」。请给我约 200 行：run_all.sh 一键跑 Playwright/Cypress/Selenium 各 10 条同语义用例各 20 轮，统计 耗时/稳定性/失败留痕 到 CSV；另给 comparison.md 报告模板（数据表+场景选型结论栏）。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第六阶段：性能、移动与流水线交付（项目 26-30）

> **目标**：测试版图收尾：性能、移动、无障碍/安全，最后把 1-29 全部串进本地 CI 流水线

### [ ] 项目 26：性能测试（Locust）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | Locust 场景类（任务权重/等待时间）、阶梯加压、RPS/延迟/P95 图表解读、找 SUT 性能拐点 |
| **产出物** | `26_locust`：对 SUT API 的压测套件 + 拐点报告 |
| **验收标准** | 10→100 并发阶梯加压出图；报告指出 SUT 的 RPS 拐点与瓶颈猜测（SQLite 锁/CPU）|

**🤖 开始提示词**：
> `我要开始性能项目 26「Locust」。请给我约 200 行代码：对 SUT API 写 Locust 场景（读写混合、任务权重）、headless 阶梯加压（10→100 并发）脚本、输出 RPS/P95 拐点报告模板。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 27：负载与阈值（k6）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行（JS）|
| **核心知识点** | k6 场景类型（ramping/smoke/spike）、thresholds 质量门禁、checks vs 断言、与 Locust 的取舍 |
| **产出物** | `27_k6`：SUT 的 k6 场景 + 阈值门禁 |
| **验收标准** | spike 场景复现 SUT 突刺；thresholds 不达标时退出码非 0（可当 CI 门禁）；报告对比 Locust 差异 |

**🤖 开始提示词**：
> `我要开始性能项目 27「k6」。请给我约 180 行代码：k6 对 SUT 的 smoke/ramping/spike 三场景，thresholds 设 P95<500ms 与错误率<1%，不达标退出码非 0，附 brew 安装与运行命令、与 Locust 对比注记。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 28：移动端测试（Appium，选做攻坚）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Appium 2 + Xcode Simulator（macOS 免费）、capabilities、元素定位（accessibility id）、iOS/Android 双端思路 |
| **产出物** | `28_appium`：对 iOS 示例 App（或 SUT 移动网页）的用例 |
| **验收标准** | Simulator 内自动完成 启动→操作→断言；若环境受阻，fallback 用 Playwright 移动视口+触屏模拟完成同等用例（如实记录）|
| **风险提示** | Appium 环境链最长（Xcode+driver），预留 2 倍时间；fallback 方案也算完成 |

**🤖 开始提示词**：
> `我要开始移动测试项目 28「Appium」。请给我约 250 行代码：Appium 2 + pytest 对 iOS Simulator 示例 App 的用例（accessibility id 定位），附 macOS 环境安装清单；另给 Playwright 移动视口 fallback 版同等用例。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 29：无障碍与安全基线测试

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | axe-core 集成 Playwright 扫 WCAG 违例、ZAP baseline 本地扫描 SUT、把两类问题变成可回归用例 |
| **产出物** | `29_a11y_security`：a11y 用例 + ZAP 报告 |
| **验收标准** | SUT 修掉 axe 扫出的 High 级违例（用例变绿）；ZAP baseline 扫出的问题清单入 docs；两者均可一键重跑 |

**🤖 开始提示词**：
> `我要开始测试项目 29「a11y 与安全基线」。请给我约 200 行代码：@axe-core/playwright 对 SUT 全页扫描断言无 critical 违例，ZAP baseline 扫描脚本（docker 版 zaproxy），报告落 docs/，附修复前后对比流程。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 🏁 项目 30：终极串联——本地 CI 流水线

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行（workflow + 脚本 + 报告聚合）|
| **核心知识点** | 分层流水线（单测→API→E2E→性能冒烟→门禁）、GitHub Actions（免费额度）/act 本地验证、HTML 报告聚合（pytest-html + Playwright report + k6）、失败即阻断的 exit code 语义 |
| **产出物** | `.github/workflows/tests.yml` + `Makefile`（`make quality` 一键全跑）+ 报告聚合页 |
| **验收标准** | push 后流水线自动：pytest 全量 → API → 三框架 E2E → k6 smoke → 阈值门禁；任一环失败即红且报告可下载；act 本地能复跑同一 workflow |
| **前置** | 项目 1-29 |

**🤖 开始提示词**：
> `我要开始测试项目 30「本地 CI 串联」。请给我约 250 行代码：GitHub Actions workflow（分层跑 pytest/API/Playwright/Cypress/Selenium/k6，artifact 上传各报告），Makefile 的 make quality 一键本地等价执行，act 本地验证命令，失败阻断语义说明。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-5（pytest 基本功）| 5 |
| **第 2 周** | 项目 6-10（高级单测）| 5 |
| **第 3-4 周** | 项目 11-15（SUT + API/集成/契约）| 5 |
| **第 5 周** | 项目 16-20（Playwright 全家桶）| 5 |
| **第 6-7 周** | 项目 21-25（Cypress/Selenium/对比）| 5 |
| **第 8-9 周** | 项目 26-30（性能/移动/CI 终极串联）| 5 |

## 🏆 里程碑

- [ ] **完成项目 1-5** → pytest 母语级：fixture/参数化/mock/覆盖率门禁
- [ ] **完成项目 6-10** → 高级单测：性质测试/快照/异步/并行/自定义插件
- [ ] **完成项目 11-15** → API/集成/契约测试闭环 + 拥有自己的被测应用
- [ ] **完成项目 16-20** → Playwright 现代 E2E 全技能（拦截/POM/多核/trace）
- [ ] **完成项目 21-25** → 三大 E2E 框架实战 + 有数据支撑的选型报告
- [ ] **完成项目 26-30** → 性能/移动/a11y 版图 + **一键本地 CI 流水线交付**
- [ ] **全部完成** → 独立为一个产品设计完整测试策略并落地工具链

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| | | | | |
| | | | | |
| | | | | |

## 🔧 环境配置

```bash
# 0. 原则：全程免费——只用开源工具本地跑，不注册任何付费 SaaS

# 1. Python 线（pytest / Playwright-Python / Locust / Pact / testcontainers）
brew install python@3.12
python3.12 -m venv ~/.venvs/pytest-lab && source ~/.venvs/pytest-lab/bin/activate
pip install pytest pytest-cov pytest-xdist pytest-asyncio pytest-playwright \
            hypothesis syrupy time-machine freezegun httpx requests \
            testcontainers[postgres] pact-python locust fastapi uvicorn

# 2. Playwright 浏览器（免费下载）
playwright install            # Chromium + Firefox + WebKit 三核

# 3. Node 线（Cypress / k6 脚本 / axe）
brew install node@20
npm init -y && npm install -D cypress @axe-core/playwright playwright

# 4. Selenium（浏览器你已有；驱动由 Selenium Manager 自动下载）
pip install selenium          # Safari 需开启：safaridriver --enable（系统自带）

# 5. 性能与安全
brew install k6               # k6 CLI
docker pull zaproxy/zap-stable # ZAP（项目 29，免费 OSS）

# 6. 本地 CI（项目 30）
brew install act              # 本地跑 GitHub Actions
# 真实 GitHub Actions：public repo 免费 / private 每月 2000 分钟免费额度

# 7. 移动端（项目 28，选做）
# Xcode（App Store 免费）+ Appium 2：npm install -g appium && appium driver install uiautomator2 xcuitest

# 8. 每项目开工前
pytest --collect-only -q      # 先看用例收集是否如预期
```

## ⚠️ 与已有清单的关系（避免重复学习）

| 已有内容 | 关系 |
|:---|:---|
| `0x_learn_test_framework_apple/`（自研硬件测试框架 14 项目）| 你**自己造框架**的实战线（设备发现/引擎/设备池/CI）；本清单是**学现成框架**的通用线，前者第 07 课的 CI 可用本清单项目 30 的做法升级 |
| `0x_learn_aws_localstack/`（AWS 本地实验）| 云服务功能验证；本清单的 E2E/性能方法学可直接复用到云上应用的验收层 |
