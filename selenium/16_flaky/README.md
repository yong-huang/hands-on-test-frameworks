# 16 · flaky 稳定性治理

## Background

flaky 用例是回归套件的信任杀手：狼来了三次之后，没人再看红灯。
治理闭环 = **检出**（多轮重跑找不一致）→ **隔离**（进隔离区不挡主干）→ **复验**（隔离后主干全绿）。
本实验在靶场外搭了一个纯 pytest 的小池子，植入 2 个 flaky，把闭环跑通（对照 architect/13）。

## What

- 植入池 `tests/`：`test_random_flake`（40% 随机失败）+ `test_order_dependent_victim`
  （首轮通过并泄漏 `.shared_state`，之后每轮必挂）+ 2 条稳定对照
- `hunt.py`：20 轮重跑收集结果 → 不一致者自动写入 `quarantine.txt` → 10 轮确认主干全绿
- 隔离机制：`tests/conftest.py` 按 nodeid 子串自动 skip
- 产物：`reports/flaky.json`（逐轮结果可追溯）+ `quarantine.txt`

## When to Use

- 主干套件出现「时红时绿」时，先用多轮重跑定位不一致用例
- 摘牌流程：修完 flaky 根因后，从 quarantine.txt 删除条目恢复监视（对照 architect/13 的摘牌）

## Quick Start

```bash
cd selenium/16_flaky
./16_flaky.sh            # 治理闭环 1 passed（约 12s，纯 pytest 池不驱动浏览器）
cat tests/quarantine.txt # 查看隔离区
```

实测输出（2026-10-26，节选）：

```text
检出 2 条 flaky：[...test_order_dependent_victim, ...test_random_flake]
稳定对照零误报：True；隔离后 10 轮失败数：0
1 passed in 12.39s
```

## How It Works

- 检测口径：同一用例在 20 轮里出现 ≥2 种结果（pass+fail）即判 flaky，稳定对照必须全程一致
- 隔离 enforcement：`pytest_collection_modifyitems` 按 quarantine.txt 子串匹配加 skip 标记
- 复验口径：隔离后确认轮**失败数为 0**（skip 不算失败——隔离的目的就是先恢复主干信任）

## Pitfalls & Q&A

- **坑：外层 pytest 把猎物池直接收集执行**——植入用例会被外层跑一次并留状态；.sh 只收集
  `governance_test.py`，猎物池由 hunt.py 的子进程轮次驱动
- **坑：junit classname 带 rootdir 前缀**（`16_flaky.tests.test_planted::...`）——
  用 `startswith("test_planted")` 过滤会全部落空（实测检出 0），要用 `in` 包含匹配
- **坑：顺序依赖靶子的残留会让它「永不如期现形」**——每轮 hunt 前必须重置 `.shared_state`
