# 16 · Playwright 入门：自动等待的现代 E2E，从三条用例开始

> Selenium 时代写 E2E，一半代码在处理"等"（页面里的异步数据请求——AJAX——
> 让元素何时出现变得不可预测）。Playwright 把等待变成默认：
> 操作自动等元素可交互，断言自动等结果成立。读完本篇你能用 pytest-playwright
> 写出 SUT 首页"下单→查询→删除"三条用例、掌握定位器优先级，
> 并会用 trace 回放与 codegen 录制两个配套工具。

## Background

浏览器端到端（E2E，end-to-end，模拟真实用户操作完整页面路径的测试）的老大难是**等待**：AJAX 渲染有快有慢、动画让元素暂不可点，脚本跑得比页面快就找不到元素。

Selenium 时代的解法是显式等待——每个动作前后手动 sleep 或 WebDriverWait，等待代码占一半篇幅，还经常等少了 flaky、等多了浪费时间。


Playwright（微软的开源浏览器自动化框架）重新设计了这一层：操作自带自动等待
（元素可见、稳定、可接收事件、启用状态四条件全满足才动作），
断言提供 web-first 形态（持续重试到条件成立或超时）。
等待从"脚本作者的责任"变成"框架的默认行为"——flaky 的头号来源就此消失。

本实验对 lab 11 的 SUT 首页写三条用例：下单、查询、删除。

## What

Playwright 的 pytest 集成（pytest-playwright 插件）提供 `page` fixture：
每条用例全新页面，失败自动截图。测试体就是"定位器 + 动作/断言"两件事。

可以把 Playwright 想成一位严格的前台接待员：访客（测试代码）说"去前台结账"（点击按钮），接待员会等柜台有人、不排队、门开着才放行（自动等待），而不是直接把人往里推。

但和接待员不同的是，等待只覆盖**动作**——断言"某个元素会出现"必须主动用 web-first 断言（`expect`）才有重试语义，用立即返回的查询函数就等于不等人。


三个核心概念：定位器优先级（语义 > CSS）、自动等待 vs web-first 断言、
trace（执行过程录制，时间旅行式调试器）。

## When to Use

典型场景：

- 关键用户路径回归：下单、登录、结账这条链，UI 一坏立刻知道。
- 跨浏览器回归：同一套用例换 `--browser firefox|webkit` 重跑（lab 20 三核）。
- 重构保护网：语义定位器对样式重构免疫，改版不误伤用例。

何时不用：接口层验证交给 API 测试（快一个数量级）；纯后端逻辑用单测；
页面状态极简、无异步渲染的内部小工具，Selenium 脚本也能活——但异步是常态，
等待问题迟早要还。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| Playwright | 自动等待 + web-first 断言 + trace | 现代项目的默认选择 |
| Selenium | 生态最广、多语言，等待靠手写 | 遗留资产、特殊浏览器需求 |
| Cypress | 内置等待、运行于浏览器内 | 前端团队自测（lab 21 起） |

## Quick Start

前置条件：labs/00 体检通过；Playwright 浏览器已装（浏览器版本与库版本不匹配时
报 `Executable doesn't exist`，跑一次 `playwright install chromium` 即可——
这是新手第一个失败点）。

```bash
cd labs/16_pw_basics
./pw_basics.sh            # 起 SUT(8916) → 三条用例 → trace 演示 → 清理
./pw_basics.sh observe
```

三条用例全绿的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 三条 E2E 全绿（自动等待，全程无 sleep）
collected 3 items

tests/test_orders_e2e.py ...                                             [100%]

============================== 3 passed in 0.79s ===============================
```

trace 留痕（observe ②，节选）：

```
=====> [observe] ② trace 留痕：--tracing on 记录执行过程，可用 trace viewer 回放
============================== 3 passed in 0.61s ===============================
>>> trace 已生成: test-results/tests-test-orders-e2e-py-test-order-list-shows-seed-data-chromium/trace.zip
>>> 回放命令: ... -m playwright show-trace test-results/.../trace.zip（GUI 工具，请手动执行查看）
```

诚实预期：三条用例（下单/查询/删除）应全绿，全程没有一行 sleep——
等待全部由框架承担。codegen 是交互式工具，需要手动体验：
`playwright codegen http://127.0.0.1:8916` 打开浏览器，操作即生成代码。

关键命令（这段在做什么：日常运行、失败留痕、出错即调三个入口）：

```bash
pytest --base-url http://... --browser chromium --tracing retain-on-failure
pytest --trace on     # 出错即进入 Playwright inspector
```

## How It Works

**一次 E2E 用例的执行链路**：pytest → `page` fixture（新页面）→ 定位器解析 →自动等待 → 动作/断言 → trace/截图落盘（可选）→ 页面销毁。

`--base-url` 让 `page.goto("/")` 拼出完整地址；缺它时相对路径直接报错（labs/00 的体检表里 Playwright 实验需要 `--base-url` 就是这个原因）。


**定位器优先级**：`get_by_role` > `get_by_placeholder`/`get_by_text` >
`locator("css")`。语义定位（按可访问性角色与名字找元素）对样式重构免疫，
role 定位器本身还要求页面可访问性达标——抗重构、可读、可访问性三赢。
CSS 选择器是最后的手段。

**自动等待 vs web-first 断言**是本实验最重要的一课：

```python
# 动作：自动等待"可交互"
page.get_by_role("button", name="提交").click()
# 断言：web-first，持续重试到成立或超时
expect(page.get_by_text("新订单")).to_be_visible()
```

为什么强调：`is_visible()` 这类查询函数**立即返回不等待**——用它断言
"将出现的元素"必挂（本实验踩过）。一句话：断言用 `expect`，不用 `is_*()`。

**trace 回放**：`--tracing on` 记录每步前后的 DOM（浏览器解析 HTML 后生成的页面结构树，自动化脚本操作页面实际操作的就是它）快照、网络请求、控制台；`show-trace` 打开时间旅行式调试器，每一步可点开看当时的页面状态——比看视频找问题快得多。

CI 里用 `--tracing retain-on-failure` 只留失败的。


## Pitfalls & Q&A

踩坑清单：

- **用 `is_visible()` 断言"将出现的元素"**。现象：偶发立刻失败。
  原因：查询函数立即返回，不等渲染。解法：改用 `expect(...).to_be_visible()`。
- **浏览器可执行文件缺失**。现象：`Executable doesn't exist at ...`。
  原因：Playwright 升级后缓存目录版本号变化。解法：重跑
  `playwright install`（labs/00 的体检脚本按目录前缀检测，升级后要手动补）。
- **`page.goto("/")` 连接拒绝**。现象：全套 ERR_CONNECTION_REFUSED。
  原因：SUT 没起。解法：脚本 apply 步骤先起服务并轮询健康检查。
- **CSS 选择器写一堆**。现象：改版即碎。解法：迁移到 role/文本语义定位器。

深入问答：

- **Q：Playwright 的自动等待覆盖什么？** 元素可见、稳定、可接收事件、启用状态；
  断言层面要主动用 web-first `expect` 才有重试语义。
- **Q：trace 里能看什么？** 每步前后的 DOM 快照、网络请求、console、源码定位——
  一次录制替代"复跑加 print"。
- **Q：为什么 selector 要语义化？** 抗重构、可读、可访问性双赢——
  role 定位器本身就要求页面可访问性达标。
