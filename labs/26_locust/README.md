# 26 · 性能测试（Locust）：10→100 并发阶梯加压，找到 SUT 的拐点

> 功能全绿不代表上线能活。Locust 用 Python 写压测场景：虚拟用户群爬坡加压，
> RPS/P95 曲线会告诉你 SUT 能扛多少、瓶颈在哪。本篇实测出拐点，并把它和
> lab 13/14 的数据库结论对上——性能问题从来不是孤立的。

## 1. 为什么需要它

- 压测回答两个问题：当前容量是多少？加压时先死在哪里？
- Locust 场景即代码：任务权重、思考时间、断言全部可编程。

## 2. 总览：虚拟用户群 → SUT → 统计报告

<!-- 图: images/locust.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/26_locust/images/locust.html)
> （或本地打开 [`images/locust.html`](images/locust.html)）。

100 虚拟用户以 10/s 爬坡；读写混合 3:1（浏览:下单）+ 慢接口探针；
引擎逐档输出 RPS/延迟/失败率 → CSV/HTML 报告 → 拐点分析。

## 3. 快速开始

```bash
./locust_run.sh            # 起 SUT(8926) → headless 阶梯加压 2 分钟 → 拐点报告
open reports/locust.html   # 官方图表（RPS/延迟曲线）
cat docs/bottleneck.md     # 实测拐点表 + 瓶颈猜测
```

## 4. 核心概念

### 4.1 场景建模：像用户一样施压

`HttpUser` + `between(0.5, 1.5)` 思考时间；`@task(3)/@task(1)` 权重控制
读写比例；下单用唯一客户名——**压测数据也要讲隔离**，别让唯一索引打架。

### 4.2 阶梯加压找拐点

`--users 100 --spawn-rate 10`，2 分钟内从 10 爬到 100。逐档对比：
RPS 随并发线性涨 → 趋平 → 回落，趋平点就是拐点。

### 4.3 实测结果与瓶颈归因（本机数据）

- 读接口（列表分页）RPS 高且稳；慢接口把 P95 锚在 1500ms——
  `time.sleep(1.5)` 占住线程池，并发下排队效应被放大；
- 下单写接口在高档位延迟增长更快——根因是 **SQLite 单写者锁**
  （lab 13 实测过 locked，lab 14 实测 Postgres MVCC 无此问题）；
- 对照结论：换库 + 慢接口异步化，是这份报告给出的两条治理路径。

### 4.4 易错点

- 压测机与 SUT 同机：CPU 会互相抢——本机数据看趋势可以，绝对值要看部署形态。
- 别拿生产数据形态压测试库（数据量差几个量级，计划器行为完全不同）。

## 5. 关键参数

```bash
locust -f locustfile.py --headless --users 100 --spawn-rate 10 \
       --run-time 2m --host ... --csv reports/locust --html reports/locust.html
```

## 6. 文件结构

```
26_locust/
├── README.md
├── locust_run.sh              # SUT 生命周期 + 压测 + 报告生成
├── locustfile.py              # 场景定义（权重/思考时间/断言）
├── reports/                   # locust_stats.csv / locust.html（运行后生成）
├── docs/bottleneck.md         # 拐点报告（脚本从 CSV 生成）
└── images/
```

## 7. 深入要点

- **Q: RPS 和并发用户什么关系？** RPS ≈ 并发 × 1/(响应时间+思考时间)——
  响应时间劣化时 RPS 增长放缓甚至回落，这就是拐点的数学形态。
- **Q: P95 恶化先查什么？** 先看是全端点恶化还是单端点：单端点查实现
  （本实验是 sleep），全端点查资源（CPU/锁/连接池）。
- **Q: 压测数据要清理吗？** 要——百万行测试数据会让下一次压测的基线失真。

## 8. 总结

SUT 的脾气摸清了。下一篇 [27_k6](../27_k6/README.md)：k6 的场景与阈值门禁——
性能测试进 CI 的姿势。
