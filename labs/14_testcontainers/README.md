# 14 · Testcontainers 真依赖容器化：Postgres 随测试起停，自动化身

> SQLite 冒充生产数据库的日子该结束了。testcontainers 让测试**自己拉起一个
> 真 Postgres 容器**——不用手动建环境，会话结束自动销毁。本篇把 SUT 数据层
> 切到真 PG 跑，并把"换库之后行为哪里不一样"实测记录成报告。

## 1. 为什么需要它

- 假库（SQLite 模拟 PG）只能证明"逻辑对"，证明不了"方言对"。
- 共享开发库会互相污染；CI 里每次装库太慢——容器是"真依赖 + 干净 + 快"的三解。
- 容器生命周期完全自动化：`docker ps` 里来无影去无踪（脚本 ② 步验证）。

## 2. 总览：测试会话与容器生命周期的对齐

<!-- 图: images/testcontainers.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/14_testcontainers/images/testcontainers.html)
> （或本地打开 [`images/testcontainers.html`](images/testcontainers.html)）。

session 开始 → testcontainers 调 Docker 拉 postgres:16-alpine → 等端口就绪 →
跑全套 → 会话结束 → 容器自动销毁。全程零手工。

## 3. 快速开始

```bash
./testcontainers_lab.sh    # 前置：Docker 已启动
cat docs/differences.md    # 与 SQLite 的 4 条实测差异
```

## 4. 核心概念

### 4.1 session 级容器复用

容器在 session fixture 里起（本套 4 条用例共享一个实例，实测全套 3s）；
每条用例内再 TRUNCATE 隔离（lab 13 的截表策略）。**贵的共享、脏的换新**，
和 lab 02 的 fixture 作用域思想一脉相承。

### 4.2 实测差异记录（docs/differences.md）

| # | 行为 | SQLite | Postgres |
|:--|:---|:---|:---|
| 1 | 类型约束 | 类型亲和，字符串可塞 INTEGER 列 | 强约束，直接拒绝 |
| 2 | 并发写 | 单写者，未串行化报 database is locked | MVCC，20 线程裸写全成功 |
| 3 | 金额存储 | REAL 浮点 0.30000000000000004 | NUMERIC 定点 0.30 |
| 4 | 取回自增 id | cursor.lastrowid | INSERT ... RETURNING |

每条差异都有对应用例（真实触发，非抄文档）。**换库不是平移，是行为迁移**。

### 4.3 方言适配层

`pg_store.py` 与 SUT 的 `store.py` 语义对齐但方言不同：占位符 `%s` vs `?`、
`RETURNING *` vs `lastrowid`。这就是为什么数据层要薄——**薄才换得动**。

### 4.4 易错点（本实验真实踩过）

- psycopg2 没有 `conn.execute`——SQL 必须经 cursor（sqlite3 养成的习惯在这翻车）。
- `with psycopg2.connect(...)` 提交但不关连接，要显式 close。
- testcontainers 新版命名空间是 `testcontainers.community.postgres`（旧名已弃用，
  代码里做了兼容导入）。

## 5. 关键字段

```python
with PostgresContainer("postgres:16-alpine") as pg:   # 随会话起停
    dsn = pg.get_connection_url()
v =  # Docker 是唯一硬前置：docker info 先体检
```

## 6. 文件结构

```
14_testcontainers/
├── README.md
├── testcontainers_lab.sh     # 起容器跑批 → 验证无残留 → 生成差异报告
├── configs/pytest.ini
├── pg_store.py               # Postgres 方言数据层（对照 SUT 的 store.py）
├── docs/differences.md       # 4 条实测差异（脚本自动生成）
├── tests/
│   ├── conftest.py           # session 级容器 + 截表隔离
│   └── test_postgres.py      # CRUD 回归 + 3 条差异实测
└── images/
```

## 7. 深入要点

- **Q: testcontainers 和 docker-compose 起依赖有什么区别？** 前者生命周期绑定
  测试会话、端口动态分配、并发安全；compose 面向长驻环境，测试要自己清理。
- **Q: 为什么不用 H2/SQLite 冒充生产库？** 方言、锁行为、类型系统都不同——
  假库测出的"绿"到真库可能翻车（本实验差异 ①② 就是实证）。
- **Q: 容器化测试怎么控制耗时？** session 级复用容器、镜像预拉取、
  ryuk 残留回收，必要时 testcontainers cloud。

## 8. 总结

真依赖的容器化已经打通。下一篇 [15_pact](../15_pact/README.md)：
换一个维度——消费者与提供者之间的契约测试。
