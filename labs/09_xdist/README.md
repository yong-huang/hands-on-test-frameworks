# 09 · 并行与分层：把 11.8 秒压到 1.9 秒，还要会切分层跑

> 套件一慢，就没人愿意跑——慢是测试最大的敌人。pytest-xdist 用多进程并行把
> 时间除以核心数，但并行是**独立性的照妖镜**：共享状态、顺序依赖全都会当场现形。
> 本实验用 200 条真实用例跑出 6 倍加速，并亲手翻车一次"污染"反面教材。

## 1. 为什么需要它

- 反馈速度决定测试的存活率：11.8s 与 1.9s 是"愿意每次保存都跑"与"懒得跑"的区别。
- `-m` marker 分层让 CI 里 push 跑冒烟（0.3s）、定时跑全量——分层也是提速。
- `--durations` 定位慢用例，优化先找大头。

## 2. 总览：主进程分派，worker 各自为政

<!-- 图: images/xdist.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/09_xdist/images/xdist.html)
> （或本地打开 [`images/xdist.html`](images/xdist.html)）。

主进程收集用例 → 分发给 N 个 worker 进程 → 各自执行、各自回传结果 → 汇总。
**每个 worker 是独立进程**——这就是模块级共享状态翻车的根源（看 4.2）。

## 3. 快速开始

```bash
./xdist_lab.sh            # 全流程：串行基线 → 并行对比 → 污染演示 → 修复 → 分层
./xdist_lab.sh observe
```

实测（M 系 MacBook，-n auto）：

| 步骤 | 耗时 |
|:---|:---|
| ① 串行 200 条 50ms 用例 | 11.8s |
| ② `-n auto` 同一批用例 | 1.9s（≈6.2x） |
| ⑤ `-m smoke` 冒烟子集 | 0.3s |

## 4. 核心概念

### 4.1 `-n auto` 与结果一致性

`-n auto` 按核心数起 worker；用例独立时，并行结果与串行**逐条一致**（本实验 ① ②
同为 200 passed）。worker 间没有共享内存——fixture 的 session 作用域也退化为
"每 worker 一次"。

### 4.2 独立性照妖镜：共享计数器翻车实录

`tests/test_pollution.py` 的三条用例共享模块级计数器，断言"我是第 N 个跑的"。
串行按文件顺序恰好全绿；`-n auto` 下每个 worker 的计数器独立从 0 起——
**2 failed, 1 passed，当场翻车**（脚本 ③ 步真实触发）。修复版用 function 级
fixture 各发各的计数器，并行全绿。教训一句话：**用例只许依赖 fixture 给的，
不许依赖"谁先跑"。**

### 4.3 marker 分层

```ini
markers = smoke: 秒级冒烟子集   e2e: 较慢的端到端
```

`-m smoke` 只跑打了标的子集；未注册的 marker 会告警（本实验修过一回
`slow_work` 未注册的 warning——这就是注册的意义）。CI 经典搭配：
push 跑 `-m smoke`，夜间跑全量。

### 4.4 --durations 找慢用例

`--durations=3` 列出最慢的 3 条。注意 `-q` 会吞掉 durations 表——
用 `-o addopts=""` 还原（脚本 ⑥ 步的注释就是这个坑）。

### 4.5 易错点

- 并行下"恰好全绿"不等于安全——顺序只是被文件顺序掩护，换台机器就爆。
- xdist 下 print 交错难读，调试用 `-n 0`（xdist 装上后 0 = 禁用并行）。
- 有副作用的用例（写同一个文件/端口）并行必然打架，一律 fixture 化或 tmp 隔离。

## 5. 关键参数

```bash
pytest -n auto            # 按核心数并行
pytest -n 4 --dist load   # 指定 worker 数（默认 load：按用例分发）
pytest -m smoke           # 分层选跑
pytest --durations=5      # 慢用例榜
```

## 6. 文件结构

```
09_xdist/
├── README.md
├── xdist_lab.sh              # 主演示脚本（含实测耗时输出）
├── configs/pytest.ini        # marker 注册（smoke/e2e/slow_work）
├── pollution.py              # 反面教材的共享计数器
├── tests/
│   ├── test_workload.py      # 200 条 50ms 用例（并行加速素材）
│   ├── test_pollution.py     # 污染三连（并行下预期红）
│   └── test_pollution_fixed.py  # 修复版（并行绿）
└── images/
```

## 7. 深入要点

- **Q: 什么样的套件不能直接并行？** 有共享可变状态、顺序依赖、外部资源竞争
  （同端口/同文件/同数据库行）的——先独立化再并行。
- **Q: xdist 下 session fixture 执行几次？** 每 worker 一次，不是全程一次；
  昂贵且可共享的资源考虑外置（独立服务/容器）。
- **Q: 还有哪些提速手段？** 按时长排序分发（--dist loadscope/loadgroup）、
  慢用例优化、分层选跑、按改动圈选（pytest-testmon 类）。

## 8. 总结

快，而且绿得干净。下一篇 [10_plugin](../10_plugin/README.md)：
把这两周沉淀的套路封装成你自己的 pytest 插件。
