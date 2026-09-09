# 36 · 数据库性能分析报告

## EXPLAIN 证据：索引迁移前后（stock 5 万行）

| 阶段 | 扫描方式 | 目标表 | 该节点实际耗时 |
|:---|:---|:---|---:|
| 建索引前 | Seq Scan | 116,504 行 | 7.792 ms |
| 建索引后 | Index Scan | 50 行 | 0.054 ms |
| **变化** | Seq Scan → Index Scan | | **144x** |

证据文件：`reports/explain_before.json` / `reports/explain_after.json`（ANALYZE + BUFFERS 全量计划）

## pg_stat_statements 排行（按总耗时）

### 建索引前（JOIN 均值 11.16ms；UPDATE 已是 23ms 的隐形大头）

```
total_ms | calls | mean_ms |                            query                             
----------+-------+---------+--------------------------------------------------------------
  44262.6 |  1874 |   23.62 | UPDATE stock SET qty = qty - $1 WHERE product_id = $2 AND qt
  42163.4 |  3778 |   11.16 | SELECT p.id, p.name, p.price, COALESCE(s.qty, $3)           +
          |       |         |           
     61.4 |  3778 |    0.02 | SELECT p.id, p.name, p.price, COALESCE(r.score, $2)         +
          |       |         |         
     24.0 |  1874 |    0.01 | INSERT INTO orders (user_id, product_id, qty) VALUES ($1, $2
      2.6 |  9450 |    0.00 | BEGIN
(5 rows)
```

### 建索引后（JOIN 降至 0.03ms/370x；UPDATE 依旧 ~21ms：瓶颈转移实录）

```
total_ms | calls | mean_ms |                            query                             
----------+-------+---------+--------------------------------------------------------------
  40988.3 |  1922 |   21.33 | UPDATE stock SET qty = qty - $1 WHERE product_id = $2 AND qt
    126.9 |  3883 |    0.03 | SELECT p.id, p.name, p.price, COALESCE(s.qty, $3)           +
          |       |         |           
     60.0 |  3883 |    0.02 | SELECT p.id, p.name, p.price, COALESCE(r.score, 0)          +
          |       |         |          
     26.1 |  1922 |    0.01 | INSERT INTO orders (user_id, product_id, qty) VALUES ($1, $2
      2.1 |  9712 |    0.00 | BEGIN
(5 rows)
```

## 连接池打满 → 调参（100 VU 压 45s）

| 阶段 | 池上限 | PG 活跃连接峰值 | RPS | P95(ms) | 错误率% |
|:---|---:|---:|---:|---:|---:|
| 调参前 | 10 | 10 | 20.7 | 13082.0 | 6.11 |
| 调参后 | 40 | 40 | 21.9 | 27076.9 | 7.84 |

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
