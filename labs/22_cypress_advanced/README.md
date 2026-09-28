# 22 · Cypress 进阶：intercept / session / 自定义命令

> lab 21 解决"能用"，本篇解决"好用"：`cy.intercept` 桩网络、`cy.session` 缓存登录、
> 自定义命令把业务动作变成 `cy.createOrder()`——对应 Playwright lab 19 的
> 全部场景，同 SUT 同语义。读完本篇你能逐条对照两代框架的表达力，
> 并知道重试机制为什么是止血不是治病。

## Background

lab 21 验证了 Cypress 能做 lab 16 的事，但真实的 E2E 套件还需要三件套：
网络桩（不依赖真后端测前端逻辑）、登录态复用（套件不为登录重复纳税）、
业务命令封装（用例说业务语言）。这三件分别决定套件的速度、稳定性和可维护性，
是框架"表达力"的核心战场。

对照的意义在此刻最大化：lab 19 已经用 Playwright 的 `page.route` /
`storageState` / POM 解过同一组题（同 SUT 同语义）。

本篇用 Cypress 的 `cy.intercept` / `cy.session` / 自定义命令再解一遍——
两条路线的取舍从对照中自然浮现，而不是从文档里背下来。

## What

三个机制各管一层：

- **`cy.intercept(pattern, handler)`**：在网络层拦截请求——给桩响应
  （`{ body: ... }`）、造网络错误（`forceNetworkError: true`）、注入状态码
  （`{ statusCode: 500 }`），并可用别名（`.as('broken')`）+ `cy.wait('@broken')`
  精确断言"这个请求发生过"。
- **`cy.session(name, setup, { validate })`**：把登录态（cookie + localStorage
  快照）按名字缓存成"会话"，同一角色整套跑批只真正登录一次；
  `validate` 失败自动重跑 setup——过期处理内建。
- **自定义命令**：`Cypress.Commands.add('createOrder', ...)` 把业务动作注册进
  `cy.*` 命名空间，`support/commands.js` 集中管理。

可以把 `cy.session` 想成会议的签到制度：每位参会人（角色）第一次到会时
真实验证证件（跑一遍登录步骤），签到表（缓存）盖了章，之后各场次（spec）
凭章入场；章失效（validate 不过）就重新办一次。但和签到不同的是，
不同角色的章绝对隔离——admin 与 user 各自一张表，互不串号。

## When to Use

典型场景：

- 前端降级路径：断网（forceNetworkError）断言"正在加载配置…"的优雅降级；
  POST 注入 500 断言"下单失败"弹窗。
- 多角色权限测试：admin/user 双会话各自注入，控制台一个看见统计一个被拒。
- 套件提速：慢接口桩成 5ms；登录按角色缓存——1.5s 接口与 N 次登录的成本归零。

何时不用：要验证真链路集成时（桩会把集成问题挡在门外，lab 19 同样的边界）；
`retries` 重试配置不应用于掩盖 flaky——它是 CI 止血，根因仍要靠等待哲学
与数据隔离解决（对照 lab 17）。

三件事的 Playwright 对照（同语义，表达形式不同）：

| 能力 | Cypress | Playwright（lab 19） |
|:---|:---|:---|
| 网络桩 | `cy.intercept` + `cy.wait('@别名')` | `page.route` + `expect_event` |
| 登录复用 | `cy.session`（validate 内建） | `storage_state` 存档注入 |
| 业务封装 | 自定义命令（长在 cy.* 上） | POM 页面对象（lab 18） |

## Quick Start

前置条件：labs/21 的 Cypress 二进制就绪；脚本自动起 SUT。

```bash
cd labs/22_cypress_advanced
./cypress_advanced.sh        # 两套 spec 各 3 条：intercept 三连 + session 三连
./cypress_advanced.sh observe
```

observe 的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 网络桩 spec（intercept 三连）
  │ ✔  intercept.cy.js                          623ms        3        3        -        -        - │
    ✔  All specs passed!                        623ms        3        3        -        -        -  

=====> [observe] ② 会话复用 + 自定义命令 spec（session 三连）
  │ ✔  session.cy.js                            00:01        3        3        -        -        - │
    ✔  All specs passed!                        00:01        3        3        -        -        -  
```

诚实预期：6 条用例全绿；断网降级、500 弹窗、双角色不串号全部复刻 lab 19 的
场景且通过——两代框架的等价性由此建立。注意 intercept spec 只用 623ms：
慢接口被桩成 5ms 后，banner 逻辑的验证不再等 1.5s。

关键命令（这段在做什么：桩、会话、业务命令、等待拦截的四个入口）：

```js
cy.intercept('POST', '**/api/orders', { statusCode: 500 }).as('broken')
cy.session('session-admin', loginSteps, { cacheAcrossSpecs: true, validate })
Cypress.Commands.add('createOrder', (customer) => { ... })
cy.wait('@broken')                 // 等拦截的请求发生
```

## How It Works

**intercept 的时序**：拦截注册在请求发生之前；`cy.wait('@broken')` 等的不是响应渲染而是"被拦截的请求发生过"——这让"前端真的发出了请求"成为可断言事实，对应 Playwright 的 `expect_event("dialog")` 级别的确定性等待。

桩跑在浏览器网络栈内，`window:alert` 这类对话框用 stub 收取断言。


**session 的缓存与验证**：`cacheAcrossSpecs: true` 让会话跨 spec 复用——整套跑批里 admin 角色只真正登录一次。

`validate` 回调校验 token 存在，失败自动重跑登录步骤：过期处理内建，这是它比裸 `storageState`多出来的一层保障（lab 19 需要自己在 fixture 里重建）。


**自定义命令的边界**：命令适合"全局业务原语"（createOrder、login——
任何 spec 都要用）；页面结构封装仍是 POM 模块的领地。Cypress 社区两者混用：
命令做动词，page object 做名词。

**retries 的定位**：`retries: { runMode: 1 }` 让 CI 里失败自动重试一次。
它提高"绿信号的可信度下限"（偶发抖动被吸收），但根因不解决就只是
把每次失败变成"第二次成功"——重试是止血不是治病。

## Pitfalls & Q&A

踩坑清单：

- **忘了 `cy.wait('@别名')` 直接断言**。现象：断言跑在请求发生之前，时绿时红。
  解法：需要断言"请求发生过"时必须 wait 别名。
- **session 的 validate 写得太弱**。现象：token 过期了还继续用坏会话。
  解法：validate 里真实校验 token 有效性（发一次轻量请求）。
- **把 flaky 藏进 retries**。现象：本地稳定 CI 偶红、重试后绿，没人治根因。
  解法：重试只是止血，等待哲学与数据隔离才是治病。
- **自定义命令塞满页面细节**。现象：命令成为大杂烩。
  解法：命令做业务原语，页面细节留给 page object 模块。

深入问答：

- **Q：intercept 和 Playwright route 的差异？** 能力同级；Cypress 桩跑在浏览器
  网络栈内、可配合 wait 精确断言"请求发生过"；PW 更自由（可改可转发）。
- **Q：session 缓存的是什么？** cookie + localStorage 快照；validate 失败会
  自动重建会话——过期处理内建。
- **Q：自定义命令与 POM 如何取舍？** 命令适合"全局业务原语"，POM 适合
  "页面结构封装"；Cypress 社区两者混用，POM 用 page object 模块实现。
