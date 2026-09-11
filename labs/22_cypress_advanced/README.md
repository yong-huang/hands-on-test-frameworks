# 22 · Cypress 进阶：intercept / session / 自定义命令

> 上篇是"能用"，本篇是"好用"：`cy.intercept` 桩网络、`cy.session` 缓存登录、
> 自定义命令把业务动作变成 `cy.createOrder()`——对应 Playwright lab 19 的
> 全部场景，同 SUT 同语义，方便逐条对照两代框架的表达力。

## 1. 为什么需要它

- 网络桩与登录复用决定套件速度与稳定性；自定义命令决定可维护性。
- 三件事都是 Cypress 的招牌能力，也是它和 Playwright 对比的核心战场。

## 2. 总览：intercept 与 session 的协作时序

<!-- 图: images/cypress_advanced.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/22_cypress_advanced/images/cypress_advanced.html)
> （或本地打开 [`images/cypress_advanced.html`](images/cypress_advanced.html)）。

intercept 在网络层拦请求（桩/断网/500），session 把登录态缓存为"角色"，
自定义命令把业务语言注入 `cy.*` 命名空间。

## 3. 快速开始

```bash
./cypress_advanced.sh        # 两套 spec 各 3 条：intercept 三连 + session 三连
```

实测：6 条用例全绿；断网降级、500 弹窗、双角色不串号全部复刻 lab 19。

## 4. 核心概念

### 4.1 cy.intercept 三连

- 桩慢接口：`{ body: {...} }`——1.5s 变 5ms，banner 逻辑照常验证；
- `forceNetworkError: true`——断网，断言"正在加载配置…"的优雅降级；
- POST 注入 500——监听 `window:alert` 断言"下单失败"提示（Cypress 用 stub 收弹窗，
  对应 PW 的 `expect_event("dialog")`）。

### 4.2 cy.session：登录态按角色缓存

`cy.session('session-admin', 登录步骤, { cacheAcrossSpecs: true, validate })`——
同一角色整套跑批只真正登录一次，validate 校验 token 存在。admin 与 user
各自独立会话，控制台一个看见统计一个被拒——**不串号**。

### 4.3 自定义命令

`Cypress.Commands.add('createOrder', ...)` 把"下单"封装成业务命令，
support/commands.js 集中注册——对应 Playwright 世界的 POM（lab 18），
但直接长在 cy.* 命名空间里。

### 4.4 失败重试与 flaky 治理

`retries: { runMode: 1 }` 让 CI 里失败自动重试一次。**重试是止血不是治病**：
根因仍要用等待哲学与数据隔离解决（对照 lab 17）。

## 5. 关键命令

```js
cy.intercept('POST', '**/api/orders', { statusCode: 500 }).as('broken')
cy.session('session-admin', loginSteps, { cacheAcrossSpecs: true, validate })
Cypress.Commands.add('createOrder', (customer) => { ... })
cy.wait('@broken')                 // 等拦截的请求发生
```

## 6. 文件结构

```
22_cypress_advanced/
├── README.md
├── cypress_advanced.sh
├── cypress.config.js           # retries 开关在这里
├── cypress/
│   ├── e2e/
│   │   ├── intercept.cy.js     # 桩/断网/500 三连
│   │   └── session.cy.js       # 双角色 + 自定义命令
│   └── support/
│       ├── commands.js         # createOrder / login
│       └── e2e.js
└── images/
```

## 7. 深入要点

- **Q: intercept 和 Playwright route 的差异？** 能力同级；Cypress 桩跑在浏览器
  网络栈内、可配合 wait 精确断言"请求发生过"；PW 更自由（可改可转发）。
- **Q: session 缓存的是什么？** cookie + localStorage 快照；validate 失败会
  自动重建会话——过期处理内建。
- **Q: 自定义命令与 POM 如何取舍？** 命令适合"全局业务原语"，POM 适合
  "页面结构封装"；Cypress 社区两者混用，POM 用 page object 模块实现。

## 8. 总结

Cypress 全技能达成，与 lab 19 逐条对应。下一篇
[23_selenium_basics](../23_selenium_basics/README.md)：回到协议时代——WebDriver 直感。
