# 04 · Python 热点剖析：火焰图拍案发现罪，P95 从 132ms 到 11.6ms

> 监控曲线把嫌疑指向"等待而非算力"，但曲线到不了函数级。py-spy 直接对
> 运行中的进程采样，画出谁在消耗线程——本实验对靶场 shop 做一次完整的
> 「采样 → 归因 → 修复 → 对比」闭环，三处缺陷一网打尽，P95 **-91%**。

## Background

监控告诉你"慢"，剖析器告诉你"**哪一行**慢"——没有这一步，
修复全凭猜。性能优化的失败案例大多始于"觉得是这里"而不是
"火焰图说是这里"。

Python 的剖析有两条轴：**CPU 上的**（纯计算热点）和 **off-CPU 的**（sleep 占线程、数据库 RTT——Round-Trip Time，一次网络往返耗时——等待）——后者在传统 CPU 剖析里完全隐形。

py-spy 的 `--idle` 一次抓全两条轴，且采样式零侵入可挂生产进程，这是它比 cProfile 适合生产的原因。


修复必须同场景复测：改前改后各跑一遍 5 VU 基线，数字才是判决书——
"感觉快了"不是工程结论。

## What

火焰图（flame graph）是剖析结果的可视化：x 轴是采样占比（不是时间），
y 轴是调用栈深度；**平顶（宽而浅的框）即热点**。

可以把 py-spy 想成给进程做的"时间透视"：每隔 20ms 偷看一眼每个线程正在执行哪个函数，几千次快照叠起来，谁最占时间一目了然。

但和透视不同的是，它必须加 `--idle` 才能看见"睡着"的线程（sleep、DB 等待）——不加的话 sleep 和 DB 等待全部隐形，火焰图会"看起来很健康"。


本实验的采集方式：k6 对容器化 shop 施压的同时，py-spy 在一个
**共享 PID namespace 的伴生容器**里采样（macOS 对跨进程读内存有 SIP
保护、py-spy 必须 root，借 Linux 侧绕开）；
火焰图点名的热点函数对照 SECRET_DEFS 修复，重建镜像后再测一轮。

## When to Use

典型场景：

- 生产进程的诊断：py-spy 挂上去采样 50 秒，零停机拿到热点画像。
- off-CPU 排查：延迟高但 CPU 低时（项目 03 联动曲线的"等待"形态），
  `--idle` 抓 sleep/DB 等待。
- 修复验证：改前改后同场景基线对比，P95 变化即判决。

何时不用：线下精测单函数性能时 cProfile 的统计式数据更细
（每函数调用次数/累计时间）；非 Python 栈走对应剖析器（项目 05 pprof）。

实测：三处缺陷一网打尽（本机数据，5 VU 基线场景）：

| 口径 | RPS | P50(ms) | P95(ms) | 错误率% |
|:---|---:|---:|---:|---:|
| 修复前 | 26.6 | 14.0 | 131.9 | 1.6 |
| 修复后 | 30.2 | 5.2 | **11.6** | 1.2 |
| **变化** | 1.14x | | **P95 -91%** | |

## Quick Start

前置条件：项目 01 靶场栈运行中；py-spy wheel 已离线预下载
（`.py-spy-pkgs/`，剖析流程零外网依赖）。

```bash
cd performance/04_python_profiling
./profile_python.sh all      # 剖析 before → 修复重建 → 剖析 after → 对比报告
./profile_python.sh restore  # 恢复带缺陷原版（复跑教学用）
open docs/analysis.md reports/flame_before.svg
```

火焰图怎么读（本实验的归因实录）——`flame_before.svg` 里三个嫌疑犯
自动站队（宽度=占用比例）：

- **`recommend_score` → `hashlib.md5`**：纯 CPU 热点，20000 次迭代/请求
  （缺陷 D2）——修复：打分是派生数据，启动时预计算入库，请求路径零 CPU；
- **`create_order` → `time.sleep`**：off-CPU 但占线程，120ms/单串行
  （缺陷 D3）——修复：砍掉假风控；真实场景应消息队列异步化；
- **`psycopg` 的 51 次 RTT**：列表页每行商品单独查库存（缺陷 D1）——
  修复：一条 LEFT JOIN。

诚实预期：修复后应 P95 11.6ms（-91%）；但"能直接上线吗"要看语义——
sleep 缺陷移除等于砍掉一段"风控"业务语义，性能修复必须与业务方确认
语义等价（异步化才是风控的正确解法）。

关键参数（这段在做什么：伴生剖析容器的核心一行）：

```bash
docker run --rm --pid=container:$SHOP_CONTAINER --cap-add SYS_PTRACE \
  python:3.13-slim bash -c "pip install --no-index --find-links /pkgs py-spy \
  && py-spy record --pid 1 --idle --duration 50 --rate 50 --format flamegraph -o /out/flame.svg"
```

## How It Works

**伴生容器的原理**。

剖析对象是**容器里的 shop**：伴生容器`--pid=container:shop` 共享目标容器的 PID namespace（进程编号空间），`--cap-add SYS_PTRACE` 授予跨进程读栈的权限——之后 `py-spy --pid 1`直接采样目标进程。

macOS 侧 SIP 挡路，Linux 侧容器绕开。


**离线安装**。py-spy 的 wheel 离线预下载
（`pip download --platform manylinux2014_aarch64`），容器内 `--no-index`
安装——剖析流程不依赖外网，可复现。

**归因→修复的对照纪律**。火焰图点名的是"哪一行占时间"，
SECRET_DEFS 告诉你"这是哪号缺陷"——两者对上才动手修；
修完必须同场景（5 VU × 30s）复测，前后数字进 `docs/analysis.md`。

## Pitfalls & Q&A

踩坑清单：

- **宿主机端口被假监听占住**。现象：health 检查的 curl 永远等不到超时
  （本实验踩过：脚本卡死 40 分钟）。原因：OrbStack 的假监听。
  解法：curl 必须 `--max-time`。
- **postgres 重建后连接池是尸体**。现象：池里的旧连接全断，请求 500。
  解法：重启 SUT 清池，或给池开健康检查。
- **忘了 `--idle`**。现象：火焰图"看起来很健康"，sleep 与 DB 等待隐形。
  解法：off-CPU 排查必加 `--idle`。
- **只看数字不看语义**。现象：P95 -91% 但砍掉了业务功能。
  解法：性能修复与业务方确认语义等价。

深入问答：

- **Q：py-spy 和 cProfile 怎么选？**
  py-spy 采样式、零侵入、可挂生产进程、能看 off-CPU；cProfile 统计式、
  有 30%+ 开销、只能看单进程函数调用。线上用 py-spy，线下精测用 cProfile。
- **Q：火焰图为什么是"倒置的"？**
  x 轴是采样占比不是时间，y 轴是调用栈深度；平顶（宽而浅的框）即热点。
  off-CPU 栈要 `--idle` 才可见。
- **Q：GIL 会让 py-spy 失真吗？**
  py-spy 抓的是原生线程栈，C 扩展（如 psycopg 的 C 层等待）也能看到；
  GIL 只影响 Python 字节码并行度，不影响"谁占着线程"。
- **Q：修复后 P95 -91%，能直接上线吗？**
  不能只看数字：sleep 缺陷移除等于砍掉了一段"风控"业务语义
  ——性能修复必须与业务方确认语义等价（异步化才是风控的正确解法）。
