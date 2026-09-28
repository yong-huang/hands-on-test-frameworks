# 09 · 浸泡测试与内存泄漏定位：让时间揭发短压测看不见的问题

> 前面所有实验都是"分钟级"的——有一类问题专门躲在时间维度里：每次请求漏
> 64KB，任何 60 秒压测都看不出来，生产上却是三天一次 OOM（Out Of Memory，
> 内存耗尽后被系统杀掉进程、容器重启）重启。
> 本实验给 shorturl 装上泄漏注入开关（`LEAK_MODE=heap|goroutine`），用
> 加速配方（大泄漏率 + 短窗口）复现 RSS（Resident Set Size，进程实际占用的物理内存）单调爬升，再用 **pprof heap 差分**
> 把泄漏钉到函数级：`main.maybeLeak`，+1151.92MB。

## Background

功能测试与短压测都测不出泄漏：它不改变响应正确性，分钟内延迟也正常
——泄漏的唯一指纹是 **RSS 随时间单调爬升不回落**。生产上它以
"三天一次 OOM 重启"的节奏出现，等监控告警时问题已经存在很久。

修复的价值不在"知道有泄漏"（OOM 重启早就告诉你了），而在**定位到
哪一行**：heap 差分给出的是函数名，不是猜测。

浸泡测试（soak test）的困境是时长：真实泄漏率微小，泡三天才能看出
趋势。加速配方把等价交换反过来用：**泄漏率调大换时间缩短**——
64KB/请求 × 30 VU，7 分钟即出肉眼可见的爬升。判据不变：趋势形状。

## What

浸泡测试是持续负载下的长时间观测：30 VU 持续跳转 7 分钟，每 10s 采
RSS/goroutines；第 2 分钟与第 5 分钟各抓一份 heap profile，alloc_space
差分定位新增分配；切回 `LEAK_MODE=off` 同配方复测，曲线平台化即闭环。

可以把泄漏排查想成水池找漏：水位（RSS）持续上涨且关不掉进水阀也
不回落 = 真漏；水池刚注水时的水位上升（runtime 暖机）不是漏。
但和水池不同的是，这里还要区分"水多了"（堆泄漏）和"水管多了"
（goroutine 泄漏）——两根曲线两个仪表。

**两类泄漏，两个仪表**：

- **堆泄漏**（本实验）：看 `process_resident_memory_bytes` 趋势 +
  `/debug/pprof/heap` 的 alloc_space 差分；
- **goroutine 泄漏**：RSS 可能几乎不动，`go_goroutines` 却单调上升
  ——每 request 孵一个阻塞在 channel 上的 goroutine 就是这种。
  两个仪表都要看。

## When to Use

典型场景：

- 发版前稳定性验证：浸泡段 RSS 平台化（尾 5 样本极差 <5MB）才放行。
- OOM 事故复盘：heap 差分把"三天崩一次"钉到函数级。
- goroutine 泄漏排查：RSS 平 + goroutines 涨的组合直接对号。

何时不用：短生命周期任务（批处理跑完即退）没有泄漏累积的土壤；
已定位到具体提交的回归（二分即可）不必全量浸泡。

实测：爬升 → 定位 → 平稳（本机数据，加速配方）：

| 阶段 | RSS | goroutines | 判定 |
|:---|:---|:---|:---|
| 泄漏注入（heap 模式，7min） | 667 → 1190MB（**Δ+523 单调上升**） | 稳定 40-70 | 泄漏实锤 |
| heap 差分 | `main.maybeLeak` **+1151.92MB** | — | 函数级定位 |
| 修复后（off，4min） | 21 → 26MB，尾部极差 1MB | 恒定 38 | 平稳 ✓ |

泄漏的指纹是**斜率**而不是绝对值：Go runtime 会周期性归还内存给 OS，
RSS 曲线呈锯齿状——看趋势线（线性回归/首尾差）而不是单点。

## Quick Start

前置条件：项目 01 靶场栈运行中；本机 Go 工具链（差分要用 go tool pprof）。

```bash
cd performance/09_soak_leak
SOAK_LEAK_SEC=420 ./soak_leak.sh all   # 泄漏段 7 分钟 + 修复验证 4 分钟
./soak_leak.sh clean                   # 恢复 LEAK_MODE=off
open docs/soak.md
```

**差分的正确姿势**：`-diff_base` 要的是**原始 profile**（curl 直接抓的
.pb.gz），不能喂 `pprof -top` 的文本报告（报 "unrecognized profile
format"）。

两次采样间隔 2-3 分钟足够（泄漏率大时差分值一眼可见）；
差分要过滤 GC 噪音：只看持续为正的业务函数，`runtime.*` 的波动忽略。

关键参数（这段在做什么：加速配方与差分三板斧）：

```bash
# 加速配方：泄漏率调大（64KB/请求 × 30VU），7 分钟即出肉眼可见的爬升
LEAK_MODE=heap docker compose up -d --build shorturl
# 差分：原始 profile 相减
curl -s http://localhost:19332/debug/pprof/heap -o t0.pb.gz
sleep 120 && curl -s .../heap -o t1.pb.gz
go tool pprof -top -sample_index=alloc_space -diff_base=t0.pb.gz t1.pb.gz
```

## How It Works

**加速配方的原理**。浸泡判据是趋势形状（单调爬升/平台化），不是绝对
时长——把泄漏率调大，7 分钟的曲线形状与 3 天的小泄漏同构，
时间成本从天级压到分钟级。

**heap 差分为什么强**。单次快照里满屏都是"正常分配"，差分把两次采样
之间**新增**的分配顶到最前面——泄漏函数自己浮出水面
（`main.maybeLeak` +1151.92MB）。

**平台化判据**。修复后曲线的验收不是"没涨"而是"尾部平台化"：
尾 5 样本极差 <5MB。预热爬坡（新进程 RSS 前 4 分钟从 8 涨到 38MB 的
runtime 暖机）不是泄漏，首尾差会误判——判据要看尾部。

## Pitfalls & Q&A

踩坑清单（本实验真踩）：

- **`mkdir -p reports` 忘了写**。现象：pprof 输出到不存在目录，
  `set -e` 静默 exit 2，日志只有 3 行——后台长任务的静默失败，
  要靠中间产物（样本文件）判断进度。
- **采样函数在子 shell 里不可用**。现象：编排脚本采不到样本。
  解法：函数定义不会自动跟到子 shell，关键采样逻辑内联。
- **预热爬坡误判为泄漏**。现象：首尾差报警，实际是 runtime 暖机。
  解法：判据看尾部平台化，不看首尾差。
- **喂差分用文本报告**。现象："unrecognized profile format"。
  解法：`-diff_base` 只吃原始 .pb.gz。

深入问答：

- **Q：浸泡测试时长怎么定？**
  看泄漏率与告警阈值的乘积：泄漏率越小微象，越要长窗口。
  加速配方的思想是把泄漏率调大换时间，**趋势形状**才是判据。
- **Q：RSS 上涨就是泄漏吗？**
  不是：runtime 暖机、缓存增长、GC 未归还都会涨。判据是
  "不回落 + 持续线性"且排除业务缓存（本系列的缓存就是合法的内存增长）。
- **Q：Go 里怎么区分堆泄漏和 goroutine 泄漏？**
  两根曲线：RSS 涨 + goroutines 平 = 堆；RSS 平 + goroutines 涨 =
  goroutine 泄漏（pprof goroutine profile 直接看阻塞在哪个 channel）。
- **Q：差分为什么比单次 heap 快照强？**
  快照里满屏都是"正常分配"，差分把两次采样之间**新增**的分配顶到
  最前面——泄漏函数自己浮出水面。
