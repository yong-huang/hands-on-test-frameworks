# 08 · RequestsLibrary 入门

## Background

接口测试在 Robot 里靠 RequestsLibrary：`Create Session`/直接 URL 都行，正向与异常
全靠 `expected_status=` 一字诀。靶场 4 个接口（创建/查询/支付/取消）在本篇被
5 条用例（正向 4 + 异常组 1）全覆盖。

## What

- 正向：201 创建（字段完整性）/ 查询 created / 支付 paid / 取消 cancelled
- 异常组：缺字段 422、不存在 404、已支付再支付 409（状态机守恒）
- 顺带修了靶场 POST 路由的下标错位（`/api/orders/{id}/pay` 打到 404 的根因）

## When to Use

- 接口回归的第一层：全端点正向 + 关键异常码
- 修服务端路由/状态机后的快速冒烟

## Quick Start

```bash
cd robotframework/08_api_intro
./08_api_intro.sh            # 5 tests, 5 passed
```

实测输出（2026-10-27）：`5 tests, 5 passed, 0 failed`

## How It Works

- `expected_status=` 让 4xx/5xx 成为普通响应（不抛 HTTPError），负向断言才可能
- 状态机用例：创建 → 支付（200/paid）→ 再支付（409）三步在一条用例里完成闭环

## Pitfalls & Q&A

- **坑：RF 内联字典 `${{...}}` 的花括号层数**——`${{"customer": "李雷"}}` 会被 RF 剥掉
  一层后按 Python 表达式求值，中文键值对直接 SyntaxError；老老实实 `Create Dictionary`
- **坑：改了 server 代码忘重启靶场**——`apply` 幂等不会重载代码；改服务端后必须
  `shop.sh restart`（本实验实测两次才记住）
- **坑：路由 `split("/")` 的下标**——`/api/orders/{id}/pay` 切出来 `""/"api"/"orders"/{id}/pay`，
  `parts[1]` 是 "api" 不是 "orders"（写路由时画个数组图）
