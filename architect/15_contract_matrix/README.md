# 15 · 契约测试平台化：provider 版本矩阵与 can-i-deploy

> labs/15 学会了一对 consumer/provider 的契约红绿；平台化的问题是——
> **provider 出了新版本，能不能发布？** 答案是把全部契约对每个候选版本跑
> 验证矩阵，全绿才放行——这就是 Pact Broker（Pact 官方的契约托管与发布判定服务）的核心语义 can-i-deploy，
> 本实验用零付费的本地实现把它做出来。实测：v1 主干全绿可发布；
> v2（把 customer 改名 clientName 的「重构事故」）被矩阵当场拦下。

## Background

微服务集成的经典事故：服务提供方（provider，实现接口的一方）重构改了响应字段，
调用方（consumer，依赖该接口的一方）上线即崩——契约测试（把「调用方对接口的
期望」固化成文件、让提供方发布前逐条验证的测试）的存在意义就是让这种事在
**发布前**爆掉。

单对契约验证（labs/15）回答的是「这个实现满足这个期望吗」——一个点。
平台化的问题是面：provider 一次发布面对 N 个 consumer 的契约，
历史上还有 M 个候选版本，人肉记住"哪个版本配哪个契约"必然失守。

「consumer 改了契约 provider 还没跟上怎么拦」的标准答案就是
can-i-deploy：契约文件 × 候选版本 = 验证矩阵，某版本那一列全绿才放行。
本实验用零付费的本地实现保留这套核心语义。

## What

契约版本矩阵是一套发布判定系统：N 个契约 × M 个候选版本 = N×M 个格子的
独立验证，每个格子一个独立 Verifier（拿着契约去验证 provider 的校验进程），红绿互不污染；
can-i-deploy = 某版本那一列全绿 → exit 0 放行，任一红 → exit 1 拦截。

可以把矩阵想成药品的兼容性对照表：新药（provider 新版本）上市前，
逐一核对它与所有常用药（consumer 契约）的组合禁忌——一格冲突就整体
禁售。但和对照表不同的是，这里的每一格都是一次真实执行的验证，
不是查表——报告能精确到「哪个契约在哪个版本上被谁破坏」。

v2 的「破坏」是一个 ASGI 中间件（插在 Web 框架请求链路上、可改写请求/响应的一层钩子）把 customer 改名 clientName——
真实重构事故的最小复刻：不改 SUT 源码，破坏被**隔离在进程边界**，
证明矩阵的拦截能力与具体实现无关。

## When to Use

典型场景：

- provider 发版前检查：对「全量 consumer 契约」跑 can-i-deploy，
  不达标禁止发布。
- provider CI 常规验证：合并前对「主干契约集」跑本版本验证（相当于 v1 列）。
- 契约协作流程：consumer 契约变更单独成 PR，通知 provider 团队评审
  ——契约 PR 是两个团队的对齐仪式。

何时不用：服务少（两三个）、发版节奏同步时，单对契约验证够用；
规模到了（几十服务、每日多版本）再上真 Pact Broker——本地文件版的
数据契约（pacts/*.json + 判定结果）完全平移。

## Quick Start

前置条件：先完成 labs/15（它生成契约资产与 consumer/provider 代码），且仓库根
存在 labs/00 创建的共享 .venv（内含 pytest 与 pact-python）。

脚本自动起 v1 真 SUT（System Under Test，被测系统）(:8899) 与 v2 破坏变体(:8902)。

```bash
cd architect/15_contract_matrix
./contract_matrix.sh apply     # 起 v1 真 SUT(:8899) 与 v2 破坏变体(:8902)
./contract_matrix.sh observe   # consumer 生成契约 → 矩阵验证 → can-i-deploy 判定
./contract_matrix.sh clean
```

实测输出：

```
契约文件 1 个；开始矩阵验证（2 个 provider 版本）
  ✅ v1-sut-8899 × ministore-frontend-ministore-api.json
  ❌ v2-broken-8902 × ministore-frontend-ministore-api.json

| 契约 | v1 主干 | v2 破坏变体 |
|:---|:---:|:---:|
| ministore-frontend-ministore-api.json | ✅ | ❌ |

# 🚦 can-i-deploy 发布检查
- v1-sut-8899: ✅ 可发布（全部契约满足）
- v2-broken-8902: ❌ 禁止发布（存在契约破坏）
```

诚实预期：v1 列应全绿（可发布），v2 列应红（禁止发布）——v2 的破坏只是
字段改名，集成测试测不出，矩阵当场拦下。真 Broker 的语义还包括环境追踪
（这个版本已在 prod 验证过），本地文件版用「主干版本预验证」近似
——语义保留，成本归零。

关键设计（这段在做什么：矩阵可信度的四个决定）：

| 设计 | 为什么 | 坑 |
|:---|:---|:---|
| Verifier host 用 localhost | pact FFI（pact 的本地校验库，经外部函数接口从 Python 调用）的 add_transport 校验 host 一致性 | 传 127.0.0.1 直接 ValueError（本次踩坑） |
| 契约文件本地交换 | labs/15 已确立：pacts/ 目录代替付费 Broker | 团队规模大了要上真 Broker 或 git 化契约评审 |
| 破坏用 middleware 不改源码 | 变体可复现、SUT 零污染 | 中间件只演示字段改名一类破坏，断言类型类破坏另测 |
| 每格独立进程 | 红绿互不污染、可并行 | 进程开销大；矩阵大了换常驻 verifier 服务 |

## How It Works

**版本矩阵：从对子到平台**。N 个契约 × M 个候选版本 = N×M 个格子的独立
验证，每格一个独立 Verifier 进程——**格子的红绿互不污染**，报告可以精确
到「哪个契约在哪个版本上被谁破坏」。

**can-i-deploy：把矩阵变成门禁**。某版本列全绿 → exit 0 放行；
任一红 → exit 1 拦截——发布判定从人肉记忆变成机器判定。

**破坏变体是最小复刻的验收法**。v2 用 ASGI 中间件改写响应字段而不是改
SUT 源码——破坏被隔离在进程边界，变体可复现、SUT 零污染。
这也是验收「平台真的会拦」的最诚实方式：自己造一个该拦的。

## Pitfalls & Q&A

踩坑清单：

- **Verifier host 传 127.0.0.1**。现象：pact FFI 直接 ValueError
  （本次踩坑）。解法：host 用 `localhost`（FFI 校验 host 一致性）。
- **矩阵大了每格起进程**。现象：验证耗时线性膨胀。
  解法：换常驻 verifier 服务，或并行跑格子。
- **只测字段改名一类破坏**。现象：断言类型类破坏漏拦。
  解法：破坏变体按破坏类型分组扩展（中间件只做最小复刻）。

深入问答：

- **Q：契约测试和集成测试什么关系？**
  契约只锁「交互的形状」（字段/类型/状态码），不锁业务正确性——它用最小
  验证面换大规模并行性：consumer 离线对着 mock 验，provider 上线前对着
  契约验，两边永不需要同时在线。集成测试答「系统对不对」，
  契约答「接口还兼容吗」。
- **Q：consumer 改了契约、provider 没跟上，流水线上谁被拦？**
  consumer 的新契约先合入 → provider 下次发布跑矩阵 → 新契约验证红 →
  can-i-deploy 拦 provider。反向同理。关键机制是「契约文件是双方共享的
  事实源」，谁破坏谁被拦，与发布顺序无关。
- **Q：为什么不用真 Pact Broker？**
  本地文件版保留了矩阵与判定的全部核心语义，去掉了网络服务与版本库管理
  ——学习与中小团队足够；规模到了再上 Broker，数据契约完全平移。
- **Q：矩阵验证怎么进流水线？**
  provider 的 CI：合并前对「主干契约集」跑本版本验证（相当于 v1 列）；
  发版前对「全量 consumer 契约」跑 can-i-deploy。consumer 的 CI：
  契约变更单独成 PR，通知 provider 团队评审——契约 PR 是两个团队的
  对齐仪式。
