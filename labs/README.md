# 🧪 labs/：测试框架主线 30 实验（Python 栈）

> 把 [../docs/test_frameworks.md](../docs/test_frameworks.md) 清单落成的可真实跑通主线：
> pytest 生态（单测/fixture/参数化/mock/覆盖率/性质测试/快照/异步/并行/插件）→ 造 SUT + API/DB/契约
> → Playwright → Cypress/Selenium 三框架硬对比 → Locust/k6/移动端 → a11y/安全 → 本地 CI 终极串联。
> 共享被测应用：实验 11 造的 FastAPI 订单管理，12-30 都测它——同目标才好横向对比。
> 每个实验 = apply/observe/clean 主演示脚本 + 六段式 README + 交互架构图三件套。
> 与 playwright/、cucumber/（TS 栈）、performance/、architect/ 四条线互补，编号即建议顺序。

进度：**30/30 (100%)** ██████████

## 🚀 快速开始

```bash
bash scripts/load_resources.sh        # 一次性环境准备（venv + 依赖 + 浏览器 + k6/act）
bash scripts/load_resources.sh check  # 只体检

cd labs/00_env_check && ./env_check.sh          # 环境体检
cd ../01_pytest_basics && ./pytest_basics.sh    # 第一个实验
cd ../11_sut_app && ./sut_app.sh                # 造被测应用（labs 12-30 都测它）
cd ../.. && make quality                        # 全量流水线（lab 30，需在仓库根目录执行）
```

每个实验的脚本都支持 `apply | observe | clean | all`：**apply** 准备环境与数据 → **observe** 分步演示（输出即教材）→ **clean** 删干净无残留。

预期失败的演示在脚本里用 `|| true` 显式标注，observe 看到"红"是教学点（完整清单见下方诚实标注节）。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [00](00_env_check/README.md) | 环境体检 | 一条命令确认 30 实验前置 | 幂等安装 + 缺项指引 |
| [01](01_pytest_basics/README.md) | pytest 起步 | 温度模块 17 用例 | 断言重写回溯、-k/-x/-s |
| [02](02_fixtures/README.md) | fixture | 作用域三件套 | session 连接只建一次的实测证据 |
| [03](03_parametrize/README.md) | 参数化 | 11 函数展开 24 用例 | ids 可读命名、indirect |
| [04](04_mock/README.md) | mock 与替身 | mock/fake 同场景对写 | freezegun 冻结截止逻辑 |
| [05](05_coverage/README.md) | 覆盖率门禁 | 78%→100% 实录 | 门禁低于阈值退出码非 0 |
| [06](06_hypothesis/README.md) | Hypothesis | 性质测试 + 收缩 | 真实挖出 2 个编解码边界 bug |
| [07](07_snapshot/README.md) | syrupy 快照 | 破坏→红→更新→绿 | diff 即审查界面 |
| [08](08_async/README.md) | 异步与时间 | 重试客户端 8 用例 | 名义退避 3.5s 实跑 <1s |
| [09](09_xdist/README.md) | xdist 并行 | 11.8s→1.9s（6.2x） | 共享计数器并行当场翻车实录 |
| [10](10_plugin/README.md) | 自定义插件 | pytest-ministore-report | 双项目 pip 复用、marker 校验 |
| [11](11_sut_app/README.md) | 被测应用 SUT | FastAPI 订单管理 | 契约冻结，种子幂等 |
| [12](12_api_tests/README.md) | API 测试 | 30 条 httpx 用例 | 乱序/并行全绿（自造自清） |
| [13](13_db_tests/README.md) | 数据库集成 | 两种隔离对决 | 裸 SQLite 必现 database is locked |
| [14](14_testcontainers/README.md) | Testcontainers | 真 Postgres 随测起停 | 4 条 SQLite↔PG 差异实测 |
| [15](15_pact/README.md) | 契约测试 | consumer→pact→verify 闭环 | 改字段名 verify 当场红 |
| [16](16_pw_basics/README.md) | Playwright 入门 | 下单/查询/删除 | trace 回放 + codegen |
| [17](17_pw_locators/README.md) | 等待哲学 | 竞态/延迟/慢接口 | 连跑 10 次不红 + 反模式必挂 |
| [18](18_pw_pom/README.md) | POM | 选择器收口 pages/ | 新用例 12 行 + 泄漏检查 |
| [19](19_pw_network/README.md) | 网络拦截 | route 桩 + storageState | 后端挂了照样测前端 |
| [20](20_pw_quality/README.md) | 三核与留痕 | 3×3 冒烟矩阵全绿 | 失败自动截图+视频+trace |
| [21](21_cypress_basics/README.md) | Cypress 入门 | 复刻 16 的 3 用例 | headless 1s 全绿 |
| [22](22_cypress_advanced/README.md) | Cypress 进阶 | intercept/session/命令 | 双角色会话不串号 |
| [23](23_selenium_basics/README.md) | Selenium 基础 | 无等待必挂 vs 显式等待 | Safari 门槛诚实标注 |
| [24](24_selenium_advanced/README.md) | Selenium 进阶 | POM + Grid | Docker Grid ×2 并行 1.8x |
| [25](25_comparison/README.md) | 三框架硬对比 | 实测 CSV + 报告 | PW 2.7s < CY 3.0s < SE 5.6s |
| [26](26_locust/README.md) | Locust | 10→100 阶梯压测 | 拐点报告对接 SQLite 锁结论 |
| [27](27_k6/README.md) | k6 | smoke/ramping/spike | thresholds 不达标即拦 |
| [28](28_appium/README.md) | 移动端 | Appium 参考 + fallback | 触屏语义实测（如实记录） |
| [29](29_a11y_security/README.md) | a11y 与安全 | axe 门禁 + ZAP 基线 | 扫出 critical→修复→复扫绿 |
| [30](30_local_ci/README.md) | 本地 CI | 六层流水线 | make / act / Actions 同源语义 |

## 🧭 学习路线

1. labs 01-10 pytest 基本功：断言、fixture、参数化、mock、覆盖率、性质测试、快照、异步、并行、插件
2. labs 11 造被测应用 → 12-15 API / 数据库隔离 / Testcontainers / 契约测试
3. labs 16-20 Playwright E2E 入门；想深挖 TS 原生栈或组件测试/视觉回归/CI 分片，转 [playwright/](../playwright/README.md)
4. labs 21-25 Cypress / Selenium 与三框架同题硬对比（PW 2.7s < CY 3.0s < SE 5.6s）
5. labs 26-27 Locust / k6 把性能当工具用；想补完整性能工程闭环，转 [performance/](../performance/README.md)
6. labs 28-29 移动端与 a11y/安全 → labs 30 六层流水线收官（make / act / GitHub Actions 同源语义）
7. 想让业务方读得懂测试 → [cucumber/](../cucumber/README.md)：BDD 让测试描述变成活文档
8. 前四线跑通后 → [architect/01](../architect/01_pyramid_audit/README.md) 金字塔审计：对 labs 全部 418 用例画像（E2E 数量占 12.2%、耗时占 48.7%，成本背离是核心发现），此后每题治理一类真实工程问题

## 🖼️ 架构图

labs 01-30 每个实验配一张交互架构图（00 为纯环境体检，不配图，共 29 张）：双主题 SVG 与可交互 HTML 在各自 `images/` 目录，浏览器直接打开 HTML 可缩放、看动画轨迹。

## ⚠️ 预期失败诚实标注

以下"红"是设计好的教学点，脚本内均有注释：

- 01 断言回溯演示、06 收缩演示（真战果：挖出编解码 2 个边界 bug）、07 快照 diff、09 并行污染翻车、13 database is locked、15 契约破坏 verify 红、17 反模式 sleep 必挂、23 无等待 NoSuchElementException、27 thresholds 违例
- 28 的 Appium 链路在无 Xcode 工具链机器上按清单走 Playwright 移动视口 fallback（探测输出如实打印断点）
- 23 的 Safari 需手动 `sudo safaridriver --enable`（脚本只探测不代执行）

## 🔧 环境要求

macOS（Apple Silicon 实测）/ Python 3.11+ / Docker（14、24、29、30 用）/ Chrome+Safari 自带。
`bash scripts/load_resources.sh check` 一条命令体检全部前置。
