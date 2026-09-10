# 08 · 并发模型与容量调参：矩阵实验找最优工作点

> 单点压测回答"这个配置多快"，矩阵实验回答"**哪个配置最优**"。把 uvicorn
> workers 和 GOMAXPROCS 变成旋钮，3×2×2 矩阵跑下来：shop 提 **63%**，
> shorturl 却纹丝不动——两种语言、两种运行时、两种诚实的结论。

## 1. 为什么需要它

- 默认配置是给"不知道你的负载"的人准备的；容量调参就是把负载形状代入，
  用矩阵实验代替拍脑袋；
- Python 的 worker 数与 GIL/线程池互相纠缠，Go 的 GOMAXPROCS 只管 CPU
  并行——两个旋钮的命运在数据里对比得清清楚楚；
- 连接池是**每进程**的：worker 翻倍 = PG 连接翻倍，容量预算必须联动。

## 2. 总览：矩阵实验拓扑

<!-- 图: images/tuning.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/08_concurrency_tuning/images/tuning.html)
> （或本地打开 [`images/tuning.html`](images/tuning.html)）。

两个旋钮（UVICORN_WORKERS / GOMAXPROCS）× 两档并发（50/200 VU）× 两服务，
每格 40s，全部读写入 `reports/matrix_results.txt`，报告脚本挑出最优工作点。

## 3. 快速开始

```bash
./tune_concurrency.sh all     # 矩阵实验 → docs/tuning.md（约 12 分钟）
./tune_concurrency.sh clean   # 恢复默认配置
```

## 4. 核心概念

### 4.1 实测矩阵（本机数据，40s/格）

**shop（FastAPI，读多写少）：**

| workers | 50 VU | 200 VU |
|---:|---:|---:|
| 1 | 1645.8 RPS / P95 13.7ms | 1546.7 / 127.3 |
| 2 | 1774.4 / 9.0 | 1880.1 / 113.3 |
| 4 | 1854.1 / 4.4 | **2526.7 / 68.3** |

最优 4 workers @200VU：**比默认 1 worker +63%**（验收线 20%）。
P50/P95 同时下降——worker 变多不只是吞吐，排队也短了。

**shorturl（Go，内存跳转）：**

| GOMAXPROCS | 50 VU | 200 VU |
|---:|---:|---:|
| 1 | 271.4 / 5.5ms | 1080.7 / 6.1 |
| 2 | 271.1 / 4.9 | 1079.9 / 9.5 |
| 4 | 270.7 / 4.6 | 1075.1 / 8.9 |

**完全无感**——三种设置误差 <1%。

### 4.2 为什么 Python 收益巨大而 Go 无感

- shop 是多进程受益型：每 worker 独立 GIL + 独立线程池，4 进程 = 4 倍
  并行处理能力；且它是 IO 密集 + DB 交互型，worker 间无共享状态冲突；
- shorturl 的跳转是**纳秒级内存操作**：单 P 的 runtime 就能喂饱网卡与
  连接处理，CPU 根本不是瓶颈——GOMAXPROCS 调的是 CPU 并行度，对
  IO 密集服务天然无感。它的真实用途是**对齐容器 CPU limit**（超卖节点
  上 GOMAXPROCS=核数会撞 throttling）。
- 结论方法论：**旋钮有没有用，取决于瓶颈在不在它管的资源上**。
  这也是为什么调参必须跟着观测（项目 3）走。

### 4.3 连接池预算：worker 数的隐藏账单

uvicorn 每个 worker 是独立进程，**各自持有完整连接池**：4 workers ×
POOL_MAX_SIZE=10 = 40 条 PG 连接。把 worker 加到 8，连接就 80——
`max_connections=100` 的默认额度瞬间见底。worker 数 × 池上限必须一起
进容量预算（项目 6 的教训在这里闭环）。

### 4.4 易错点（本实验真踩）

- **postgres 健康检查写死精确值**（`grep -q 5000`）：压测写入新短链后
  count≠5000，检查永远失败 → 依赖它的容器卡在 Created 状态起不来，
  k6 对着空气打出"7734 RPS / P95 0ms / 100% 失败"的假数据。
  健康检查语义要用**下限/范围**，不要精确值；
- **压测脚本写死 VU 数**：smoke_shorturl 固定 5 VU，GOMAXPROCS 矩阵
  第一轮全跑成了 5 VU——旋钮实验里每个维度都必须真的在变；
- 重启 worker 后立刻开压，首个数据点会被连接池预热污染（出现过
  78 RPS 的假低点），等 8s 再压。

## 5. 关键参数

```bash
# 旋钮 1：uvicorn workers（shell 形式 CMD 展开环境变量）
UVICORN_WORKERS=4 docker compose up -d --build shop
# 旋钮 2：GOMAXPROCS（Go runtime 原生识别；0=默认核数）
GOMAXPROCS=2 docker compose up -d shorturl
```

## 6. 文件结构

```
08_concurrency_tuning/
├── README.md
├── tune_concurrency.sh    # prereq/matrix-shop/matrix-go/report/clean
├── gen_tuning.py          # 矩阵结果 → docs/tuning.md（自动挑最优工作点）
├── reports/               # matrix_results.txt + 各格 JSON
├── docs/tuning.md         # 矩阵报告（验收物）
└── images/                # 图三件套
```

## 7. 面试要点

- **Q: uvicorn 的 workers 怎么定？** 起点是容器 CPU 核数；用矩阵实验在
  目标并发下实测 RPS/P95，收益归零即停。同时乘上每进程连接池算 PG 连接账。
- **Q: GOMAXPROCS 什么时候需要调？** 容器设了 CPU limit 但节点超卖时，
  对齐 limit 避免调度抖动；IO 密集服务通常无感（本实验实测 0%）。
- **Q: 怎么判断到了饱和区？** RPS 不随并发增长而 P95 直线上涨；饱和区里
  选 P95 最低的配置为最优工作点。
- **Q: 多进程 SQLAlchemy/连接池要注意什么？** 每进程独立池：总连接数 =
  进程数 × 池上限，必须小于 PG max_connections 减去运维预留。

## 8. 总结

矩阵实验给了两个诚实的答案：shop 加 worker 值 63%，shorturl 拧 GOMAXPROCS
一文不值——旋钮的价值取决于瓶颈在不在它管的资源上。下一篇项目 9
「浸泡测试与内存泄漏」，把时间维度加进来：短压测看不见的问题，让时间揭发。
