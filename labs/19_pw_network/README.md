# 19 · 网络拦截与登录态复用：前端测试不再看后端脸色

> E2E 必须整条链路都活着才能跑？Playwright 的 `page.route` 能把任何请求
> 桩掉、改写、注入错误——后端挂了照样测前端；`storageState` 把登录态存成文件，
> 双角色会话随取随用，且互不串号。

## 1. 为什么需要它

- 前端逻辑（降级提示、状态机、边界渲染）不需要真后端就能验证。
- 故障注入（500/断网/慢响应）在真实后端上很难造，route 一行搞定。
- 登录是最慢的用例前置——存一次状态，全套用例零登录成本。

## 2. 总览：route 拦截与 storageState 的位置

<!-- 图: images/pw_network.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/19_pw_network/images/pw_network.html)
> （或本地打开 [`images/pw_network.html`](images/pw_network.html)）。

route 中间人：请求出浏览器即被拦截（fulfill 假响应 / abort 模拟断网），
真后端全程无感；storageState 把 localStorage 快照化，注入任意新 context。

## 3. 快速开始

```bash
./pw_network.sh    # 三组观察：网络桩 / 错误注入 / 双角色会话
ls .auth/          # admin.json / user.json 两份登录态
```

## 4. 核心概念

### 4.1 route 桩：给假响应提速 300 倍

`**/api/slow-config` 被 fulfill 成 5ms 的 mock——前端拿到的是**同样的结构**，
banner 逻辑照常验证。测的是前端处理响应的能力，不是后端的快慢。

### 4.2 错误注入：abort 与 500

- `route.abort("connectionrefused")` 模拟后端断网：banner 停留加载态、
  列表为空——**优雅降级路径被真实测到**。
- POST 注入 500 → 前端弹"下单失败" alert。对话框断言用 `expect_event("dialog")`
  （本实验踩过坑：click 后立即读回调列表是竞态，必须用事件上下文等待）。

### 4.3 storageState：登录态快照

流程：UI 真登录一次 → `context.storage_state(path=...)` 存档 →
新 context 直接 `storage_state=...` 带态启动。登录态里是 localStorage 的
token/role，SUT 据此鉴权。

### 4.4 双角色不串号

admin.json 与 user.json 各自独立注入：admin 打开控制台看到统计；user 看到拒绝；
user 的 token 直接打 admin API 仍是 403——**UI 层与 API 层双重验证权限边界**。

### 4.5 易错点（本实验真实踩过）

- `localStorage` 依赖站点 origin：about:blank 上 evaluate 读取会被拒——先 goto 再读。
- route 的 glob 写 `**/api/**` 才能覆盖子路径；注册要发生在 goto 之前。

## 5. 关键字段

```python
page.route("**/api/**", handler)          # handler 里 fulfill 或 abort
route.fulfill(status=500, body=json.dumps(...))
with page.expect_event("dialog") as di:   # 对话框的确定性等待
    ...
context.storage_state(path=".auth/admin.json")
browser.new_context(storage_state=".auth/admin.json")
```

## 6. 文件结构

```
19_pw_network/
├── README.md
├── pw_network.sh
├── configs/pytest.ini
├── .auth/                    # admin.json / user.json（运行时生成）
├── tests/
│   ├── test_route_mock.py    # 桩/断网/500 三条
│   └── test_sessions.py      # 登录态保存 + 双角色三条
└── images/
```

## 7. 深入要点

- **Q: mock 后端后 E2E 还算端到端吗？** 分层看：前端交互层是端到端（浏览器→
  网络层→UI），业务正确性由真链路套件保障——两者互补，按目标选层。
- **Q: storageState 的失效怎么办？** 存"刷新凭证"或登录接口造态（API 登录比
  UI 登录快一个量级）；过期在 fixture 里自动重建。
- **Q: 故障注入还能做哪些？** 超时（fulfill 延迟）、弱网（节流）、半响应
  （截断 body）——route 回调里都是一行事。

## 8. 总结

前端测试从此独立自主。下一篇 [20_pw_quality](../20_pw_quality/README.md)：
三浏览器矩阵、视觉留痕与失败自动取证。
