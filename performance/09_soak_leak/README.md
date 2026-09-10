# 09 · 浸泡测试与内存泄漏定位：让时间揭发短压测看不见的问题

> 前面所有实验都是"分钟级"的——有一类问题专门躲在时间维度里：每次请求漏
> 64KB，任何 60 秒压测都看不出来，生产上却是三天一次 OOM 重启。本项目给
> shorturl 装上泄漏注入开关（`LEAK_MODE=heap|goroutine`），用加速配方
> （大泄漏率 + 短窗口）复现 RSS 单调爬升，再用 **pprof heap 差分**把泄漏
> 钉到函数级：`main.maybeLeak`，+1151.92MB。

## 1. 为什么需要它

- 功能测试与短压测都测不出泄漏：它不改变响应正确性，分钟内延迟也正常——
  只有 RSS 随时间**单调爬升不回落**这一个指纹；
- 修复的价值不在"知道有泄漏"（OOM 重启早就告诉你了），而在**定位到哪一行**：
  heap 差分给出的是函数名，不是猜测。

## 2. 总览：加速配方的浸泡闭环

<!-- 图: images/soak.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/09_soak_leak/images/soak.html)
> （或本地打开 [`images/soak.html`](images/soak.html)）。

30 VU 持续跳转 7 分钟，每 10s 采 RSS/goroutines；第 2 分钟与第 5 分钟各抓
一份 heap profile，alloc_space 差分定位新增分配；切回 LEAK_MODE=off 同配方
复测，曲线平台化即闭环。

## 3. 快速开始

```bash
SOAK_LEAK_SEC=420 ./soak_leak.sh all   # 泄漏段 7 分钟 + 修复验证 4 分钟
./soak_leak.sh clean                   # 恢复 LEAK_MODE=off
open docs/soak.md
```

## 4. 核心概念

### 4.1 实测：爬升 → 定位 → 平稳（本机数据，加速配方）

| 阶段 | RSS | goroutines | 判定 |
|:---|:---|:---|:---|
| 泄漏注入（heap 模式，7min） | 667 → 1190MB（**Δ+523 单调上升**） | 稳定 40-70 | 泄漏实锤 |
| heap 差分 | `main.maybeLeak` **+1151.92MB** | — | 函数级定位 |
| 修复后（off，4min） | 21 → 26MB，尾部极差 1MB | 恒定 38 | 平稳 ✓ |

泄漏的指纹是**斜率**而不是绝对值：Go runtime 会周期性归还内存给 OS，
RSS 曲线呈锯齿状——看趋势线（线性回归/首尾差）而不是单点。

### 4.2 两类泄漏，两个仪表

- **堆泄漏**（本实验）：看 `process_resident_memory_bytes` 趋势 +
  `/debug/pprof/heap` 的 alloc_space 差分；
- **goroutine 泄漏**：RSS 可能几乎不动，`go_goroutines` 却单调上升——
  每 request 孵一个阻塞在 channel 上的 goroutine 就是这种。两个仪表都要看。

### 4.3 差分的正确姿势

- `-diff_base` 要的是**原始 profile**（curl 直接抓的 .pb.gz），不能喂
  `pprof -top` 的文本报告（报 "unrecognized profile format"）；
- 两次采样间隔 2-3 分钟足够：泄漏率大时差分值一眼可见；
- 差分要过滤 GC 噪音：只看持续为正的业务函数，`runtime.*` 的波动忽略。

### 4.4 易错点（本实验真踩）

- **`mkdir -p reports` 忘了写**：pprof 输出到不存在目录，`set -e` 静默
  exit 2，日志只有 3 行——后台长任务的静默失败，要靠中间产物（样本文件）
  判断进度；
- **采样函数在子 shell 里不可用**：编排脚本时函数定义不会自动跟过去；
- **预热爬坡 ≠ 泄漏**：新进程 RSS 前 4 分钟从 8 涨到 38MB 是 runtime
  暖机，判据要看**尾部平台化**（尾 5 样本极差 <5MB），不是首尾差。

## 5. 关键参数

```bash
# 加速配方：泄漏率调大（64KB/请求 × 30VU），7 分钟即出肉眼可见的爬升
LEAK_MODE=heap docker compose up -d --build shorturl
# 差分：原始 profile 相减
curl -s http://localhost:19332/debug/pprof/heap -o t0.pb.gz
sleep 120 && curl -s .../heap -o t1.pb.gz
go tool pprof -top -sample_index=alloc_space -diff_base=t0.pb.gz t1.pb.gz
```

## 6. 文件结构

```
09_soak_leak/
├── README.md
├── soak_leak.sh           # prereq/soak/diff/report/clean（all 含修复验证）
├── gen_soak_report.py     # 样本/差分 → docs/soak.md
├── reports/               # soak_*_samples.txt、heap_t0/t1.pb.gz、heap_diff.txt
├── docs/soak.md           # 证据报告（验收物）
└── images/                # 图三件套
```

泄漏开关本体在 `../01_perf_baseline/shorturl/main.go` 的 `maybeLeak()`
（LEAK_MODE 环境变量，默认 off）。

## 7. 面试要点

- **Q: 浸泡测试时长怎么定？** 看泄漏率与告警阈值的乘积：泄漏率越小微象，
  越要长窗口。加速配方的思想是把泄漏率调大换时间，**趋势形状**才是判据。
- **Q: RSS 上涨就是泄漏吗？** 不是：runtime 暖机、缓存增长、GC 未归还
  都会涨。判据是"不回落 + 持续线性"且排除业务缓存（本系列的缓存就是
  合法的内存增长）。
- **Q: Go 里怎么区分堆泄漏和 goroutine 泄漏？** 两根曲线：RSS 涨 +
  goroutines 平 = 堆；RSS 平 + goroutines 涨 = goroutine 泄漏
  （pprof goroutine profile 直接看阻塞在哪个 channel）。
- **Q: 差分为什么比单次 heap 快照强？** 快照里满屏都是"正常分配"，
  差分把两次采样之间**新增**的分配顶到最前面——泄漏函数自己浮出水面。

## 8. 总结

7 分钟的加速浸泡让 RSS 爬了 523MB，heap 差分直接点名 `main.maybeLeak`，
修复后同配方曲线平台化——泄漏定位从"三天一次 OOM 的玄学"变成了
"半小时的流水线"。下一篇就是终点🏁：项目 10 把全部 9 个实验的结论串成
性能回归门禁 + 容量评估报告。
