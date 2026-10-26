# 🧪 hands-on-test-frameworks：测试框架动手学习系列

> 十份项目清单落成的动手实验仓库：**10 条实验线、189 个实验**，全部在本机（Apple Silicon）真实跑通，
> 只用开源工具、不碰任何付费 SaaS。每个实验 = **主演示脚本**（apply/observe/clean 生命周期）
> + **六段式 README** + **交互式架构图**，clone 下来照着跑就能复现每一个结论。

## 🗺️ 八条实验线

| 线 | 目录 | 技术栈 | 内容 | 进度 |
|:---|:---|:---|:---|:---|
| 框架主线 | [labs/](labs/README.md) | Python | pytest 基本功 → 造 SUT + API/DB/契约 → Playwright → Cypress/Selenium 三框架硬对比 → Locust/k6/移动/a11y → 本地 CI | ✅ 00 体检 + 30/30 |
| Playwright 进阶 | [playwright/](playwright/README.md) | TypeScript | 靶场 pw-store → 定位/认证/网络/视觉/组件 → 调试/POM/并行/矩阵/报告/flaky → CI 分片 → 🏁 终极串联（163 用例一条命令） | ✅ 19/19 |
| Cucumber BDD | [cucumber/](cucumber/README.md) | TypeScript | Gherkin 闭环 → 步骤设计/World → 数据驱动/好坏 Gherkin → 工程化四件套 → 方法论 → CI → 🏁 终极套件 | ✅ 14/14 |
| 性能工程 | [performance/](performance/README.md) | Python + Go + Docker | 双靶场贯穿：基线 → 负载建模 → 监控 → 双栈剖析 → DB/缓存/调参 → 泄漏 → 回归门禁 + 容量报告 | ✅ 10/10 |
| 测试架构师 | [architect/](architect/README.md) | Python | 问题驱动 28 题：分层审计/风险策略/质量门禁/精准测试/flaky 治理/环境工厂/度量看板/AI 评测，治理对象是 labs/ 全部 30 个实验与其 SUT | ✅ 28/28 |
| Appium iOS | [appium/](appium/README.md) | Java + iOS | 真实 App 贯穿：首会话 → 定位/登录/购物车/结算 → 手势/WebView/Face ID/生命周期 → 数据驱动/POM（页面对象模型）/报告 → 🏁 双模拟器终极套件 | ✅ 14/14 |
| 测试左移 | [shiftleft/](shiftleft/README.md) | Python | 成本漏斗 → 需求可测性/卡片/矩阵 → 契约先行/TDD/变异 → 静态门禁/SAST/供应链/pre-commit → CI 分层/性能预算 → 🏁 全景串联 | ✅ 20/20 |
| 服务虚拟化 | [mocking/](mocking/README.md) | Python + Docker | 订单 BFF（Backend for Frontend，聚合多个下游、专供前端的后端层）三下游贯穿：声明式 stub → WireMock/状态机/模板 → 录制回放/故障矩阵 → 契约融合/漂移门禁 → GraphQL/gRPC/WS/Kafka → 🏁 compose 全家桶 | ✅ 18/18 |
| Selenium Web | [selenium/](selenium/README.md) | Python + Java 双栈 | 带病靶场贯穿：定位/等待 → 窗口/iframe/JS/Actions → 证据链/POM/数据驱动 → Grid 并行/浏览器矩阵/CDP/flaky → 🏁 双栈终极套件 | ✅ 18/18 |
| Robot Framework | [robotframework/](robotframework/README.md) | Python | 关键字驱动：Web（SeleniumLibrary）/API（RequestsLibrary）/RPA（Excel+桌面）→ 自定义库/编排并行 → 🏁 Web+API+RPA 三合一串联 | ✅ 17/17 |

缩写：a11y＝无障碍可访问性；POM＝页面对象模型；SAST＝静态应用安全测试；WS＝WebSocket。

递进关系：labs 练**用工具** → performance 学**测性能** → playwright/cucumber 挖**深水区** →
appium 上**真移动 App** → selenium/robotframework 吃透 **Web 双流派**。

再往右走：mocking 斩**依赖** → shiftleft **向左移** → architect 练**体系**。

十份清单文档（阶段规划/验收标准/周计划）见 [docs/](docs/)。

共享被测应用让同主题实验可横向对比：labs 12-30 都测 labs/11 造的 FastAPI 订单管理（SUT，被测系统）；
playwright/03 起与 cucumber/ 全线都测 playwright/02 造的靶场 pw-store。

selenium/ 与 robotframework/ 各有自建靶场（带病电商站 / Robot 商店）。

appium/ 全线测 SauceLabs My Demo App 真实 iOS 应用；shiftleft/ 拿 labs/11 的订单应用当治理对象；mocking/ 的 09 用 labs/11 当真 provider 对账。

## 🚀 快速开始

```bash
# labs 主线：环境一条命令备齐（venv + 依赖 + 浏览器 + k6 压测工具 / act 本地 CI 运行器）
bash scripts/load_resources.sh            # 加 check 只体检

cd labs/00_env_check && ./env_check.sh                      # labs 从环境体检开始
bash playwright/load_resources.sh                           # playwright/ 环境：node 依赖 + 三核浏览器
bash cucumber/load_resources.sh                             # cucumber/ 环境：cucumber 13 + playwright 1.62 + tsx
cd performance/01_perf_baseline && ./perf_baseline.sh all   # performance/ 首个实验（需 Docker + k6）
cd architect/01_pyramid_audit && ./pyramid_audit.sh all     # architect/ 首题（治理 labs 全部资产）
cd appium/00_env && ./setup.sh                              # appium/ 环境：Appium 3.8 + XCUITest driver + doctor（需 Xcode + Java）
cd shiftleft/01_cost_funnel && ./cost_funnel.sh             # shiftleft/ 首题（缺陷成本漏斗）
cd mocking/01_declarative_mock && ./declarative_mock.sh all # mocking/ 首个实验（纯标准库声明式替身）
```

每条线的入口实验、逐实验总表与学习路线见各自系列 README。

实验脚本统一支持 `apply | observe | clean | all`：**apply** 准备环境与数据 → **observe** 分步演示（输出即教材）→ **clean** 删干净无残留。预期失败的演示在脚本里用 `|| true` 显式标注，observe 看到"红"是教学点，不是环境坏了。

## ⚠️ 预期失败诚实标注

每条线都有设计好的教学点红，脚本内均有显式标注，完整清单见各系列 README 的同名小节：

- labs：断言回溯、快照 diff、并行污染、契约破坏、反模式必挂……
- playwright：设计为红的病例、失败标本、注入 flaky
- cucumber：失败标本、保持 pending 的场景
- performance：故意埋病的靶场、注入回归验证门禁
- appium：真实 App 的元素歧义与排序键缺陷、WebView context 不可见（降级断言）、Face ID 提示「卡住」、报告线的故意失败
- shiftleft：预期红贯穿全线（strict 卡点、停挡板全红、门禁 exit 1、超预算即红，脚本内均显式标注）
- mocking：响亮未命中 404、断网门红、契约外 500、Kafka 毒丸进 DLQ（死信队列）——红是验收的一部分
- selenium：sleep 版必挂（数据说话）、注入失败留证据、Safari 非前台 click 不生效（JS 兜底）
- robotframework：负向 422/409 按预期绿、注入失败截图留证、RPA 非法行记表不中断——红是验收的一部分
- architect：labs 的故意失败用例被审计声明豁免、植入 flaky/劣化 canary/植入 CVE 的抓红即验收

两个跨线注意点：

- labs 23 的 Safari 需手动 `sudo safaridriver --enable`（脚本只探测不代执行）
- playwright/18 与 cucumber/13 的 act 校验依赖代理与本地镜像（踩坑链见 playwright/18 的 README）

## 🔧 环境要求

- macOS（Apple Silicon 实测）
- Python 3.11+：labs、performance、architect、shiftleft、mocking、selenium、robotframework
- Node 20+：playwright/ 与 cucumber/（shiftleft 仅 03 复用、mocking 仅 08/10 的 Prism）
- Docker：labs 14/24/29/30、performance/ 全线、mocking 02-04/07/14/17/18、architect 10（act 本地流水线）、selenium 13/18（Grid）、robotframework 15（act）
- Java 17 + Maven + 完整 Xcode（iPhone 17 / iOS 26.5 模拟器）：appium/
- Chrome+Safari 自带
- labs 前置一条命令体检：`bash scripts/load_resources.sh check`

## 📝 来源与许可

八份学习清单在 [docs/](docs/)，与实验目录一一对应：

- [test_frameworks.md](docs/test_frameworks.md)（labs 30）
- [performance.md](docs/performance.md)（10）
- [playwright.md](docs/playwright.md)（19）
- [cucumber.md](docs/cucumber.md)（14）
- [test_architect.md](docs/test_architect.md)（28）
- [appium.md](docs/appium.md)（14）
- [shiftleft.md](docs/shiftleft.md)（20）
- [mocking.md](docs/mocking.md)（18）
- [selenium.md](docs/selenium.md)（18）
- [robotframework.md](docs/robotframework.md)（17）

实验实现与脚本为系列配套产物。LICENSE 待定（默认保留所有权利，如需 MIT 请告知）。
