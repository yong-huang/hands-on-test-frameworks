# 30 · 终极串联：分层本地 CI 流水线（GitHub Actions + make + act）

> 30 个实验的最后一课：把 1-29 全部串进一条**分层流水线**——
> 单测秒级反馈在前，重型验证在后，任一环红即整体红。三种入口同一语义：
> push 触发 GitHub Actions、`make` 本地等价执行、`act` 在 Docker 里复跑。

## 1. 为什么需要它

- 分层是流水线的灵魂：unit（秒）→ api（十秒）→ e2e（分钟）→ perf/a11y（末段）。
- "失败即阻断"的退出码语义是整条链路的法律；报告 artifact 是它的存证。

## 2. 总览：六层流水线与三种入口

<!-- 图: images/local_ci.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/30_local_ci/images/local_ci.html)
> （或本地打开 [`images/local_ci.html`](images/local_ci.html)）。

unit-core → unit-advanced → api-tests → e2e-playwright → perf-smoke →
a11y-security，needs 链式依赖；a11y 的 ZAP 报告 `always()` 上传 artifact。

## 3. 快速开始

```bash
./local_ci.sh          # git 检查 → make unit api → act 复跑 unit-core
make quality           # 全量本地等价：单测→API→E2E→k6→a11y（约 10 分钟）
act push -j unit-core -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

实测：make 快速层全绿（16+24+8 单测、30 API）；act 在 Docker 内成功复跑
`unit-core` job（与 CI 同一 workflow 文件）。

## 4. 核心概念

### 4.1 分层与 needs 链

快而稳定的层在前（unit-core 10 秒级），重依赖在后（E2E 要装浏览器、
perf 要起 SUT、a11y 要 docker）——**反馈速度决定问题定位成本**。

### 4.2 教学脚本与门禁用例的分离

`make unit` 直接调 pytest 绿色子集而不是教学脚本——因为 lab 01 的
故意失败用例会让流水线红。**演示用的"预期失败"永远不该进门禁**。

### 4.3 act 本地复跑

act 把 workflow 装进 Docker 跑（catthehacker/ubuntu 镜像含 Python），
本地即可验证 CI 语义，不用 push 探路。两个前置：Docker 运行 + 仓库已
`git init`（act 依赖 git 上下文，本仓库由 lab 30 首跑时初始化，不推送远端）。

### 4.4 退出码即法律

每一层的脚本都遵守"失败非 0"：pytest 红、k6 thresholds 违例、axe critical
超限、API 断言失败——make 的 `needs` 式顺序执行自然形成阻断。

### 4.5 易错点（本实验真实踩过）

- `act` 输出接 `head` 会 SIGPIPE——加 `|| true`；
- 教学脚本里的预期失败必须排除在门禁外；
- `serial` 类数据窗口用例在并行轮要跳过（lab 12 的 `-m "not serial"`）。

## 5. 关键文件

```yaml
jobs:
  unit-core:      # 秒级，act 可本地复跑
  api-tests:      # needs: unit-advanced
  e2e-playwright: # needs: api-tests
  perf-smoke:     # needs: e2e-playwright（k6 thresholds 即门禁）
  a11y-security:  # needs: perf-smoke（ZAP 报告 always() 上传）
```

## 6. 文件结构

```
30_local_ci/
├── README.md
├── local_ci.sh                     # git/act 前置 + make 快速层 + act 复跑
└── images/
.github/workflows/tests.yml          # 六层 workflow（仓库根）
Makefile                             # make quality / unit / api / e2e / perf / a11y / clean
```

## 7. 深入要点

- **Q: 流水线怎么分层？** 按反馈速度×失败概率排：最快最稳的最先；
  用 needs 表达依赖，让"红灯"尽量早出现在便宜的层。
- **Q: 本地与 CI 的语义一致性怎么保证？** 同一批脚本入口（lab 脚本/Makefile），
  CI 只是换了运行环境；act 把"环境"的差异也抹掉。
- **Q: 报告 artifact 为什么 always() 上传？** 失败时的报告比成功时的更有价值。

## 8. 总结

30 个实验收束成一条流水线：从第一行 `assert` 到一条完整的质量门禁链。
系列全文见 [根 README](../../README.md)——愿你的测试从今天起可执行、可回归、可信任。
