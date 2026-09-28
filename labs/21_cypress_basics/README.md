# 21 · Cypress 入门：测试跑在浏览器里的另一种世界观

> Playwright 从外部驱动浏览器，Cypress 把测试放进浏览器里跑——命令链执行在
> 你眼前，时间旅行调试是招牌。读完本篇你能跑通同一 SUT 的三条 Cypress 用例
> （与 lab 16 同语义），并形成两代框架的第一印象对照——为 lab 25 的选型收口攒依据。

## Background

E2E 框架有两条技术路线。Playwright（lab 16-20）代表"外部驱动"：
Node 侧的测试代码通过协议指挥浏览器，测试进程与页面进程分离。
另一条路线是"浏览器内执行"：测试代码被注入到页面所在的浏览器里，
与前端应用同进程——Cypress 是这条路线的代表，也是前端团队接受度最高的框架。

外部驱动的调试是事后的：跑完才能打开 trace 回看。前端团队想要的是当场看到
每条命令后的页面状态、错误信息直接面向 UI——Cypress 由此把测试搬进浏览器内。

为什么值得学第二套：选型判断需要第一手对照。同一 SUT、同样三条用例
（下单/查询/删除），用两个框架各写一遍，执行位置、等待语义、调试体验的
差异才会从"文档上的对比表"变成"亲手用过的感受"。lab 25 的三国杀收口
（Playwright / Cypress / Selenium 同题对比）就从这里开始攒证据。

## What

Cypress 是一个"测试运行在浏览器里"的 E2E 框架：spec（测试文件）经代理层
注入 Electron 浏览器（自带 Chromium 内核的桌面应用），测试代码与页面同进程
执行；`cypress open` 是交互式运行器（命令日志 + 快照悬停），
`cypress run` 是 headless 跑批。

可以把 Cypress 想成考场设在家里：考官（测试代码）和考生（页面）在同一个房间（浏览器进程）里，考官每个动作（点击、填表）当场记录在黑板上（命令日志），每个瞬间都能回看（时间旅行快照）。

但和在家里考试不同的是，考场规则也更严：单域/同源限制（同源：协议+域名+端口三者相同才允许互相访问，浏览器的安全规则）、只用自带的一个内核——自由度换来了体验。


目录约定即配置：`cypress/e2e/` 放 spec，`cypress/support/` 放自定义命令
（lab 22），根上 `cypress.config.js` 是唯一配置位。

## When to Use

典型场景：

- 前端团队自维护 E2E：运行器可视化、错误信息面向 UI，前端工程师上手最快。
- 组件级交互回归：命令链 + 自动重试适合"点开下拉→选项出现→选中"这类链式交互。
- 需要给非工程师演示测试：交互式运行器的命令日志与快照就是现成的演示。

何时不用：需要多内核矩阵（lab 20 的三核）或多标签/多域场景——Cypress
单内核单域的安全模型是硬约束；重后端集成验证也更适合 API 层
（lab 12）+ Playwright 组合。

与 Playwright 的三条第一印象差异（同 SUT 同用例实测）：

| 维度 | Cypress | Playwright |
|:---|:---|:---|
| 执行位置 | 浏览器内（同进程） | Node 侧驱动（跨进程） |
| 调试体验 | 运行器命令日志 + 快照悬停 | trace viewer 时间旅行 |
| 自由度 | 单域、单内核（Electron） | 多核多标签多域 |

## Quick Start

前置条件：labs/00 体检通过（Node 20+ / npm 就绪，cypress 为本实验 package.json
里的 devDependency，首次运行会下载二进制）。

```bash
cd labs/21_cypress_basics
./cypress_basics.sh          # 起 SUT(8921) → cypress run 三条 spec → 清理
CYPRESS_SUT_URL=http://127.0.0.1:8921 npx cypress open   # 交互式体验
```

headless 跑批的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① headless 跑三条 spec（与 Playwright 项目 16 同语义）
  Running:  orders.cy.js                                                                    (1 of 1)
    ✓ 下单：填表提交后新订单出现在列表 (527ms)
    ✓ 查询：订单列表至少有一行且表头齐全 (42ms)
    ✓ 删除：创建一行再删掉，行从列表消失 (536ms)
  │ ✔  orders.cy.js                             00:01        3        3        -        -        - │
    ✔  All specs passed!                        00:01        3        3        -        -        -  
```

诚实预期：三条用例 headless 约 1 秒全绿（Electron 启动后极快）；
交互式运行器需要手动体验，命令是上面第二行——运行器里每条命令
点击可展开当时的页面快照。新手第一个失败点：spec 文件名不匹配
`specPattern`（默认 `**/*.cy.js`）时会显示"没有找到用例"。

关键配置 `cypress.config.js`（这段在做什么：baseUrl、supportFile 与取证开关）：

```js
module.exports = defineConfig({
  e2e: { baseUrl, supportFile, video: false, screenshotOnRunFailure: true },
})
```

## How It Works

**命令链的执行模型**：`cy.get(...).type(...)` 是命令链不是 Promise——命令入队、按序执行、`should()` 自带重试。

写下这行代码的瞬间命令并没有执行，它们被排进队列由 Cypress 运行器逐条消费。理解"入队"才能解释两个常见困惑：为什么不能把 `cy.get()` 的返回值存变量（队列入队时值还不存在），为什么 `.then()` 里才能拿到真实值。


**等待语义对照**：`should()` 的重试与 Playwright 的 `expect` 异曲同工，
但重试粒度不同——Cypress 重试"最后一条命令链"（整链重放），
Playwright 重试"locator 解析"（表达式重查）。表达形式不同，
"断言结果不断言时刻"的哲学一致（lab 17）。

**进程模型带来的差异**：测试代码与页面同进程，所以 Cypress 能做时间旅行快照
（每条命令后的页面状态都在内存里）；同样的原因，它出不了这个进程——
多标签、跨域、多内核都受限。跨域需实验性的 `cy.origin`，
多内核则完全不提供。

**baseUrl 的注入**：写死在 config 里会被环境变量覆盖——本实验用
`CYPRESS_SUT_URL` 注入 8921 端口的 SUT，配置文件因此无需为环境改动。

## Pitfalls & Q&A

踩坑清单：

- **把 `cy.get()` 的返回值存进变量**。现象：变量是 undefined 或"过期"。
  原因：命令链是入队不是执行，变量赋值瞬间值不存在。解法：用 `.then()` 或
  继续链式。
- **spec 文件名不匹配 specPattern**。现象：运行器显示 0 个用例。
  解法：默认 `**/*.cy.js`，要么按约定命名，要么改 config 的 specPattern。
- **期待多标签/多域支持**。现象：跨域操作报错。原因：同进程同源的安全模型。
  解法：实验性 `cy.origin`，或此类场景换 Playwright。
- **首次运行卡在下载**。现象：`cypress run` 长时间无输出。
  原因：Electron 二进制下载。解法：等一次（之后有缓存），或配镜像。

深入问答：

- **Q：Cypress 为什么不能多标签/多域？** 同进程同源的安全模型决定；
  跨域需实验性 `cy.origin`。
- **Q：`should` 的重试和 Playwright `expect` 有何不同？** 语义相近；
  Cypress 重试"最后一条命令链"，PW 重试"locator 解析"——粒度不同。
- **Q：什么时候选 Cypress？** 前端团队自维护、需要最好的运行器体验、
  接受单内核约束的场景——完整对照见 lab 25。
