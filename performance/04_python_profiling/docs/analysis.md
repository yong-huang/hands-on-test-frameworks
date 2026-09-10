# 04 · Python 剖析修复对比报告

| 口径 | RPS | P50(ms) | P95(ms) | 错误率% |
|:---|---:|---:|---:|---:|
| 修复前 | 26.6 | 14.0 | 131.9 | 1.6 |
| 修复后 | 30.2 | 5.2 | 11.6 | 1.2 |
| **变化** | 1.14x | | **P95 -91%** | |

## 火焰图归因（修复前）

- CPU 热点：`recommend_score` → `hashlib.md5`（D2，每次详情请求 ~25ms 纯 CPU）
- off-CPU（--idle）：`time.sleep` 占住工作线程（D3）+ `psycopg` 逐行查库存的 51 次 RTT（D1）
- 证据文件：`reports/flame_before.svg`（或 .json speedscope）、`reports/top_before.txt`

## 修复动作

| 缺陷 | 修复 | 效果 |
|:---|:---|:---|
| D1 N+1 | LEFT JOIN 一条 SQL | 列表接口 SQL 数 51→1 |
| D2 CPU 热点 | 打分预计算入 recommend_scores 表 | 详情接口 0 用户态 CPU |
| D3 同步 sleep | 移除假风控 | 线程池不再被 120ms/单 占据 |

## 验收判定

- 火焰图定位到具体函数：**是**（md5 热点 + sleep/IO 占比）
- 同场景 P95 改善 ≥30%：**通过**（实测 -91%）
