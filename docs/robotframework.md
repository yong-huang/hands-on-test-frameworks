# 🤖 robotframework：Robot Framework 自动化 17 小项目学习清单 · Todo List（Web + API + RPA 全家桶）

> 通过 17 个小项目（每项目 150-350 行代码/配置）把「关键字驱动自动化」练成「非代码背景也能读的回归套件」：
> 地基（语法与数据驱动）→ Web（SeleniumLibrary）→ API（RequestsLibrary）→ 工程化与 RPA（自定义库/编排/桌面流程）→ 🏁 串联交付
> 约束：全部本机 macOS（Apple Silicon）可跑、零云依赖、免费开源工具；Robot Framework 本体跑在仓库 venv 的 Python 上，桌面 RPA 用 RPA.Framework
> 串联机制：知识体系型——阶段即能力等级（地基 → Web → API → 工程化与 RPA → 串联交付）；贯穿场景是项目 1 自建的「Robot 专属靶场」（Web 下单表单 + REST 接口，与 selenium.md 的靶场互不依赖）
> 预计周期：6 周（每天 1-2 小时）

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始 Robot Framework 项目「[名称]」，目标是 [目标]。请给我完整的 .robot/.py 文件约 [行数] 行，用 robotframework 6 + [相关库]，被测对象是 docs/robotframework.md 描述的自建靶场，含断言验证。只输出代码。` |
| **排障** | `我的 Robot 用例出现 [FAIL 原文/日志]，报错：[粘贴]。请分析是定位器、等待还是关键字用法问题并给修复。` |
| **造关键字库** | `用 PythonLibCore 把这段 Python 逻辑封装成 Robot Library：[粘贴代码]，类名 [XxxLibrary]，关键字命名与文档字符串规范。` |

## 📊 总进度

进度：░░░░░░░░░░░░░░░░░░ 0/17 (0%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：地基（语法与数据驱动） | 3 | 0 |
| 第二阶段：Web（SeleniumLibrary） | 4 | 0 |
| 第三阶段：API（RequestsLibrary） | 3 | 0 |
| 第四阶段：工程化与 RPA | 4 | 0 |
| 第五阶段：串联交付 | 3 | 0 |
| **合计** | **17** | **0** |

---

## 🗂️ 第一阶段：地基（项目 1-3）

> **目标**：读懂 Robot 的表格语法与关键字宇宙——套件/用例/关键字三层、变量与数据驱动上手，靶场就位

### [x] 项目 1：自建靶场 + 首个套件

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行（靶场 + 首套件） |
| **核心知识点** | 套件/测试用例/关键字三层结构、log/report/output 三件套、Settings/Variables/Test Cases/Keywords 四张表 |
| **技术栈** | robotframework（venv 需安装，见环境配置）；靶场为纯 HTML/JS + Python http server，零外部依赖 |
| **验收标准** | `robot first_suite/` 一条命令跑通；log.html 里能看到用例→关键字两级树；靶场 Web 表单与 4 个 REST 接口可独立访问 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「自建靶场 + 首个套件」。请给我完整代码约 300 行：一个自包含靶场（Web 下单表单 + 4 个 REST 接口：创建订单/查询/支付/取消，Python http server 实现），加第一个 .robot 套件（打开页面断言标题、curl 式调一个接口断言 200）。附 robot 命令与查看 log.html 的验收步骤。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 2：关键字宇宙与变量体系

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | 内建关键字、用户关键字（带参数/返回值）、.resource 资源文件、scalar/list/dict 变量、IF/FOR 循环 |
| **前置** | 项目 1 |
| **验收标准** | 业务关键字全部下沉到 .resource（测试用例层只剩业务语言）；一个用例演示 FOR + IF 组合；`robot --dryrun` 通过 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「关键字宇宙与变量体系」。请给我完整代码约 250 行：把项目 1 的用例重构成 测试层（业务语言）+ .resource 关键字层（带默认参数/返回值），演示 scalar/list/dict 三种变量、FOR 循环 + IF 分支各一个真实场景。附 --dryrun 验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 3：数据驱动两板斧

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | [Template] 模板关键字、DataDriver 插件（CSV/Excel 外部数据）、两种数据驱动取舍 |
| **前置** | 项目 2 |
| **验收标准** | 同一订单场景用模板关键字与 CSV DataDriver 各实现一遍（5 组数据含中文与非法组）；非法组负向断言通过且日志可区分两种实现 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「数据驱动两板斧」。请给我完整代码约 250 行：订单场景分别用 [Template] 模板关键字和 DataDriver + CSV（5 组国际地址数据 + 1 组非法）实现，非法数据走负向断言；输出两种方式的对比说明（何时用哪个）。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

## 🗂️ 第二阶段：Web（SeleniumLibrary）（项目 4-7）

> **目标**：Web 自动化全套——Robot 风格的定位与等待、控件全集、iframe/窗口/懒加载三难、期望失败与留证

### [x] 项目 4：SeleniumLibrary 入门

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Open/Browser 关键字、Robot 风格定位器（id:/css:/xpath: 前缀）、Wait Until Element Is Visible 等显式等待关键字族 |
| **前置** | 项目 1 |
| **技术栈** | SeleniumLibrary（底层 selenium 4.48 ✅）；Chrome / Safari / Firefox 158.0.1 三浏览器均实测在位 |
| **验收标准** | 靶场下单主流程（打开→选品→提交）套件全绿；慢元素用 Wait Until 族关键字而非 sleep；`--variable HEADLESS:true` 有头/无头同参同过 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「SeleniumLibrary 入门」。请给我完整代码约 250 行：SeleniumLibrary 打开靶场完成下单主流程，定位器用 id:/css: 前缀风格，慢元素全部用 Wait Until 显式等待族（不用 sleep），支持 HEADLESS 变量切换无头模式。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 5：Web 表单与控件全集

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | List Selection/Checkbox/Radio/日期/文件上传关键字、断言关键字族（Should Be / Should Not / Element Text Should Be） |
| **前置** | 项目 4 |
| **验收标准** | 靶场 8 类控件全部用关键字操作并提交；服务端回读与输入逐字段一致（含中文「李雷」）；断言失败时的报告截图可见 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「Web 表单与控件全集」。请给我完整代码约 250 行：List Selection Should Be Selected 等关键字操作靶场 8 类控件（下拉/多选/复选/radio/日期/滑块/上传），提交后断言回读逐字段一致，演示一个故意断言失败让 log.html 留截图。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 6：复杂页面三难

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Select Frame 三层嵌套、Switch Window 句柄、Execute Javascript 懒加载滚动、关键字组合封装 |
| **前置** | 项目 4 |
| **验收标准** | 三层 iframe 购买→支付→切回断言订单号；新窗口往返操作；懒加载 30 件商品滚动全载断言；三难各封装成一个业务关键字 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「复杂页面三难」。请给我完整代码约 250 行：靶场三层 iframe 购买按钮、比价新开窗口、滚动懒加载 30 件商品，各封装成一个业务关键字（内组合 Select Frame/Switch Window/Execute Javascript），三个场景各一条用例。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 7：期望失败与失败留证

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | Run Keyword And Ignore Error / Expect Error、Test Teardown 统一截图、Run Keyword If Test Failed、TRY/FINALLY |
| **前置** | 项目 5 |
| **验收标准** | 4 条负向用例（错价格/空表单/断网按钮/缺失元素）全部「按预期红」且套件退出码可控；失败用例自动留整页截图到 reports/，通过用例零附件 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「期望失败与失败留证」。请给我完整代码约 220 行：用 Run Keyword And Expect Error / TRY-FINALLY 写 4 条负向用例，Test Teardown 里 Run Keyword If Test Failed 自动截图到 reports/（通过不留），演示 --exitonfailure 与退出码控制。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

## 🗂️ 第三阶段：API（RequestsLibrary）（项目 8-10）

> **目标**：接口测试同样关键字化——请求/断言/schema 校验，最后和 Web 拼成前后端贯通的场景

### [x] 项目 8：RequestsLibrary 入门

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | Create Session、GET/POST/PUT/DELETE 关键字、Status Should Be、Should Be Equal As Strings、JSON 断言（Evaluate） |
| **前置** | 项目 1 |
| **验收标准** | 靶场 4 个接口全覆盖（正向 6 条 + 异常 4 条）全绿；响应 JSON 字段断言不写一行裸 Python（全用关键字与 Evaluate 表达式） |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「RequestsLibrary 入门」。请给我完整代码约 220 行：Create Session 打靶场 4 个 REST 接口，正向（创建/查询/支付/取消）+ 异常（缺字段 422/不存在 404/重复支付 409/非法金额 400）逐接口断言状态码与 JSON 字段（Should Be Equal As Strings + Evaluate）。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 9：Schema 校验与负向矩阵

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | JSONLibrary/JSONSchema 断言、响应结构守恒、负向矩阵编排（模板关键字 × 异常集） |
| **前置** | 项目 8 |
| **验收标准** | 4 个接口响应全部过 JSON Schema；负向矩阵（3 接口 × 3 异常 = 9 格）由模板关键字驱动，逐格断言错误码与 message |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「Schema 校验与负向矩阵」。请给我完整代码约 250 行：为靶场 4 个接口写 JSON Schema 并用 JSONLibrary 断言结构；负向矩阵用 [Template] 模板关键字驱动 3×3 组合（接口 × 异常输入），逐格断言错误码与 message 字段。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 10：⛓️ API + Web 混合场景

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | API 造数 → Web 验证 → API 清理的贯通模式、Suite Setup/Teardown 编排、两库同套件共存 |
| **前置** | 项目 5、8 |
| **验收标准** | 一条用例完成「API 创建订单 → Web 页面查到该订单并支付 → API 断言状态流转」；套件级 Teardown 清理全部造数（API 查证 0 残留） |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「API + Web 混合场景」。请给我完整代码约 250 行：RequestsLibrary 与 SeleniumLibrary 同套件协作——API 创建 3 笔订单，Web 页面逐笔查询并支付，API 断言状态机流转，Suite Teardown 用 API 批量取消并断言零残留。附验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

## 🗂️ 第四阶段：工程化与 RPA（项目 11-14）

> **目标**：造自己的关键字库、编排套件与并行、再把 Robot 的 RPA 面向（Excel/桌面流程）拿下

### [x] 项目 11：自定义 Python 关键字库

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | PythonLibCore、Library 类与关键字命名/文档字符串、库参数与 scope、失败时抛异常的语义 |
| **前置** | 项目 8 |
| **验收标准** | 自研 `ShopLibrary`（订单签名/金额校验/测试数据工厂 ≥6 个关键字）被三套件复用；`robot --dryrun` + 文档生成（libdoc）产出关键字 API 文档 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「自定义 Python 关键字库」。请给我完整代码约 250 行：用 PythonLibCore 写 ShopLibrary（生成唯一订单号、金额 BigDecimal 校验、测试数据工厂、签名计算等 ≥6 关键字，带 docstring），libdoc 生成 API 文档，三个套件复用。附 robot --dryrun 验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [x] 项目 12：标签策略与套件编排

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | Force Tags/--include/--exclude、pabot 并行、--rerunfailed + rebot 合并、--outputdir 报告治理 |
| **前置** | 项目 10 |
| **验收标准** | 全量套件打 smoke/regression 标签按需运行；pabot 并行实测提速 ≥50%；故意让 2 条失败后 --rerunfailed 重跑 + rebot 合并出统一报告 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「标签策略与套件编排」。请给我完整代码约 250 行：全套件打标签（smoke/regression/web/api），演示 --include 组合运行；pabot 并行跑全量统计串行/并行墙钟；故意 2 条失败用 --rerunfailed + rebot 合并出统一 log/report。附三条验收命令。只输出代码。`

**完成日期**：2026-10-27
**踩坑记录**：________

---

### [ ] 项目 13：RPA——Excel 驱动批量下单

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | RPA.Excel.Files 库、RPA Tables、批量流程编排、结果写回与汇总行 |
| **技术栈** | rpaframework（需安装，见环境配置） |
| **前置** | 项目 10 |
| **验收标准** | orders.xlsx 10 行订单全流程自动下单，结果列写回 通过/失败 + 耗时；非法行被逐行捕获且不中断批处理；处理后文件可人工复核 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「RPA——Excel 驱动批量下单」。请给我完整代码约 250 行：RPA.Excel.Files 读 orders.xlsx（10 行订单含 2 行非法），逐行调 Web 下单关键字，结果与耗时写回 Excel 新列，非法行 Run Keyword And Ignore Error 捕获不中断，末尾汇总成功/失败计数。附验收命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 14：RPA——桌面应用自动化

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | RPA.Desktop / RPA.Windows、图像定位 vs 坐标定位、桌面计算器/文本编辑流程、剪贴板关键字 |
| **前置** | 项目 13 |
| **⚠️ 风险** | 桌面自动化对 macOS 辅助功能权限有要求（系统设置里授权终端）；图像定位对分辨率敏感——⚠️ 开工探活，不可行则降级为 RPA.Clipboard + RPA.Windows 键盘流程 |
| **验收标准** | 自动化 macOS 计算器完成 5 道四则运算并断言结果；剪贴板关键字完成跨应用文本搬运；全程无人值守跑完 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「RPA——桌面应用自动化」。请给我完整代码约 220 行：RPA.Desktop/RPA.Windows 驱动 macOS 计算器做 5 道四则运算并断言屏显结果，RPA.Clipboard 完成跨应用文本搬运；流程含辅助功能权限的失败提示。附无人值守验收步骤。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 🗂️ 第五阶段：串联交付（项目 15-17）

> **目标**：三个 🏁——Web 回归、API 回归各自成套，最后 Web+API+RPA 三合一全景串联

### [ ] 项目 15：🏁 Web 回归套件 + CI

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~350 行 |
| **核心知识点** | 资源文件分层（业务关键字库化）、失败留证、act 本地 CI 跑 robot、报告 artifact |
| **前置** | 项目 7、12 |
| **验收标准** | `--include regression` 一条命令全绿 + 失败自动截图；GitHub Actions workflow 被 act 本地真跑成功并上传报告 artifact（对照 labs/30 的 act 用法） |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「🏁 Web 回归套件 + CI」。请给我完整代码约 350 行：Web 关键字库化分层 + regression 标签套件（失败自动截图留证），加 GitHub Actions workflow（装依赖→robot→上传 log/report artifact），用 act 本地真跑一遍。附本地与 act 两条验收命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 16：🏁 API 回归套件

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行 |
| **核心知识点** | 接口回归全集（正向/异常/schema/状态机流转）、套件编排与报告治理 |
| **前置** | 项目 9、11 |
| **验收标准** | 靶场 4 接口回归全集（≥20 条用例）一条命令全绿；含订单状态机全流转用例（创建→支付→取消→不可再支付 409） |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「🏁 API 回归套件」。请给我完整代码约 300 行：靶场 4 接口 ≥20 条回归用例（正向/异常矩阵/schema/订单状态机全流转含 409），复用项目 11 的 ShopLibrary，输出统一 log/report。附验收命令。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

### [ ] 项目 17：🏁 全景串联（Web + API + RPA 三合一）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~350 行 |
| **核心知识点** | Excel 驱动 → API 造数 → Web 验证 → 结果回写 → rebot 多输出合并的全景编排 |
| **前置** | 项目 13、15、16 |
| **验收标准** | 一条命令完成「读 Excel 订单 → API 批量建单 → Web 逐笔支付验证 → 结果写回 Excel → rebot 合并三份输出出总报告」；总报告用例数/通过率与各分报告一致 |

**🤖 开始提示词**：
> `我要开始 Robot Framework 项目「🏁 全景串联」。请给我完整代码约 350 行：一条命令编排 Excel 驱动（RPA 读单）→ API 批量建单 → Web 逐笔支付验证 → 结果写回 Excel，三段各自输出 output.xml 后用 rebot 合并出总报告，断言总数/通过率一致。附一条命令验收步骤。只输出代码。`

**完成日期**：________
**踩坑记录**：________

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-3（地基：靶场/关键字/数据驱动） | 3 |
| **第 2 周** | 项目 4-5（Web 入门 + 控件） | 2 |
| **第 3 周** | 项目 6-7（三难 + 期望失败） | 2 |
| **第 4 周** | 项目 8-10（API 三连 + 混合场景） | 3 |
| **第 5 周** | 项目 11-12（关键字库 + 编排并行） | 2 |
| **第 6 周** | 项目 13-14（RPA 两连） | 2 |
| **第 7 周** | 项目 15-17（🏁 三连串联） | 3 |

## 🏆 里程碑

- [ ] **完成项目 1-3** → 语法上手：表格语法与关键字思维成型，数据驱动两板斧会用
- [ ] **完成项目 4-7** → Web 关键字化：真实页面三难与期望失败都有 Robot 解法
- [ ] **完成项目 8-10** → 接口关键字化：API 全覆盖且能与 Web 拼贯通场景
- [ ] **完成项目 11-14** → 工程化 + RPA：自己的关键字库、编排并行、Excel/桌面流程自动化
- [ ] **全部完成** → Web+API+RPA 三合一全景套件，一条命令出统一报告

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| | | | | |

## 🔧 环境配置

```bash
# 0. 已就绪（2026-10-25 实测）：
#    仓库 venv（Python 3.13）✅   Chrome ✅   Safari + safaridriver ✅   Firefox 158.0.1 + geckodriver 0.37.1 ✅
#    Docker ✅（项目 15 act 本地 CI 用，labs/30 同款）
# 1. 需安装（全部进仓库 venv，不污染全局）：
.venv/bin/pip install robotframework robotframework-seleniumlibrary \
    robotframework-requests robotframework-jsonlibrary \
    robotframework-datadriver robotframework-pabot rpaframework
# 2. 每项目开工前：
.venv/bin/robot --version && .venv/bin/python -c "import SeleniumLibrary, RequestsLibrary"   # 环境体检
```

## ⚠️ 与已有清单的关系

| 已有清单/实验 | 关系 |
|:---|:---|
| docs/selenium.md（selenium 线） | 同为 Web 自动化但流派不同：SeleniumLibrary 底层就是 Selenium——selenium 线用 Python 代码驱动，本线用关键字驱动；两边靶场独立（本线自建），学完可做「同一场景两种流派」对照 |
| docs/playwright.md（playwright/ 系列） | 另一 Web 自动化技术栈（代码驱动 + 自带运行时），与本线零重叠，对比视角同上 |
| labs/23-25（Selenium/Cypress/三框架对比） | labs 只给了 Selenium 单点入门与对比结论；本线把关键字驱动流派单独练透，可回头修正对比结论里 Robot 缺席的空白 |
| docs/appium.md（appium/ 系列） | RPA 项目 13/14 的「流程自动化」与移动端自动化思路相邻（都是驱动 GUI），但平台不同零重叠；Java 工程化经验在两线间通用 |
| docs/mocking.md（mocking/ 系列） | 本线 RequestsLibrary 打的是真靶场接口；mocking 线练的是「依赖不可控时用替身」——思路互补，09 的 pact-as-stub 也可反过来给本线当接口替身 |
| labs/30_local_ci（act 本地 CI） | 项目 15 的 act workflow 直接复用其镜像与用法 |
