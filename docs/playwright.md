# 🎭 Playwright 进阶 19 小项目学习清单 · Todo List（TypeScript 原生栈）

> 通过 19 个小项目（每项目 100-400 行 TS 测试代码）掌握 Playwright **深水区**：定位引擎、认证矩阵、视觉回归、组件测试、并行 sharding、本地 CI
> 全部**免费**、全部在 **MacBook 本地跑通**；TypeScript 原生栈（`@playwright/test`），不碰任何付费 SaaS
> **完整系统型串联**：项目 2 造共享靶场 `pw-store`（Vite+React），后续 17 个项目全部测它，每阶段末 ⛓️ 接线，项目 19 🏁 终极串联
> 与已完成的实验 16-20（Python 基础线）**互补**：跳过入门与等待基础，直接进阶——见文末关系表
> 预计周期：6-8 周（每天 1-2 小时）
>
> ✅ **已全部完成（2026-09-30）**。交付说明与清单的差异：
> ① 实验落在仓库根 `playwright/` 目录（独立于 labs/），编号 01-19，端口约定 90NN；
> ② 共享靶场为 `playwright/02_pw_sut` 的 pw-store（Vite+React+Node 服务，端口 9002），
>    实现过程中为系列补充了深色样式、locale 跟随、订单分页等被测能力；
> ③ 组件测试锁 `@playwright/experimental-ct-react` 1.62.1（与 test 同版本，1.63 稳定版未发布）；
> ④ lab 18 的 act 本地校验依赖代理与 `--bind`（踩坑链见其 README）；
> ⑤ 🏁 终极串联：`playwright/19_pw_final_suite/run_suite.sh` 一条命令 15 套件
>    163 用例全绿（78s），系列总目录见 `playwright/README.md`。

## 🏗️ 终极蓝图（项目 19 完成时的完整回归套件）

```
              🏁 pw-store 全功能回归套件（项目 19）
   认证矩阵 │ 核心路径 │ 视觉基线 │ 实时推送 │ i18n/a11y │ API+UI 混合
 ───────────────────────┬──────────────────────────
     playwright.config.ts（projects 设备矩阵 / sharding / 多 reporter / retries）
                        │
     自定义 fixtures（角色登录态 / 数据工厂 / 类型安全 page objects）
                        │
              🎯 pw-store（项目 2 造的 SUT，Vite+React）
   登录/角色 │ 订单 CRUD │ 文件上传下载 │ WebSocket 推送 │ i18n │ 慢加载组件
```

每阶段末把该阶段能力**接线**进共享套件；项目 19 一条命令跑全部。

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始 Playwright 项目「[名称]」，被测对象是 pw-store。请给我完整 TypeScript 代码约 [行数] 行（@playwright/test），macOS 可运行，含断言和运行命令。只输出代码。` |
| **排障** | `我的 Playwright 测试在 [操作] 时 [失败现象]，报错：[粘贴]。请分析根因（选择器/等待/异步/mock）并给修复。` |
| **config/矩阵调优** | `审查这份 playwright.config.ts：[粘贴]。给出 projects 矩阵、并行、retries、reporter 的优化建议并给修改版。` |
| **flaky 排查** | `这条用例连跑 N 次有 [k] 次失败：[粘贴代码+失败截图]。请定位竞态/等待/隔离问题，用 expect.poll 或 fixture 改稳定。` |

## 📊 总进度

进度：███████████████████ 19/19 (100%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：TS 栈与靶场 | 2 | 2 |
| 第二阶段：测试深水区 | 6 | 6 |
| 第三阶段：工程化流水 | 5 | 5 |
| 第四阶段：真实场景攻坚 | 4 | 4 |
| 第五阶段：CI 交付与终极串联 | 2 | 2 |
| **合计** | **19** | **0** |

---

## 🗂️ 第一阶段：TS 栈与靶场（项目 1-2）

> **目标**：立起 TS 原生测试栈，造一个功能足够丰富的被测应用，后续 17 个项目都打它

### [x] 项目 1：TS 原生测试栈起步（@playwright/test）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~120 行 |
| **核心知识点** | `@playwright/test` 与 pytest-playwright 的差异、playwright.config.ts（baseURL/retries/reporter）、test fixtures 初识、三浏览器首跑 |
| **产出模块** | `playwright/01_pw_ts_stack` |
| **技术栈** | Node 22 + pnpm + @playwright/test 1.63（✅ 已实测三浏览器跑通）|
| **验收标准** | 一条用例 `npx playwright test` 三浏览器全绿；config 改 baseURL 后用例零改动；`--ui` 能打开 UI Mode |
| **前置** | 无（实验 16-20 的 Python 基础不要求复习）|

**🤖 开始提示词**：
> `我要开始 Playwright 项目 1「TS 原生测试栈起步」。请给我约 120 行代码：pnpm 初始化 @playwright/test、playwright.config.ts（baseURL/retries/HTML reporter/chromium+firefox+webkit 三 project）、一条演示 fixture 与 web-first 断言的用例，附三浏览器运行命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 2：⛓️ 造靶场 SUT「pw-store」（Vite+React 多功能应用）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~400 行 |
| **核心知识点** | Vite+React 脚手架、登录态与角色（admin/customer）、订单 CRUD、文件上传下载、WebSocket 实时推送、i18n（中/英）、慢加载组件、iframe+shadow DOM 演示区 |
| **产出模块** | `playwright/02_pw_sut`（SUT 源码 + 启停脚本）|
| **⚠️ 风险** | `npm create vite` 需联网（✅ npm 直连已实测可用）；若脚手架失败，fallback：手写 vite.config + 最小 React 工程，学习目标不变 |
| **验收标准** | `pnpm dev` 起服后 `curl -s localhost:9002/api/health` 探活通过；登录/订单/上传/推送/i18n/慢组件 6 个功能区页面可见可点；启停脚本 `apply/observe/clean` 干净无残留 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 2「造靶场 pw-store」。请给我约 400 行代码：Vite+React 应用含 admin/customer 登录、订单 CRUD、文件上传下载、WebSocket 推送（订单状态变更广播）、中英文 i18n、慢加载组件、iframe 与 shadow DOM 演示区，附 apply/observe/clean 启停脚本。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第二阶段：测试深水区（项目 3-8）

> **目标**：吃透 Playwright 区别于其他框架的核心能力——定位引擎、会话复用、网络控制、视觉回归、组件测试、调试武器库

### [x] 项目 3：定位引擎深水区（iframe / shadow DOM / 严格模式）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | iframe 帧穿透（frameLocator）、shadow DOM 定位、`locator.filter`/`nth`/链式收窄、strict mode 歧义报错、`locator.or()` |
| **产出模块** | `playwright/03_pw_locators_pro` |
| **前置** | 项目 2 |
| **验收标准** | 对 SUT 的 iframe 与 shadow DOM 区域共 10 条用例连跑 10 次不红；故意写的歧义选择器被 strict mode 拒绝（断言报错文案）|

**🤖 开始提示词**：
> `我要开始 Playwright 项目 3「定位引擎深水区」。被测对象是 pw-store。请给我约 150 行 TypeScript 代码：frameLocator 穿 iframe 订单面板、shadow DOM 组件定位、filter/链式收窄演示、strict mode 歧义选择器负例断言，附 10 连跑脚本。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 4：认证与多用户矩阵（storageState 深度）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | global-setup 预登录、storageState 按角色分文件、自定义 `adminPage/customerPage` fixture、权限矩阵用例、会话过期场景模拟 |
| **产出模块** | `playwright/04_pw_auth` |
| **前置** | 项目 2 |
| **验收标准** | 全套件登录请求只出现 1 次/角色（route 计数断言）；admin/customer 权限矩阵 6 条断言全过（admin 可删、customer 仅可见等）|

**🤖 开始提示词**：
> `我要开始 Playwright 项目 4「认证与多用户矩阵」。请给我约 200 行 TypeScript 代码：global-setup 预登录两角色、storageState 按角色落盘、adminPage/customerPage fixture、权限矩阵用例（6 断言）、route 计数验证登录只执行一次。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 5：网络控制进阶（HAR 回放 / 错误注入 / 慢接口模拟）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `page.routeFromHAR` 录制与回放、后端离线跑前端用例、按 URL 模式注入 500/超时/慢响应、`waitForResponse` 与竞态 |
| **产出模块** | `playwright/05_pw_network_pro` |
| **前置** | 项目 2 |
| **验收标准** | 不启动 SUT 后端（仅前端静态服务）用 HAR 回放跑通核心下单路径；注入 500 后用例断言到正确错误 UI；慢接口 3s 模拟下断言 loading 态出现 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 5「网络控制进阶」。请给我约 200 行 TypeScript 代码：routeFromHAR 录制+回放（离线跑通下单）、URL 模式注入 500/超时/3s 慢响应三组用例、waitForResponse 断言，附录制与回放两条命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 6：视觉回归流水线（toHaveScreenshot 全流程）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | `toHaveScreenshot` 基线管理、mask 动态区域、maxDiffPixelRatio 阈值、多浏览器基线目录、`--update-snapshots` 流程、基线入库策略 |
| **产出模块** | `playwright/06_pw_visual` |
| **前置** | 项目 2 |
| **验收标准** | 故意改 1px CSS → 测试变红；`--update-snapshots` 更新基线 → 转绿；`git status` 显示基线 png 入库；mask 掉时间戳后订单页快照稳定 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 6「视觉回归流水线」。请给我约 180 行 TypeScript 代码：SUT 关键页 toHaveScreenshot 基线、mask 时间戳/头像等动态区、阈值配置、基线更新与入库流程脚本，附"改 1px 变红→更新转绿"的演示命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 7：组件测试（@playwright/experimental-ct-react）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | ct-react 挂载（`mount`）、props/事件/slot 测试、组件级 fixture、ct 与 E2E 的分工边界 |
| **产出模块** | `playwright/07_pw_component` |
| **技术栈** | @playwright/experimental-ct-react（与 test 同版本）|
| **前置** | 项目 2 |
| **⚠️ 风险** | ct 插件本机未单独实测（⚠️ 开工探活）：先跑官方模板最小挂载；失败 fallback：降级为「轻挂载集成测试」（vite preview + 单组件页），学习目标不变 |
| **验收标准** | 按钮/订单表单/订单卡片 3 个组件 ct 用例全绿；ct 套件运行时长 < E2E 套件的 1/10（报告数值对比）|

**🤖 开始提示词**：
> `我要开始 Playwright 项目 7「组件测试」。请给我约 200 行 TypeScript 代码：pw-store 的 OrderCard/OrderForm/Button 三个 React 组件的 ct-react 用例（mount、props、事件、无障碍快照），playwright-ct.config，附 ct 与 E2E 耗时对比命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 8：调试武器库（UI Mode / trace viewer / VS Code）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~100 行（以配置与流程为主）|
| **核心知识点** | UI Mode watch 与时间旅行、trace viewer 三打开方式（配置/CLI/API）、`--debug` Inspector、VS Code 扩展断点、`PWDEBUG=1` |
| **产出模块** | `playwright/08_pw_debug`（排查手册 + 演示用例）|
| **前置** | 项目 2（建议在 3-7 任一失败排障时并行实践）|
| **验收标准** | 人为失败用例的 trace.zip 经 `unzip -l` 确认含 network 快照与截图；用 UI Mode 定位该失败并说出根因；trace 打开命令写进排查手册 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 8「调试武器库」。请给我约 100 行代码：一条故意失败的 pw-store 用例、trace 全量开启配置、UI Mode/trace viewer/--debug 三种排查路径演示命令，输出一份 markdown 排查手册（何时用哪个工具）。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第三阶段：工程化流水（项目 9-13）

> **目标**：让套件可维护（fixture/POM）、可并行（隔离）、可配置（矩阵）、可观测（报告）、抗 flaky

### [x] 项目 9：Fixture 体系 + 类型安全 POM

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | `test.extend` 自定义 fixture、worker-scoped vs test-scoped、fixture 组合与依赖注入、TypeScript 泛型类型安全 page objects、选择器收口 |
| **产出模块** | `playwright/09_pw_fixtures_pom` |
| **前置** | 项目 2、4 |
| **验收标准** | 新增一条「admin 创建订单并验证」用例 ≤10 行（`wc -l` 证明）；`npx tsc --noEmit` 零错误；选择器只存在于 pages/ 目录 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 9「Fixture 体系+类型安全 POM」。请给我约 250 行 TypeScript 代码：test.extend 组合 adminPage/customerPage/orderData 工厂 fixture、worker-scoped 示例、泛型类型安全 Page Object 基类、演示新用例 10 行写完，附 tsc 校验命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 10：并行与隔离（fullyParallel / workers / 串行控制）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | `fullyParallel` 与 test.each 展开、workers 调优、数据隔离策略（独立账号/前缀数据）、`describe.serial` 依赖链、并行反模式 |
| **产出模块** | `playwright/10_pw_parallel` |
| **前置** | 项目 9 |
| **验收标准** | 20 条订单用例 4 workers 全绿且无串号（每用例断言自己唯一前缀的数据）；serial 组日志确认按序；改回 workers=1 总时长对比数据记录在案 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 10「并行与隔离」。请给我约 180 行 TypeScript 代码：fullyParallel 20 用例（唯一数据前缀防串号）、describe.serial 依赖链示例、workers 1/4 耗时对比脚本与结论注释。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 11：设备与仿真矩阵（projects / locale / 深色模式 / 离线）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | projects 多设备矩阵（iPhone/Pixel/桌面）、`viewport`/`hasTouch`、`locale`/`timezoneId`、`colorScheme: 'dark'`、`context.offline` |
| **产出模块** | `playwright/11_pw_matrix` |
| **前置** | 项目 1 |
| **验收标准** | 一条响应式用例在 6 个 project（3 设备 × 明/暗）下全绿；深色模式截图背景非纯白；locale 切到 en 后页面文案断言为英文 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 11「设备与仿真矩阵」。请给我约 150 行 TypeScript 代码：iPhone/Pixel/桌面三设备 project × 明暗主题、响应式布局断言用例、locale/timezone/深色模式/离线仿真各一条演示用例。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 12：报告与产物体系（reporter / 截图视频 trace 挂载）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | list/HTML/JUnit 多 reporter 组合、`trace: 'retain-on-failure'`、按需截图与视频、自定义 reporter、CI 可消费的产物布局 |
| **产出模块** | `playwright/12_pw_reports` |
| **前置** | 项目 2 |
| **验收标准** | 人为失败用例在 HTML 报告中同时挂 trace+截图+视频三产物；`report.xml`（JUnit）生成且被 `xmllint --noout` 校验合法 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 12「报告与产物体系」。请给我约 150 行 TypeScript 代码：HTML+JUnit+list 组合 reporter、retain-on-failure trace、按需 screenshot/video、一条人为失败用例验证三产物挂载，附产物检查命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 13：flaky 治理（retries / expect.poll / 稳定性分级）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | retries 策略与代价、`expect.poll`/`expect.toPass` 最终一致断言、`test.flaky/fixme/skip` 分级标注、报告里的 flaky 指标、稳定性度量脚本 |
| **产出模块** | `playwright/13_pw_flaky` |
| **前置** | 项目 2 |
| **验收标准** | 注入的 2 个 flaky 用例经 retries 全绿且 HTML 报告标 flaky；expect.poll 用例在异步数据最终一致后 5s 内收敛；连续 5 轮套件 0 unexpected |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 13「flaky 治理」。请给我约 180 行 TypeScript 代码：retries=2 配置、2 个注入 flaky 的演示用例、expect.poll 处理异步最终一致、test.flaky 分级标注示例、连跑 5 轮统计 unexpected/flaky 的脚本。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第四阶段：真实场景攻坚（项目 14-17）

> **目标**：把高频难啃的真实业务场景一个个拿下

### [x] 项目 14：文件上传下载与拖拽

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | `setInputFiles`（单/多/大文件）、`download` 事件与保存、上传进度反馈断言、`dragTo` 拖拽上传 |
| **产出模块** | `playwright/14_pw_files` |
| **前置** | 项目 2 |
| **验收标准** | 一次上传 3 个文件后列表断言全部可见；下载的文件 sha256 与源文件一致；拖拽上传用例绿 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 14「文件上传下载」。请给我约 150 行 TypeScript 代码：pw-store 上传页 setInputFiles 多文件用例、download 事件保存+sha256 比对、上传进度条断言、dragTo 拖拽上传用例。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 15：实时推送与竞态（WebSocket）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `page.waitForEvent('websocket')`、mock WS 帧驱动 UI 断言、断连重连恢复、乐观更新与回滚竞态 |
| **产出模块** | `playwright/15_pw_realtime` |
| **前置** | 项目 2 |
| **验收标准** | mock WS 推送后订单状态 UI 1s 内更新（断言通过）；断连重连用例验证状态恢复；乐观更新失败回滚用例绿 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 15「实时推送与竞态」。请给我约 200 行 TypeScript 代码：监听 pw-store 的 WebSocket 帧断言、mock WS 推送驱动 UI 1s 更新用例、断连重连恢复用例、乐观更新失败回滚用例。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 16：i18n 与无障碍（locale / axe / 键盘导航）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | locale 切换与文案矩阵、`@axe-core/playwright` 扫描、ARIA 违规修复闭环、纯键盘走完核心表单 |
| **产出模块** | `playwright/16_pw_i18n_a11y` |
| **前置** | 项目 2 |
| **验收标准** | 中/英 locale 各自文案断言通过；axe 扫描 SUT 关键 3 页 critical 违规 = 0；纯 Tab 键走完下单表单并提交成功 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 16「i18n 与无障碍」。请给我约 180 行 TypeScript 代码：中英 locale 文案矩阵用例、axe-core 扫描 SUT 三页且 critical=0、纯键盘走完下单表单的用例。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 17：API+UI 混合测试（request fixture 造数）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | `request`/`playwright.request` fixture 直打 API、API 预置数据 + UI 验证的分层、API 清场 teardown、混合用例耗时收益 |
| **产出模块** | `playwright/17_pw_api_ui` |
| **前置** | 项目 2、4 |
| **验收标准** | API 造 100 条订单 ≤5s（与纯 UI 造数的耗时对比记录在案）；10 条「API 预置 + UI 分页验证」混合用例全绿；teardown 后数据清零 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 17「API+UI 混合测试」。请给我约 200 行 TypeScript 代码：request fixture 调 pw-store API 造 100 条订单（带耗时统计）、API 预置+UI 分页验证 10 条混合用例、teardown 清场，附纯 UI 造数对比命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第五阶段：CI 交付与终极串联（项目 18-19）

> **目标**：本地 CI 分片交付，前 17 个项目的产物组合成一条命令可跑的全功能回归套件

### [x] 项目 18：⛓️ 本地 CI + sharding（act / 分片 / 产物上传）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行（workflow yaml + config）|
| **核心知识点** | `--shard=x/y` 分片、GitHub Actions workflow（本地 act 执行）、浏览器二进制与 node_modules 缓存、分片报告合并、失败产物 artifact |
| **产出模块** | `playwright/18_pw_ci_sharding`（`.github/workflows/e2e.yml` + act 脚本）|
| **技术栈** | act 0.2.89（✅ 本机已装，repo 实验 30 已验证可跑 workflow）|
| **前置** | 项目 12（报告产物是 CI 的输入）|
| **验收标准** | act 本地跑 4 分片全绿且总时长 < 单机串行一半（两组数据记录在案）；人为失败时分片报告与截图产物可从 artifact 目录找到 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 18「本地 CI+sharding」。请给我约 250 行代码：e2e.yml workflow（pnpm 安装+浏览器缓存+--shard=1/4 到 4/4+报告合并+失败产物上传）、act 本地执行脚本、串行 vs 分片耗时对比命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 19：🏁 终极串联——pw-store 全功能回归套件

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行（套件组装 + 门禁脚本）|
| **核心知识点** | 项目 1-18 产物组装：认证矩阵+核心路径+视觉基线+实时+a11y+API 混合；统一 config 的 projects/retries/sharding 终局编排；质量门禁脚本 |
| **产出模块** | `playwright/19_pw_final_suite` |
| **前置** | 项目 1-18 全部 |
| **验收标准** | 一条命令（`npm run e2e`）跑全量套件，本机 ≤20 分钟全绿；HTML 报告 0 unexpected（flaky 明示标注）；门禁脚本对「失败/flaky 超阈值」返回非零退出码 |

**🤖 开始提示词**：
> `我要开始 Playwright 项目 19「终极串联回归套件」。请给我约 300 行代码：统一 playwright.config 终局编排（复用 9/11/12/13/18 的 fixture、矩阵、报告、分片）、按功能域分组的用例组装、质量门禁脚本（失败/flaky 阈值判断）、一条命令入口，附全量运行命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-2（TS 栈立住 + pw-store 靶场开张）| 2 |
| **第 2 周** | 项目 3-5（定位深水区 / 认证矩阵 / 网络控制）| 3 |
| **第 3 周** | 项目 6-8（视觉回归 / 组件测试 / 调试武器库）| 3 |
| **第 4 周** | 项目 9-11（fixture+POM / 并行隔离 / 仿真矩阵）| 3 |
| **第 5 周** | 项目 12-13（报告产物 / flaky 治理）| 2 |
| **第 6 周** | 项目 14-16（文件 / 实时推送 / i18n+a11y）| 3 |
| **第 7 周** | 项目 17-18（API 混合 / 本地 CI+sharding）| 2 |
| **第 8 周** | 项目 19（🏁 终极串联 + 收尾复盘）| 1 |

## 🏆 里程碑

- [ ] **完成项目 1-2** → TS 原生栈立住 + 自有靶场 pw-store 开张
- [ ] **完成项目 3-8** → Playwright 深水区六件套（定位/认证/网络/视觉/组件/调试）
- [ ] **完成项目 9-13** → 工程化：可维护、可并行、可配置、可观测、抗 flaky 的套件
- [ ] **完成项目 14-17** → 文件/实时/无障碍/API 混合四个真实场景攻坚
- [ ] **全部完成（19/19）** → 一条命令、分片并行、报告齐全的全功能回归套件 🏁

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| | | | | |

## 🔧 环境配置

```bash
# 0. 已就绪（2026-09-29 实测，见文末速查表）：
#    node v22.23.2 / pnpm / npm
#    @playwright/test 1.63.0（npm 直连安装）
#    chromium / firefox / webkit 三浏览器二进制已缓存
#    act 0.2.89、k6（repo 实验 30 已装）
which node pnpm act

# 1. 需安装：无硬性新增。项目 2 开工时执行：
npm create vite@latest pw-store -- --template react-ts

# 2. 每项目开工前统一体检：
npx playwright --version && ls ~/Library/Caches/ms-playwright | grep -c 'chromium\|firefox\|webkit'

# 3. 浏览器二进制缺失/升级时（直连下载已实测可用，无需镜像）：
npx playwright install chromium firefox webkit
```

## ⚠️ 与已有清单的关系

本清单是 **互补开线**：`test_frameworks.md` 的实验 16-20 已完成 Playwright **Python 入门线**（pytest-playwright），本清单用 **TS 原生栈**走**进阶线**，跳过已覆盖内容：

| 已有实验（已完成 ✅） | 本清单对应 | 分工与跳过项 |
|:---|:---|:---|
| 实验 16 pw_basics（pytest-playwright 入门）| 项目 1 | 换 TS 原生栈重立地基；codegen、安装等入门内容**不再重复**，增量是 config/projects 体系 |
| 实验 17 pw_locators（定位与等待基础）| 项目 3 | 等待与 web-first 断言基础**跳过**，只做 iframe/shadow DOM/严格模式进阶 |
| 实验 18 pw_pom（POM，Python 版）| 项目 9 | 基础 POM 概念**跳过**，进阶为 TS 类型安全 POM + fixture 依赖注入 |
| 实验 19 pw_network（route mock + storageState 入门）| 项目 4、5 | 基础 mock 与 storageState 保存**跳过**，深化为 HAR 回放、错误注入矩阵、global-setup 多角色 |
| 实验 20 pw_quality（三核+截图对比+trace 入门）| 项目 6、8、12 | 基础 trace 与截图**跳过**，系统化为基线管理流水线、调试手册、reporter 产物体系 |
| `test_architect.md`（28 实验，测试架构视角）| 不重叠 | 那条线讲测试架构设计方法论，本清单讲 Playwright 工具深度 |
| `performance.md`（k6/Locust，性能视角）| 不重叠 | 性能压测线；本清单的 UI 自动化不涉及负载注入 |

## 📚 来源

- [Playwright 官方文档](https://playwright.dev/docs/intro)
- [Component Testing (experimental)](https://playwright.dev/docs/test-components)
- [Visual comparisons](https://playwright.dev/docs/test-snapshots)
- [Parallelism and isolation](https://playwright.dev/docs/test-parallel)
- [Sharding](https://playwright.dev/docs/test-sharding)
- [.NET/JS API 差异与 pytest-playwright 对比](https://playwright.dev/python/docs/intro)

## 🧪 本机能力实测速查表（2026-09-29）

| 能力 | 计划 | 实测结论 |
|:---|:---|:---|
| @playwright/test 安装 | npm 直连 | ✅ 实测通过（1.63.0，~30s）|
| 三浏览器跑批 | chromium/firefox/webkit | ✅ 实测 3 passed（6.2s 冒烟）|
| 浏览器二进制下载 | playwright CDN | ✅ 直连成功（104MB，无需镜像）|
| act 本地 CI | 项目 18 | ✅ 已装 0.2.89，repo 实验 30 验证过 workflow 执行 |
| Vite+React 脚手架 | 项目 2 | ⚠️ 开工探活（npm 直连风险低）；fallback：手写最小 vite 工程 |
| 组件测试 ct-react | 项目 7 | ⚠️ 待验证（需与 test 同版本挂载）；fallback：降级为轻挂载集成测试 |
