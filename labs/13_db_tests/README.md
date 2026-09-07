# 13 · 数据库集成测试：绕过 HTTP，直击数据层，两种隔离正面对决

> API 测试证明"HTTP 接起来对"，但数据层自己呢？迁移脚本在旧库上敢重跑吗？
> 两个人同时下单会互相踩吗？本篇直接对 SUT 的 `store.py` 做集成测试——
> 并实测对比两种隔离策略，再亲手复现一次"database is locked"。

## 1. 为什么需要它

- 数据层是 bug 藏身处：事务边界、并发锁、迁移幂等，HTTP 层测不出来。
- 隔离策略决定测试的速度与可信度——选错就是"慢"或"假绿"。

## 2. 总览：两种隔离策略的数据流

<!-- 图: images/db_tests.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/13_db_tests/images/db_tests.html)
> （或本地打开 [`images/db_tests.html`](images/db_tests.html)）。

fresh 策略每条用例建全新库（最干净、最慢）；truncate 策略共享库、用例前后
DELETE FROM（最快、依赖清理纪律）。`@pytest.mark.isolation("fresh"|"truncate")`
一键切换。

## 3. 快速开始

```bash
./db_tests.sh            # 全量 → 两种隔离分别跑 → 并发冲突演示
./db_tests.sh observe
```

## 4. 核心概念

### 4.1 隔离策略对比（本实验实测）

| 策略 | 做法 | 优点 | 代价 |
|:---|:---|:---|:---|
| fresh_db | 每用例新库文件 | 零污染，最可信 | 每例付建表成本 |
| truncate_db | 共享库 + DELETE FROM | 快 | teardown 忘清就串味 |

同组用例两种策略跑，结果一致（脚本 ②③）——**策略只影响速度与成本，不该影响正确性**。

### 4.2 迁移可重复执行

`store.init_db` 用 `CREATE TABLE IF NOT EXISTS` + `INSERT OR IGNORE` 版本表。
实测：空库可执行、旧库重复执行不报错、**数据不丢、版本号不重复累加**（3 条迁移用例）。
迁移脚本的最高纪律：幂等。

### 4.3 事务回滚隔离为何缺席（诚实记录）

SUT 数据层是"一操作一连接"设计——用例拿不到事务控制权，无法把操作包进
SAVEPOINT 回滚。**回滚隔离要求"测试控制事务、数据层在同连接里干活"**——
这是数据层设计的真实取舍，不是测试技巧能弥补的。想要回滚隔离，先改造数据层
接受注入连接。

### 4.4 并发写冲突：亲手摸一次锁

裸 SQLite：写者 A 持锁期间，写者 B（timeout=0）当场 `database is locked`
（测试真实触发）；而 `store.py` 用应用层 `threading.Lock` 串行化写——20 线程
并发下单全部成功。记住这个行为：**lab 26 压测的 RPS 拐点就长在这里**。

### 4.5 易错点

- 自定义 mark 记得注册（`isolation` 没注册会告警——lab 09 的教训再次应验）。
- `with sqlite3.connect(...)` 只提交不关连接；长跑套件会累积连接。
- SQLite 的锁在**库文件级**，不在表级/行级。

## 5. 关键字段

```python
sys.path.insert(0, str(SUT_DIR))     # 直接 import SUT 的 store，绕过 HTTP
@pytest.mark.isolation("fresh")      # mark 驱动的策略切换
conn.execute("BEGIN IMMEDIATE")      # 主动抢写锁（复现冲突的关键）
```

## 6. 文件结构

```
13_db_tests/
├── README.md
├── db_tests.sh               # 主演示脚本
├── configs/pytest.ini        # 注册 isolation marker
├── tests/
│   ├── conftest.py           # fresh_db / truncate_db / db 三件套
│   ├── test_isolation.py     # 两种策略跑同组操作
│   ├── test_migration.py     # 幂等三连：空库/旧库重跑/版本单调
│   └── test_concurrent.py    # 裸库必锁 vs 应用层串行化
└── images/
```

## 7. 面试要点

- **Q: 事务回滚隔离和截表隔离怎么选？** 数据层支持事务注入选回滚（快且干净）；
  不支持时截表/新建是务实解；共享库必须 teardown 兜底清理。
- **Q: 怎么测迁移脚本？** 三板斧：空库可执行、旧库重复执行幂等、迁移后数据完好。
- **Q: database is locked 是什么？** SQLite 库级写锁被占；治本是缩短写事务/
  串行化写/换支持 MVCC 的库（lab 14 的 Postgres）。

## 8. 总结

数据层已被夹击验证。下一篇 [14_testcontainers](../14_testcontainers/README.md)：
把数据层切到真 Postgres——容器随测试起停，差异实测记录。
