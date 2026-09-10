# 06 · 数据库性能：EXPLAIN 会说真话，瓶颈会转移

> 双语言剖析把代码层清干净了，但数据库是另一个世界：这里的行为由**数据量、
> 统计信息和计划器**决定。本项目让靶场的 Postgres 开口说话——
> pg_stat_statements 排行揪出头号查询，EXPLAIN ANALYZE 拍下 Seq Scan →
> Index Scan 的 **144 倍**，再亲手复现连接池打满。最大的收获却是一条方法论：
> **解决一个瓶颈，下一个瓶颈才现形。**

## 1. 为什么需要它

- 应用侧剖析永远照不到数据库内部：慢在扫表、慢在锁、慢在死元组，各有各的证据链；
- "数据量太小计划器永远选 Seq Scan"——性能实验必须先把数据量做到真实量级；
- 连接池是应用与 DB 之间的隐形成本中心：打满时 P95 的形状（排队到超时）
  与慢查询的形状完全不同，得学会分辨。

## 2. 总览：三层证据

<!-- 图: images/dbperf.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/06_db_performance/images/dbperf.html)
> （或本地打开 [`images/dbperf.html`](images/dbperf.html)）。

放大数据 → pg_stat_statements 排行定嫌疑 → EXPLAIN ANALYZE 拍执行计划 →
建索引看数字跳水 → 100 VU 复现连接池打满 → 调参验证钳制解除。

## 3. 快速开始

```bash
./db_perf.sh all      # 全证据链：排行→EXPLAIN→索引→池实验→报告
./db_perf.sh drop-index   # 撤索引恢复 D7 现场（复跑教学用）
open docs/db_analysis.md
```

## 4. 核心概念

### 4.1 EXPLAIN 证据：Seq Scan → Index Scan（本机实测，stock 15 万行）

| 阶段 | 扫描方式 | 扫描行数 | 该节点耗时 |
|:---|:---|---:|---:|
| 建索引前 | Seq Scan | 116,504 | 7.792 ms |
| 建索引后 | Index Scan | 50 | **0.054 ms** |
| **变化** | 计划器改主意 | 2330x | **144x** |

配套排行证据：列表 JOIN 的 mean 从 11.16ms → 0.03ms（**370x**）。
EXPLAIN 的两个数字要一起看：扫描行数（决定成本）与实际耗时（决定体验）。

### 4.2 瓶颈转移实录（本项目最有价值的一课）

索引修好后再看排行：**UPDATE stock 以 21ms 均值顶成了头号查询**——
15 万行高频更新表死元组膨胀 + 同商品热点行锁竞争。它一直都在（建索引前
23.62ms），只是当时被更慢的 JOIN 挡着。连接池调参后 P95 没降反而横住，
正是因为瓶颈已经转移到它身上。治理方向（本系列不展开）：降低更新频率、
表分区、autovacuum 调优。

### 4.3 连接池打满：形状辨认

100 VU 压 45s，池上限 10 时：`pg_stat_activity` 的活跃连接被钉死在
**10**，请求在应用侧排队直到池超时（psycopg_pool 默认 30s）——P95 呈
30s 阶梯状、错误率 13%。把上限调到 40 后峰值钉在 40，**钳制确认解除**；
P95 没降是 4.2 说的瓶颈转移，不是池的锅。判别口诀：**连接池打满 =
活跃连接贴着上限 + PG 自己很闲；慢查询 = 活跃连接个个都在干活。**

上限不是越大越好：每个连接是一个 PG 进程（~10MB），max_connections=100
的默认额度要先留给运维、监控和备份连接。

### 4.4 易错点（本实验真踩）

- **psql 的 `-f`/`-o` 路径在容器里解析**：宿主机路径要用 stdin 管道和
  shell 重定向；
- **EXPLAIN FORMAT JSON 被 psql 包了层表头**：加 `-tA` 拿纯 JSON；
- **数据量不够，计划器不说真话**：200 行的表 Seq Scan 就是 optimal，
  先放大到十万行级再做计划实验；
- **bash 的 `$VAR` 后面紧跟全角字符**：多字节字节会被并进变量名，
  "unbound variable" 报在根本不存在的名字上——变量一律加 `${}`；
- **改了代码 `up -d` 不重建镜像**：POOL_MAX_SIZE 旋钮上线必须 `--build`。

## 5. 关键参数

```sql
-- 排行榜（总耗时视角；mean_ms 看单条，total_ms 看总量）
SELECT round(total_exec_time::numeric,1) total_ms, calls,
       round(mean_exec_time::numeric,2) mean_ms, left(query,60)
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 5;
-- 拍计划（BUFFERS 告诉你缓存命中）
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT ...;
```

## 6. 文件结构

```
06_db_performance/
├── README.md
├── db_perf.sh             # prereq/scale/drop-index/burst/top/explain/index/pool/report
├── sql/
│   ├── setup.sql          # pg_stat_statements 扩展 + 慢查询阈值（幂等）
│   └── index_migration.sql# stock/orders 索引（D7 的修复）
├── gen_db_report.py       # EXPLAIN/排行/池数据 → docs/db_analysis.md
├── reports/               # explain_*.json、pg_stat_top_*.txt、pool_*.json
├── docs/db_analysis.md    # 三层证据报告（验收物）
└── images/                # 图三件套
```

## 7. 面试要点

- **Q: 怎么找到最该优化的 SQL？** pg_stat_statements 按 total（总量）与
  mean（单条）两个视角各看一遍：总量高的是优化收益，单条高的是用户体验。
- **Q: 为什么有了索引计划器还可能不用？** 统计信息过期（ANALYZE）、选择率
  估算偏差、小表全扫更便宜、索引列上的函数/类型转换导致不可用。
- **Q: 连接池打满和慢查询怎么区分？** 打满：活跃连接=池上限且 PG 空闲，
  P95 呈超时阶梯；慢查询：连接个个在干活，pg_stat_statements 有对应慢语句。
- **Q: 高频 UPDATE 表会出什么问题？** 死元组膨胀（表/索引变大变慢）、
  autovacuum 追不上、热点行锁竞争——本实验的 UPDATE stock 21ms 就是活标本。

## 8. 总结

三层证据各司其职：排行确定嫌疑、EXPLAIN 定罪、池实验辨认排队形状。
索引让 JOIN 快了 370 倍，但真正的教训是瓶颈转移——打地鼠式优化是性能
工程的常态，数据驱动才能打完一只再看下一只。下一篇项目 7「缓存三大问题」，
把 Redis 从弹药库搬上战场：命中率、穿透、击穿、雪崩，逐一复现逐一设防。
