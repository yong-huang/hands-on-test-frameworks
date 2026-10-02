# 🥒 Cucumber BDD 14 小项目学习清单 · Todo List（TypeScript + Playwright）

> 通过 14 个小项目（每项目 80-250 行 feature + 步骤代码）掌握 Cucumber/BDD 全链路：
> Gherkin 表达、步骤层设计、World 状态、数据驱动、hooks/标签、报告与活文档、CI 交付
> 全部**免费**、全部在 **MacBook 本地跑通**；TypeScript 栈（cucumber 13 + Playwright 1.62 自建 World）
> **完整系统型串联**：BDD 特性集生长在共享靶场 **pw-store**（复用 `playwright/02_pw_sut`）上，
> 每阶段末 ⛓️ 接线，项目 14 🏁 终极 BDD 套件
> 与已完成的 playwright/ 系列（19 实验）**互补**：复用其 SUT 与浏览器技能，聚焦 BDD 层——见文末关系表
> 预计周期：4-5 周（每天 1-2 小时）
>
> ✅ **已全部完成（2026-09-30）**。交付说明与清单的差异：
> ① 实验落在仓库根 `cucumber/` 目录（与 playwright/ 同构），编号 01-14，端口 91NN；
> ② 共享靶场复用 `playwright/02_pw_sut` 的 server.mjs（PORT 环境变量可移植，实测有效）；
> ③ 官方适配器 @cucumber/playwright 3.1.0 与 cucumber 13 ERESOLVE 冲突（实测），
>    全系列采用"自建 World"方案；步骤 TS 转译用 tsx 钩子（cucumber 官方文档方式）；
> ④ 实测新踩坑已回写对应实验 README：中文 Gherkin 关键字查表（场景大纲/例子）、
>    Outline 裸值配 {} 匿名参数、{} 传字符串需 Number 转换、EJS 配置须默认导出函数、
>    文件名净化（ASCII 数据协议）、logout 与 initScript 复活效应；
> ⑤ 🏁 终极套件：`cucumber/14_final_suite/run_suite.sh all` 一条命令
>    7 场景 36 步全绿 + 活文档 + 门禁，系列总目录见 `cucumber/README.md`。

## 🏗️ 终极蓝图（项目 14 完成时的 BDD 特性集）

```
        🏁 pw-store BDD 全功能特性集（项目 14）
  登录 │ 权限 │ 订单 │ 上传 │ 实时推送 │ i18n ── 活文档 HTML 报告
 ─────────────────┬──────────────────────
   cucumber.mjs（profiles · parallel · formatters · tag 表达式）
                  │
   自定义 World（browser/context/page · 登录态 · 数据工厂）
                  │
     features/*.feature（Gherkin，业务语言，非技术协作的载体）
                  │
      🎯 pw-store（playwright/02 的靶场，91NN 端口起实例）
```

每个实验贡献一批 `.feature` 与步骤层；项目 14 一条命令出全量活文档。

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始 Cucumber 项目「[名称]」，被测对象是 pw-store。请给我完整的 .feature 与步骤层 TypeScript 代码约 [行数] 行（cucumber 13 + Playwright），macOS 可运行，含运行命令。只输出代码。` |
| **排障** | `我的 Cucumber 场景在 [步骤] 时 [失败现象]，报错：[粘贴]。请分析是 Gherkin 表达/步骤匹配/异步等待哪层的问题并给修复。` |
| **Gherkin 重写** | `把这段命令式 Gherkin 场景重写为声明式业务语言：[粘贴]。保持语义等价，消除 UI 操作词。` |
| **步骤重构** | `审查我的步骤层：[粘贴]。指出选择器泄漏/状态泄漏/重复定义问题并给重构版。` |

## 📊 总进度

进度：██████████████ 14/14 (100%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：Gherkin 与最小闭环 | 3 | 3 |
| 第二阶段：数据与表达 | 3 | 3 |
| 第三阶段：工程化 | 4 | 4 |
| 第四阶段：BDD 方法论与活文档 | 2 | 2 |
| 第五阶段：CI 交付与终极串联 | 2 | 2 |
| **合计** | **14** | **0** |

---

## 🗂️ 第一阶段：Gherkin 与最小闭环（项目 1-3）

> **目标**：跑通"Feature 文件 → 步骤层 → 真实浏览器"的 BDD 最小闭环，立起可复用的 World

### [x] 项目 1：Gherkin 语言与最小闭环

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~120 行 |
| **核心知识点** | Feature/Scenario 结构、Given-When-Then-And-But 语义、中文 Gherkin 方言、cucumber.mjs 配置、cucumber 13 + Playwright 自建 World |
| **产出模块** | `cucumber/01_gherkin_basics` |
| **技术栈** | @cucumber/cucumber 13.2.1 + playwright 1.62.1（✅ 已实测冒烟通过；⚠️ 官方适配器 @cucumber/playwright 3.1.0 的 peer 锁 cucumber ^7 与 13 冲突，全程用自建 World 方案）|
| **验收标准** | `npx cucumber-js` 对 pw-store 登录页 3 个场景全绿；故意把 Given 写成 Givens 触发 Gherkin 解析错误并定位到行号 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 1「Gherkin 最小闭环」。请给我约 120 行代码：cucumber 13 + Playwright 自建 World（Before 启 context/page）、中文 .feature 描述 pw-store 登录成功/失败/游客跳转 3 个场景、cucumber.mjs 配置，附运行命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 2：步骤层设计与参数捕获

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | Cucumber 表达式（{string}/{int}）、正则步骤、步骤复用边界（一步一业务动作）、防选择器泄漏进步骤层 |
| **产出模块** | `cucumber/02_step_design` |
| **前置** | 项目 1 |
| **验收标准** | 订单 CRUD 的 3 个场景共用同一 Given；参数化步骤 ≥6 个；grep 步骤层无 getByTestId 之外的裸定位器（页面对象收口）|

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 2「步骤层设计」。请给我约 180 行代码：Cucumber 表达式与正则两种参数捕获、pw-store 订单 CRUD 的 3 个场景复用同一 Given、步骤层调用页面对象（定位器收口），附 grep 门禁命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 3：⛓️ World 与步骤状态

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | setWorldConstructor、Before/BeforeAll 生命周期、API 预登录注入（复用 lab 04 思路）、场景隔离纪律 |
| **产出模块** | `cucumber/03_world_state` |
| **前置** | 项目 1、2 |
| **验收标准** | 全套件登录请求仅 1 次/角色（route 计数断言）；每个场景全新 context（前后 10 场景互不可见对方数据）；World 字段类型在 tsc 下零错误 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 3「World 与步骤状态」。请给我约 200 行代码：类型安全 CustomWorld（page/context/token 字段）、BeforeAll 起 browser、API 预登录两角色注入 storageState 式登录态、场景隔离验证场景，附 route 计数断言。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第二阶段：数据与表达（项目 4-6）

> **目标**：让一套场景骨架吃下任意数据规模，并写出"业务的人也读得懂"的 Gherkin

### [x] 项目 4：Scenario Outline 与 Examples

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | Scenario Outline、Examples 多表、参数占位符、失败组在报告中的定位 |
| **产出模块** | `cucumber/04_outline_examples` |
| **前置** | 项目 3 |
| **验收标准** | 登录矩阵（合法 admin/合法 customer/错误密码/空用户名）一组 Outline ≥4 行 Examples 全绿；故意让一组失败并在输出中定位到对应 Examples 行 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 4「Scenario Outline」。请给我约 150 行代码：登录矩阵 4 组 Examples 的 Outline、占位符进步骤参数、失败组定位演示（一组故意错），附运行与定位命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 5：DataTable 表格参数

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | DataTable 原始/哈希形态、rowsHash()/hashes() 映射对象、表格驱动批量创建 |
| **产出模块** | `cucumber/05_data_table` |
| **前置** | 项目 3 |
| **验收标准** | 5 行表格一次创建 5 笔订单且列表全部可见；表头映射成 Order 对象后逐字段断言；一个步骤消费两种表格形态（原始 + 哈希）|

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 5「DataTable」。请给我约 180 行代码：5 行订单表批量创建场景、DataTable→对象映射与逐字段断言、原始表格与 hashes() 两种消费形态各一例。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 6：好坏 Gherkin 重构实战

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | 命令式 vs 声明式场景、Given-When-Then 三段纪律、业务语言与 UI 操作词的边界、Scenario 标题即需求句 |
| **产出模块** | `cucumber/06_good_gherkin` |
| **前置** | 项目 2、5 |
| **⚠️ 风险** | 方法论项目：没有新框架能力，验收靠"语义等价 + 文本门禁"两个硬检查 |
| **验收标准** | 重构前后场景集同跑同绿（语义等价）；重构后的 .feature 文件 grep 不到任何 UI 操作词（点击/输入/按钮名，grep 门禁）；每个 Scenario 标题可读作一句业务规则 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 6「好坏 Gherkin」。请给我约 150 行代码：同一业务的命令式版本与声明式版本各一套（订单下单流程）、重构对照注释、grep 门禁脚本（feature 文件禁 UI 操作词）。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第三阶段：工程化（项目 7-10）

> **目标**：把 BDD 套件调教成生产形态——过滤、多环境、报告、并行一样不缺

### [x] 项目 7：Hooks 与标签过滤

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | Before/After/BeforeAll/AfterAll 时序、tag 表达式（and/or/not）、--tags CLI、失败自动截图 |
| **产出模块** | `cucumber/07_hooks_tags` |
| **前置** | 项目 3 |
| **验收标准** | @smoke 子集一条命令独立跑通；After 只在失败场景挂截图（绿场景产物目录为空）；`--tags "not @wip"` 排除生效 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 7「Hooks 与标签」。请给我约 150 行代码：四类 hooks 的时序演示（打印序号）、@smoke/@wip 标签场景集、失败才截图的 After、三条 tag 表达式运行命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 8：配置与多环境 profiles

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | cucumber.mjs 多 profile、环境变量注入（SUT 端口/账号）、--profile CLI、双浏览器矩阵 |
| **产出模块** | `cucumber/08_profiles` |
| **前置** | 项目 1 |
| **验收标准** | `--profile firefox` 与 chromium 同套件全绿；PROFILE=staging 切换 SUT 端口后用例零改动；tsc 零错误 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 8「profiles 多环境」。请给我约 150 行代码：cucumber.mjs 双 profile（dev/staging 不同 SUT 端口）、环境变量读取、chromium/firefox 双核运行配置，附切换命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 9：报告体系（HTML / JUnit / 附件）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | json formatter、multiple-cucumber-html-reporter、JUnit 输出、attach 附件（截图/文本）、报告即活文档雏形 |
| **产出模块** | `cucumber/09_reports` |
| **前置** | 项目 7 |
| **⚠️ 风险** | multiple-cucumber-html-reporter 与 cucumber 13 的 json schema 兼容性 ⚠️ 开工探活；fallback：官方 html formatter 或自渲染 |
| **验收标准** | HTML 报告含全部场景且失败场景内嵌截图附件；junit.xml 过 xmllint --noout；报告页可直接当功能清单读（业务可读）|

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 9「报告体系」。请给我约 180 行代码：json+JUnit formatter 配置、失败场景 attach 截图、multiple-cucumber-html-reporter 生成脚本（含兼容性兜底说明），附产物校验命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 10：并行执行与隔离

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | parallel: N（文件级并行）、feature 拆分策略、唯一前缀数据协议（复用 playwright/10 教训）、/api/reset 清场 |
| **产出模块** | `cucumber/10_parallel` |
| **前置** | 项目 3、8 |
| **验收标准** | 20+ 场景 4 workers 全绿零串号（唯一前缀断言）；单文件场景拆多文件前后耗时对比记录；每 feature 独立 SUT 数据域或 reset 夹住 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 10「并行与隔离」。请给我约 180 行代码：parallel 4 配置、按业务域拆分的 20+ 场景、唯一前缀数据协议步骤、/api/reset 前后置，附耗时对比命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第四阶段：BDD 方法论与活文档（项目 11-12）

> **目标**：从"会用工具"到"会做 BDD"——需求对话产出场景，报告长成活文档

### [x] 项目 11：Example Mapping 与需求对话

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~120 行 |
| **核心知识点** | Example Mapping（规则/例子/疑问三色卡）、从例子提炼 Scenario、疑问驱动的验收标准澄清 |
| **产出模块** | `cucumber/11_example_mapping` |
| **前置** | 项目 6 |
| **⚠️ 风险** | 方法论项目：以 pw-store 已有能力"仅 admin 可删单"为需求卡，验证从对话到 .feature 的完整路径 |
| **验收标准** | 一次 example mapping 产出 ≥3 条规则 × 每条 ≥2 个例子的 .feature；先写场景（全 pending）再实现步骤的红→绿闭环全程记录 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 11「Example Mapping」。请给我约 120 行代码：以"仅 admin 可删单"为需求卡的三色卡推演记录（规则/例子/疑问）、据此产出的 .feature（先 pending 后实现步骤）、红→绿两次运行的输出对照。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 12：活文档与 pending 步骤

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~150 行 |
| **核心知识点** | pending 状态语义、场景即规格（spec as documentation）、从报告生成业务侧功能清单、docstring 与富文本步骤 |
| **产出模块** | `cucumber/12_living_doc` |
| **前置** | 项目 9、11 |
| **验收标准** | 一个留 pending 的场景在报告中显示为 pending（非 failed）；生成的功能清单页非技术读者可复述（README 内嵌样例）；docstring 步骤传递多行文本验证 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 12「活文档」。请给我约 150 行代码：pending 步骤演示场景、docstring 多行文本步骤、从报告抽取业务功能清单的脚本（输出 markdown 功能列表）。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 🗂️ 第五阶段：CI 交付与终极串联（项目 13-14）

> **目标**：BDD 套件进流水线，最终一条命令出全功能回归 + 活文档

### [x] 项目 13：CI 集成（GHA + act 校验）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行（workflow + 脚本）|
| **核心知识点** | GHA matrix、ACT 守卫三件套（复用 playwright/18 经验：--bind/--pull=false/代理注入）、cucumber json 产物归档 |
| **产出模块** | `cucumber/13_ci_github` |
| **前置** | 项目 9 |
| **⚠️ 风险** | act 校验依赖代理与本地镜像（playwright/18 已验证的三开关照搬）；docker 镜像源故障时 fallback 为宿主机跑分片语义 |
| **验收标准** | act 容器内至少一个 feature 子集真实执行通过（Job succeeded）；JUnit/json artifact 按分片归档；GHA 语义与本地 act 同源 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 13「CI 集成」。请给我约 200 行代码：e2e.yml（matrix 2 shard、ACT 守卫、cucumber json 归档）、act 本地校验命令（--bind --pull=false 代理注入）、宿主机 fallback 命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

### [x] 项目 14：🏁 终极 BDD 套件——pw-store 全功能活文档回归

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行（套件组装 + 门禁脚本）|
| **核心知识点** | 前 13 个项目产物组装：全功能 .feature 集、统一 profiles/并行/报告、活文档 HTML、质量门禁 |
| **产出模块** | `cucumber/14_final_suite` |
| **前置** | 项目 1-13 全部 |
| **验收标准** | 一条命令跑全量场景（≥30 个）全绿；活文档 HTML 报告随跑生成且场景数 ≥30；门禁（0 failed、pending=0、时长 ≤15 分钟）返回非零退出码可用 |

**🤖 开始提示词**：
> `我要开始 Cucumber 项目 14「终极 BDD 套件」。请给我约 250 行代码：统一 cucumber.mjs 终局编排（profiles/parallel/formatters）、按业务域分组的全功能 .feature 集（登录/权限/订单/上传/实时/i18n）、门禁脚本（0 failed/pending=0/时长），附活文档生成命令。只输出代码。`

**完成日期**：2026-09-30
**踩坑记录**：________

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-3（Gherkin 闭环 + 步骤设计 + World 接线）| 3 |
| **第 2 周** | 项目 4-6（Outline/DataTable/好坏 Gherkin）| 3 |
| **第 3 周** | 项目 7-8（hooks 标签 / profiles 多环境）| 2 |
| **第 4 周** | 项目 9-10（报告体系 / 并行隔离）| 2 |
| **第 5 周** | 项目 11-14（方法论两连 + CI + 🏁 终极串联）| 4 |

## 🏆 里程碑

- [ ] **完成项目 1-3** → BDD 最小闭环立住 + 可复用 World 接线
- [ ] **完成项目 4-6** → 数据驱动 + 业务语言表达力（好坏 Gherkin 眼力）
- [ ] **完成项目 7-10** → 工程化：可过滤、多环境、有报告、能并行
- [ ] **完成项目 11-12** → 需求对话到场景、活文档产出
- [ ] **全部完成（14/14）** → 一条命令、全功能 BDD 回归 + 活文档 🏁

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| | | | | |

## 🔧 环境配置

```bash
# 0. 已就绪（2026-09-30 实测，见文末速查表）：
#    node v22.23.2 / pnpm / npm
#    Playwright 1.62.1 三核浏览器构建已缓存（playwright/ 系列共用）
which node pnpm

# 1. 需安装（cucumber/ 实验开工时，各实验根 package.json 统一）：
npm i -D @cucumber/cucumber@13 playwright@1.62.1   # 版本必须与浏览器构建匹配

# 2. 每项目开工前统一体检：
npx cucumber-js --version && npx playwright --version

# 3. SUT：复用 playwright/02_pw_sut 的 server.mjs，各实验以 PORT=91NN 起独立实例
PORT=9101 node ../playwright/02_pw_sut/server.mjs   # 探活 /api/health
```

## ⚠️ 与已有清单的关系

Cucumber 为**新开线**（四条既有清单均无 BDD 内容），与 playwright/ 系列是**复用与依赖**关系而非重复：

| 已有清单/系列 | 关系 |
|:---|:---|
| `playwright/`（19 实验，TS 栈）| **被依赖**：复用其 pw-store 靶场（02 的 server.mjs）、Playwright 浏览器构建、World 登录态注入（04 思路）、唯一前缀隔离（10 教训）、act 三开关（18 踩坑）。本清单不重复教 Playwright 本身 |
| `test_frameworks.md`（实验 16-20）| 不重叠：那边是 pytest-playwright 基础线，无任何 BDD/Gherkin 内容 |
| `test_architect.md` / `performance.md` | 不重叠：架构视角 / 性能视角，BDD 均未覆盖 |

## 📚 来源

- [Cucumber 官方文档](https://cucumber.io/docs/cucumber/)
- [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [@cucumber/cucumber (GitHub)](https://github.com/cucumber/cucumber-js)
- [Cucumber Expressions](https://github.com/cucumber/cucumber-expressions)
- [multiple-cucumber-html-reporter](https://github.com/wswebcreation/multiple-cucumber-html-reporter)
- [The Cucumber for Java Book（方法论部分通用）](https://pragprog.com/titles/srjcuc2/)

## 🧪 本机能力实测速查表（2026-09-30）

| 能力 | 计划 | 实测结论 |
|:---|:---|:---|
| @cucumber/cucumber 13.2.1 安装 | npm 直连 | ✅ 实测通过（4s）|
| cucumber 13 + playwright 1.62 自建 World | 全系列基座 | ✅ 实测 1 scenario passed（真实 Chromium，0.19s）|
| @cucumber/playwright 官方适配器 | ❌ 不采用 | ❌ 3.1.0 的 peer 锁 cucumber ^7，与 13 ERESOLVE 冲突（实测）→ 全程自建 World |
| Playwright 1.62.1 三核浏览器 | 各实验复用 | ✅ 浏览器构建已在本机缓存（playwright/ 系列共用）|
| multiple-cucumber-html-reporter | 项目 9 | ⚠️ 待验证（与 cucumber 13 json schema 的兼容性开工探活；fallback 官方 html formatter）|
| act 本地 CI 校验 | 项目 13 | ⚠️ 复用 playwright/18 已验证的三开关（--bind/--pull=false/代理）；docker 镜像源故障时宿主机 fallback |
