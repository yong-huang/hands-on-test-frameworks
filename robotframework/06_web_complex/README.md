# 06 · 复杂页面三难

## Background

iframe、多窗口、懒加载——真实站点的三大「找不到元素」高发区。Robot 的解法关键字：
`Select Frame/Unselect Frame`、`Switch Window`、`Execute Javascript` +
`Wait Until Keyword Succeeds`（重试语义）。

## What

- 靶场新增：iframe 支付面板（生成订单号）、价格对照页（新窗口打开）、懒加载推荐区（30 件分 3 页）
- 三条用例：iframe 内生成订单号后回主文档断言主表单仍在；新窗口往返；懒加载 30 件全载
  + 「加载完成」提示可见

## When to Use

- 支付/客服等第三方嵌入组件
- 分享/对比/帮助等新窗口流程
- 无限滚动信息流

## Quick Start

```bash
cd robotframework/06_web_complex
./06_web_complex.sh            # 3 tests, 3 passed
```

实测输出（2026-10-27）：`3 tests, 3 passed, 0 failed`

## How It Works

- iframe：`Select Frame    id:pay-frame` 进入后所有关键字都在子文档里找，`Unselect Frame` 回主文档
- 多窗口：`Switch Window    locator=NEW` 切到刚打开的窗口，`Close Window` 后 `Switch Window    main` 回主窗
- 懒加载：`Execute Javascript window.scrollTo(...)` 触发 + `Wait Until Keyword Succeeds 3x 1s`
  重试语义兜底（等 fetch 慢返回）

## Pitfalls & Q&A

- **坑：切进 iframe 后找主文档元素**——必须先 `Unselect Frame`；Robot 没有「回上一层」，
  与 Selenium 一致只有「一键到顶」
- **Q：`Wait Until Keyword Succeeds` 和 `Wait Until Page Contains Element` 怎么选？**
  前者重试任意关键字组合（如「滚动+计数」），后者只等单个条件；懒加载常两者嵌套
