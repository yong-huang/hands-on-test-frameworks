# 兼容性差异清单（本机实测）

> 口径：macOS Apple Silicon / Chrome 156 / Firefox 158 / Safari 26.5 / Selenium 4.48。
> 只收本仓库实测确认的条目，未测的不编。

| # | 现象 | Chrome | Firefox | Safari | 应对 |
|:--|:---|:---|:---|:---|:---|
| 1 | 无头模式 | ✅ `--headless=new` | ✅ `-headless` | ❌ 无无头模式，恒有头 | 矩阵夹具按浏览器分支 |
| 2 | 相对定位器锚写法（元组形式） | 神秘崩溃 `call function result missing` | 明确报错 `Unsupported locator strategy` | 明确报错 | 一律用 `{By: 值}` 字典形式，三浏览器一致 ✅ |
| 3 | `switch_to.new_window()` 返回值 | 返回 null | 正常返回 | 正常返回 | 不读返回值，从 `window_handles` 差集取句柄 |
| 4 | 日期控件键入段位顺序 | 跟随系统 locale（本机 zh-CN：年/月/日） | 键入行为不同（未深测） | 键入行为不同（未深测） | 键入法不可移植：JS 设值 + 派发 change（见项目 04） |
| 5 | 原生 click 在 Safari 非前台时 | — | — | ❌ 不产生 click 事件；激活前台后原生点击反而阻塞（实测 120s 超时） | Safari 分支用 JS click 兜底（矩阵要验证表单逻辑而非点击机制） |
| 6 | safaridriver 单会话配对：卡死的会话占住配对 | — | — | ❌ 新会话 `SessionNotCreated: already paired` | `pkill -f safaridriver` 释放后重试 |
