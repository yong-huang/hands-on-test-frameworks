# 14 · Testcontainers 真依赖容器化：Postgres 随测试起停，自动化身

> SQLite 冒充生产数据库的日子该结束了。testcontainers 让测试自己拉起一个
> 真 Postgres 容器（Docker 容器——用容器化工具打包出的可随时启停的隔离运行环境）——不用手动建环境，会话结束自动销毁。读完本篇你能把 SUT
> 数据层切到真 PG 跑通，并理解"换库之后行为哪里不一样"——本实验有 4 条实测差异。

## Background

用 SQLite 给"生产环境是 Postgres"的应用做集成测试，是常见妥协：轻、快、零部署。
代价是它只能证明"逻辑对"，证明不了"方言对"——类型约束、并发锁行为、金额精度、
自增 id 取法，每种数据库都有一套自己的脾气，假库全绿不代表真库不翻车。

另一头，共享开发库（团队连同一个 PG 实例做测试）会互相污染：谁造的数据都会
漏进别人的用例；CI（持续集成，提交后自动跑检查的服务）里每次裸装数据库又太慢、太脆。

testcontainers 给出第三个选项：测试自己调 Docker 拉起一个全新 Postgres 容器，
会话结束自动销毁。真依赖、干净、快——三件事同时成立，而且全程零手工。

## What

testcontainers 是一个测试工具库：在测试代码里声明"我要一个 postgres:16-alpine"，
它在 Docker 里启动容器、等端口就绪、把连接串交给你，测试会话结束时销毁容器。

可以把 testcontainers 想成剧组租设备：开拍（session 开始）租来一台摄影机
（Postgres 容器），收工（会话结束）自动还回去，租金只按拍摄时长算。
但和租设备不同的是，它还负责"验货"（端口就绪轮询）和"清场"（容器销毁、
无残留）——`docker ps` 里来无影去无踪。

本实验的对照实验设计：`pg_store.py` 是 Postgres 方言的数据层，与 SUT 的
`store.py` 语义对齐但方言不同（占位符 `%s` vs `?`、`RETURNING *` vs
`lastrowid`）——数据层薄才换得动。

## When to Use

典型场景：

- 集成测试要真数据库：迁移脚本、约束、并发行为都要在真方言上验证。
- CI 里的"真依赖"环节：容器随流水线起停，环境永远新鲜。
- 换库评估：把行为差异实测成报告（本实验 `docs/differences.md` 就是这么生成的），
  而不是抄文档。

何时不用：纯逻辑单测不需要容器（慢一个数量级）；本地无法跑 Docker 且 CI 也
没有 Docker 时，退回 lab 13 的 SQLite 直测 + 已知差异清单是务实解。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| H2/SQLite 假库 | 快，但方言行为是假的 | 纯逻辑验证 |
| 共享开发库 | 真方言，但互相污染 | 临时排查 |
| testcontainers | 真方言 + 每次全新 + 自动起停 | 集成测试默认解 |

## Quick Start

前置条件：**Docker 是唯一硬前置**——先 `docker info` 体检（labs/00 的体检项之一），
Docker 没起时本实验无法运行，这是新手第一个失败点。

```bash
cd labs/14_testcontainers
./testcontainers_lab.sh    # 起容器跑批 → 验证无残留 → 生成差异报告
cat docs/differences.md    # 与 SQLite 的 4 条实测差异
```

预期行为（本机 Docker 未启动，无法提供实时输出；以下为实验设计的确定性流程）：
脚本先起 session 级容器（4 条用例共享一个实例，实验作者实测全套约 3 秒），
跑 CRUD（增删改查）回归与 3 条差异实测用例，最后验证 `docker ps` 无残留容器。
Docker 环境就绪时应全部通过。

与 SQLite 的 4 条实测差异（`docs/differences.md`，实验作者真机跑出，每条都有
对应用例，非抄文档）：

| # | 行为 | SQLite | Postgres |
|:--|:---|:---|:---|
| 1 | 类型约束 | 类型亲和，字符串可塞 INTEGER 列 | 强约束，直接拒绝 |
| 2 | 并发写 | 单写者，未串行化报 database is locked | MVCC，20 线程裸写全成功 |
| 3 | 金额存储 | REAL 浮点 0.30000000000000004 | NUMERIC 定点 0.30 |
| 4 | 取回自增 id | cursor.lastrowid | INSERT ... RETURNING |

容器随会话起停的关键代码（这段在做什么：声明式要一个容器，连接串自动到手）：

```python
with PostgresContainer("postgres:16-alpine") as pg:   # 随会话起停
    dsn = pg.get_connection_url()
```

## How It Works

**session 级容器复用**：容器在 session fixture 里起（4 条用例共享一个实例），
每条用例内再 TRUNCATE 隔离（lab 13 的截表策略）。"贵的共享、脏的换新"——
和 lab 02 的 fixture 作用域思想一脉相承：容器启动是秒级成本，
按用例起新容器就太奢侈了。

**生命周期对齐**：session 开始 → testcontainers 调 Docker 拉镜像（首跑要下载，这就是 lab 00 体检里给本实验配 600s 超时的原因）→ 等端口就绪 →跑全套 → 会话结束 → 容器自动销毁。

实验作者实测的首跑 144s（拉镜像）与二跑 6.2s（镜像已缓存）之差，就是环境成本与套件成本的分野。


**方言适配层**：`pg_store.py` 与 `store.py` 保持同样的函数签名与语义，
只换方言——测试因此可以"同一组用例两种后端各跑一遍"（本实验用差异用例
固化四条行为差异）。这就是 lab 11 强调数据层要薄的回报：薄才换得动。

**差异实证**：差异 ② 是 lab 13 的续集——SQLite 未串行化并发写报
`database is locked`，Postgres 凭 MVCC（多版本并发控制）20 线程裸写全成功；
差异 ③ 的 `0.30000000000000004` 是浮点存储的经典事故，
NUMERIC 定点类型直接根治。

## Pitfalls & Q&A

踩坑清单（本实验真实踩过）：

- **psycopg2 没有 `conn.execute`**。现象：从 sqlite3 迁移来的代码直接炸。
  原因：psycopg2 的 SQL 必须经 cursor。解法：`cur = conn.cursor(); cur.execute(...)`。
- **`with psycopg2.connect(...)` 提交但不关连接**。现象：长跑套件连接累积。
  解法：显式 `conn.close()`（与 lab 13 的 SQLite 坑同源）。
- **testcontainers 新版命名空间变化**。现象：`from testcontainers.postgres import ...`
  报 ImportError。原因：新版命名空间是 `testcontainers.community.postgres`，
  旧名已弃用。解法：兼容导入（实验代码里已做）。
- **Docker 没起就跑**。现象：容器创建超时/报错。解法：脚本先 `docker info`
  体检，失败给出明确指引。

深入问答：

- **Q：testcontainers 和 docker-compose 起依赖有什么区别？** 前者生命周期绑定
  测试会话、端口动态分配、并发安全；compose 面向长驻环境，测试要自己清理。
- **Q：为什么不用 H2/SQLite 冒充生产库？** 方言、锁行为、类型系统都不同——
  假库测出的"绿"到真库可能翻车（本实验差异 ①② 就是实证）。
- **Q：容器化测试怎么控制耗时？** session 级复用容器、镜像预拉取、
  ryuk（testcontainers 的残留容器回收器）兜底，必要时用 testcontainers cloud。
