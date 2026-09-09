# 32 · 负载建模：开放 vs 封闭模型——你的 P95 可能是压测器替 SUT 隐瞒的

> 上一实验的基线用 5 VU 冒烟，稳定但保守。这一篇把负载当变量做实验：
> 同一套请求动作，分别用**封闭模型**（VU 固定，等响应才发下一单）和
> **开放模型**（到达率恒定，请求互不等待）压同一个 SUT。同吞吐下 P95
> 差出 3.6 秒——这就是 Coordinated Omission，性能面试的必考陷阱。

## 1. 为什么需要它

- 封闭模型里 VU 是"有耐心的用户"：SUT 变慢它就自动少发请求，压测机成了
  SUT 的节流阀，排队被藏起来，P95 被系统性低估；
- 真实用户没有耐心：页面卡住只会再开一个标签页。开放模型才贴近生产流量；
- 尖峰（spike）、浸泡（soak）等场景族也是负载建模的一部分，本篇顺带跑通 spike。

## 2. 总览：两种执行器，同一套动作

<!-- 图: images/modeling.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/32_load_modeling/images/modeling.html)
> （或本地打开 [`images/modeling.html`](images/modeling.html)）。

k6 引擎跑完全相同的三连击（浏览+详情+半概率下单），只换执行器：封闭档位
VU=10/50/100，开放档位 50/150/300 it/s。SUT 一变慢，两条路的命运分岔——
封闭自节流、开放真排队。

## 3. 快速开始

```bash
./load_modeling.sh all     # 拉起靶场(如未起) → 封闭3档+开放3档+spike+locust → 对比报告
./load_modeling.sh clean   # 停掉 lab 31 靶场并删卷
open docs/modeling.md
```

## 4. 核心概念

### 4.1 实测：同吞吐，P95 差 3.6 秒（本机数据，Apple Silicon / Docker Desktop）

| 模型 | 档位 | 实测 RPS | P50(ms) | P95(ms) | 错误率% |
|:---|:---|---:|---:|---:|---:|
| 封闭 | VU10 | 138.0 | 8.6 | 126.4 | 0 |
| 封闭 | VU50 | 169.7 | 262.6 | 365.3 | 0 |
| 封闭 | VU100 | 169.9 | 538.9 | 750.8 | 0 |
| 开放 | 50 it/s | 127.1 | 8.2 | 124.1 | 0 |
| 开放 | 150 it/s | 173.9 | 3296.0 | **3905.7** | 1.75 |
| 开放 | 300 it/s | 169.6 | 3546.5 | **4337.7** | 22.13 |
| 封闭(Locust) | 50 VU | 161.8 | 210.0 | 310.0 | 0.21 |

读表三件事：
- **吞吐天花板 ≈170 req/s**：三档高负载殊途同归，这就是靶场当前的真实容量
  （sleep 缺陷占满线程池的后果，项目 4/8 揪它）；
- **同吞吐配对**：~170 req/s 下封闭 P95=750ms、开放 P95=4337ms——差的部分
  全是封闭模型替 SUT"瞒报"的排队；
- **Locust 交叉验证**：50 VU 读数与 k6 VU50 同量级（P95 310 vs 365ms），
  证明差距来自执行模型而非工具。

### 4.2 Coordinated Omission（CO）

压测端与 SUT"合谋"跳过了本该发出的请求：响应慢 → VU 下一单晚 → 高延迟
样本根本没机会产生。Gil Tene 的经典论述。结论写进报告模板：**容量结论以
开放模型为准，封闭模型用于观察并发行为特征**（比如 VU50→VU100 的 P50 翻倍
揭示了线程池排队）。

### 4.3 尖峰场景实测

30→400→30 it/s 阶梯：平稳期 P95≈130ms，尖峰期全程聚合 P95 冲到 7701ms、
300 it/s 档错误率 22%——容量天花板被突破时，延迟先炸、错误随后。生产上的
对应物：大促开抢的瞬间。

### 4.4 易错点

- **开放模型里别加思考时间**：到达率负责节奏，迭代内 sleep 只会让"到达"
  名不副实（本实验 closed.js 有 sleep、open.js 刻意没有）；
- **Locust 的 CSV 分位数单位就是 ms**，别二次换算；`--csv` 产物要认准
  `_stats.csv` 里的 Aggregated 行；
- 开放模型打满后 **preAllocatedVUs 要够**，否则"到达率恒定"变成 VU 不够
  的自我设限，CO 从反向再骗你一次。

## 5. 关键参数

```bash
VUS=100   k6 run k6/closed.js                 # 封闭：并发数是旋钮
RATE=300  k6 run k6/open.js                   # 开放：到达率是旋钮
~/.venvs/perf-lab/bin/locust -f locustfile.py --headless -u 50 -r 25 -t 40s \
    --host http://localhost:19331 --csv reports/locust_VU50
```

## 6. 文件结构

```
32_load_modeling/
├── README.md
├── load_modeling.sh         # prereq/closed/open/spike/locust/report/clean
├── k6/closed.js             # 封闭模型（ramping-vus 思路，VU 可注入）
├── k6/open.js               # 开放模型（constant-arrival-rate）
├── k6/spike.js              # 尖峰场景（ramping-arrival-rate）
├── locustfile.py            # Locust 等效封闭场景（交叉验证）
├── gen_compare.py           # 两工具多轮结果 → docs/modeling.md（含自动配对）
├── reports/                 # 各轮 summary-export JSON / locust CSV
├── docs/modeling.md         # 对比报告（验收物）
└── images/                  # 图三件套
```

## 7. 面试要点

- **Q: 什么是 Coordinated Omission？** 压测器因 SUT 变慢而协同式地少发请求，
  高延迟样本缺失，P95 被低估。对策：开放模型（恒定到达率）+ 记录"应发未发"
  的补偿样本。
- **Q: 封闭模型还有什么用？** 并发行为特征：连接池耗尽、锁竞争、线程池排队
  都对并发数敏感，VU 阶梯是放大它们的可控手段。
- **Q: 吞吐天花板怎么读出来的？** 多档加压后 RPS 不再增长（169.9→169.7→169.6）
  而 P95 直线上涨，即进入饱和区；天花板数值就是当前架构的容量。
- **Q: 压测时该用思考时间吗？** 封闭模型要加（模拟真人节奏，否则并发=纯
  back-to-back）；开放模型不加（节奏由到达率负责）。

## 8. 总结

同一份代码、两种执行模型，读数差出一个数量级——你以后看到任何"P95 报告"，
都会先问一句：这压力是怎么发出去的？下一篇项目 3「监控栈与黄金信号」，
给靶场装上 Prometheus + Grafana，让压测时的资源曲线与延迟曲线同屏对质。
