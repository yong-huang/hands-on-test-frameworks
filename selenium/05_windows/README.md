# 05 · 窗口与标签管理

## Background

点一个按钮跳出新标签页，是真实网站的基本操作，也是新手的第一次「元素明明在、就是找不到」——
因为 driver 还盯着旧窗口。本实验把句柄往返、Selenium 4 的 newWindow、窗口尺寸一次练熟。

## What

- 靶场新增「🔍 与友商比价」按钮（`window.open` 新开 compare.html 价格对照表）
- 用例 ①：点比价 → 切到新 tab → 断言对照表 3 行与结论 → 切回原窗口 → 再切过去 → close → 回主页
- 用例 ②：`switch_to.new_window("tab")` API 造新标签页
- 用例 ③：`set_window_size` / `get_window_size` / innerWidth 三方对照

## When to Use

- 任何「点按钮开新页」的流程（支付跳转、帮助中心、比价/分享）
- 分辨率敏感布局的回归（配合无头模式做 CI 尺寸固定）

## Quick Start

```bash
cd selenium/05_windows
./05_windows.sh            # 3 passed
```

实测输出（2026-10-26）：`3 passed in 1.65s`

## How It Works

- 句柄模型：`window_handles` 是当前会话所有窗口/标签的句柄列表，`switch_to.window(句柄)` 切换
- 惯用句式：记下 `origin`，用「句柄差集」找新窗口；关新窗口前先切过去，`close()` 只关当前
- newWindow API 不经过页面 JS，被 CSP/弹窗拦截器卡住时是备选通道

## Pitfalls & Q&A

- **坑：`switch_to.new_window()` 的返回值在 chromedriver 上是 null**——别用 `["handle"]` 取句柄，
  从 `window_handles` 差集拿才稳
- **坑：点开新页后直接找元素**——driver 还在旧窗口上下文里，先切句柄
- **Q：close 和 quit 区别？** `close()` 关当前窗口，`quit()` 结束整个会话；关掉非当前窗口前要先切过去
