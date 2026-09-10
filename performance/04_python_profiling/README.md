# 04 · Python 热点剖析：火焰图拍案发现罪，P95 从 132ms 到 11.6ms

> 监控曲线把嫌疑指向"等待而非算力"，但曲线到不了函数级。py-spy 直接对
> 运行中的进程采样，画出谁在消耗线程——本项目对靶场 shop 做一次完整的
> 「采样 → 归因 → 修复 → 对比」闭环，三处缺陷一网打尽，P95 **-91%**。

## 1. 为什么需要它

- 监控告诉你"慢"，剖析器告诉你"**哪一行**慢"：没有这一步，修复全凭猜；
- Python 的剖析有两条轴：CPU 上的（md5 热点）和 off-CPU 的（sleep 占线程、
  数据库 RTT）——`py-spy --idle` 一次抓全，这是它比 cProfile 适合生产的原因；
- 修复必须同场景复测：改前改后各跑一遍 5 VU 基线，数字才是判决书。

## 2. 总览：剖析闭环

<!-- 图: images/profiling.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/performance/04_python_profiling/images/profiling.html)
> （或本地打开 [`images/profiling.html`](images/profiling.html)）。

k6 对容器化 shop 施压的同时，py-spy 在一个**共享 PID namespace 的伴生容器**
里采样（macOS 上 py-spy 要 root，借 Linux 侧绕开）；火焰图点名的热点函数
对照 SECRET_DEFS 修复，重建镜像后再测一轮。

## 3. 快速开始

```bash
./profile_python.sh all      # 剖析 before → 修复重建 → 剖析 after → 对比报告
./profile_python.sh restore  # 恢复带缺陷原版（复跑教学用）
open docs/analysis.md reports/flame_before.svg
```

## 4. 核心概念

### 4.1 实测：三处缺陷一网打尽（本机数据，5 VU 基线场景）

| 口径 | RPS | P50(ms) | P95(ms) | 错误率% |
|:---|---:|---:|---:|---:|
| 修复前 | 26.6 | 14.0 | 131.9 | 1.6 |
| 修复后 | 30.2 | 5.2 | **11.6** | 1.2 |
| **变化** | 1.14x | | **P95 -91%** | |

### 4.2 火焰图怎么读（本实验的归因实录）

`flame_before.svg` 里三个嫌疑犯自动站队（宽度=占用比例）：

- **`recommend_score` → `hashlib.md5`**：纯 CPU 热点，20000 次迭代/请求
  （缺陷 D2）——修复：打分是派生数据，启动时预计算入库，请求路径零 CPU；
- **`create_order` → `time.sleep`**：off-CPU 但占线程，120ms/单串行
  （缺陷 D3）——修复：砍掉假风控；真实场景应消息队列异步化；
- **`psycopg` 的 51 次 RTT**：列表页每行商品单独查库存（缺陷 D1）——
  修复：一条 LEFT JOIN。

### 4.3 为什么在容器里跑 py-spy（方法论沉淀）

- macOS 对跨进程读内存有 SIP 保护，py-spy 必须 root；
- 剖析对象是**容器里的 shop**：伴生容器 `--pid=container:shop`
  + `--cap-add SYS_PTRACE`，共享 PID namespace 后 `py-spy --pid 1`；
- py-spy 的 wheel 离线预下载（`pip download --platform manylinux2014_aarch64`），
  容器内 `--no-index` 安装——剖析流程零外网依赖。

### 4.4 易错点

- **宿主机端口可能被 OrbStack 的假监听占住**：health 检查的 curl 必须
  `--max-time`，否则永远等不到超时（本实验踩过：脚本卡死 40 分钟）；
- **postgres 重建后连接池是尸体**：池里的旧连接全断，请求 500——重启 SUT
  清池，或给池开健康检查；
- `--idle` 不加的话 sleep 和 DB 等待全部隐形，火焰图会"看起来很健康"。

## 5. 关键参数

```bash
# 伴生剖析容器（核心一行）
docker run --rm --pid=container:$SHOP_CONTAINER --cap-add SYS_PTRACE \
  python:3.13-slim bash -c "pip install --no-index --find-links /pkgs py-spy \
  && py-spy record --pid 1 --idle --duration 50 --rate 50 --format flamegraph -o /out/flame.svg"
```

## 6. 文件结构

```
04_python_profiling/
├── README.md
├── profile_python.sh        # prereq/profile/verify/fix/restore/report
├── fixes/
│   ├── shop_main.py         # 修复版（JOIN/预计算/砍 sleep）
│   └── shop_main_original.py# 缺陷原版备份（restore 用）
├── gen_analysis.py          # 前后 verify JSON → docs/analysis.md
├── .py-spy-pkgs/            # linux/arm64 py-spy wheel（离线安装）
├── reports/                 # flame_before/after.svg + verify_*.json（验收物）
├── docs/analysis.md         # 对比报告（-91% 判决书）
└── images/                  # 图三件套
```

## 7. 面试要点

- **Q: py-spy 和 cProfile 怎么选？** py-spy 采样式、零侵入、可挂生产进程、
  能看 off-CPU；cProfile 统计式、有 30%+ 开销、只能看单进程函数调用。
  线上用 py-spy，线下精测用 cProfile。
- **Q: 火焰图为什么是"倒置的"？** x 轴是采样占比不是时间，y 轴是调用栈深度；
  平顶（宽而浅的框）即热点。off-CPU 栈要 --idle 才可见。
- **Q: GIL 会让 py-spy 失真吗？** py-spy 抓的是原生线程栈，C 扩展（如 psycopg
  的 C 层等待）也能看到；GIL 只影响 Python 字节码并行度，不影响"谁占着线程"。
- **Q: 修复后 P95 -91%，能直接上线吗？** 不能只看数字：sleep 缺陷移除等于
  砍掉了一段"风控"业务语义——性能修复必须与业务方确认语义等价（异步化
  才是风控的正确解法）。

## 8. 总结

火焰图把"shop 慢"拆成了三个具体的函数名，修复后同场景 P95 从 131.9ms 到
11.6ms——这就是剖析闭环的价值。下一站项目 5，把同一套方法论带到 Go 世界：
pprof 的 CPU/heap profile 会揪出 shorturl 里的线性扫描与分配风暴。
