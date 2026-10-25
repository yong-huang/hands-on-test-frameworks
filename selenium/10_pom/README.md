# 10 · POM 分层重构

## Background

把定位、操作、断言全写在一个测试函数里，前期最快，第三个月最痛：页面改版要改 N 处、
用例读不懂、定位细节淹没业务语义。Page Object Model 用三层把它拆开：
**pages**（定位与操作）→ **flows**（业务编排）→ **tests**（只有业务语言）。

## What

- `pages/checkout_page.py`：结账页唯一住址——URL、三层 frame 切换、buy/pay 操作
- `flows/purchase_flow.py`：buy_and_pay() 完整业务编排，返回订单号
- `tests/purchase_test.py`：调 flow + API 侧复核 status=paid，**零定位细节**
- 硬规则由 .sh 强制执行：`grep find_element tests/ | wc -l` 必须为 0

## When to Use

- 同一页面的用例 ≥3 条，或页面即将进入频繁改版期
- 测试代码要交给不熟悉页面结构的人维护时

## Quick Start

```bash
cd selenium/10_pom
./10_pom.sh            # 硬规则校验 + 1 passed
```

实测输出（2026-10-26，节选）：

```text
tests/ 内 find_element 命中数: 0（要求 0）
1 passed in 1.23s
```

## How It Works

- 依赖方向单向：tests → flows → pages → selenium，反向禁止
- 页面对象只暴露业务动作（`buy()` 返回订单号），不暴露 WebElement
- flow 返回值供测试做 API 侧交叉复核（页面自说自话不算数）

## Pitfalls & Q&A

- **坑：macOS 自带 bash 3.2 的多字节变量解析**——`echo "$hits（要求 0）"` 里全角括号会被
  并进变量名报 unbound variable；中文语境下变量一律写 `${hits}` 花括号断开
- **坑：grep 零命中退出码 1 撞上 pipefail**——`hits=$(grep ... | wc -l)` 在没有匹配时整条
  赋值失败，要写 `{ grep ... || true; } | wc -l`
- **Q：flow 和 page 为什么要分两层？** page 管一页之内的事，flow 管跨页业务；改版时
  只动 page，业务流程变化只动 flow，测试层永远稳定
