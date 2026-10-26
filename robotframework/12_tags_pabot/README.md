# 12 · 标签策略与套件编排

## Background

套件一大，就得回答三个问题：怎么只跑一小片（标签）、怎么跑得快（并行）、
失败了怎么补而不全量重跑（--rerunfailed + rebot 合并）。本实验用 7 条用例的小套件
把三个机制全部打通。

## What

- 三个套件文件打标签（smoke/api、regression/web），`--include smoke` 只筛出 2 条
- pabot 3 进程并行全量（7 条小套件：并行开销 6s vs 串行 3s——**如实标注**小套件
  下进程启动开销占主导，机制验证 ≠ 提速验证，收益随套件规模线性放大）
- 失败重跑合并：INJECT=1 注 1 红 → `--rerunfailed` 只选中那 1 条 → 修好重跑 →
  `rebot -R` 合并成 pass=7 fail=0 的统一报告

## When to Use

- CI 按标签分层（smoke 先行、regression 夜间）
- 夜间全量挂了几条时的补跑：只重跑失败的，合并进主报告

## Quick Start

```bash
cd robotframework/12_tags_pabot
./12_tags_pabot.sh            # 三项验收 ✅
```

实测输出（2026-10-27，节选）：

```text
smoke 标签筛出 2 条，全过
首轮：pass=6 fail=1（注入 1 条预期红）
重跑：--rerunfailed 只选中失败用例（1 条，全部通过）
合并后：pass=7 fail=0
✅ 标签选择 / 并行机制 / 重跑合并 三项验收通过
```

## How It Works

- `Force Tags` 套件级打标；`--include/--exclude` 按标签筛
- pabot 按套件粒度分发给 N 个进程，各写独立 output 再自动汇总
- 合并语义：`rebot -R orig.xml rerun.xml`——**orig 在前**，rerun 的结果覆盖 orig 里的同名用例

## Pitfalls & Q&A

- **坑：pabot 子进程找不到 robot**——pabot 以 `robot` 命令派生 worker，PATH 里必须有
  venv/bin（脚本 export 解决）
- **坑：`rebot -R` 的参数顺序**——rerun 在前会以失败结果覆盖成功（实测 pass=6 fail=1）；
  官方语义 `rebot --merge orig.xml rerun.xml`，orig 永远在前
- **坑：`python -m rebot` 不存在**——rebot 是独立可执行文件（venv/bin/rebot），不是模块入口
- **Q：小套件并行反而慢正常吗？** 正常：每进程要起 Python + 浏览器，7 条用例撑不起；
  并行调优要在 ≥50 条的套件上做（对照 architect/11 的 246 条口径）
