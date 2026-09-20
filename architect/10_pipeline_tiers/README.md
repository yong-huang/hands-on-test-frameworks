# 10 · 分层流水线架构：失败信号要多久回来

> 前面 9 个实验造的零件——分层标记、质量门禁、覆盖档案——现在要接进流水线。
> 本实验回答流水线设计的核心问题：**不是「跑什么」，而是「失败信号多久回来」**。
> PR 等 3 分钟（tier1 冒烟）、合并等 10 分钟（tier2 全量+门禁）、夜间慢层不挡人
> （tier3 档案刷新）。act 本地实跑 tier1：23 秒全绿，语义与 CI 同源。清单第 10/28 项。

## 1. 为什么需要它

- 单层流水线只有两种死法：太慢（人人绕过）或太浅（红灯失去含义）；
- 「PR 上跑不跑全量」是流水线设计第一辩题——答案不是比例是分层：每层都有明确的
  触发时机、超时预算和失败语义；
- 本地 act 复跑 = CI 调试不再靠 push 祈祷。

## 2. 总览：核心机制一图看懂

![三层流水线](images/pipeline_tiers.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/10_pipeline_tiers/images/pipeline_tiers.html)
> （或本地打开 [`images/pipeline_tiers.html`](images/pipeline_tiers.html)）。

心智模型一句话：**主路径就是时间轴**——push 后 3 分钟冒烟回信号，合并前全量+门禁兜底，
夜间档案/慢排行归档不挡任何人。每层的取舍写在 workflow 注释里被人评审。

## 3. 快速开始

```bash
cd architect/10_pipeline_tiers
./pipeline_tiers.sh apply     # git/docker/act/yaml 四项前置自检
./pipeline_tiers.sh observe   # act 复跑 tier1 → 冒烟比例验收 → 三层语义速览
./pipeline_tiers.sh clean
```

实测输出（2026-09-20）：

```
① act 本地复跑 tier1（Docker 内，与 CI 同源）：
   ✅ Set up job → ✅ checkout → ✅ 安装最小依赖(9s) → ✅ P0 冒烟
>>> act 退出码 0，tier1 耗时 23s（验收线 <300s）
② 冒烟层比例验收：smoke=2 / 全量=10 → 冒烟占比 20% ≤ 20% ✅
   P0 下单路径在冒烟层 ✅
```

## 4. 核心概念

### 4.1 三层各自的失败语义
tier1 红 = 「你的改动碰了 P0 路径，现在就修」（3 分钟内）；tier2 红 = 「主干要有你
不能合入的问题」；tier3 红 = 「趋势问题，明早看」。**同是红色，含义完全不同**——
单层流水线给不了这个语义密度。

### 4.2 冒烟圈选：比例 + 覆盖双约束
`-k "create_and_get_fresh or init_db_repeatable"` 圈出 2/10=20%（比例达标）且必含
create（P0 下单路径）。只有比例约束会被钻空子（圈 10 条最慢的也行），双约束才完整。

### 4.3 act：CI 语义的本地等价
`act -W <workflow> -j tier1-quick --pull=false` 在 Docker 内复跑同一个 yaml——
「本地绿 CI 红」的环境差异被消灭大半。两个本地化的坑：act 以 cwd 为项目根
（必须从仓库根跑），容器内 pip 需要 `--break-system-packages`（PEP 668）。

## 5. YAML 关键字段（workflow）

| 字段 | 为什么 | 坑 |
|:---|:---|:---|
| `timeout-minutes: 5` | tier1 的时间预算写进契约 | 不写超时的快反馈层一定会慢死 |
| `needs: tier1-quick-feedback` | tier2 依赖 tier1 绿 | 想要「并行跑但合并前都绿」就不加 needs，语义完全不同 |
| `working-directory` | 步骤级 cwd | act 把 cwd 当项目根：从仓库根跑才挂对工作区 |
| `--pull=false`（act 参数） | 用本地镜像缓存 | 镜像源抽风时一次 pull 卡 17 分钟 |

## 6. 文件结构

```
architect/10_pipeline_tiers/
├── README.md
├── pipeline_tiers.sh              # apply(前置自检) → observe(act+验收) → clean
├── workflows/architect-tiers.yml  # 三层流水线的声明式定义（可被 act 与真 CI 共用）
└── images/                        # 图三件套
```

## 7. 深入要点

**Q1：tier1 为什么圈 2 条而不是 5 条？** 20% 是比例上限，P0 覆盖是内容下限；条数
越少信号越快，但每砍一条都在赌它不出事。圈选依据 = 项目 2 策略文档的 P0 功能映射
到用例（本实验用 `-k`，规模大了换项目 5 的 case_level 标记 + 项目 4 的精准推荐）。

**Q2：tier2 全量+门禁串行还是并行？** 串行（本实验 needs 链）：门禁消费的是全量的
覆盖率产物，天然串行。若门禁数据来自独立采集，可并行再 merge 裁决——「数据流决定
任务图」是流水线设计的一般原则。

**Q3：夜间层红了怎么办？** 夜间层的问题必须有日间的消化机制：慢排行进每日站会、
flaky 报告进项目 13 的隔离平台、档案刷新失败自动重试。夜间层变成「红色垃圾场」是
所有质量体系的死亡螺旋起点。

**Q4：act 和真 CI 还差什么？** 密钥/缓存/并发组/矩阵策略是 act 覆盖不到的四件——
本地能验证「yaml 语法+步骤语义」，验证不了「云端资源模型」。所以 tier1 本地必绿、
tier2/3 推上去让 CI 跑，是成本最低的验证分层。

**Q5：为什么流水线不是从这 28 项里最优先做？** 流水线是零件的组装厂：没有分层标记
（05）、门禁（03）、覆盖档案（04）之前，三层只是三个空壳。先零件后流水线，是本清单
阶段排序的用意。

## 8. 总结

23 秒的 P0 冒烟、20% 的圈选比例、三层各自的红绿语义——流水线从「跑测试的地方」
升级为「失败信号的调度系统」。工程效能篇自此开张：下一篇是清单项目 11「耗时均衡
分片调度器」——套件跑 2 小时怎么砍到 20 分钟，LPT 贪心算法见。
