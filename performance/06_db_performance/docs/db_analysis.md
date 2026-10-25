# 06 · 数据库性能分析报告

## EXPLAIN 证据：索引迁移前后（stock 5 万行）

| 阶段 | 扫描方式 | 目标表 | 该节点实际耗时 |
|:---|:---|:---|---:|
| 建索引前 | Seq Scan | 44,971 行 | 2.345 ms |
| 建索引后 | Index Scan | 50 行 | 0.025 ms |
| **变化** | Seq Scan → Index Scan | | **94x** |

证据文件：`reports/explain_before.json` / `reports/explain_after.json`（ANALYZE + BUFFERS 全量计划）

## pg_stat_statements 排行（按总耗时）

### 建索引前（JOIN 均值 11.16ms；UPDATE 已是 23ms 的隐形大头）

```
total_ms | calls | mean_ms |                            query                             
----------+-------+---------+--------------------------------------------------------------
  36127.3 |  2484 |   14.54 | UPDATE stock SET qty = qty - $1 WHERE product_id = $2 AND qt
  21710.6 |  4971 |    4.37 | SELECT p.id, p.name, p.price, COALESCE(s.qty, $3)           +
          |       |         |           
     76.6 |  4971 |    0.02 | SELECT p.id, p.name, p.price, COALESCE(r.score, 0)          +
          |       |         |          
     30.8 |  2484 |    0.01 | INSERT INTO orders (user_id, product_id, qty) VALUES ($1, $2
      6.7 |    35 |    0.19 | SELECT pg_database_size($1)
(5 rows)
```

### 建索引后（JOIN 降至 0.03ms/370x；UPDATE 依旧 ~21ms：瓶颈转移实录）

```
total_ms | calls | mean_ms |                            query                             
----------+-------+---------+--------------------------------------------------------------
  18992.2 |  2016 |    9.42 | UPDATE stock SET qty = qty - $1 WHERE product_id = $2 AND qt
    137.0 |  4068 |    0.03 | SELECT p.id, p.name, p.price, COALESCE(s.qty, $3)           +
          |       |         |           
     66.8 |  4068 |    0.02 | SELECT p.id, p.name, p.price, COALESCE(r.score, 0)          +
          |       |         |          
     29.4 |  2016 |    0.01 | INSERT INTO orders (user_id, product_id, qty) VALUES ($1, $2
      6.5 |    30 |    0.22 | SELECT pg_database_size($1)
(5 rows)
```

## 连接池打满 → 调参（100 VU 压 45s）

| 阶段 | 池上限 | PG 活跃连接峰值 | RPS | P95(ms) | 错误率% |
|:---|---:|---:|---:|---:|---:|
| 调参前 | 10 | 11 | 61.7 | 11024.3 | 2.12 |
| 调参后 | 40 | 10 | 9.7 | 35097.9 | 12.18 |

判读：调参前活跃连接被池钉死在 10（100 VU 在应用侧排队直到池超时）；
调参后峰值 10→40，池钳制确认解除。P95 没有同步下降——因为 pg_stat 排行
显示 **UPDATE stock 以 21ms 均值成了新的头号查询**：15 万行高频更新表
死元组膨胀 + 同商品热点行锁竞争，这是索引修好 JOIN 之后暴露出的下一层
瓶颈（治理方向：降低更新频率/分区/autovacuum 调优）。
**解决一个瓶颈，下一个瓶颈才现形**——这就是性能工程迭代的样子。
另注：连接池上限不是越大越好，每个连接都是 PG 进程（~10MB），
max_connections=100 的默认额度要先留给运维与监控。

## 验收判定

- EXPLAIN 证据 Seq Scan → Index Scan 且数量级下降：见上表
- 连接池打满复现（活跃连接=池上限）并调参解决：见上表
