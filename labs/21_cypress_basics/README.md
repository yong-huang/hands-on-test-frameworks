# 21 · Cypress 入门：测试跑在浏览器里的另一种世界观

> Playwright 从外部驱动浏览器，Cypress 把测试**放进浏览器里跑**——
> 命令链执行在你眼前，时间旅行调试是招牌。本篇用同一 SUT 复刻项目 16 的
> 三条用例，亲手对比两代框架的第一印象。

## 1. 为什么需要它

- 前端团队最爱 Cypress：运行器可视化、错误信息面向 UI、生态插件成熟。
- 与 Playwright 同 SUT 同用例对照，才能形成有依据的选型判断（lab 25 收口）。

## 2. 总览：Cypress 的进程模型

<!-- 图: images/cypress_basics.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/21_cypress_basics/images/cypress_basics.html)
> （或本地打开 [`images/cypress_basics.html`](images/cypress_basics.html)）。

spec 经代理层注入 Electron 浏览器，测试代码与页面同进程执行；
`cypress open` 是交互式运行器，`cypress run` 是 headless 跑批。

## 3. 快速开始

```bash
./cypress_basics.sh          # 起 SUT(8921) → cypress run 三条 spec → 清理
CYPRESS_SUT_URL=http://127.0.0.1:8921 npx cypress open   # 交互式体验
```

实测：3 条用例 headless 1 秒全绿（Electron 启动后极快）。

## 4. 核心概念

### 4.1 命令链与自动等待

`cy.get(...).type(...)` 是命令链不是 Promise——命令入队、按序执行、
`should()` 自带重试。等待哲学与 Playwright 的 expect 异曲同工，但表达形式不同。

### 4.2 与 Playwright 的三条第一印象差异（实测）

1. **执行位置**：Cypress 在浏览器内跑，Playwright 在 Node 侧驱动。
2. **调试体验**：Cypress 运行器命令日志 + 快照悬停是招牌；PW 靠 trace viewer。
3. **约束**：Cypress 单域/同源限制、单内核（Electron）；PW 多核多标签自由。

### 4.3 目录约定

`cypress/e2e/` 放 spec，`cypress/support/` 放自定义命令（lab 22），
根上 `cypress.config.js` 是唯一配置位——约定即配置。

### 4.4 易错点

- baseUrl 写在 config 里可被环境变量覆盖（本实验用 `CYPRESS_SUT_URL` 注入）。
- spec 文件命名必须匹配 specPattern（默认 `**/*.cy.js`）。

## 5. 关键配置

```js
module.exports = defineConfig({
  e2e: { baseUrl, supportFile, video: false, screenshotOnRunFailure: true },
})
```

## 6. 文件结构

```
21_cypress_basics/
├── README.md
├── cypress_basics.sh          # SUT 生命周期 + headless 跑批
├── cypress.config.js
├── cypress/e2e/orders.cy.js   # 下单/查询/删除（与 lab 16 同语义）
├── package.json               # npm 工程（cypress 为 devDependency）
└── images/
```

## 7. 深入要点

- **Q: Cypress 为什么不能多标签/多域？** 同进程同源的安全模型决定；
  跨域需实验性 `cy.origin`。
- **Q: should 的重试和 Playwright expect 有何不同？** 语义相近；
  Cypress 重试"最后一条命令链"，PW 重试"locator 解析"——粒度不同。
- **Q: 什么时候选 Cypress？** 前端团队自维护、需要最好的运行器体验、
  接受单内核约束的场景。

## 8. 总结

三国杀开局。下一篇 [22_cypress_advanced](../22_cypress_advanced/README.md)：
intercept、session 与自定义命令——复刻 lab 19 的全套场景。
