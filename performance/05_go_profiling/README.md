# 05 · Go 剖析（pprof）：1025 次分配的一次性手术

> Python 世界的剖析靠采样器旁路观测，Go 更进一步：runtime 自带 profiler，
> 一个 HTTP 端点就是观测面。本实验对 shorturl 重复项目 04 的闭环——
> pprof top 定位 → benchmark 判决 → 修复重建 → 同尺复测。结果：
> genCode 从 79µs/1025 allocs 到 66ns/2 allocs，跳转快 32 倍。

## Background

CPU profile 回答"时间花在哪"，heap profile（`-sample_index=alloc_space`）
回答"垃圾在哪"——Go 的 GC 压力问题几乎都是分配问题：分配本身便宜
（tcmalloc 式缓存），贵在 GC 回收与缓存失效。

修复结论需要法律文书：`go test -benchmem` 的 ns/op、B/op、allocs/op
三个数字，修复前后同尺丈量——不接受"感觉快了"。

pprof 数据由 runtime 采样，性能损耗 <5%，可以常开（生产标配）——
这是 Go 相对其他语言在可观测性上的结构优势：观测面内建，
不用旁路工具。

## What

pprof 是 Go runtime 内建的性能剖析器：CPU profile 每 10ms（默认 100Hz）
对运行中的 goroutine 采样一次用户态栈，聚合出自我时间/累计时间；
heap profile 记录分配点与分配量。

可以把 pprof 想成程序的"自报家门"：不用外部探头，程序自己每 10ms
记一笔"我在哪"、每次分配记一笔"我生了多少"——观测者只要去
`/debug/pprof/*` 端点取账本。但和自报家门不同的是，账本是采样汇总的
统计结果，不是全量流水——所以开销才低到可以常开。

**两条独立的轴**。CPU/延迟问题和内存分配问题是两个独立维度：
实测里 Redirect 修复后快 32 倍但 allocs 不变——profile 要分开看，
别用一个指标替代另一个。

## When to Use

典型场景：

- 热循环定位：CPU profile top 里调用方自动站队（本实验三个 fmt 函数
  全指向 `main.genCode`）。
- GC 压力治理：alloc_space 视角找分配风暴（1025 allocs → 2）。
- 修复判决：`go test -benchmem` 前后同尺，三个数字说话。

何时不用：查内存泄漏用 inuse_space 而不是 alloc_space（项目 9 的 OOM
视角）；锁竞争问题 CPU profile 看不见，要看 block/mutex profile。

实测判决（本机数据，Apple M5 Pro）：

| 基准 | ns/op | B/op | allocs/op |
|:---|---:|---:|---:|
| GenCode（修复前） | 79,112 | 555,480 | **1025** |
| GenCode（修复后） | 66 | 55 | **2** |
| Redirect（修复前） | 3,702 | 160 | 2 |
| Redirect（修复后） | 116 | 160 | 2 |

## Quick Start

前置条件：项目 01 靶场栈运行中；本机 Go 工具链（`go tool pprof` 与
`go test`）。

```bash
cd performance/05_go_profiling
./go_profiling.sh all      # pprof 抓取 → bench → 修复重建 → 复测 → 对比报告
./go_profiling.sh restore  # 恢复缺陷原版（复跑教学用）
cat docs/pprof_analysis.md
```

pprof 归因实录：CPU profile 里三个函数自动站队——`fmt.(*pp).doPrintf`、`fmt.Sprintf`、`runtime.concatstring2`，调用方全是 `main.genCode`（缺陷 D5：热循环里 1024 次 Sprintf 拼字符串）。

alloc_space 同样指向它。修复：byte slice 一次分配到底，1025 allocs → 2。


Redirect 的 3702ns 来自 5000 条短链的线性扫描（缺陷 D4）：map 化后
116ns，**快 32 倍但 allocs 不变**。全局锁（缺陷 D6）在单实例 benchmark
里不可见——它要并发负载才现形，本项目用 RWMutex 直接治理。

诚实预期：`docker compose up -d` **不会重建镜像**——改了 Go 代码先
`--build`，否则 pprof 抓的是旧二进制（本实验踩过：pprof 端点 404 才
发现）。bench 的 `-run XXX` 必须加：默认 `go test` 会先跑单元测试污染
计时。

关键参数（这段在做什么：抓取、分配视角、判决书三个入口）：

```bash
# 25 秒 CPU profile（负载期间抓）
go tool pprof -top -seconds 25 -output reports/cpu.txt http://localhost:19332/debug/pprof/profile
# 分配视角（不是 in_use，是累计分配）
go tool pprof -top -sample_index=alloc_space -output reports/heap.txt .../debug/pprof/heap
# 判决书
go test -bench . -benchmem -run XXX -count 1
```

## How It Works

**远程 pprof 的符号化**。

`go tool pprof http://localhost:19332/debug/pprof/profile`会自动：拉 profile → 访问 `/debug/pprof/symbol` 补符号 → 输出可读栈——所以**不需要**把容器里的二进制拷出来。

加 `-http=:8080` 还能打开交互火焰图。


**为什么 1025 allocs 只花 79µs**。分配本身便宜，贵在 GC 回收与缓存
失效——分配风暴的伤害常在 profile 的 GC 函数里，而不在业务函数里。
这就是为什么 alloc_space（累计分配视角）比 inuse_space（存活对象视角）
更适合查 GC 压力。

**单实例看不见的问题**。全局锁竞争在高并发下才显著——CPU/heap profile
都照不出它。下一层工具是 block/mutex profile
（`/debug/pprof/mutex`，配合 `runtime.SetMutexProfileFraction` 开启采样），
或直接并发负载压出来。

## Pitfalls & Q&A

踩坑清单：

- **改了代码没重建镜像**。现象：pprof 端点 404 或数据是旧行为
  （本实验踩过）。解法：`docker compose up -d --build`。
- **bench 忘了 `-run XXX`**。现象：计时被单元测试污染。
  解法：只跑基准，`-count 1` 防缓存。
- **用 allocs/op 当速度指标**。现象：Redirect 分配没变却快了 32 倍，
  数字对不上直觉。解法：分配数与延迟是两根轴，分开报告。
- **alloc_space 和 inuse_space 混用**。查 GC 慢用前者（累计分配），
  查 OOM 用后者（存活对象），别拿错视角。

深入问答：

- **Q：pprof 的 CPU profile 原理？**
  runtime 每 10ms（默认 100Hz）对运行中的 goroutine 采样一次用户态栈，
  聚合出自我时间/累计时间——采样式，开销极低。
- **Q：alloc_space 和 inuse_space 的区别？**
  前者是累计分配（GC 压力视角），后者是存活对象（内存泄漏视角）。
  查 GC 慢用前者，查 OOM 用后者（项目 9）。
- **Q：为什么 1025 allocs 只花 79µs？**
  分配本身便宜（tcmalloc 式缓存），贵在 GC 回收与缓存失效——
  分配风暴的伤害常在 profile 的 GC 函数里，而不在业务函数里。
- **Q：mutex profile 什么时候看？**
  锁竞争在高并发下才显著：`/debug/pprof/mutex` 记录持锁等待，
  配合 `runtime.SetMutexProfileFraction` 开启采样。
