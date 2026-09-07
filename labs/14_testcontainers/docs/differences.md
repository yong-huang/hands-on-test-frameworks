# SUT 数据层：SQLite vs Postgres 行为差异实测（lab 14）

| # | 行为 | SQLite（SUT 现状） | Postgres（lab 14 实测） | 影响 |
|:--|:---|:---|:---|:---|
| 1 | 类型约束 | 类型亲和：字符串可塞进 INTEGER 列不报错 | 强约束：错误类型直接拒绝 | SQLite 掩盖了脏数据 bug |
| 2 | 并发写 | 单写者：并发写未串行化时报 database is locked（lab 13 实测） | MVCC：20 线程裸写全部成功 | lab 26 压测拐点的根源 |
| 3 | 金额存储 | REAL 浮点：0.1+0.2 = 0.30000000000000004 | NUMERIC(10,2) 定点：0.30 | 金额计算口径必须统一 |
| 4 | 取回自增 id | cursor.lastrowid | INSERT ... RETURNING * | 数据层不可直接互换，需方言适配 |
