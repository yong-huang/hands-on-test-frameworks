# 30 · 终极串联：分层本地 CI 流水线（GitHub Actions + make + act）

> 30 个实验的最后一课：把 1-29 全部串进一条分层流水线——单测秒级反馈在前，
> 重型验证在后，任一环红即整体红。三种入口同一语义：push 触发 GitHub Actions、
> `make` 本地等价执行、`act` 在 Docker 里复跑。读完本篇你能读懂六层 workflow
> 的分层设计，并本地验证与 CI 同源的流水线语义。

## Background

30 个实验各自为政时，"质量"是一堆散落的脚本；串进流水线后，它变成
**一条有顺序、有依赖、有阻断语义的链**。散脚本的问题在集成时刻爆发：
先跑重型还是轻型全凭习惯，红灯出现得太晚（E2E 跑了 5 分钟才暴露一个
单测错），重复消耗所有人的时间。

分层流水线的原则：**反馈速度决定问题定位成本**——快而稳定的层在前
（unit-core 10 秒级），重依赖在后（E2E 要装浏览器、perf 要起 SUT、
a11y 要 Docker），needs 链式依赖让红灯尽量早出现在便宜的层。

三种入口的语义一致性是工程关键：push 后 GitHub Actions 跑云端流水线；
`make` 在本地跑同一批命令（等价语义）；`act` 把 workflow 装进 Docker
本地复跑（连环境差异都抹掉）——不需要 push 探路。

## What

本实验的流水线分六层，`needs` 表达依赖：

```yaml
jobs:
  unit-core:      # 秒级，act 可本地复跑
  api-tests:      # needs: unit-advanced
  e2e-playwright: # needs: api-tests
  perf-smoke:     # needs: e2e-playwright（k6 thresholds 即门禁）
  a11y-security:  # needs: perf-smoke（ZAP 报告 always() 上传）
```

可以把流水线想成机场安检的分层：证件检查（单测）在门口秒过，过不了就别进候机厅；行李扫描（API）、全身扫描（E2E）、防爆检查（perf/a11y）逐层加重——每层只处理上一层放行的人，红灯永远出现在最便宜的层。

但和安检不同的是，每一层都有"失败即整体失败"的退出码语义（pytest 红、k6 thresholds 违例、axe critical 超限），报告 artifact 是失败时的存证。


教学脚本与门禁用例必须分离：`make unit` 直接调 pytest 绿色子集
（`-k "not regression_demo"`）而不是 lab 01 的教学脚本——因为教学脚本里的
故意失败用例会让流水线红。**演示用的"预期失败"永远不该进门禁**。

## When to Use

典型场景：

- 仓库落地 CI 的参考骨架：六层分层 + needs 依赖 + artifact 存证，
  直接照抄再裁剪。
- 本地预检：push 前跑 `make unit api`，把 10 秒能发现的错留在本地。
- CI 语义本地验证：改了 workflow 想验证语法与语义，`act` 本地复跑
  不用 push 探路。

何时不用：单人玩具仓库全套六层是过度工程——一层单测 + 一层 E2E 足够；
流水线层数应该随团队的失败模式生长，而不是一次配齐显得专业。

## Quick Start

前置条件：labs/00 体检通过；act 本地复跑需要 **Docker 运行**
（本机实测 Docker 未启动，act 步骤在 Set up job 处失败——
这正是实验设计的"前置探测"要拦住的情况）。

```bash
cd labs/30_local_ci
./local_ci.sh          # git 检查 → make unit api → act 复跑 unit-core
make quality           # 全量本地等价：单测→API→E2E→k6→a11y（约 10 分钟）
act push -j unit-core -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

make 快速流水线的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① make 快速流水线：unit → api（失败即阻断，语义同 CI）
=====> [unit] pytest 基本功 + 高级单测（绿色子集；教学脚本含故意失败，故直接调 pytest）
cd labs/01_pytest_basics && ... pytest -c configs/pytest.ini --rootdir=. -q -k "not regression_demo"
collected 17 items / 1 deselected / 16 selected

tests/test_temperature.py ................                               [100%]

======================= 16 passed, 1 deselected in 0.06s =======================
```

api 层收尾的真实输出（2026-09-29 `make api` 实测，节选）：

```
=====> [observe] ④ 并行模式跑一遍：自造自清的用例天然 xdist 安全（serial 窗口用例除外）
============================== 29 passed in 2.27s ==============================
```

29 条而非 30 条：第 30 条是 serial 标记的数据窗口用例，被 `make api` 所调的
labs/12 脚本以 `-m "not serial"` 排除（labs/12 的并行纪律），单独在串行轮跑。

act 本地复跑的真实输出（本机 Docker 未启动，节选）：

```
=====> [observe] ② act 本地复跑 workflow 的 unit-core job（Docker 内执行，与 CI 同源）
[tests/unit-core]   ❌  Failure - Set up job
```

诚实预期：make 快速层（unit 16+24+8 条单测、api 30 条）在本机全绿；act 复跑
在 Docker 就绪的机器上应成功执行 unit-core job（与 CI 同一 workflow 文件）。

**本机 Docker 未启动所以这步失败，失败点在容器拉起（Set up job）而非
workflow 语义**，Docker 就绪后重跑即绿。

GitHub 云端流水线在 push 后自动跑全部六层。


关键文件（这段在做什么：workflow 定义与本地等价入口）：

- `.github/workflows/tests.yml`：六层 workflow（仓库根）。
- `Makefile`：`make quality` / `unit` / `api` / `e2e` / `perf` / `a11y` / `clean`。

## How It Works

**needs 链的阻断语义**：GitHub Actions 的 `needs` 让后层等前层成功才启动；`make` 的顺序执行 + 每个命令"失败非 0"达成同样语义。

两条链路的每一环都遵守退出码即法律——pytest 红、k6 thresholds 违例（lab 27 的退出码 99）、axe critical 超限（lab 29 的断言）、API 断言失败，任何一环非 0 整体红。


**本地与 CI 的语义一致性**：同一批脚本入口（lab 脚本/Makefile），CI 只是换了运行环境；act 再把"环境"的差异也抹掉——workflow 装进catthehacker/ubuntu 镜像（含 Python）执行，与云端同一个 YAML。

两个前置：Docker 运行 + 仓库已 `git init`（act 依赖 git 上下文，本仓库由 lab 30 首跑时初始化，不推送远端）。


**失败留存的 always() 上传**：a11y 的 ZAP 报告用 `if: always()` 上传
artifact——失败时的报告比成功时的更有价值，job 被取消也要把证据留下。

**并行中的 serial 窗口**：api 层在并行轮要跳过数据窗口类用例
（lab 12 的 `-m "not serial"`）——流水线里并行是常态，serial 标记
是留给"必须独占"用例的逃生门。

## Pitfalls & Q&A

踩坑清单（本实验真实踩过）：

- **act 输出接管道被 SIGPIPE**。现象：act 输出接 `head` 时异常退出。
  解法：加 `|| true` 吸收。
- **教学脚本的预期失败进了门禁**。现象：流水线永远红。
  解法：门禁直接调 pytest 绿色子集，预期失败留在教学脚本里。
- **serial 用例在并行轮打架**。现象：并行跑时数据窗口断言偶发失败。
  解法：`-m "not serial"` 排除，serial 用例单独串行轮跑。
- **Docker 没起就跑 act**。现象：Set up job 失败。
  解法：先 `docker info` 体检（labs/00 的体检项）。

深入问答：

- **Q：流水线怎么分层？** 按反馈速度×失败概率排：最快最稳的最先；
  用 needs 表达依赖，让"红灯"尽量早出现在便宜的层。
- **Q：本地与 CI 的语义一致性怎么保证？** 同一批脚本入口（lab 脚本/Makefile），
  CI 只是换了运行环境；act 把"环境"的差异也抹掉。
- **Q：报告 artifact 为什么 always() 上传？** 失败时的报告比成功时的更有价值。

系列全文见 [根 README](../../README.md)。
