# 03 · 等待机制全集

## Background

自动化最不稳定的来源不是页面复杂，而是「等」：睡少了元素没到必挂，睡多了套件慢成蜗牛还遮住真实问题。
靶场的秒杀横幅固定 2.5s 现身，正好给三种等待策略当秒表。

## What

- **sleep 下注实验**：赌 1s/2s/3s 各跑 3 次，实测 0/3、0/3、3/3——结论「sleep 是赌时序」
- **显式等待**：`WebDriverWait.until(条件)` 连跑 10 次 10/10，平均 2.57s（贴近真值）
- **FluentWait 式轮询**：0.2s 自定义轮询间隔，同样 2.57s 拿到，粒度更细
- **隐式+显式叠加陷阱**：隐式 5s + 显式 2s 找不存在的元素，实测耗时 5.0s——显式超时被隐性放大
- 产物：`reports/waits_report.csv`

## When to Use

- 用例偶发超时先查等待策略，再查网络
- 任何人往用例里加 `sleep()` 时，把这张 CSV 甩给他

## Quick Start

```bash
cd selenium/03_waits
./03_waits.sh            # apply → observe（5 条用例 + CSV）→ clean
```

实测输出（2026-10-26，节选）：

```text
sleep(1s): 0/3 通过 … sleep(3s): 3/3 通过
显式等待 10/10 通过，平均现身耗时 2.57s
显式只给 2s，实际耗时 5.0s（每次轮询的 findElement 都被隐式拖 5s）
5 passed in 54.08s
```

## How It Works

- 显式等待等的是**条件函数**（横幅可见），条件一成立立刻返回——既不早也不晚
- 隐式等待作用于每一次 `findElement`：显式等待每轮轮询里藏着一个隐式 find，
  所以「隐式 5s + 显式 2s」的实际超时 ≈ 5s × 轮询次数，2s 的预算形同虚设

## Pitfalls & Q&A

- **坑：赌 3s 全过所以 sleep 也行？** 换台慢机器、页面加个接口，3s 就变 0/3——sleep 的结论不可迁移
- **坑：隐式等待设了忘还原**（`implicitly_wait(0)` 收尾）——会污染同 driver 的所有后续用例
- **Q：FluentWait 比 WebDriverWait 快吗？** 不快，只是轮询粒度可调；对已知 2.5s 的横幅，两者同样 2.57s
