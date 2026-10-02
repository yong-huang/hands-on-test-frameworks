# 🔬 performance/：性能工程 10 实验（压测 → 观测 → 剖析 → 调优 → 容量）

> 把 [../docs/performance.md](../docs/performance.md) 清单落成的可真实跑通系列：
> 基线 → 负载建模 → 监控 → Python/Go 双栈剖析 → 数据库 → 缓存 → 并发调参 → 浸泡泄漏 → 回归门禁 + 容量报告。
> 两个**故意带病上线**的靶场贯穿全程：FastAPI 商店 + Go 短链服务，每个实验完成一轮
> 「压测 → 定位 → 修复 → 数据说话」，全部提升都拿 01 的基线做对照。
> 与 labs 26/27 互补：那边把 Locust/k6 当工具入门，这边做完整性能工程闭环。
> 全程免费本机：Docker 官方 arm64 镜像 + k6，零云依赖。

进度：**10/10 (100%)** ██████████

## 🚀 快速开始

前置条件：Docker 运行中；k6 CLI 就绪（labs 的 `bash scripts/load_resources.sh` 会用 brew 一并装好）。

```bash
cd performance/01_perf_baseline
./perf_baseline.sh all      # 起靶场 + 基线压测（第一个实验）
./perf_baseline.sh observe  # 只重跑压测与报告（对比修复效果时用）
./perf_baseline.sh clean    # 停栈删卷，回到实验前状态
```

每个实验同构：`apply` 起栈等健康 → `observe` 压测与取证 → `clean` 零残留。

诚实预期：首次要拉取 Postgres/Redis/Prometheus/Grafana 等镜像，耗时较长；双 SUT 固定端口 19331（perf-shop）/ 19332（shorturl），端口被占先 `clean` 上一个实验。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_perf_baseline/README.md) | 靶场与基线 | 双 SUT 起栈 + 优化前基线 | 故意带病上线，答案锁 `SECRET_DEFS.md` |
| [02](02_load_modeling/README.md) | 负载建模 | 封闭 vs 开放模型对照 | 同吞吐 P95 差 3.6s：压测模型会替 SUT 隐瞒 |
| [03](03_observability/README.md) | 监控栈 | Prometheus + Grafana 黄金信号 | SLO 告警在压测中真实触发，双侧证据 |
| [04](04_python_profiling/README.md) | Python 剖析 | py-spy 采样→归因→修复 | 三处缺陷一网打尽，P95 132ms→11.6ms（-91%） |
| [05](05_go_profiling/README.md) | Go 剖析 | pprof top → benchmark 判决 | genCode 79µs/1025 allocs→66ns/2 allocs，跳转快 32 倍 |
| [06](06_db_performance/README.md) | 数据库 | pg_stat_statements + EXPLAIN | Seq Scan→Index Scan 144 倍；连接池打满复现 |
| [07](07_caching/README.md) | 缓存三大问题 | Cache-Aside 三档设防 | 命中 97.6%；穿透 11968→305；雪崩 402→20/s（20 倍削峰） |
| [08](08_concurrency_tuning/README.md) | 并发调参 | workers/GOMAXPROCS 矩阵 | 3×2×2：shop +63%，shorturl 纹丝不动——两种诚实结论 |
| [09](09_soak_leak/README.md) | 浸泡与泄漏 | `LEAK_MODE` 注入 + heap 差分 | RSS 爬升钉到 `main.maybeLeak`（+1151.92MB） |
| [10](10_regression_gate/README.md) | 🏁 门禁与容量 | 性能门禁 + 容量评估报告 | 14.1ms → 注入回归 132.1ms（+836%）→ 修复 12.6ms |

## 🧭 学习路线

按编号 01 → 10 即路线，前后互为对照：

1. **01-03 打地基**：靶场与基线 → 负载建模（选对压测模型）→ 监控栈（给结论补上资源侧证据）
2. **04-06 剖析三层**：Python 进程（py-spy）→ Go 进程（pprof）→ 数据库（EXPLAIN）——解决一个瓶颈，下一个瓶颈才现形
3. **07-09 手段箱**：缓存设防 → 并发调参找最优工作点 → 时间维度的内存泄漏
4. **10 收官**：把全部结论变成会咬人的门禁与容量评估报告

## ⚠️ 预期失败诚实标注

- 全系列的"病"都是故意埋的：缺陷答案集中锁在 [01_perf_baseline/SECRET_DEFS.md](01_perf_baseline/SECRET_DEFS.md)，破案前别看
- 08 的 shorturl 纹丝不动是实验结论（该负载对 GOMAXPROCS 无感），不是做砸了
- 09 的内存泄漏来自 `LEAK_MODE=heap|goroutine` 注入开关；10 的回归（+836%）同样是注入验证门禁会咬人

## 🔧 环境要求

macOS（Apple Silicon 实测）/ Docker（Postgres、Redis、Prometheus、Grafana 官方 arm64 镜像）/ k6 CLI。
无独立 load_resources 脚本：依赖随各实验 `apply` 自动起停，`clean` 后零残留。
