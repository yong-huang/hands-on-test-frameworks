# 04 · SeleniumLibrary 入门

## Background

SeleniumLibrary 把 Selenium 的能力包成关键字：`Open Browser`、`Input Text`、
`Wait Until Element Is Visible`……这一篇用 Robot 的方式走通「下单主流程」，
并立下本系列的等待纪律：**只用 Wait Until 族，不碰 sleep**。

## What

- 靶场新增慢元素（2s 后现身的订单横幅）——显式等待的靶子
- 主流程用例：`id:` 前缀定位 → 填单 → 选品 → 提交 → 等订单号出现 → 断言 ROB- 前缀
- 慢元素用例：`Wait Until Element Is Visible` + 自定义 error 提示
- HEADLESS 双跑：`headlesschrome` 与 `chrome` 同参同过

## When to Use

- 新页面接入自动化时的第一步：主流程 + 显式等待打底
- CI 环境与本地环境的行为一致性验证（无头/有头双跑）

## Quick Start

```bash
cd robotframework/04_web_intro
./04_web_intro.sh            # 无头 2 passed + 有头 2 passed
```

实测输出（2026-10-27，节选）：无头 `2 tests, 2 passed`；有头 `2 tests, 2 passed`

## How It Works

- 定位器前缀：`id:customer` / `css:.x` / `xpath://x`——前缀显式声明策略，避免默认策略歧义
- `Wait Until Element Is Visible    id:x    10s    error=自定义提示`——超时错误里直接看到人话
- `${BROWSER}` 变量从 sh 注入（`--variable BROWSER:headlesschrome`），套件零改动切换模式

## Pitfalls & Q&A

- **坑：跨系列复制用例时的"惯性前缀"**——selenium 线订单号是 ORD-、本靶场是 ROB-，
  断言前缀错了报错信息里直接给实际文本（实测 `its text was '订单号 ROB-dc9e8adf'`）
- **Q：为什么不用 `Sleep 2s` 等慢元素？** 见 docs/selenium.md 项目 03 的数据：
  sleep 是赌时序，Wait Until 是等条件
