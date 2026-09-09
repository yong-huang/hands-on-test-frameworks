# 🔞 SECRET_DEFS · 靶场缺陷清单（做完对应实验前不要看）

双 SUT 共 7 处刻意性能缺陷。每个项目"破案"后再来对答案：
定位手段与缺陷是否对上，是验收的一部分。

| # | 服务 | 位置 | 缺陷 | 由哪个项目揪出 |
|:---|:---|:---|:---|:---|
| D1 | shop | `list_products` | **N+1 查询**：每行商品单独查一次 stock（每页 51 条 SQL） | 项目 4（cProfile）/项目 6（pg_stat_statements） |
| D2 | shop | `recommend_score` | **纯 CPU 热点**：20000 次 MD5 迭代 ≈ 每次请求 20-30ms 用户态 CPU | 项目 4（py-spy 火焰图） |
| D3 | shop | `create_order` | **同步阻塞**：`time.sleep(0.12)` 串行调用"风控"，占满线程池 | 项目 4（py-spy）/项目 8 |
| D4 | shorturl | `redirectHandler` | **线性扫描**：5000 条短链放 slice 逐条比对，O(n) | 项目 5（pprof CPU/火焰图） |
| D5 | shorturl | `genCode` | **热循环 Sprintf 拼接**：1024 次字符串 += 分配风暴 | 项目 5（pprof allocs） |
| D6 | shorturl | `redirectHandler` | **全局互斥锁**：读读也互斥，并发越高锁竞争越凶 | 项目 5/项目 8 |
| D7 | shop/db | `01_schema.sql` | **缺索引**：stock.product_id、orders.product_id 无索引；N+1 放大成 Seq Scan | 项目 6（EXPLAIN ANALYZE） |

## 对应的"标准修复"（写给做完实验的你复核用）

- D1：一条 JOIN 带回库存
- D2：打分结果预计算/缓存，或降采样
- D3：异步化（后台任务/消息队列），或砍掉假风控
- D4：map[code]index 或直接走 DB 主键
- D5：byte slice + charset 索引拼接，砍掉 Sprintf
- D6：读写锁 → 真正的方案是读路径无锁（map + RCU 风格替换）
- D7：`CREATE INDEX ON stock(product_id)` 等

## 实验纪律

- 做对应实验**之前**禁止阅读本文件；破案后先自己写归因，再来对答案。
- 每次修复要在 `docs/baseline.md` 登记表中登记 P95 前后变化。
