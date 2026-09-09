# 35 · Go 剖析（pprof）：1025 次分配的一次性手术

> Python 世界的剖析靠采样器旁路观测，Go 更进一步：runtime 自带 profiler，
> 一个 HTTP 端点就是观测面。本项目对 shorturl 重复 lab 34 的闭环——
> pprof top 定位 → benchmark 判决 → 修复重建 → 同尺复测。结果：
> genCode 从 79µs/1025 allocs 到 66ns/2 allocs，跳转快 32 倍。

## 1. 为什么需要它

- CPU profile 回答"时间花在哪"，heap profile（`-sample_index=alloc_space`）
  回答"垃圾在哪"——Go 的 GC 压力问题几乎都是分配问题；
- `go test -benchmem` 是剖析结论的**法律文书**：ns/op、B/op、allocs/op
  三个数字，修复前后同尺丈量，不接受"感觉快了"；
- pprof 数据由 runtime 采样，性能损耗 <5%，可以常开（生产标配）。

## 2. 总览：观测面与闭环

<!-- 图: images/goprofiling.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/35_go_profiling/images/goprofiling.html)
> （或本地打开 [`images/goprofiling.html`](images/goprofiling.html)）。

k6 从左侧施压；`/debug/pprof/profile`（CPU）与 `/debug/pprof/heap`（分配）
被 `go tool pprof` 拉走分析；`go test -benchmem` 在宿主机给出独立判决；
三处缺陷（线性扫/Sprintf 风暴/全局锁）逐一对号修复。

## 3. 快速开始

```bash
./go_profiling.sh all      # pprof 抓取 → bench → 修复重建 → 复测 → 对比报告
./go_profiling.sh restore  # 恢复缺陷原版（复跑教学用）
cat docs/pprof_analysis.md
```

## 4. 核心概念

### 4.1 实测判决（本机数据，Apple M5 Pro）

| 基准 | ns/op | B/op | allocs/op |
|:---|---:|---:|---:|
| GenCode（修复前） | 79,112 | 555,480 | **1025** |
| GenCode（修复后） | 66 | 55 | **2** |
| Redirect（修复前） | 3,702 | 160 | 2 |
| Redirect（修复后） | 116 | 160 | 2 |

### 4.2 pprof 归因实录

CPU profile 里三个函数自动站队：`fmt.(*pp).doPrintf`、`fmt.Sprintf`、
`runtime.concatstring2`——调用方全是 `main.genCode`（缺陷 D5：热循环里
1024 次 Sprintf 拼字符串）。alloc_space 同样指向它。修复：byte slice 一次
分配到底，1025 allocs → 2。

Redirect 的 3702ns 来自 5000 条短链的线性扫描（缺陷 D4）：map 化后 116ns，
**快 32 倍但 allocs 不变**——这解释了为什么 CPU/延迟问题和内存分配问题是
两个独立的轴，profile 要分开看。

全局锁（缺陷 D6）在单实例 benchmark 里不可见，它要并发负载才现形——
pprof 的 block/mutex profile 是下一层工具，本项目用 RWMutex 直接治理。

### 4.3 远程 pprof 的符号化

`go tool pprof http://localhost:19332/debug/pprof/profile` 会自动：
拉 profile → 访问 `/debug/pprof/symbol` 补符号 → 输出可读栈。
所以**不需要**把容器里的二进制拷出来。加 `-http=: ` 还能打开交互火焰图。

### 4.4 易错点

- **`docker compose up -d` 不会重建镜像**：改了 Go 代码先 `--build`，
  否则 pprof 抓的是旧二进制（本实验踩过：pprof 端点 404 才发现）；
- bench 的 `-run XXX` 必须加：默认 `go test` 会先跑单元测试污染计时；
- allocs/op 低不代表快：Redirect 分配没变但快了 32 倍——**分配数与延迟
  是两根轴**，别用一个指标替代另一个。

## 5. 关键参数

```bash
# 30 秒 CPU profile（负载期间抓）
go tool pprof -top -seconds 25 -output reports/cpu.txt http://localhost:19332/debug/pprof/profile
# 分配视角（不是 in_use，是累计分配）
go tool pprof -top -sample_index=alloc_space -output reports/heap.txt .../debug/pprof/heap
# 判决书
go test -bench . -benchmem -run XXX -count 1
```

## 6. 文件结构

```
35_go_profiling/
├── README.md
├── go_profiling.sh         # prereq/pprof/bench/fix/restore/report
├── fixes/
│   ├── main_original.go    # 缺陷版备份（slice 线性扫 + Sprintf 风暴 + Mutex）
│   └── main_fixed.go       # 修复版（map + byte-slice + RWMutex）
├── gen_pprof_report.py     # bench/pprof 文本 → docs/pprof_analysis.md
├── reports/                # cpu/heap top 文本 + bench_before/after.txt
├── docs/pprof_analysis.md  # 对比报告（验收物）
└── images/                 # 图三件套
```

## 7. 面试要点

- **Q: pprof 的 CPU profile 原理？** runtime 每 10ms（默认 100Hz）对运行中的
  goroutine 采样一次用户态栈，聚合出自我时间/累计时间——采样式，开销极低。
- **Q: alloc_space 和 inuse_space 的区别？** 前者是累计分配（GC 压力视角），
  后者是存活对象（内存泄漏视角）。查 GC 慢用前者，查 OOM 用后者（项目 9）。
- **Q: 为什么 1025 allocs 只花 79µs？** 分配本身便宜（tcmalloc 式缓存），
  贵在 GC 回收与缓存失效——分配风暴的伤害常在 profile 的 GC 函数里，
  而不在业务函数里。
- **Q: mutex profile 什么时候看？** 锁竞争在高并发下才显著：`/debug/pprof/mutex`
  记录持锁等待，配合 `runtime.SetMutexProfileFraction` 开启采样。

## 8. 总结

pprof 把 shorturl 的三处缺陷钉死在函数级，benchmark 给出 1025→2 的判决。
双语言剖析闭环到此打通：Python 靠旁路采样，Go 靠 runtime 自报家门——
方法论一致，工具各有性格。下一篇项目 6「数据库性能」，下潜到 EXPLAIN
ANALYZE 的世界，揪出最后一个藏在 schema 里的缺陷 D7。
