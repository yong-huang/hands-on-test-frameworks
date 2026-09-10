# 05 · Go pprof 剖析修复对比报告

## 基准测试（go test -benchmem，同机 arm64）

| 基准 | ns/op | B/op | allocs/op | allocs 降幅 |
|:---|---:|---:|---:|---:|
| BenchmarkGenCode | 79,112 → 66 | 555,480 → 55 | 1025 → 2 | **-100%** |
| BenchmarkRedirect | 3,702 → 116 | 160 → 160 | 2 → 2 | **-0%** |

## pprof 归因（修复前）

- CPU top：fmt.(*fmt).fmtC, fmt.(*pp).doPrintf, fmt.(*pp).fmtInteger
- 火焰图级证据：`go tool pprof -http=: ` 可交互查看（reports/cpu_before.txt 为 top 文本）

## 修复动作

| 缺陷 | 修复 |
|:---|:---|
| D4 线性扫描 | slice → map，跳转 O(1) |
| D5 Sprintf 风暴 | byte slice 一次分配（1025 → 2 allocs/op） |
| D6 全局互斥锁 | RWMutex，读读不互斥 |

## 验收判定

- pprof top 定位到热点函数：**是**（见上）
- 单请求 allocs 下降 ≥40%：**通过**（GenCode 实测见上表）
