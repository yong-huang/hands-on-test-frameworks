# 03 · 监控栈与黄金信号：压测从黑盒变成直播

> 前两个实验的压测报告只有 SUT 的视角——延迟涨了，但**资源侧发生了什么**
> 全靠猜。这一篇给靶场装上 Prometheus + Grafana：四条黄金信号（流量/延迟/
> 错误/资源）同屏联动，SLO 告警在压测中真实触发。从此每个性能结论都有
> 双侧证据：压测器看到的 + 系统承受的。

## Background

只看压测端数据无法归因：P95 从 130ms 涨到 4s，是 CPU 打满？连接池排队？
还是下游变慢？黑盒压测的每个结论后面都跟着一个问号。

性能监控的方法论有现成的两套：RED 方法（Rate/Errors/Duration，面向服务
请求）与 USE 方法（Utilization/Saturation/Errors，面向资源）——前者回答
"服务怎么样"，后者回答"资源够不够"，互补成完整视角。

告警规则是 SLO（Service Level Objective，服务质量目标）的执行形态：
"P95 > 500ms"不是文档里的一句话，而是一条会 firing 的 PromQL——
SLO 不能被执行的告警表达，就只是愿望。

## What

监控栈是压测的观测基础设施：Prometheus（时序数据库 + 抓取器）每 5s
抓取两 SUT 的 /metrics 与 pg/redis exporter（指标导出器：把 Postgres/Redis
内部状态翻译成 /metrics 文本的适配组件）。

Grafana 面板同屏画四条黄金信号；告警规则超阈值即 firing（告警处于触发中）。

可以把监控栈想成给靶场装上的行车记录仪 + 警笛：压测期间系统承受了什么
（CPU、内存、事务率）全程留痕（记录仪），SLO 被击穿时自动响（警笛）。

但和行车记录仪不同的是，它按 5s 间隔聚合采样而非逐帧全录——瞬时毛刺可能没进画面，结论必须与压测端数据对照后再下。

**联动读数是本篇的核心技能**。实测开压（开放模型 150 it/s × 90s）后
的告警时间线：

```
[t+20s] firing: HighP95Latency          ← P95 破 500ms SLO
[t+35s] firing: HighP95Latency,HighErrorRate   ← 错误率破 5%
[t+105s] firing: HighP95Latency          ← 压力回落后错误率先恢复
```

压测窗口的黄金信号实测值（PromQL 可复算，见 `docs/golden.md`）：

| 信号 | 实测值 |
|:---|:---|
| shop RPS | 121.2 |
| shop P95 | 4.38s（远超 SLO 500ms） |
| shop 进程 CPU | 1.06 核 |
| shop RSS（Resident Set Size，进程实际占用的物理内存） | 82.9MB |
| PG 事务/s | 126.7 |

延迟暴涨 + **CPU 只有 1 核** + 内存平稳 = 瓶颈不在算力，在等待
（线程池排队 + sleep 缺陷）——这正是项目 4 要用 py-spy 证明的事。
**先看联动形态再动手，是性能工程的纪律。**

## When to Use

典型场景：

- 压测归因：延迟曲线与资源曲线同屏，瓶颈类型一眼分档
  （算力满 vs 等待满）。
- SLO 落地：告警规则写进 configs，压测中验证告警真的会 firing。
- 修复效果复核：优化前后的资源曲线对比，证明"省的是哪类资源"。

何时不用：一次性功能验证无需监控栈（起栈有成本）；已经定位到函数级
热点的调试阶段，剖析器（项目 4/5）比指标更锋利——
监控回答"哪类资源"，剖析回答"哪行代码"。

## Quick Start

前置条件：项目 01 的靶场栈在运行（监控栈外挂它的网络）；
Docker 运行中。

```bash
cd performance/03_observability
./observe_observability.sh all     # 靶场就绪 → 起监控栈 → 边压边盯告警 → 证据报告
./observe_observability.sh clean   # 停监控栈（靶场保留，是公共设施）
open docs/golden.md                # 黄金信号实测证据
```

诚实预期：压测期间告警应真实触发（时间线见上方三行 firing 记录，
`reports/.alert_fired` 留痕）；`docs/golden.md` 的每个数字都附
PromQL 查询，可复算。注意 t+20s 才首次 firing——`for: 15s` 防抖在起作用。

指标从哪来（两套 SUT 两种口径）：

- shop：prometheus-fastapi-instrumentator 自动挂 `http_requests_total`
  与高精度直方图 `http_request_duration_highr_seconds`；
- shorturl：`promhttp.InstrumentHandler*` 中间件 + 显式 handler 标签
  （`withObs()`，见项目 01 的 main.go）；
- 告警规则用 `or` 兼容两家的直方图名——**真实世界的指标命名从不统一**。

关键参数（这段在做什么：抓取、告警语义、面板免手工配置）：

```bash
# 抓取目标（容器网络内服务名寻址）
static_configs: [{ targets: ["shop:8931", ...] }]
# 告警语义
histogram_quantile(0.95, sum(rate(..._bucket[30s])) by (le)) > 0.5   # P95>SLO
for: 15s                                  # 持续时长才触发
# Grafana 面板 provisioning：configs/grafana/ 下挂载即生效，免手工配置
```

## How It Works

**四路抓取**。Prometheus 每 5s 抓取：两 SUT 的 /metrics、postgresexporter、redis exporter。

macOS Docker Desktop 拿不到宿主机级指标，资源信号用**进程级**（process_cpu_seconds / RSS）替代——SUT 进程的CPU 与内存恰恰才是本系列关心的，且 process_* 指标跨部署形态可复用（物理机/K8s 里照抓）。


**告警的防抖语义**。`for: 15s` 要求条件持续满足才触发——瞬时毛刺不该
page 人。时间线里 t+20s 才首次 firing，就是 for 在起作用。
设太短会狼来了，太长会漏掉真实事故——SLO 的燃烧速率（错误预算被消耗的速度：超标越频繁、持续越久，烧得越快）决定它。

**联动归因的形态学**。三种典型形态对应三种瓶颈：延迟涨 + CPU 满 =
算力瓶颈（先扩容/优化算法）；延迟涨 + CPU 低 + 内存稳 = 等待瓶颈
（锁、线程池、慢下游）；延迟涨 + 内存爬升不回落 = 泄漏（项目 9）。
曲线形态就是第一层归因。

## Pitfalls & Q&A

踩坑清单：

- **用 pg_isready 当"存储就绪"信号**（项目 01 踩过）。同样，exporter
  的 target up ≠ 有数据——报告前先跑一遍查询。
- **promhttp 的 handler 标签缺失**。现象：所有流量挤在同一个标签值里，
  按路由聚合失效。解法：`MustCurryWith` 显式给路由名。
- **告警没有 for**。现象：瞬时毛刺频繁 page 人，告警疲劳。
  解法：持续时长条件，燃烧速率定参数。
- **把容器级指标当 SUT 级**。现象：资源信号对不上进程行为。
  解法：本系列用 process_* 进程级指标，跨部署形态可复用。

深入问答：

- **Q：四个黄金信号是什么？**
  流量、延迟、错误、饱和度（Google SRE）。本实验用 RPS/P95/错误率/
  进程 CPU+RSS 对应；饱和度在进程模型里看排队与连接池（项目 6/8 深入）。
- **Q：USE 和 RED 的区别？**
  RED 面向服务请求（Rate/Errors/Duration），USE 面向资源
  （Utilization/Saturation/Errors）；前者回答"服务怎么样"，
  后者回答"资源够不够"。
- **Q：为什么选进程级指标而不是容器级？**
  macOS Docker Desktop 的 cAdvisor 拿不到宿主机指标；而性能归因往往
  只需要 SUT 进程自身视角，还能跨部署形态复用。
- **Q：告警 for 参数的作用？**
  持续满足条件才触发，滤掉瞬时毛刺；设太短会狼来了，
  太长会漏掉真实事故——SLO 的燃烧速率决定它。
