# 03 · ⛓️ World 与步骤状态：类型字段、场景装备与数据隔离

> 步骤之间靠什么共享数据？答案是 World——cucumber 的场景上下文对象。
> 本实验把 lab 01 的最小 World 升级为类型安全的 SessionWorld：
> 双角色会话切换（token 直写 localStorage）、每场景前 /api/reset 隔离、
> 并以一条"探针不泄漏"场景证明隔离真实生效。

## Background

lab 02 的步骤用局部变量在 Given 与 Then 之间传数据——同一场景内够用，
但两个问题随之而来：跨步骤的类型安全靠 TS 推导勉强维持，跨角色的会话切换
（admin 与 customer 各要一个登录态）则完全没有着落。

更隐蔽的是 SUT 侧：pw-store 的订单是跨场景共享的内存态，上一个场景造的
"隔离探针甲"会在下一个场景的列表里阴魂不散。场景隔离必须两端同时做：
浏览器侧每场景全新 context（cookie/localStorage 不残留），SUT 侧每场景
reset 回种子。

## What

本实验的 SessionWorld 提供三个机制：类型化字段（page/context/role/createdTitles）、
`asRole()` 双角色会话切换（token 直写 localStorage，零 UI 登录成本）、
Before 钩子里的 /api/reset + 全新 context 装备。

可以把 World 想成剧场的后台：每个场景开演前，道具组（Before）重置舞台
（reset）并给演员全新的戏服（context），演员手里的道具清单就是 World 字段。
但和剧场不同，这里"换戏服"（asRole）不需要退场——同一个场景内可以随时
切换角色会话，前后台数据仍以服务端为准。

![World 三机制：类型字段、场景装备、数据隔离](images/world.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/03_world_state/images/world.html)
> （或本地打开 [`images/world.html`](images/world.html)）。
> 隔离有两翼：SUT 侧 /api/reset 与浏览器侧全新 context，缺一即漏。

## When to Use

| 需求 | World 字段 | 步骤局部变量 |
|:---|:---|:---|
| 多个步骤文件共享同一状态 | ✅ 唯一选择 | ❌ 局部变量跨文件不可见 |
| 双角色会话切换 | ✅ asRole 封装 | 每次手写登录 |
| 场景间数据隔离 | ✅ Before reset | ❌ 管不到 SUT |
| 单场景内临时计算值 | ⚠️ 会污染 World 命名空间 | ✅ 就近声明 |

判断口径：**跨步骤/跨文件的放 World，场景内临时的用局部变量**。
World 字段要命名得像业务概念（createdTitles），不是垃圾抽屉。

## Quick Start

```bash
cd cucumber/03_world_state
./world_state.sh          # apply 起靶场 → observe 隔离三场景 → clean
```

observe ① 三场景全绿，其中场景 2 是隔离性的直接证明：

```
...........

2 hooks (2 passed)
3 scenarios (3 passed)
15 steps (15 passed)
```

场景 1 创建"隔离探针甲"并断言可见；场景 2 创建"隔离探针乙"后断言
"探针甲"**不存在**——若 Before 里没有 /api/reset，这条必红。
验收方式：三场景全绿；变异实验：注释掉 Before 里的 reset 调用重跑，
场景 2 立即变红（上一个场景的数据泄漏进来了）。

## How It Works

**setWorldConstructor 换掉默认 World。** cucumber 的步骤函数 this 默认是
空 World；注册自定义类后，this 就是 SessionWorld 实例——字段带类型，
TS 全程校验。与 lab 01 的差别只在字段多了、语义清晰了，机制相同。

**asRole 重开 context 而不是改 localStorage。** 同一 context 里改
localStorage 后已加载的页面不会重新读取（SPA 只在启动时读一次）；
重开 context + 新 page 才是干净的会话切换。

注意 initScript 里写入的 role/username 必须与 token 一致——
UI 展示读 localStorage，API 鉴权读 token，
两者不一致会出现"界面是 admin、接口 403"的错位（本实验实测踩坑）。

**隔离是两端动作。** SUT 侧 Before 里 `POST /api/reset`（管理员权限）把
订单回种子；浏览器侧每场景全新 context。

只做前者，localStorage 的登录态会跨场景残留；
只做后者，SUT 的订单数据会累积。双翼齐飞才有真正的"每个场景都是新世界"。

**探针场景是隔离性的回归测试。** 场景 1 埋"探针甲"、场景 2 断言其不存在——
这条用例测的不是产品功能而是测试基础设施本身。

基础设施的回归测试与业务回归同等重要：
隔离一旦失效，所有计数类断言全部失真。

## Pitfalls & Q&A

**Q：为什么 asRole 重开 context 而不是直接改 localStorage？**
SPA 只在启动时读一次 localStorage（App 初始化函数），改完存储已加载的
页面不会重读——除非 reload。

重开 context 是确定性的：新页面、新存储、新 WS 连接，一次到位。
reload 也能触发重读，但旧 context 里的其他状态（service worker、缓存）
仍会残留。

**Q：localStorage 的 role 和 token 不一致会怎样？**
界面显示按 localStorage（欢迎语、角色徽标），API 鉴权按 token 解码——
不一致时会出现"界面显示管理员、接口 403"的错位（实测踩过：token 用
customer 的、展示字段忘改）。

原则：两处必须同源写入，asRole 的 initScript 就是同源写入点。

**Q：Before 里的 reset 失败了会怎样？**
World 的 Before 抛错，该场景标记失败并跳过步骤——不会带病执行。

这是想要的行为：隔离失败比断言失败更严重，因为它影响的不止一条断言。
dbg 排障时先确认 reset 的响应是 200（非 admin token 会得到 403）。

**Q：World 字段越加越多怎么办？**
按业务域拆分访问器：World 只挂两三个聚合对象（page/store/auth），
细节藏在各自类里。cucumber 也支持多个 setWorldConstructor 的参数合并
（mixin 形态），但优先用组合——World 的命名空间和页面一样需要设计。

**Q：场景内切换角色后，之前的 page 还能用吗？**
不能。asRole 关闭了旧 context，旧 page 引用已失效——继续用会报
"Target closed"。本实验的步骤定义每次从 `this.asRole(...)` 的返回值
取新 page，不用 World 上缓存的旧引用。切换即换页，这是纪律。
