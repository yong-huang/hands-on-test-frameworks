# 08 · 调试武器库：trace、UI Mode 与三个典型病例

> 用例红了不可怕，可怕的是不知道它为什么红。本实验准备三条"设计好的红"用例
> （定位拼写错、立即查询拿瞬时值、断言与业务演进矛盾），用 trace viewer 逐帧解剖，
> 验证 trace 产物的完整性，并把四个调试工具的分工写成速查手册（`DEBUGGING.md`）。

## Background

没有调试工具的 E2E 排障是这样的：跑一遍、绿了又红、加 print、凭感觉改。
一次失败的现场信息（每步做了什么、页面当时长什么样、接口回了什么）随用例结束而消失。

Playwright 的解法是**失败现场可回放**：trace（轨迹录制）把用例执行期间的每个动作、
每帧截图、每个请求都存进一个 zip。任何一次失败都能像看行车记录仪一样逐帧回放——
排障从"猜"变成"看"。

## What

Playwright 的调试工具有四件，输入不同、场景不同：trace viewer（事后精读单条用例的
完整轨迹）、HTML 报告（跑批汇总，从失败条目一键进轨迹）、UI Mode（watch 模式，
改代码自动重跑）、Inspector（`--debug` 单步执行，现场试定位器）。

可以把 trace 想成用例的行车记录仪：时间线上每一脚油门（动作）都有画面（截图）、
路况（DOM 快照）和仪表读数（网络与 console）。但和行车记录仪不同，
trace 里可以**点任何一帧直接看当时的 DOM 树**，还能在快照上试跑定位器——
"当时如果用这个定位器能不能找到元素"当场可验证。

![排障决策流：从一条红用例到根因归类](images/debugging.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/08_pw_debug/images/debugging.html)
> （或本地打开 [`images/debugging.html`](images/debugging.html)）。
> 主干是"报告汇总 → 轨迹精读 → 根因归类 → 对症修复"；失败用例的留痕由配置自动完成。

## When to Use

| 症状 | 首选工具 | 一句话理由 |
|:---|:---|:---|
| 单条用例失败，想知道每一步 | trace viewer | 逐帧回放，信息最全 |
| 一批跑完，先看哪些红 | HTML 报告 | 汇总视图 + 一键进轨迹 |
| 用例写得慢、想边改边验证 | UI Mode | watch + 勾选重跑 |
| 定位器拿不准，想现场试 | Inspector（--debug） | 点元素直接生成 locator |
| 怀疑后端而不是前端 | curl / lab 05 注入 | 分层定位，先二分 |

何时不用 trace：开发循环里的高频重跑开 `trace: 'on'` 会拖慢速度且吃磁盘——
日常 `retain-on-failure`（只在失败时留痕），排障时才手动开全量。

## Quick Start

```bash
cd playwright/08_pw_debug
./debug_tools.sh          # apply 体检 → observe 跑病例 + 验 trace → clean
```

observe ① 跑三条病例用例——**3 failed 是预期结果**，脚本对此显式容忍：

```
✘  1 [chromium] › 病例一：定位器拼写错误
✘  2 [chromium] › 病例二：立即查询代替 web-first 断言
✘  3 [chromium] › 病例三：断言了与业务演进矛盾的状态
  3 failed
```

observe ② 用 `unzip -l` 解剖 trace 产物，验证两类关键内容在位：

```
>>> 样本: test-results/broken-病例二…/trace.zip
test.trace
0-trace.trace
0-trace.network
>>> 逐步截图 10 张 ✓（每步动作都有留影）
>>> 网络快照存在 ✓
```

observe ③ 打印四个工具的打开命令（GUI 需手动体验），其中 trace viewer：

```
npx playwright show-trace test-results/broken-病例二…/trace.zip
```

验收方式：三条病例都能在 trace viewer 里找到各自的"红步"，并按 `DEBUGGING.md`
的指引说出根因（先自查再看答案）；`unzip -l` 确认网络快照与逐步截图在位。

## How It Works

**trace 的时间线是主线索。** trace viewer 左侧是 Actions 列表，红的一步就是案发点；
点它，中间面板出现当时的页面快照，右侧 Network/Console 同步过滤到该时刻。

病例一的排查路径：红步显示"waiting for getByTestId('order-titel')"，
在快照 DOM 里搜 `order-title` 立刻看到正确定位器——拼写错误当场定案。

**trace 让"时序问题"可见。** 病例二的断言在点击后立刻执行，trace 的时间线清楚显示
`count()` 那一步的页面还在 loading（截图是 spinner），1.2 秒后表格才渲染——
"拿瞬时值"这个抽象概念变成两帧画面的对比。

病例三同理：网络面板里能看到 WebSocket 帧把订单状态从 created 推到 paid，
"回头断言旧状态"的荒谬一目了然。

**UI Mode 与 Inspector 是"事中"工具。** trace 是事后法医，这两个是现场巡逻：
UI Mode 里勾一条用例反复重跑，每步可暂停可回看。

Inspector（`--debug`）每步暂停，Pick locator 点页面元素直接生成定位器代码——
写用例阶段就该开着它校准定位，而不是等跑挂了再排。

**三族根因是排障的分类学。** 本实验三个病例对应三类：定位错（找不到元素）、
时序错（拿瞬时值不重试）、预期错（断言与业务规则矛盾）。

绝大多数 E2E 红都能归入其中一族——归类之后，修复手法是确定的
（改定位器 / 改用 web-first 断言 / 改预期）。

## Pitfalls & Q&A

**Q：为什么病例二的"坑"没有用 `textContent()` 演示？**
本实验第一版确实用它——结果用例过了：`textContent()` 这类查询虽然不重试，
却会**等元素出现**，表格渲染出来后它拿到的是正确文本。

真正的坑换成了 `count()`：它连等待都没有，点击瞬间返回 0。
教训是"非等待 API"家族各有各的等法，排障要靠 trace 确认实际行为，不能背文档。

**Q：trace 开 `on` 什么时候算过度？**
每个用例都全量录制时。trace 的成本是磁盘与轻微减速，日常套件配
`retain-on-failure`（失败才留）即可；`on` 只留给本实验这种排障教学，
或某个疑难 flaky 的定向排查窗口。

**Q：三条病例永远红，会不会污染套件状态？**
病例都跑在独立端口（9008）的独立 SUT 实例上，失败点各不相同且不产生持久数据
（病例一的订单没创建成功，病例二/三的数据随进程消失）。`clean` 后一切复原，
`broken.spec.ts` 保持原样——下次实验它还会再红一遍，这是设计。

**Q：CI 上没有 GUI，调试怎么办？**
CI 配 `retain-on-failure`，失败产物的 trace.zip 随 artifact 上传，
下载后本地 `show-trace` 打开——与本地失败完全相同的回放体验。
产物体系（HTML 报告、JUnit、截图视频）是 lab 12 的主题。

**Q：三个根因族之外还有第四族吗？**
有：环境错（服务没起、端口被占、浏览器构建缺失）。它的特征是**整批用例
同一种方式红**而不是个别红，先查 `load_resources.sh` 体检与 webServer 探活，
再进用例级排障。

本系列把它放在手册的速查表第一行之前——先排除环境，再怀疑代码。
