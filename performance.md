# 🔬 性能工程 10 小项目学习清单 · Todo List

> 通过 10 个小项目（每项目 150-400 行代码/配置）掌握「压测 → 观测 → 剖析 → 调优 → 容量」完整性能工程闭环
> 约束：本机可跑、全免费、零云依赖；Postgres/Redis/监控栈走 Docker 官方 arm64 镜像
> 串联机制：完整系统型——全部项目共同生长为双 SUT 靶场（FastAPI 商店 API + Go 短链服务，均含刻意性能缺陷），每项目完成一轮「压测→定位→修复→数据说话」，项目 10 🏁 终极串联为容量评估报告
> 预计周期：5-6 周（每天 1-1.5 小时）

## 🏗️ 终极蓝图（项目 10 完成时的双 SUT 靶场）

```
                    k6 / locust / wrk（负载生成）
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌──────────────────┐  SQL   ┌──────────┐   ┌──────────────────┐
│ perf-shop (FastAPI)──────▶│ Postgres │   │ shorturl (Go)    │
│  Redis 缓存层     │        └──────────┘   │  pprof endpoints │
└────────┬─────────┘                        └────────┬─────────┘
         │ /metrics                                  │ /metrics
         ▼                                           ▼
┌─────────────────────────────────────────────────────────────┐
│        Prometheus + Grafana（黄金信号面板 + 告警）            │
└─────────────────────────────────────────────────────────────┘
         │ 项目 10：基线自动对比 + 性能预算 + CI 门禁 + 容量报告
```

两个 SUT 从项目 1 起就是「带病上线」的：各埋 3-4 处刻意性能缺陷（同步阻塞、低效算法、N+1、缺索引、无缓存、泄漏），后续项目逐一用数据揪出并修复，最终报告记录全程 before/after。

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始性能工程项目「[名称]」，目标是 [目标]。请给我完整代码约 [行数] 行，本机 macOS arm64 可跑，含验收命令。只输出代码。` |
| **排障** | `我的 [项目/工具] 出现 [现象]，压测数据/火焰图/日志：[粘贴]。请分析根因并给修复。` |
| **数据解读** | `这是压测报告/EXPLAIN 结果/pprof 输出：[粘贴]。请解读瓶颈在哪，给出下一步动作。` |

## 📊 总进度

进度：███████░░░░░░░░░░░░░░░ 7/10 (70%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：地基——指标与场景 | 2 | 2 |
| 第二阶段：观测——让瓶颈现形 | 1 | 1 |
| 第三阶段：剖析——代码级定位 | 3 | 3 |
| 第四阶段：调优——架构级优化 | 2 | 2 |
| 第五阶段：体系化——门禁与容量 | 2 | 2 |
| **合计** | **10** | **0** |

---

## 🗂️ 第一阶段：地基——指标与场景（项目 1-2）

> **目标**：搭起贯穿全程的双 SUT 靶场，会用 SLI/SLO 描述性能需求，会设计区分开放/封闭模型的负载场景

### [x] 项目 1：双 SUT 靶场搭建 + 基线压测

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~400 行 |
| **核心知识点** | docker compose 编排、FastAPI 服务、Go net/http 服务、SLI/SLO 定义、RED 方法、k6 smoke 场景、基线报告 |
| **产出模块** | `performance/31_perf_baseline/`（perf-shop + shorturl + compose + k6 基线脚本 + 报告模板） |
| **技术栈** | Python 3.13 ✅、Go ✅、k6 ✅、Docker Compose ✅（均本机实测已装） |
| **⚠️ 风险** | 两个 SUT 各埋 3-4 处性能缺陷但先不告诉自己在哪，留给项目 4-9 揪出；缺陷清单写进 `SECRET_DEFS.md`（做完对应项目才能看） |
| **验收标准** | `docker compose up -d` 一条命令起全栈且 `/health` 两服务均 200；基线报告含 RPS/P50/P95/P99/错误率五指标 × 两服务各一份 |

**🤖 开始提示词**：
> `我要开始性能工程项目「双 SUT 靶场搭建 + 基线压测」。请给我完整代码约 400 行：FastAPI 商店 API（商品列表/下单，内埋 3 处性能缺陷）+ Go 短链服务（转码+Postgres 读写，内埋 3 处缺陷），docker compose 编排含 Postgres/Redis，各自暴露 /metrics 与 /health，k6 smoke 基线脚本与五指标报告模板，附 SECRET_DEFS.md 缺陷清单。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：见 `performance/31_perf_baseline/README.md` §4.4——postgres 健康检查竞态（改种子 count 检查）、init 脚本角色权限（OWNER 转移 + 别吞 rows.Err()）、本机 893x 被 OrbStack 占用（宿主侧改 1933x）、镜像加速器间歇 EOF（vendor + 重试）

---

### [x] 项目 2：负载建模——开放 vs 封闭模型

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | 封闭模型（VU）vs 开放模型（constant-arrival-rate）、思考时间、ramping/spike/soak 场景、Coordinated Omission、读写比建模 |
| **产出模块** | `performance/32_load_modeling/`（六套 k6 场景 + 模型对比报告） |
| **技术栈** | k6 ✅、locust（pip 安装） |
| **前置** | 项目 1 |
| **验收标准** | 同一 SUT 同目标 RPS 下开放/封闭两模型 P95 差异有实测数据且报告里能解释差异来源；spike 场景在 Grafana/报告里复现一次突刺 |

**🤖 开始提示词**：
> `我要开始性能工程项目「负载建模：开放 vs 封闭模型」。请给我完整代码约 250 行：对 perf-shop 写 k6 封闭模型（ramping-vus）与开放模型（constant-arrival-rate）各一套、思考时间版本、spike 场景，Locust 等效场景一套，附模型对比报告模板（含 Coordinated Omission 解释章节）。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：locust 新版 `success()` 不吃布尔参数（去掉 catch_response）；其 CSV 分位数单位是 ms 别二次换算；开放模型迭代内不要加思考时间；同吞吐 ~170 req/s 下开放 P95 比封闭高 3587ms，CO 实锤（详见 performance/32_load_modeling/docs/modeling.md）

---

## 🗂️ 第二阶段：观测——让瓶颈现形（项目 3）

> **目标**：压测不再是黑盒——搭监控栈，压测期间资源与延迟曲线联动可见

### [x] 项目 3：监控栈与黄金信号

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行 |
| **核心知识点** | Prometheus 数据模型、prometheus-fastapi-instrumentator、Go /metrics、Grafana 面板、USE 方法、Four Golden Signals、告警规则 |
| **产出模块** | `performance/33_observability/`（监控栈 compose + Grafana 面板 JSON + 告警规则 + USE 面板） |
| **技术栈** | Prometheus/Grafana Docker 镜像（arm64 官方）⚠️ 开工探活 |
| **前置** | 项目 1、2 |
| **⚠️ 风险** | macOS Docker Desktop 拿不到宿主机级指标（cAdvisor 局限）→ 全部用容器/进程级 exporter（含 postgres_exporter、redis_exporter），学习目标不变 |
| **验收标准** | 压测期间 Grafana 单屏可见 RPS/延迟/CPU/内存四条联动曲线；P95 超 SLO 的告警规则触发过一次（有 Alertmanager 或 UI 证据） |

**🤖 开始提示词**：
> `我要开始性能工程项目「监控栈与黄金信号」。请给我完整代码约 300 行：Prometheus + Grafana + postgres/redis exporter 的 compose 编排，FastAPI 接入 prometheus-fastapi-instrumentator、Go 服务接入 prometheus/client_golang，黄金信号 Grafana 面板 JSON，P95 超 SLO 告警规则，附验证命令。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：macOS Docker Desktop 无宿主机级指标（进程级指标替代，目标不变）；promhttp handler 标签需 MustCurryWith 显式指定；告警 for:15s 防抖后 t+20s 才首次 firing；实测双响 HighP95Latency+HighErrorRate，黄金信号联动数据入册（performance/33_observability/docs/golden.md）

---

## 🗂️ 第三阶段：剖析——代码级定位（项目 4-6）

> **目标**：从「慢」到「哪里慢、为什么慢」——双语言剖析器 + 数据库诊断三板斧

### [x] 项目 4：Python 热点剖析（py-spy + cProfile）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | py-spy 采样原理与火焰图、cProfile 统计式剖析、GIL 与同步阻塞、修复前后对比方法论 |
| **产出模块** | `performance/34_python_profiling/`（剖析脚本 + 火焰图 + 修复 diff + 对比报告） |
| **技术栈** | py-spy（pip 安装，arm64 支持）⚠️ 开工探活 |
| **前置** | 项目 1、3 |
| **验收标准** | 火焰图指到具体热点函数名且与 SECRET_DEFS.md 缺陷对上；修复后同场景 P95 改善 ≥30%（同一 k6 脚本两次跑，数据入报告） |

**🤖 开始提示词**：
> `我要开始性能工程项目「Python 热点剖析」。请给我完整代码约 200 行：py-spy record/top 与 cProfile 对 perf-shop 的剖析脚本、火焰图生成命令、修复性能缺陷的示例 diff 结构、修复前后 P95 对比报告模板。不要直接告诉我埋的缺陷答案，教我方法。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：macOS py-spy 要 root → 改共享 PID namespace 的 Linux 伴生容器采样（wheel 离线装）；宿主机 8931 被 OrbStack 假监听占用致 curl 无限挂起（探活一律 --max-time）；postgres 重建后连接池尸体连接致 500（重启清池）；实测 P95 131.9→11.6ms（-91%），火焰图点名 md5/sleep/51×RTT

---

### [x] 项目 5：Go 剖析（pprof）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | net/http/pprof、CPU profile 与 heap profile、allocs 分析、go tool pprof 火焰图、内存逃逸 |
| **产出模块** | `performance/35_go_profiling/`（剖析脚本 + 火焰图 + 修复 diff + 对比报告） |
| **技术栈** | Go pprof（标准库，零安装）✅ |
| **前置** | 项目 1、3 |
| **验收标准** | pprof top/火焰图定位到 shorturl 热点函数；修复后单请求 allocs 下降 ≥40%（benchstat 或 before/after 数据入报告） |

**🤖 开始提示词**：
> `我要开始性能工程项目「Go 剖析 pprof」。请给我完整代码约 180 行：go tool pprof 采集 shorturl CPU/heap profile 的脚本、火焰图与 top 输出解读清单、benchmark 前后对比（benchstat）流程、修复报告模板。不要直接告诉我埋的缺陷答案。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：docker compose up -d 不重建镜像（改 Go 代码必须 --build，否则 pprof 抓的是旧二进制）；bench 要 -run XXX 跳过单元测试；allocs 与延迟是两根轴（redirect 分配不变但快 32 倍）；实测 GenCode allocs 1025→2（-100%）、Redirect 3702→116ns（32x），pprof top 点名 fmt.Sprintf/concatstring2

---

### [x] 项目 6：数据库性能——慢 SQL 与连接池

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | 慢查询日志、EXPLAIN ANALYZE、索引设计、Seq Scan vs Index Scan、SQLAlchemy/Go 连接池参数、连接池打满症状 |
| **产出模块** | `performance/36_db_performance/`（慢 SQL 清单 + EXPLAIN 证据 + 索引迁移 + 连接池调参记录） |
| **技术栈** | Postgres 16 Docker 镜像、pg_stat_statements |
| **前置** | 项目 1、3 |
| **验收标准** | 至少一条慢 SQL 有 EXPLAIN 证据显示 Seq Scan→Index Scan 且耗时数量级下降；用压测复现一次连接池打满（报错/排队），调参后消除并记录参数依据 |

**🤖 开始提示词**：
> `我要开始性能工程项目「数据库性能：慢 SQL 与连接池」。请给我完整代码约 250 行：开启 pg_stat_statements 与慢查询日志的 compose 配置、EXPLAIN ANALYZE 操作手册、给 perf-shop 加索引的迁移脚本、SQLAlchemy 与 Go 侧连接池参数矩阵实验脚本。不要直接告诉我埋的缺陷答案。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：psql -f/-o 路径在容器内解析（用 stdin 管道+宿主机重定向）；EXPLAIN JSON 要 -tA 去表头；数据量不够计划器不说真话（stock 放大到 15 万行）；bash $VAR 后紧跟全角字符会把多字节并进变量名报 unbound（${} 一律加）；up -d 不重建镜像致 POOL_MAX_SIZE 未生效；实测 JOIN Seq→Index 144x/mean 370x，池钳制解除（活跃连接 10→40），P95 未降系瓶颈转移至 UPDATE stock（21ms 死元组+热点锁）——如实入册

---

## 🗂️ 第四阶段：调优——架构级优化（项目 7-8）

> **目标**：代码之外——用缓存与并发调参把吞吐抬一个台阶

### [x] 项目 7：缓存与三大问题

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行 |
| **核心知识点** | Cache-Aside 模式、命中率统计、缓存穿透/击穿/雪崩、TTL 抖动、singleflight（Go）/请求合并、空值缓存 |
| **产出模块** | `performance/37_caching/`（缓存层实现 + 三大问题复现脚本 + 防护代码 + 命中率面板） |
| **技术栈** | Redis 7 Docker 镜像、redis_exporter ✅（项目 3 已接） |
| **前置** | 项目 3、6 |
| **验收标准** | 热点读场景命中率 >90% 有 Grafana 面板数据；逐一复现穿透/击穿/雪崩（脚本+曲线证据），防护后击穿场景 DB QPS 尖峰被抹平（数据入报告） |

**🤖 开始提示词**：
> `我要开始性能工程项目「缓存与三大问题」。请给我完整代码约 300 行：perf-shop 的 Cache-Aside 缓存层（Python）、命中率统计与 Grafana 指标、穿透/击穿/雪崩三个复现脚本、对应防护实现（TTL 抖动/空值缓存/singleflight），附验证命令。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：redis.setex 单位是秒（传 ttl*1000 = 缓存 18h，雪崩实验三轮无信号）；singleflight 回填必须在锁内（锁外回填让 hardened 反而比裸缓存差 2 倍）；写失效 DEL 会拉低命中率（命中率实验用只读场景）；雪崩测瞬时峰值（逐秒采样）而非总量；实测：命中 97.6%、穿透 11968→305、击穿 554→109、雪崩峰值 402→20/s

---

### [x] 项目 8：并发模型与容量调参

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~250 行 |
| **核心知识点** | uvicorn workers 与 GIL、Go GOMAXPROCS 与 goroutine 池、并发×资源矩阵实验、最优工作点、过饱和症状（上下文切换/排队） |
| **产出模块** | `performance/38_concurrency_tuning/`（矩阵实验脚本 + 结果表 + 最优配置） |
| **前置** | 项目 2、4、5 |
| **验收标准** | 产出 worker 数×目标 RPS 矩阵数据表（两 SUT 各一张）；最优配置比默认配置吞吐提升 ≥20% 或同吞吐 P95 下降 ≥25%（数据入报告） |

**🤖 开始提示词**：
> `我要开始性能工程项目「并发模型与容量调参」。请给我完整代码约 250 行：uvicorn workers 数与 Go GOMAXPROCS 的矩阵实验脚本（自动跑多组配置并汇总）、结果数据表模板、判读最优工作点的方法说明。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：健康检查写死精确 count 值（压测写入后永久失败→依赖容器卡 Created，假数据 7734 RPS）；压测脚本写死 VU 数使矩阵维度失效（GOMAXPROCS 白跑一轮）；重启后立即开压会采到污染点；实测 shop 4 workers +63%（连接池每进程的隐藏账单），Go GOMAXPROCS 无感（IO 密集，诚实入册 0%）

---

## 🗂️ 第五阶段：体系化——门禁与容量（项目 9-10）

> **目标**：从一次调优到长期守护——泄漏能定位、回归能拦截、容量能算清

### [x] 项目 9：浸泡测试与内存泄漏定位 ⚠️ 耗时

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | soak 测试设计、Prometheus 内存趋势判读、pprof heap 差分、goroutine 泄漏定位、tracemalloc（选做） |
| **产出模块** | `performance/39_soak_leak/`（soak 场景 + 泄漏注入开关 + 差分分析脚本 + 定位报告） |
| **前置** | 项目 3、5 |
| **⚠️ 风险** | 真实 soak 需 12h+ → 用加速配方：泄漏率调大 + 1h 短 soak 判趋势，方法论不变；长 soak 可过夜后台跑 |
| **验收标准** | 注入泄漏版 1h soak 内存曲线单调上升被复现（Grafana 截图）；pprof heap 差分/goroutine 数定位到具体分配点与 SECRET_DEFS.md 对上；修复后同配方曲线平稳 |

**🤖 开始提示词**：
> `我要开始性能工程项目「浸泡测试与内存泄漏定位」。请给我完整代码约 200 行：k6 1h soak 场景、shorturl 与 perf-shop 的泄漏注入开关（环境变量控制）、pprof heap 差分与 goroutine 数曲线分析脚本、定位报告模板。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：加速配方生效（泄漏率调大，7 分钟 RSS +523MB 单调爬升）；pprof -diff_base 要原始 pb.gz 不能喂文本 top 报告；bash $VAR 后跟全角字符的幽灵 unbound 全仓库统一 ${} 修复；后台长脚本静默挂于缺 reports 目录（set -e + 相对路径输出）；暖机爬坡≠泄漏（判据=尾部平台化）；差分点名 main.maybeLeak +1151.92MB，修复后尾部极差 1MB 平稳

---

### [x] 🏁 项目 10：性能回归门禁 + 容量评估报告（终极串联）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~350 行 |
| **核心知识点** | 性能基线自动对比（k6 thresholds + 统计显著性）、性能预算、CI 门禁语义、性能拐点与饱和点、容量规划、调优报告写作 |
| **产出模块** | `performance/40_regression_gate/`（对比脚本 + 门禁配置 + CI workflow + 双 SUT 容量评估报告） |
| **技术栈** | k6 ✅（thresholds 进阶用法）、GitHub Actions 免费额度或 act 本地验证 |
| **前置** | 项目 1-9 全部 |
| **验收标准** | 人为注入一处性能回归（还原项目 4 的缺陷）后 CI 门禁自动红且报告指出退化指标；最终容量评估报告含双 SUT 拐点/饱和点数据、扩容建议、项目 1-9 全部 before/after 指标汇总表 |

**🤖 开始提示词**：
> `我要开始性能工程项目「性能回归门禁 + 容量评估报告」，这是终极串联项目。请给我完整代码约 350 行：基线保存与 k6 结果自动对比脚本（含 P95 退化阈值判定）、性能预算配置、CI workflow（复用本仓库 labs/30_local_ci 的分层思路，性能门禁接在其后）、双 SUT 容量评估报告模板（拐点/饱和点/扩容建议/全程 before-after 汇总表）。只输出代码。`

**完成日期**：2026-09-08
**踩坑记录**：手写 YAML 解析器 strip 掉缩进致预算键全错层（换 stdlib tomllib，预算改 TOML）；门禁基线不得污染 31 号实验的历史基线（分目录固化）；健康检查精确值 5000 语义修复后回归；实测三连：🟢 14.1ms → 注入 🔴 132.1ms（+836%，还连累 shorturl +87%）→ 修复 🟢 12.6ms

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-2（靶场 + 负载建模）| 2 |
| **第 2 周** | 项目 3（监控栈）| 1 |
| **第 3 周** | 项目 4-6（双语言剖析 + 数据库）| 3 |
| **第 4 周** | 项目 7-8（缓存 + 并发调参）| 2 |
| **第 5 周** | 项目 9-10（soak + 门禁与容量报告）| 2 |

## 🏆 里程碑

- [x] **完成项目 1-2** → 会定 SLO、会设计区分开放/封闭模型的负载场景
- [x] **完成项目 3** → 压测全程可观测，黄金信号面板在手
- [x] **完成项目 4-6** → 双语言剖析器 + 数据库诊断，能从「慢」定位到「哪一行慢」
- [x] **完成项目 7-8** → 缓存与并发调参，吞吐台阶式提升且数据可复现
- [x] **完成项目 9-10** → 泄漏能定位、回归能拦截，交付双 SUT 完整容量评估报告
- [x] **全部完成** → 具备性能工程师完整闭环能力：压测 → 观测 → 剖析 → 调优 → 容量

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| 2026-09-08 | 1 | ~2h | 双 SUT 靶场跑通，基线五指标入册；shop P95 断裂已现形 | compose 健康检查竞态、init 角色权限、OrbStack 端口占用、加速器抖动 |
| 2026-09-08 | 2 | ~1.5h | 同吞吐下开放/封闭 P95 差 3.6s，CO 实测入册；靶场容量天花板 ≈170 req/s | locust success() API 变更、CSV 单位 ms、open 场景别加 sleep |
| 2026-09-08 | 3 | ~1.5h | 监控栈 4/4 target 全绿，压测中双告警真实 firing，黄金信号联动入册 | 进程级指标替代宿主机指标、promhttp 标签 curry、Go 侧补 HTTP 直方图 |
| 2026-09-08 | 4 | ~2h | 剖析闭环跑通：火焰图函数级归因三缺陷，P95 -91% | py-spy root 限制（容器伴生绕行）、OrbStack 假监听、连接池尸体 |
| 2026-09-08 | 5 | ~1.5h | Go pprof 闭环：GenCode 分配 -100%、跳转快 32 倍，双轴归因入册 | compose 不自动重建镜像、-run XXX 必加、allocs≠延迟 |
| 2026-09-08 | 6 | ~2.5h | EXPLAIN 三层证据链：JOIN 370x、池钳制解除；瓶颈转移至 UPDATE（21ms）如实归因 | psql 容器路径、psql 表头包 JSON、全角字符进变量名、镜像未重建 |
| 2026-09-08 | 7 | ~2h | 三大问题逐一复现+设防全绿：97.6% / 305 / 109 / 20/s；锁内回填陷阱亲踩 | setex 秒 vs 毫秒、锁外回填、写失效拉低命中率、雪崩测峰值 |
| 2026-09-08 | 8 | ~2h | 矩阵实验闭环：shop 最优 4 workers（+63%），Go 无感的诚实结论；健康检查精确值坑修复 | 健康检查精确值、脚本写死 VU、池是每进程的 |
| 2026-09-08 | 9 | ~2h | 泄漏闭环：注入→+523MB 爬升→差分点名 maybeLeak→修复后平台化 | setex 式单位坑复发？无；全角变量名、静默 exit2、暖机≠泄漏 |
| 2026-09-08 | 10 | ~2.5h | 门禁三连 🟢→🔴→🟢 实测闭环；容量评估报告汇总全系列 9 实验数字 | tomllib 替代手写 YAML、基线分目录、TAG/位置参数混用 |
| | | | | |

## 🔧 环境配置

```bash
# 0. 已就绪（2026-09-07 实测）：k6 ✅ /opt/homebrew/bin/k6、Docker + Compose v5.1.2 ✅、
#    Go ✅、Python 3.13.9 ✅、ab ✅
# 1. 需安装（按阶段分组）：
pip install locust py-spy          # 项目 2、4（Python venv 内）
brew install wrk                   # 项目 2（可选，对照工具）
docker pull postgres:16-alpine redis:7-alpine prom/prometheus grafana/grafana   # 项目 1、3
# 2. 每项目开工前：
docker compose -f performance/<NN>_xxx/docker-compose.yml up -d && docker compose ps   # 全栈健康
```

## ⚠️ 与已有清单的关系（test_frameworks.md 30 项目系列）

| 已有清单项目 | 关系 |
|:---|:---|
| 项目 26（Locust 入门） | 本清单默认已会其场景语法/阶梯加压/拐点判读，不重复；本清单直接进入开放模型与 Coordinated Omission（项目 2） |
| 项目 27（k6 阈值门禁） | thresholds 基础用法不重复；本清单项目 10 是其工程化进阶（基线自动对比 + 统计判定 + 容量结论） |
| 项目 30（本地 CI 串联） | 本清单项目 10 的门禁 workflow 复用其分层流水线思路，性能门禁接在其后，不重建流水线 |
| 其余 27 项（pytest/Playwright/Cypress/Selenium 等） | 功能/正确性视角，与本清单性能视角互补，零重叠 |

## ⚠️ 环境能力速查表

| 能力 | 计划 | 实测结论（2026-09-07） |
|:---|:---|:---|
| k6 CLI | 全部压测场景 | ✅ 已装 /opt/homebrew/bin/k6 |
| Docker Compose | 靶场与监控栈编排 | ✅ v5.1.2 |
| Go 工具链 | shorturl SUT + pprof | ✅ 已装（go version 正常响应） |
| Python | perf-shop SUT + 剖析 | ✅ 3.13.9 |
| locust / py-spy | 项目 2、4 | ⚠️ 待装（pip，arm64 官方支持，开工时验证） |
| Postgres/Redis/Prometheus/Grafana 镜像 | 项目 1、3 | ⚠️ 待拉取（官方 arm64 镜像，开工探活） |
| 宿主机级指标（macOS Docker Desktop） | 项目 3 | ❌ 不可用（cAdvisor 局限）→ 用容器/进程级 exporter 替代 |
