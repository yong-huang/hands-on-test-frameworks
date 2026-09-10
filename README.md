# 🧪 hands-on-test-frameworks：30 个小项目吃透 pytest / Playwright / Cypress / Selenium

> 把 [test_frameworks.md](test_frameworks.md) 的 30 项目清单落成**全部可真实跑通**的动手系列：
> pytest 生态（单测/参数化/性质测试）→ API/DB/契约 → Playwright → Cypress/Selenium 三国杀 →
> 性能（Locust/k6）→ 移动端 → a11y/安全 → 本地 CI 终极串联。
> 每个实验 = **主演示脚本**（apply/observe/clean 生命周期）+ **编号 README** + **交互式架构图三件套**。
> 共享被测应用 SUT（实验 11 造的 FastAPI 订单管理），同目标才好对比。
> 全程免费：只用开源工具本地跑，不碰任何付费 SaaS。

进度：**30/30 (100%)** ██████████

## 🗺️ 学习路线

```
 阶段一/二 (01-10)          阶段三 (11-15)          阶段四 (16-20)
 pytest 单测基本功     →    造 SUT + API/契约   →   Playwright E2E
 ───────────────────────────────────────────────────────────────
 阶段五 (21-25)                               阶段六 (26-30)
 Cypress + Selenium + 硬对比  →   Locust/k6/移动/a11y/CI 终极串联
          ↑ 全程共用同一个被测应用 SUT（实验 11 造）↑
```

## 🚀 快速开始

```bash
bash scripts/load_resources.sh      # 一次性环境准备（venv + 依赖 + 浏览器 + k6/act）
bash scripts/load_resources.sh check  # 只体检

cd labs/01_pytest_basics && ./pytest_basics.sh    # 第一个实验
cd labs/11_sut_app && ./sut_app.sh                # 被测应用（后续 19 个实验都测它）
make quality                                       # 全量流水线（lab 30）
```

每个实验的脚本都支持 `apply | observe | clean | all`：
**apply** 准备环境与数据 → **observe** 分步演示（输出即教材）→ **clean** 删干净无残留。
预期失败的演示（断言回溯、快照变红、Grid 锁冲突……）在脚本里用 `|| true` 显式标注。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [00](labs/00_env_check/README.md) | 环境体检 | 一条命令确认 30 实验前置 | 幂等安装 + 缺项指引 |
| [01](labs/01_pytest_basics/README.md) | pytest 起步 | 温度模块 17 用例 | 断言重写回溯、-k/-x/-s |
| [02](labs/02_fixtures/README.md) | fixture | 作用域三件套 | session 连接只建一次的实测证据 |
| [03](labs/03_parametrize/README.md) | 参数化 | 11 函数展开 24 用例 | ids 可读命名、indirect |
| [04](labs/04_mock/README.md) | mock 与替身 | mock/fake 同场景对写 | freezegun 冻结截止逻辑 |
| [05](labs/05_coverage/README.md) | 覆盖率门禁 | 78%→100% 实录 | 门禁低于阈值退出码非 0 |
| [06](labs/06_hypothesis/README.md) | Hypothesis | 性质测试 + 收缩 | 真实挖出 2 个编解码边界 bug |
| [07](labs/07_snapshot/README.md) | syrupy 快照 | 破坏→红→更新→绿 | diff 即审查界面 |
| [08](labs/08_async/README.md) | 异步与时间 | 重试客户端 8 用例 | 名义退避 3.5s 实跑 <1s |
| [09](labs/09_xdist/README.md) | xdist 并行 | 11.8s→1.9s（6.2x） | 共享计数器并行当场翻车实录 |
| [10](labs/10_plugin/README.md) | 自定义插件 | pytest-ministore-report | 双项目 pip 复用、marker 校验 |
| [11](labs/11_sut_app/README.md) | 被测应用 SUT | FastAPI 订单管理 | 契约冻结，种子幂等 |
| [12](labs/12_api_tests/README.md) | API 测试 | 30 条 httpx 用例 | 乱序/并行全绿（自造自清） |
| [13](labs/13_db_tests/README.md) | 数据库集成 | 两种隔离对决 | 裸 SQLite 必现 database is locked |
| [14](labs/14_testcontainers/README.md) | Testcontainers | 真 Postgres 随测起停 | 4 条 SQLite↔PG 差异实测 |
| [15](labs/15_pact/README.md) | 契约测试 | consumer→pact→verify 闭环 | 改字段名 verify 当场红 |
| [16](labs/16_pw_basics/README.md) | Playwright 入门 | 下单/查询/删除 | trace 回放 + codegen |
| [17](labs/17_pw_locators/README.md) | 等待哲学 | 竞态/延迟/慢接口 | 连跑 10 次不红 + 反模式必挂 |
| [18](labs/18_pw_pom/README.md) | POM | 选择器收口 pages/ | 新用例 12 行 + 泄漏检查 |
| [19](labs/19_pw_network/README.md) | 网络拦截 | route 桩 + storageState | 后端挂了照样测前端 |
| [20](labs/20_pw_quality/README.md) | 三核与留痕 | 3×3 冒烟矩阵全绿 | 失败自动截图+视频+trace |
| [21](labs/21_cypress_basics/README.md) | Cypress 入门 | 复刻 16 的 3 用例 | headless 1s 全绿 |
| [22](labs/22_cypress_advanced/README.md) | Cypress 进阶 | intercept/session/命令 | 双角色会话不串号 |
| [23](labs/23_selenium_basics/README.md) | Selenium 基础 | 无等待必挂 vs 显式等待 | Safari 门槛诚实标注 |
| [24](labs/24_selenium_advanced/README.md) | Selenium 进阶 | POM + Grid | Docker Grid ×2 并行 1.8x |
| [25](labs/25_comparison/README.md) | 三框架硬对比 | 实测 CSV + 报告 | PW 2.7s < CY 3.0s < SE 5.6s |
| [26](labs/26_locust/README.md) | Locust | 10→100 阶梯压测 | 拐点报告对接 SQLite 锁结论 |
| [27](labs/27_k6/README.md) | k6 | smoke/ramping/spike | thresholds 不达标即拦 |
| [28](labs/28_appium/README.md) | 移动端 | Appium 参考 + fallback | 触屏语义实测（如实记录） |
| [29](labs/29_a11y_security/README.md) | a11y 与安全 | axe 门禁 + ZAP 基线 | 扫出 critical→修复→复扫绿 |
| [30](labs/30_local_ci/README.md) | 本地 CI | 六层流水线 | make / act / Actions 同源语义 |

## 📐 目录结构

```
hands-on-test-frameworks/
├── README.md                  # 本文件
├── test_frameworks.md         # 原始 30 项目清单（来源）
├── Makefile                   # make quality 一键流水线（lab 30）
├── .github/workflows/tests.yml# 六层 CI workflow
├── scripts/
│   ├── load_resources.sh      # 共享环境准备（幂等）
│   └── gen-diagrams.py        # 架构图图源生成器（29 张图，调 Archify 技能渲染）
└── labs/
    └── NN_short_name/         # 30 个实验，结构完全一致
        ├── README.md          # 编号章节 + 交互图链接
        ├── xxx.sh             # 主演示脚本（apply/observe/clean）
        ├── configs/           # pytest.ini / .coveragerc / k6 场景等
        ├── tests|cypress|...  # 实验代码
        └── images/            # 图三件套：xxx.<type>.json + xxx.html + xxx.svg
```

## 🖼️ 架构图

每个实验 README 的「总览」节内嵌双主题 SVG，并附交互版链接：
本地直接打开 `labs/NN_xxx/images/xxx.html`（自包含单文件，可缩放/看动画轨迹）。

## ⚠️ 预期失败诚实标注

以下"红"是设计好的教学点，脚本内均有注释：
01 断言回溯演示、06 收缩演示（另附真战果：编解码 2 个边界 bug）、
07 快照 diff、09 并行污染翻车、13 database is locked、
15 契约破坏 verify 红、17 反模式 sleep 必挂、23 无等待 NoSuchElementException、
27 thresholds 违例。28 的 Appium 链路在无 Xcode 工具链机器上按清单走
Playwright 移动视口 fallback（探测输出如实打印断点）；23 的 Safari 需手动
`sudo safaridriver --enable`（脚本只探测不代执行）。

## 🔧 环境要求

macOS（Apple Silicon 实测）/ Python 3.11+ / Node 20+ / Docker（14、24、29、30 用）
/ Chrome+Safari 自带。`bash scripts/load_resources.sh check` 一条命令体检全部。

## 📝 来源与许可

学习路线与项目定义来自 [test_frameworks.md](test_frameworks.md)；
实验实现与脚本为系列配套产物。LICENSE 待定（默认保留所有权利，如需 MIT 请告知）。

## 🔬 性能工程系列（10/10 全部跑通）

[performance.md](performance.md) 定义了独立的 10 项目性能工程清单（观测/剖析/调优/容量），
实验从 [performance/31_perf_baseline](performance/31_perf_baseline) 起编号，与上面 30 个框架实验互补不重叠。
