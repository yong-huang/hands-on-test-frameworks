# 03 · 定位引擎深水区：iframe（内嵌文档）、Shadow DOM（独立 DOM 子树）与 strict mode（多命中即拒绝）

> E2E 的红有一半源自"找错元素"或"找不到元素"。本实验在 pw-store 上练四件深水区武器：
> frameLocator 穿内嵌文档、Shadow DOM 自动穿透、filter 链式收窄、strict mode 歧义拒绝。
> 十条用例连跑 10 轮全绿——定位器稳了，断言才有资格谈稳定。

## Background

lab 01 已经用过 `getByRole`，lab 02 的冒烟套件用过 `getByTestId`，
它们适用于"元素在主文档里、全局唯一"的简单场景。

真实页面的两个现实会让简单定位失效：一是页面存在嵌套文档（iframe 内嵌另一份 HTML），
主文档的选择器对帧内元素天然失明；二是元素有重名（列表里 10 个同款按钮），
定位器命中多个时行为必须可预期。

Playwright（微软开源的浏览器自动化框架）对此有两层设计：官方推荐定位语法按
**角色 → 标签 → testid → CSS** 的顺序选用（越靠前越贴近用户视角），歧义由兜底机制处理；
执行时强制 **strict mode**（命中多个元素就拒绝执行并报错，而不是静默取第一个）。

"取错元素导致断言假绿"这类最难排查的问题，从源头被堵住。

## What

定位器（locator）是"如何找到元素"的查询描述，不是元素本身的引用——
页面重渲染后它仍能重新找到目标，这是与"拿到元素句柄再操作"的传统方案的本质区别。
一条可靠的定位器 = 合适的查询方式 + 必要的收窄 + 唯一性确认。

可以把写定位器想成寄快递填地址：优先写"收件人姓名 + 部门"（getByRole，语义明确），
没有姓名才写工位编号（getByTestId），最后才是经纬度（CSS 选择器）；
写完还要确认地址唯一——两栋楼同名收件人时，strict mode 会拒收而不是随机扔一家。

但和快递不同，定位器是声明式的：页面加载快慢不影响它，
它总在执行瞬间重新解析。

![定位器决策流：选型 → 嵌套换轨 → 收窄 → strict mode 门禁](images/locators.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/03_pw_locators_pro/images/locators.html)
> （或本地打开 [`images/locators.html`](images/locators.html)）。
> 图中虚线是 strict mode 的回退路径：命中多个时退回上一步继续收窄。

## When to Use

| 定位方式 | 适用场景 | 本实验靶点 |
|:---|:---|:---|
| `getByRole` / `getByLabel` | 一切有可访问角色或表单标签的元素 | 导航 tab、登录输入框 |
| `getByTestId` | 无语义角色的自定义组件 | 订单行、页面区域 |
| `locator('#id')` | 第三方内容只有 id（广告、客服组件） | iframe 内嵌页面 |
| `frameLocator()` / `contentFrame()` | 元素在 iframe 里 | 嵌入面板 |
| `locator.filter()` / 区域链 | 同名元素多，需按内容或区域收窄 | 订单列表 |

何时不用：页面结构还没定型时别急着写精细定位器，先与前端约定 `data-testid`，
成本远低于事后维护 CSS 路径。

## Quick Start

```bash
cd playwright/03_pw_locators_pro
./locators_pro.sh          # apply 体检 → observe 十条用例 + 10 连跑 → clean
```

apply 阶段做类型检查并确认 pw-store 已构建（构建产物与 lab 02 共享）。
observe ① 跑十条用例，webServer 在独立端口 9003 托管靶场：

```
=====> [observe] ① 十条定位深水区用例（chromium，webServer 托管 :9003）
  ✓  1 iframe：帧内标题可见，帧内按钮可连点
  ✓  2 Shadow DOM：穿透点击 shadow 内按钮，驱动主文档计数
  ✓  3 strict mode：locator("button") 命中多个即拒绝执行
  ……（✓ 4-10 省略）
  10 passed (3.6s)
```

observe ② 是本实验的验收线：同一套用例连跑 10 轮，任何一轮出现红即失败：

```
=====> [observe] ② 稳定性 10 连跑（验收线：连续 10 次全绿）
>>> 第 1/10 轮：绿   ……   >>> 第 10/10 轮：绿
>>> 10 连跑全绿 ✓
```

验收方式：10 连跑全绿。再做一个变异实验——把用例 ③ 里的
`page.locator('button')` 改成 `page.locator('nav button').first()` 重跑，
用例 ③ 会红，因为它断言的正是"歧义定位器必须被拒绝"这个行为本身。

## How It Works

**iframe 是换轨，不是加前缀。** iframe（页面内嵌另一个文档的框架）内部是完整的
DOM 树，主文档定位器看不见它。`page.getByTestId('embed-iframe').contentFrame()`
拿到帧上下文后，后续定位器全部在帧内解析。

帧内内容模拟第三方页面，只有 `id` 没有 `data-testid`——这正是真实嵌入组件的常态，
`locator('#embed-btn')` 在此是合理选择。

**Shadow DOM 零写法差异。** Shadow DOM（挂在元素内部的独立 DOM 子树，
常规 CSS 选择器看不到内部）分 open 与 closed 两种模式。

Playwright 对 open 模式自动穿透：`page.getByTestId('shadow-host').getByTestId('shadow-btn')`
直接命中 shadow 内部按钮，与普通元素写法完全一致。

本实验的 shadow 按钮点击后通过 composed 事件（可穿越 shadow 边界的自定义事件）
驱动主文档计数变化，断言落在主文档元素上——
"shadow 内操作、主文档验证"是这类组件的标准测法。

**strict mode 把隐性 bug 变显性报错。** `locator('button')` 命中一批候选时（订单页按钮不止一个），
传统框架静默取第一个（可能根本不是你想点的），断言以错误的前提继续跑。

Playwright 直接抛出 `strict mode violation`，报错里列出全部候选。
用例 ③ 用 try/catch 捕获这条报错并断言其内容——验证"框架会拒绝"本身就是测试目标。

**filter 与区域链是收窄的两种思路。** `getByTestId('order-item').filter({ hasText: '机械键盘' })`
按内容收窄；`getByTestId('orders-page').getByRole('button')` 按区域收窄。

前者适合列表，后者适合"同名元素分布在不同功能区"的页面。两者可叠加，
收窄的终点是 strict mode 认可的唯一匹配。

## Pitfalls & Q&A

**Q：为什么帧内按钮用 `#embed-btn` 而不用 testid？**
因为嵌入内容模拟的是第三方页面（广告、客服组件）。第三方代码不归你管，
不可能为测试加 `data-testid`，此时 `id` 是务实选择。

定位优先级的本意是"可控范围内贴近用户视角"，而不是教条。
可控的代码（pw-store 本体）坚持 testid。

**Q：`locator.or()` 在什么时候用？**
两个互斥状态只会有一个出现时。用例 ⑦ 点击慢加载按钮后，loading 与表格
先后出现，`or()` 组合断言"其中之一可见"，覆盖加载的过渡期，不猜时序。

代价是报错信息不如单一断言精确，过渡期过后应紧跟终态断言（`toHaveCount(3)`）。

**Q：`first()` / `last()` 什么时候安全？**
仅当顺序本身是被测语义时。用例 ⑥ 断言"种子列表首尾"，顺序来自服务端
排序契约，安全。反例是"点第一个删除按钮"——顺序多半是渲染巧合，
应改为 `filter({ hasText: '目标商品' })` 定位到具体行再操作。

**Q：十条用例为什么能连跑 10 轮不红？**
三条保障：登录后即时导航、无跨用例状态依赖（每条用例重新 `goto`）、
断言全部走 web-first 重试（断言在超时窗口内反复读取当前页面重新求值，
而非失败即判红）。

定位器只决定"找得到"，稳定还依赖"页面到达可交互态"的等待语义——
那是 lab 01 已经建立的基础。

**Q：closed shadow root 能穿透吗？**
不能。open 模式对外可见，closed 模式连 JavaScript 都拿不到内部引用，
Playwright 也不例外——这是浏览器安全模型的边界。

遇到 closed shadow 组件，从它暴露的对外接口（属性、事件、slot 渲染结果）断言，
而不是硬闯内部。
