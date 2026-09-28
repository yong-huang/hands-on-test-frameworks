# 13 · 数据库集成测试：绕过 HTTP，直击数据层，两种隔离正面对决

> API 测试证明"HTTP 接起来对"，但数据层自己呢？迁移脚本在旧库上敢重跑吗？
> 两个人同时下单会互相踩吗？本实验直接对 SUT 的 `store.py` 做集成测试，
> 实测对比两种隔离策略，并亲手复现一次 `database is locked`。
> 读完本篇你能按场景选对测试隔离策略，并用三板斧测迁移脚本。

## Background

API 测试全绿之后，数据层仍有自己的雷区：事务（transaction，把一组数据库操作绑成"要么全成功要么全回滚"的单元）边界画错、并发写互相踩锁、迁移脚本在旧库上重跑炸裂——这些都在 HTTP 层看不出来。

一条 422 不会告诉你`CREATE TABLE` 写了没有 `IF NOT EXISTS`，只有直接对数据层跑一遍才知道。


数据层测试的特有难题是**隔离**（每条用例面对什么状态的数据）：数据库是有状态的，
前一条用例留下的数据会污染后一条用例的断言。隔离策略选错了，代价要么是慢
（每条用例重建库），要么是假绿（清理纪律失守后用例互相串味）。

本实验对 lab 11 的 SUT 数据层 `store.py` 直测——不起 HTTP 服务，
用两种隔离策略跑同一组操作，再并发写压一次锁。

## What

数据库集成测试是对数据层代码（连着真实数据库执行的）做的测试：迁移脚本、
CRUD（增删改查）行为、约束与并发，全部在真库上验证。它绕过 HTTP 层，
`sys.path.insert` 后直接 `import` SUT 的 `store` 模块。

可以把数据层测试想成仓库验收：API 测试是前台验单（单据流程对不对），
数据层测试是进库房盘点（货架结构、入库记录、两个搬运工同时抢一条通道会不会堵死）。
但和盘点不同的是，测试要自己解决"上一批验货留下的货"——这就是隔离策略。

两种策略：**fresh**（每条用例建全新库文件，零污染、最慢）与
**truncate**（共享库 + 用例前后 `DELETE FROM`，最快、依赖清理纪律）。
本实验用 `@pytest.mark.isolation("fresh"|"truncate")` 一键切换。

## When to Use

典型场景：

- 迁移脚本验收：空库可执行、旧库重跑幂等、数据完好——迁移的"三板斧"。
- 并发行为验证：写锁、事务边界、串行化策略，只有并发用例能暴露。
- 数据约束回归：唯一键、外键、状态机约束的负向路径。

何时不用：业务规则验证优先走 API 层（契约是给接口的）；纯内存数据结构
用普通单测就够了——拉真库是有成本的，别为测一个纯函数建库。

隔离策略对比（本实验实测）：

| 策略 | 做法 | 优点 | 代价 |
|:---|:---|:---|:---|
| fresh_db | 每用例新库文件 | 零污染，最可信 | 每例付建表成本 |
| truncate_db | 共享库 + DELETE FROM | 快 | teardown 忘清就串味 |

同组用例两种策略跑结果一致（脚本 ②③）——**策略只影响速度与成本，
不该影响正确性**。

## Quick Start

前置条件：labs/00 体检通过；不依赖 Docker 与 HTTP 服务（数据层直测）。

```bash
cd labs/13_db_tests
./db_tests.sh            # 全量 → 两种隔离分别跑 → 并发冲突演示
./db_tests.sh observe
```

全量运行的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 全量：隔离/迁移/并发一次跑齐（数据层直测，不起 HTTP 服务）
collected 10 items

tests/test_concurrent.py ..                                              [ 20%]
tests/test_isolation.py .....                                            [ 70%]
tests/test_migration.py ...                                              [100%]

============================== 10 passed in 0.08s ==============================
```

两种隔离策略分别运行（observe ②③，节选）：

```
=====> [observe] ② 只跑 truncate 策略（共享库 + 截表）
======================= 4 passed, 6 deselected in 0.07s ========================

=====> [observe] ③ 只跑 fresh 策略（每用例全新库）对比
======================= 2 passed, 8 deselected in 0.06s ========================
```

并发写冲突演示（observe ④，节选）：

```
tests/test_concurrent.py::test_unserialized_writers_conflict PASSED      [ 50%]
tests/test_concurrent.py::test_store_serializes_writes PASSED            [100%]
======================= 2 passed, 8 deselected in 0.07s ========================
```

诚实预期：10 条全绿。注意 `test_unserialized_writers_conflict` 名字里的
"conflict"：这条用例断言的是"裸 SQLite 并发写**必然**报 `database is locked`"——
冲突被预期并断言，而不是碰运气。这也是为什么它 PASSED 是正常态。

关键代码（这段在做什么：绕过 HTTP 的三个关键手法）：

```python
sys.path.insert(0, str(SUT_DIR))     # 直接 import SUT 的 store，绕过 HTTP
@pytest.mark.isolation("fresh")      # mark 驱动的策略切换
conn.execute("BEGIN IMMEDIATE")      # 主动抢写锁（复现冲突的关键）
```

## How It Works

**隔离策略的实现**：`conftest.py` 提供三件套。

- `fresh_db`：function 级 fixture，每条用例在 `tempfile` 里建全新库、跑 `init_db`。
- `truncate_db`：session 级共享库，function 级 teardown `DELETE FROM` 全表。
- `db`：按用例的 isolation mark 把请求转发到对应 fixture。

mark 驱动切换让"同一组操作"能两种策略各跑一遍，结果一致性肉眼可比。


**迁移幂等三板斧**：`store.init_db` 用 `CREATE TABLE IF NOT EXISTS` +
`INSERT OR IGNORE` 版本表——实测三条：空库可执行、旧库重复执行不报错且数据不丢、
版本号不重复累加。迁移脚本的最高纪律就是幂等（同脚本跑多少遍结果都一样）。

**并发写冲突的机制**：SQLite 的写锁在**库文件级**（不是表级/行级）。

裸 SQLite写者 A 持锁期间，写者 B（`timeout=0`）当场 `database is locked`；而 `store.py`用应用层 `threading.Lock` 串行化写——20 线程并发下单全部成功。

记住这个行为：**lab 26 压测的 RPS 拐点就长在这里**。


**事务回滚隔离为何缺席（诚实记录）**：SUT 数据层是"一操作一连接"设计——用例拿不到事务控制权，无法把操作包进 SAVEPOINT（事务内部的保存点，允许只回滚到该点、不废弃整个事务）回滚。

回滚隔离要求"测试控制事务、数据层在同连接里干活"，这是数据层设计的真实取舍，不是测试技巧能弥补的。想要回滚隔离，先改造数据层接受注入连接。


## Pitfalls & Q&A

踩坑清单：

- **自定义 mark 忘了注册**。现象：`isolation` 未注册时运行告警——lab 09 的教训
  再次应验。解法：`configs/pytest.ini` 里登记。
- **`with sqlite3.connect(...)` 只提交不关连接**。现象：长跑套件累积连接、文件句柄
  耗尽。解法：显式 close 或 try/finally。
- **以为 SQLite 锁在行级**。锁在库文件级——并发设计必须围绕"串行化写"展开。
- **共享库用例不清理**。现象：单独跑绿、合跑挂（串味）。解法：teardown
  兜底 `DELETE FROM`，并把清理写进 fixture 而不是用例里。

深入问答：

- **Q：事务回滚隔离和截表隔离怎么选？** 数据层支持事务注入选回滚（快且干净）；
  不支持时截表/新建是务实解；共享库必须 teardown 兜底清理。
- **Q：怎么测迁移脚本？** 三板斧：空库可执行、旧库重复执行幂等、迁移后数据完好。
- **Q：`database is locked` 是什么？** SQLite 库级写锁被占。治本是缩短写事务/
  串行化写/换支持 MVCC（多版本并发控制，读写互不阻塞的并发模型）的库
  （lab 14 的 Postgres）。
