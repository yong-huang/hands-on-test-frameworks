# 01 · 双 SUT 靶场 + 基线压测：性能工程闭环的起点

> 功能测试回答"对不对"，性能工程回答"快不快、能扛多少、慢在哪"。
> 本系列用两个**故意带病上线**的被测系统当靶场：FastAPI 商店 + Go 短链服务，
> 各埋了若干性能缺陷（答案锁在 `SECRET_DEFS.md`，破案前别看）。本篇先把靶场
> 立起来，跑出**优化前基线**——后面每个实验的"提升了多少"，都拿它做对照。

## 1. 为什么需要它

- 没有基线的优化是玄学：改了一行，P95 从 130ms 变 128ms，算提升吗？可能是抖动。
- 双语言 SUT 是刻意的：Python 与 Go 的剖析器（py-spy vs pprof）、并发模型
  （GIL vs goroutine）完全不同，一个靶场吃透两边。
- 本实验是 `docs/performance.md` 清单项目 1；定位手段分别在项目 4-9 揭晓。

## 2. 总览：靶场拓扑一图看懂

<!-- 图: images/testbed.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/01_perf_baseline/images/testbed.html)
> （或本地打开 [`images/testbed.html`](images/testbed.html)）。

k6 从左右两路施压：shop（读写≈2:1）与 shorturl（跳转:创建≈9:1）；两个 SUT
共享一套 Postgres（各自独立库），Redis 本篇空载入库（项目 7 的弹药）；
压测产物经 summary-export 汇成五指标基线报告。

## 3. 快速开始

```bash
./perf_baseline.sh all      # 起栈+等健康+抽查 → 压测两轮 → 生成基线报告
./perf_baseline.sh observe  # 只重跑压测与报告（对比修复效果时用）
./perf_baseline.sh clean    # 停栈删卷，回到实验前状态
```

首跑实测（已在本机验证，2026-09）：

```
=====> [wait] 等两个 SUT 健康
✅ perf-shop 就绪: http://localhost:19331/health
✅ shorturl 就绪: http://localhost:19332/healthz
=====> [verify] 抽查种子数据与核心端点
{"items":[{"id":1,"name":"product-1","price":211.93,"stock":1000},...],"total":2}
301 -> https://example.com/long/target/1
```

## 4. 核心概念

### 4.1 基线：一切对比的原点

基线报告（`docs/baseline.md`）固定五指标：RPS / P50 / P95 / P99 / 错误率。
场景锁定 5 VU × 30s——**基线要的是稳定可复现，不是压垮**。后续每个调优
实验跑同一场景，把 P95 变化登记进报告的"后续项目登记表"。

### 4.2 实测基线（本机数据，Apple Silicon / Docker Desktop）

| 服务 | RPS | P50(ms) | P95(ms) | P99(ms) | 错误率 |
|:---|---:|---:|---:|---:|---:|
| perf-shop (FastAPI) | 43.0 | 12.8 | **130.7** | 133.5 | 0% |
| shorturl (Go) | 19.0 | 1.2 | 3.6 | 4.5 | 0% |

先自己读数据再往下看：shop 的 P50 才 12.8ms，P95 却跳到 130.7ms——**分位数
断裂**说明少数请求被某个固定开销拖住（下单路径里有一段 120ms 的串行调用，
每两次迭代触发一次，恰好锚在 P50~P95 之间）。shorturl 各分位平滑，量级也
小一个数量级——但别被表象骗了，它肚子里另有货。

### 4.3 缺陷纪律（本系列的学习方法）

- 靶场代码里的缺陷位都有 `【缺陷位之一】` 注释占位，但**是什么、为什么慢、
  怎么确认**，要靠后续实验的剖析器自己找；
- `SECRET_DEFS.md` 是答案册：破案前不看，破案后对照归因是否成立；
- 每次修复跑 `observe`，用数据说话——这也是清单验收标准的一部分。

### 4.4 易错点（本实验踩过的真坑）

- **postgres 健康检查不能只用 `pg_isready`**：TCP 就绪时 init 脚本可能还没
  跑完，下游会 load 到空表。本实验用"种子 count 查询"当健康信号。
- **init 脚本以 `POSTGRES_USER` 身份执行**：给第二个服务建的库，表 owner
  也是 shop 角色——记得 `ALTER TABLE ... OWNER TO`，且别吞 `rows.Err()`，
  否则权限错误会伪装成"0 行数据"。
- **端口冲突**：本机 893x 已被 OrbStack 的端口转发占用，宿主侧改用 1933x。
  装了多套 Docker 运行时（OrbStack/Docker Desktop）时先 `lsof -iTCP` 查占位。

## 5. 关键参数

```bash
# compose：shop/shorturl 的环境变量里藏着连接串与并发参数（项目 8 的旋钮）
DATABASE_URL=postgres://shop:shop@postgres:5432/shop
# k6：summaryTrendStats 决定导出哪些分位；BASE 切换被测目标
BASE=http://localhost:19331 k6 run --summary-export reports/smoke_shop.json k6/smoke_shop.js
```

## 6. 文件结构

```
01_perf_baseline/
├── README.md
├── perf_baseline.sh        # 主脚本：apply / observe / clean
├── docker-compose.yml      # postgres + redis + 双 SUT，健康检查含种子校验
├── SECRET_DEFS.md          # 🔞 缺陷答案册（破案前勿看）
├── gen_report.py           # summary-export JSON → 五指标基线报告
├── shop/                   # FastAPI SUT（缺陷 D1-D3 + 缺索引 D7 的库表）
│   ├── Dockerfile / requirements.txt
│   └── app/main.py
├── shorturl/               # Go SUT（缺陷 D4-D6，vendor 目录免外网构建）
│   ├── Dockerfile / go.mod / main.go / vendor/
├── db/init/                # 建库建用户 + schema + 种子（00/01/02 按序执行）
├── k6/                     # smoke_shop.js / smoke_shorturl.js
├── docs/baseline.md        # 基线报告（observe 重新生成）
├── reports/                # k6 原始导出 JSON
└── images/                 # 图三件套（json 图源 / html 交互版 / svg 内嵌版）
```

## 7. 深入要点

- **Q: 基线为什么固定 5 VU 而不是压满？** 基线的职责是提供可复现的对照系；
  压满会撞拐点，抖动放大，修复效果淹没在噪声里。找拐点是另一场景（项目 2）。
- **Q: P50 正常但 P95 断崖，说明什么？** 少数请求吃到了固定开销或排队：
  慢下游调用、锁等待、GC 停顿。分位数形态本身就是第一层归因。
- **Q: 压测机与 SUT 同机会怎样？** 相互抢 CPU，绝对值失真但趋势可用；
  严肃结论要分机或至少记录资源曲线（项目 3 的监控栈就是为此）。
- **Q: 为什么一个靶场要两种语言？** 性能问题与运行时模型强相关：GIL 下的
  CPU 热点、goroutine 泄漏、锁竞争的表现与排查工具完全不同，双语言逼你
  掌握两套剖析方法论。

## 8. 总结

靶场立起来了：一套 compose 拉起双 SUT + 双存储，k6 冒烟产出五指标基线，
shop 的分位数断裂已经把第一条线索递到你手上。下一站项目 2「负载建模」——
换开放模型再压一次，看 Coordinated Omission 怎么骗过封闭模型的延迟统计。
