# 03 · 监控栈与黄金信号：压测从黑盒变成直播

> 前两个实验的压测报告只有 SUT 的视角——延迟涨了，但**资源侧发生了什么**
> 全靠猜。这一篇给靶场装上 Prometheus + Grafana：四条黄金信号（流量/延迟/
> 错误/资源）同屏联动，SLO 告警在压测中真实触发。从此每个性能结论都有
> 双侧证据：压测器看到的 + 系统承受的。

## 1. 为什么需要它

- 只看压测端数据无法归因：P95 从 130ms 涨到 4s，是 CPU 打满？连接池排队？
  还是下游变慢？监控栈让答案在曲线上；
- USE 方法（资源）+ RED 方法（服务）互补：本实验的面板两套齐备；
- 告警规则是 SLO 的执行形态——"P95 > 500ms"不是文档里的一句话，
  而是一条会 firing 的 PromQL。

## 2. 总览：抓取 4 路，一屏对照

<!-- 图: images/observability.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/03_observability/images/observability.html)
> （或本地打开 [`images/observability.html`](images/observability.html)）。

Prometheus 每 5s 抓取两 SUT 的 /metrics 与 pg/redis exporter；Grafana 面板
同屏画四条信号；告警规则超阈值即 firing。macOS Docker Desktop 拿不到宿主机
级指标，资源信号用**进程级**（process_cpu_seconds / RSS）替代——SUT 进程
的 CPU 与内存恰恰才是本系列关心的。

## 3. 快速开始

```bash
./observe_observability.sh all     # 靶场就绪 → 起监控栈 → 边压边盯告警 → 证据报告
./observe_observability.sh clean   # 停监控栈（靶场保留，是公共设施）
open docs/golden.md                # 黄金信号实测证据
```

## 4. 核心概念

### 4.1 实测：告警在压测中真实触发（本机数据）

开压（开放模型 150 it/s × 90s）后告警时间线：

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
| shop RSS | 82.9MB |
| PG 事务/s | 126.7 |

### 4.2 联动读数：曲线会讲因果

延迟暴涨 + **CPU 只有 1 核** + 内存平稳 = 瓶颈不在算力，在等待
（线程池排队 + sleep 缺陷）——这正是项目 4 要用 py-spy 证明的事。
若是 CPU 贴满 4 核、延迟同步上涨，故事就完全不同（算力瓶颈，先扩容）。
**先看联动形态再动手，是性能工程的纪律。**

### 4.3 指标从哪来（两套 SUT 两种口径）

- shop：prometheus-fastapi-instrumentator 自动挂 `http_requests_total`
  与高精度直方图 `http_request_duration_highr_seconds`；
- shorturl：`promhttp.InstrumentHandler*` 中间件 + 显式 handler 标签
  （`withObs()`，见 lab 01 的 main.go）；
- 告警规则用 `or` 兼容两家的直方图名——**真实世界的指标命名从不统一**。

### 4.4 易错点

- **别用 pg_isready 当"存储就绪"信号**（lab 01 踩过）；同样，exporter
  的 target up ≠ 有数据，报告前先跑一遍查询；
- promhttp 的 handler 标签默认拿不到路由名，必须 `MustCurryWith` 显式给，
  否则所有流量挤在同一个标签值里；
- `for: 15s` 是防抖：瞬时毛刺不该 page 人。观察时间线里 t+20s 才首次
  firing，就是 for 在起作用。

## 5. 关键参数

```bash
# 抓取目标（容器网络内服务名寻址）
static_configs: [{ targets: ["shop:8931", ...] }]
# 告警语义
histogram_quantile(0.95, sum(rate(..._bucket[30s])) by (le)) > 0.5   # P95>SLO
for: 15s                                  # 持续时长才触发
# Grafana 面板 provisioning：configs/grafana/ 下挂载即生效，免手工配置
```

## 6. 文件结构

```
03_observability/
├── README.md
├── observe_observability.sh   # prereq/apply/load/report/clean
├── docker-compose.monitor.yml # 监控四件套，外挂 lab 01 网络
├── configs/
│   ├── prometheus.yml         # 抓取配置（4 job × 5s）
│   ├── alerts.yml             # HighP95Latency / HighErrorRate
│   └── grafana/               # 数据源 + 面板 provisioning（免手工导入）
├── gen_golden.py              # PromQL 查询 → docs/golden.md（可复算的证据）
├── reports/.alert_fired       # 压测期间告警是否触发（load 步骤写入）
├── docs/golden.md             # 黄金信号证据（验收物）
└── images/                    # 图三件套
```

## 7. 深入要点

- **Q: 四个黄金信号是什么？** 流量、延迟、错误、饱和度（Google SRE）。
  本实验用 RPS/P95/错误率/进程CPU+RSS 对应；饱和度在进程模型里看排队与
  连接池（项目 6/8 深入）。
- **Q: USE 和 RED 的区别？** RED 面向服务请求（Rate/Errors/Duration），
  USE 面向资源（Utilization/Saturation/Errors）；前者回答"服务怎么样"，
  后者回答"资源够不够"。
- **Q: 为什么选进程级指标而不是容器级？** macOS Docker Desktop 的 cAdvisor
  拿不到宿主机指标；而性能归因往往只需要 SUT 进程自身视角，还能跨部署
  形态复用（物理机/K8s 里 process_* 指标照抓）。
- **Q: 告警 for 参数的作用？** 持续满足条件才触发，滤掉瞬时毛刺；
  设太短会狼来了，太长会漏掉真实事故——SLO 的燃烧速率决定它。

## 8. 总结

靶场现在有了"仪表盘 + 警笛"：压测中的资源侧行为全部留痕，告警在 SLO
被击穿时真实 firing。联动曲线已经把嫌疑指向"等待而非算力"——下一篇
项目 4「Python 热点剖析」，用 py-spy 火焰图把 shop 的 CPU 与阻塞现场
拍到函数级，揪出第一只缺陷。
