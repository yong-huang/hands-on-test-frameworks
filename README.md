# 🧪 hands-on-test-frameworks：测试框架动手学习系列

> 五份项目清单落成的动手实验仓库：**5 条实验线、102 个实验**，全部在本机（Apple Silicon）真实跑通，
> 只用开源工具、不碰任何付费 SaaS。每个实验 = **主演示脚本**（apply/observe/clean 生命周期）
> + **六段式 README** + **交互式架构图**，clone 下来照着跑就能复现每一个结论。

## 🗺️ 五条实验线

| 线 | 目录 | 技术栈 | 内容 | 进度 |
|:---|:---|:---|:---|:---|
| 框架主线 | [labs/](labs/README.md) | Python | pytest 基本功 → 造 SUT + API/DB/契约 → Playwright → Cypress/Selenium 三框架硬对比 → Locust/k6/移动/a11y → 本地 CI | ✅ 00 体检 + 30/30 |
| Playwright 进阶 | [playwright/](playwright/README.md) | TypeScript | 靶场 pw-store → 定位/认证/网络/视觉/组件 → 调试/POM/并行/矩阵/报告/flaky → CI 分片 → 🏁 终极串联（163 用例一条命令） | ✅ 19/19 |
| Cucumber BDD | [cucumber/](cucumber/README.md) | TypeScript | Gherkin 闭环 → 步骤设计/World → 数据驱动/好坏 Gherkin → 工程化四件套 → 方法论 → CI → 🏁 终极套件 | ✅ 14/14 |
| 性能工程 | [performance/](performance/README.md) | Python + Go + Docker | 双靶场贯穿：基线 → 负载建模 → 监控 → 双栈剖析 → DB/缓存/调参 → 泄漏 → 回归门禁 + 容量报告 | ✅ 10/10 |
| 测试架构师 | [architect/](architect/README.md) | Python | 问题驱动 28 题：分层审计/风险策略/质量门禁/精准测试/flaky 治理/环境工厂/度量看板/AI 评测，治理对象就是其余四条线的资产 | ✅ 28/28 |

递进关系：labs 学会**用工具** → performance 学会**测性能** → playwright/cucumber 把单点挖到**深水区** → architect 练**设计体系**。五份清单文档（阶段规划/验收标准/周计划）在 [docs/](docs/)。

共享被测应用让同主题实验可横向对比：labs 12-30 都测 labs/11 造的 FastAPI 订单管理（SUT，被测系统）；playwright/03 起与 cucumber/ 全线都测 playwright/02 造的靶场 pw-store。

## 🚀 快速开始

```bash
# labs 主线：环境一条命令备齐（venv + 依赖 + 浏览器 + k6 压测工具 / act 本地 CI 运行器）
bash scripts/load_resources.sh            # 加 check 只体检

cd labs/00_env_check && ./env_check.sh                      # labs 从环境体检开始
bash playwright/load_resources.sh                           # playwright/ 环境：node 依赖 + 三核浏览器
bash cucumber/load_resources.sh                             # cucumber/ 环境：cucumber 13 + playwright 1.62 + tsx
cd performance/01_perf_baseline && ./perf_baseline.sh all   # performance/ 首个实验（需 Docker + k6）
cd architect/01_pyramid_audit && ./pyramid_audit.sh all     # architect/ 首题（治理 labs 全部资产）
```

每条线的入口实验、逐实验总表与学习路线见各自系列 README。

实验脚本统一支持 `apply | observe | clean | all`：**apply** 准备环境与数据 → **observe** 分步演示（输出即教材）→ **clean** 删干净无残留。预期失败的演示在脚本里用 `|| true` 显式标注，observe 看到"红"是教学点，不是环境坏了。

## ⚠️ 预期失败诚实标注

每条线都有设计好的教学点红，脚本内均有显式标注，完整清单见各系列 README 的同名小节：

- labs：断言回溯、快照 diff、并行污染、契约破坏、反模式必挂……
- playwright：设计为红的病例、失败标本、注入 flaky
- cucumber：失败标本、保持 pending 的场景
- performance：故意埋病的靶场、注入回归验证门禁

两个跨线注意点：

- labs 23 的 Safari 需手动 `sudo safaridriver --enable`（脚本只探测不代执行）
- playwright/18 与 cucumber/13 的 act 校验依赖代理与本地镜像（踩坑链见 playwright/18 的 README）

## 🔧 环境要求

- macOS（Apple Silicon 实测）
- Python 3.11+：labs、performance、architect
- Node 20+：playwright/ 与 cucumber/
- Docker：labs 14/24/29/30 与 performance/ 全线
- Chrome+Safari 自带
- labs 前置一条命令体检：`bash scripts/load_resources.sh check`

## 📝 来源与许可

五份学习清单在 [docs/](docs/)，与实验目录一一对应：

- [test_frameworks.md](docs/test_frameworks.md)（labs 30）
- [performance.md](docs/performance.md)（10）
- [playwright.md](docs/playwright.md)（19）
- [cucumber.md](docs/cucumber.md)（14）
- [test_architect.md](docs/test_architect.md)（28）

实验实现与脚本为系列配套产物。LICENSE 待定（默认保留所有权利，如需 MIT 请告知）。
