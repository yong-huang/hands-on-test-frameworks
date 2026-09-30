# DEBUGGING.md — Playwright 排障工具速查手册（lab 08 产出）

> 先按"症状"选工具，再按"用法"操作。四个 GUI 工具覆盖 95% 的排障场景。

## 工具速查表

| 症状 | 首选工具 | 命令（在本目录执行） |
|:---|:---|:---|
| 用例红了，想知道失败前每一步发生了什么 | trace viewer | `npx playwright show-trace test-results/<用例目录>/trace.zip` |
| 想边改边跑、逐条勾选重放 | UI Mode | `npx playwright test --ui` |
| 想一步步单步执行、实时看 locator 命中 | Inspector | `npx playwright test --debug` |
| 想看汇总报告 + 失败截图/视频 | HTML 报告 | `npx playwright show-report` |
| 怀疑是环境/接口问题而非用例问题 | HAR/探针 | `curl <接口>`；或 lab 05 的注入套路 |

## trace.zip 里有什么

`unzip -l test-results/<用例>/trace.zip` 可见四类内容：

- `trace.trace` —— 操作时间线（每步动作、网络、console）
- `*.png` —— 每步的页面截图（time travel 的素材）
- `network` 文件 —— 请求/响应体快照
- `.json` 元数据 —— 用例名、浏览器、起止时间

trace viewer 打开后的排查路径：**左侧时间线找红步 → 中间 DOM 快照点元素看 locator 命中 →
右侧 Network/Console 面板看接口与报错**。

## 本实验三个病例的根因（先自查再看）

### 病例一：定位器拼写错误
- **症状**：`element(s) not found`，等待 `getByTestId('order-titel')` 超时。
- **trace 证据**：Actions 时间线里这一步是红的；DOM 快照里手动搜 `order-title` 能找到正确元素。
- **根因**：testid 拼错（`titel` → `title`）。trace 的 "Pick locator" 功能可直接点页面元素拿正确定位器。

### 病例二：立即查询代替 web-first 断言
- **症状**：`count()` 返回 0，`expect(rows).toBe(3)` 红，但 trace 里明明能看到表格稍后渲染出来了。
- **trace 证据**：时间线显示 `count()` 在点击后立即执行（接口 1.2s 后才返回），
  截图对比可见"查询瞬间页面还是 loading"。
- **根因**：`count()` 这类非等待 API 拿瞬时值、不重试。改成
  `await expect(page.getByTestId('slow-row')).toHaveCount(3)` 即可。

### 病例三：断言基于过时的世界观
- **症状**：用例先等到 `paid`（这步绿了），随后回头断言 `created`（这步恒红）。
- **trace 证据**：时间线可见属性从 `created` 变为 `paid` 的确切时刻；
  Network 面板的 WebSocket 帧记录了服务端广播。
- **根因**：断言与业务规则矛盾——服务端 2 秒后推进状态，"回头验证旧状态"永远失败。
  修正方向：删掉过时断言，或改为断言演进序列（created → paid 各断言一次，顺序正确）。

## UI Mode 与 --debug 的分工

- **UI Mode**（`--ui`）：事后分析 + 用例筛选。watch 模式改代码自动重跑，
  时间旅行逐帧看。适合"我知道哪条红，想慢慢看"。
- **Inspector**（`--debug`）：事中单步。每步暂停，Playwright Inspector 面板
  可以现场试 locator（Pick locator 点选元素直接生成）。适合"写用例时边写边校定位器"。

## 与 CI 的衔接

CI 里没有 GUI，trace 全靠 `retain-on-failure`（lab 12 系统化）。
产物 artifact 里带着 trace.zip，本地 `show-trace` 打开——本地调试体验与线上失败现场一致。
