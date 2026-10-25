# 10 · ⛓️ API + Web 混合场景

## Background

纯 API 测试验证不了「页面真的把订单显示/操作对了」，纯 Web 测试又造数慢、清理难。
混合场景是两者的合体：**API 造数（快）→ Web 验证与操作（真）→ API 复核（准）**，
最后 Suite Teardown 清理造数，做到零残留。

## What

- 靶场新增 `orders.html` 订单查询页：输入订单号 → 渲染详情 → 「支付此订单」按钮（仅 created 态出现）
- 三条用例串联：API 批量创建 3 笔 → Web 逐笔查询并点击支付 → API 复核全部 paid
- Suite Teardown：created 状态的订单一律取消，API 查证无 created 残留

## When to Use

- 状态机类业务（下单/支付/发货）的端到端验证
- Web 测试需要大量前置数据时——造数走 API，验证走 UI

## Quick Start

```bash
cd robotframework/10_api_web_hybrid
./10_api_web_hybrid.sh            # 3 tests, 3 passed
```

实测输出（2026-10-27）：`3 tests, 3 passed, 0 failed`

## How It Works

- 三个测试共享 Suite 级变量 `@{ORDER_IDS}`（Set Suite Variable 从第一用例传出）
- Web 侧用 `Wait Until Page Contains    ${oid}` 等**本轮唯一订单号**渲染完成
- 清理语义：本靶场 paid 不可取消，故「残留」定义为 created 态——Teardown 里
  created 一律 cancel，并逐单复核状态 ≠ created

## Pitfalls & Q&A

- **坑：等待条件用公前缀被旧内容假命中**——三条订单客户名都叫「混合场景员-N」，
  `Wait Until Page Contains 混合场景员` 上一轮的旧渲染也能命中；改等唯一订单号
- **Q：为什么不用 Web 直接创建三笔？** 造数追求快与稳，API 是最优通道；
  Web 环节只保留「被测行为」（查询与支付）
