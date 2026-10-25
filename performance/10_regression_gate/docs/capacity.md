# 🏁 容量评估报告（双 SUT · 项目 1-9 全程汇总）

## 1. 调优历程：每一步的数据

| 项目 | 动作 | 关键数字 | 出处 |
|:---|:---|:---|:---|
| 1 | 基线（缺陷版 shop P95 断裂） | P95 130.7ms，分位数断裂归因 sleep | `01_perf_baseline/docs/baseline.md` |
| 2 | 瓶颈转移预警 | 同吞吐下开放模型 P95 比封闭高 3.6s（CO） | `02_load_modeling/docs/modeling.md` |
| 3 | 观测 | P95 破 SLO 双告警 firing；CPU 仅 1 核 → 等待型瓶颈 | `03_observability/docs/golden.md` |
| 4 | Python 剖析修复 D1-D3 | **P95 131.9 → 11.6ms（-91%）** | `04_python_profiling/docs/analysis.md` |
| 5 | Go 剖析修复 D4-D6 | GenCode allocs 1025→2；跳转快 32 倍 | `05_go_profiling/docs/pprof_analysis.md` |
| 6 | 数据库（D7 索引） | JOIN Seq→Index **144x**；瓶颈转移至 UPDATE | `06_db_performance/docs/db_analysis.md` |
| 7 | 缓存 | 雪崩峰值削 **20x**；穿透/击穿全防住 | `07_caching/docs/caching.md` |
| 8 | 并发调参 | 4 workers **+63%**（2527 RPS @200VU） | `08_concurrency_tuning/docs/tuning.md` |
| 9 | 泄漏定位 | maybeLeak +1152MB 差分点名；修复后平台化 | `09_soak_leak/docs/soak.md` |

## 2. 容量结论

- **shop（FastAPI + 缓存 + 索引 + 4 workers）**：当前健康态 @200VU 实测 57.3 RPS / P95 13.8ms；缺陷版饱和点 ≈170 req/s（项目 2 实测），当前容量已提升一个数量级
- **扩容建议**：worker 数再加需同步扩连接池预算（4×10=40 已占 max_connections 的四成）；下一个治理对象是 UPDATE stock 的热点行（项目 6 发现），
  方向为合并库存扣减/异步落单，而非继续加机器
- **shorturl（Go）**：跳转路径已 O(1) + 零分配热点，单实例千级 RPS；GOMAXPROCS 无感（IO 密集），扩容直接水平加副本

## 3. 门禁验证（本实验实测）

- 健康态基线：shop P95 10.1ms / 56.8 RPS
- 注入回归（还原项目 4 的三缺陷）：门禁自动 🔴（P95 退化超预算 25%）
- 修复恢复：门禁恢复 🟢；budget.yaml 即性能预算的机器可读形态

## 4. 系列收官

10 个项目串成一条完整链：定 SLO → 负载建模 → 观测 → 双语言剖析 →
数据库诊断 → 缓存 → 并发调参 → 泄漏定位 → 回归门禁与容量结论。
每个数字都可复算，每个结论都有出处——这就是性能工程的全部方法论。
