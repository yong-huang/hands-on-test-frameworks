# 15 · 契约测试平台化：provider 版本矩阵与 can-i-deploy

> labs/15 学会了一对 consumer/provider 的契约红绿；平台化的问题是——**provider 出了
> 新版本，能不能发布？** 答案是把全部契约对每个候选版本跑验证矩阵，全绿才放行——
> 这就是 Pact Broker 的核心语义 can-i-deploy，本实验用零付费的本地实现把它做出来。
> 实测：v1 主干全绿可发布；v2（把 customer 改名 clientName 的「重构事故」）被矩阵
> 当场拦下。清单第 15/28 项，阶段三收官。

## 1. 为什么需要它

- 微服务集成的经典事故：provider 重构改了响应字段，consumer 上线即崩——
  契约测试的存在意义就是让这种事在**发布前**爆掉；
- 单对契约回答「这个实现满足这个期望吗」，矩阵回答「这个**版本**能发布吗」——
  平台化的本质是把答案从人肉记忆变成机器判定；
- 「consumer 改了契约 provider 还没跟上怎么拦」的标准答案就是 can-i-deploy。

## 2. 总览：核心机制一图看懂

![契约版本矩阵](images/contract_matrix.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/15_contract_matrix/images/contract_matrix.html)
> （或本地打开 [`images/contract_matrix.html`](images/contract_matrix.html)）。

心智模型一句话：**契约文件 × 候选版本 = 验证矩阵**，每个格子一次独立验证；
can-i-deploy = 某版本那一列全绿。v2 的「破坏」是一个 ASGI 中间件把 customer 改名
clientName——真实重构事故的最小复刻。

## 3. 快速开始

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

## 4. 核心概念

### 4.1 版本矩阵：从对子到平台
单对验证（labs/15）是点，矩阵是面：N 个契约 × M 个候选版本 = N×M 个格子的独立性
验证。每格一个独立 Verifier 进程——**格子的红绿互不污染**，报告可以精确到
「哪个契约在哪个版本上被谁破坏」。

### 4.2 can-i-deploy：把矩阵变成门禁
某版本列全绿 → exit 0 放行；任一红 → exit 1 拦截。真 Broker 的语义还包括环境追踪
（这个版本已在 prod 验证过），本地文件版用「主干版本预验证」近似——语义保留，
成本归零。

### 4.3 破坏变体是最小复刻的验收法
v2 不改 SUT 源码，用中间件改写响应字段——破坏被**隔离在进程边界**，证明矩阵的
拦截能力与具体实现无关。这也是验收「平台真的会拦」的最诚实方式：自己造一个该拦的。

## 5. 关键设计

| 设计 | 为什么 | 坑 |
|:---|:---|:---|
| Verifier host 用 localhost | pact FFI 的 add_transport 校验 host 一致性 | 传 127.0.0.1 直接 ValueError（本次踩坑） |
| 契约文件本地交换 | labs/15 已确立：pacts/ 目录代替付费 Broker | 团队规模大了要上真 Broker 或 git 化契约评审 |
| 破坏用 middleware 不改源码 | 变体可复现、SUT 零污染 | 中间件只演示字段改名一类破坏，断言类型类破坏另测 |
| 每格独立进程 | 红绿互不污染、可并行 | 进程开销大；矩阵大了换常驻 verifier 服务 |

## 6. 文件结构

```
architect/15_contract_matrix/
├── README.md
├── contract_matrix.sh         # apply(双 provider) → observe(矩阵+判定) → clean
├── matrix.py                  # 矩阵构建 + can-i-deploy 判定（约 140 行）
├── broken_provider.py         # v2 破坏变体（ASGI 中间件改写字段名）
├── reports/matrix.json        # 矩阵与判定结果（clean 清除）
└── images/                    # 图三件套
```

## 7. 深入要点

**Q1：契约测试和集成测试什么关系？** 契约只锁「交互的形状」（字段/类型/状态码），
不锁业务正确性——它用最小验证面换大规模并行性：consumer 离线对着 mock 验，
provider 上线前对着契约验，两边永不需要同时在线。集成测试答「系统对不对」，
契约答「接口还兼容吗」。

**Q2：consumer 改了契约、provider 没跟上，流水线上谁被拦？** consumer 的新契约先合入
→ provider 下次发布跑矩阵 → 新契约验证红 → can-i-deploy 拦 provider。反向同理。
关键机制是「契约文件是双方共享的事实源」，谁破坏谁被拦，与发布顺序无关。

**Q3：为什么不用真 Pact Broker？** 本地文件版保留了矩阵与判定的全部核心语义，
去掉了网络服务与版本库管理——学习与中小团队足够；规模到了（几十服务、每日
多版本）再上 Broker，数据契约（pacts/*.json + can-i-deploy 判定）完全平移。

**Q4：矩阵验证怎么进流水线？** provider 的 CI：合并前对「主干契约集」跑本版本验证
（相当于 v1 列）；发版前对「全量 consumer 契约」跑 can-i-deploy。consumer 的 CI：
契约变更单独成 PR，通知 provider 团队评审——契约 PR 是两个团队的对齐仪式。

**Q5：labs/15 与本实验的分界？** labs/15 证明「契约测试的两个半边都能跑通」；
本实验把它平台化：多版本、矩阵化、自动判定。「会做一对」和「能管一堆」之间
隔着的正是平台思维，这也是阶段三到阶段四的接力点。

## 8. 总结

一张矩阵表回答「能不能发布」，can-i-deploy 把答案变成流水线退出码——契约测试
从工具升级为微服务时代的发布质量制度。阶段三（流水线与工程效能）六项全部收官；
下一篇进入阶段四，清单项目 16「Ephemeral 环境工厂」：环境抢占与隔离的终极解法。
