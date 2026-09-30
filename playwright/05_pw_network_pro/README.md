# 05 · 网络控制进阶：HAR 回放与错误注入

> E2E 最大的依赖就是"后端活着且数据恰好对"。本实验把网络层变成测试的可控输入：
> 用 HAR（HTTP Archive，一次真实流量轨迹的存档文件）录制回放，让前端用例脱离后端运行；
> 用 route 钩子注入 500、断连与 3 秒慢接口，验证页面的降级表现。
> 全流程脚本里有一段"先杀后端再跑回放"的硬核演示。

## Background

lab 02-04 的用例都跑在真实后端上，这带来两类麻烦：一是环境耦合——后端挂了、
测试数据被别人改了，用例就集体变红；二是异常路径测不到——"接口返回 500 时页面怎么办"、
"接口慢到 3 秒时用户看到什么"，真实后端很难稳定配合演出。

网络虚拟化（在测试与真实网络之间插入一层可编程的拦截层）是解法。
Playwright 把这层做成了 route 钩子：每个请求流经测试代码，可以放行、改写、拦截或延迟。
其中 HAR 回放是力度最大的一种：把一次真实交互的完整 HTTP 轨迹存成文件，
之后测试完全离线运行。

## What

route（路由钩子）是 Playwright 在网络栈里开的口子，注册时给定 URL 匹配模式与处理函数。
本实验用到它的三种形态：`routeFromHAR`（整站录制与回放）、`route.fulfill`（伪造应答）、
`route.fetch` + delay（取真实应答但人为压慢）。

可以把 route 层想成快递分拣中心：所有包裹（请求）必须过安检台，
安检员可以盖"照常投递"章（continue，可顺手延迟）、拿出伪造的签收单直接回执（fulfill）、
或把包裹直接扔掉（abort）。但和真实分拣不同，安检规则写在测试代码里，
每个用例可以临时换一套规则，互不影响。

![网络控制层：page 请求经三种 route 处理后流向 HAR / 后端 / 降级 UI](images/netflow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/playwright/05_pw_network_pro/images/netflow.html)
> （或本地打开 [`images/netflow.html`](images/netflow.html)）。
> 图上三条"请求上行"边分别进入 HAR 层、拦截层、延迟层——同一个钩子机制的三种用法。

## When to Use

| 手段 | 适用场景 | 本实验靶点 |
|:---|:---|:---|
| HAR 回放 | 核心路径回归不依赖后端；演示/开发用前端数据 | 离线跑通登录 + 下单 |
| `route.fulfill` 伪造 | 异常码、畸形数据、边界响应 | 500 注入看错误 UI |
| `route.abort` | 断网、超时、服务不可达 | 断连注入看降级 |
| `route.fetch` + delay | 真实数据 + 人为延迟 | 3s 慢接口看 loading |
| `waitForResponse` | 断言"响应本身"而非仅 UI | 下单 201 与响应体 |

何时不用：需要"随请求变化的有状态 mock"时，HAR 回放力不从心（见 Pitfalls），
应改用 `route.fulfill` + 闭包计数，或直接起一个内存版 mock 服务。

## Quick Start

```bash
cd playwright/05_pw_network_pro
./network_pro.sh          # apply 体检 → observe 录制/注入/离线三步 → clean
```

observe ① 用 `update: true` 模式走一遍真实路径（登录 → 下单），全程 HTTP 交互
被录进 `har/pw-store.har`（含响应体，约 168KB）。

observe ② 是注入套件：伪造 500 看错误提示、3 秒慢接口看 loading、
断连看降级、`waitForResponse` 对齐下单响应：

```
✓  1 [chromium] › 录制：登录 → 下单 的完整 HTTP 轨迹 (709ms)
✓  2 [chromium] › 500 注入：订单接口挂了，页面出现正确错误提示 (158ms)
✓  3 [chromium] › 3s 慢接口注入：loading 态真实可见，数据到达后表格渲染 (4.5s)
  5 passed (6.1s)

四条注入用例之外还有一条录制用例——脚本故意让它随跑：保证回放用的 HAR
永远新鲜。验收口径：注入套件 4 条全绿（连同录制共 5 条）。
```

observe ③ 是本实验的高光：先 `kill` 掉 9005 端口的后端并确认探活不可达，
然后用独立配置（`configs/offline.config.ts`，不含 webServer）跑回放套件：

```
>>> 后端已确认下线（/api/health 不可达），开始离线回放：
  1 passed (483ms)
>>> 后端不在线，回放套件全绿 ✓
```

验收方式：回放套件在后端下线状态下全绿；注入套件 4 条全绿；
`./network_pro.sh clean` 后 `lsof -i :9005` 无残留。

## How It Works

**录制是"穿透 + 记账"。** `routeFromHAR(har, { update: true, updateContent: 'embed' })`
让请求照常打到真实后端，同时把每个请求/应答对写进 HAR 文件。

`updateContent: 'embed'` 必须带上——它把响应体嵌进文件，否则录到的是只有头的空壳
（本实验实测踩过：回放侧 JSON 解析直接失败）。录完的 HAR 就是回放侧的全部家当。

**回放是"按 URL + 方法查表"。** 不带 `update` 的 `routeFromHAR` 在每个请求发出时
查 HAR 里的录制条目，命中即回放应答。

查表意味着：登录页不发请求就不会有登录应答；WebSocket 完全不在 HAR 能力范围内
（它是协议升级不是 HTTP 请求，lab 15 用 mock 帧解决）。

**注入是在安检台上换规则。** `page.route('**/api/orders', handler)` 注册后，
命中模式的请求进 handler，处理方式三选一：伪造回执（`route.fulfill`，本实验伪造 500）、
模拟断连（`route.abort`）、或放行真实请求。

第三种最巧：`route.fetch()` 先取真实应答，压住 3 秒再回执——
数据是真的，慢是人造的，loading 态因此真实可见。

**`waitForResponse` 是"先等后动"。** 断言响应本身时，先挂 `waitForResponse` 拿到
Promise，再触发点击，最后 `await`——顺序反了就会错过响应。
比事后翻 `page.on('response')` 日志更精确，是竞态断言的标准姿势。

## Pitfalls & Q&A

**Q：为什么离线回放只断言到"下单返回 201"，不刷新列表验证新订单出现？**
这是 HAR 回放的语义边界：**同一请求永远拿到同一条录制应答**，它不按调用次数
推进条目，也不理解服务端状态（本实验实测踩过：reload 后列表仍是录制时的种子数据）。

HAR 是一盘录像带：每次播放同一段录像，不因你看了一遍就改剧情——
所以回放路径的断言应落在每一步的响应正确，而不是服务端状态演进。

**Q：`configs/offline.config.ts` 为什么把 testDir 写成相对路径的绝对化形式？**
Playwright 的路径（testDir、storageState 等）相对**配置文件自身**解析。

配置放在 `configs/` 子目录时 `./tests` 会指到不存在的 `configs/tests`，
所以要写 `fileURLToPath(new URL('../tests', import.meta.url))` 显式指回实验根。

配置放在 `configs/` 子目录时，`./tests` 会指到 `configs/tests`（不存在），
于是报 "No tests found"（本实验实测踩过）。子目录配置一律用绝对路径指回实验根。

**Q：回放路径必须和录制路径完全一样吗？**
请求序列同形最稳。回放按 URL + 方法查表，回放时多发一个录制里没有的请求
会以失败告终；少发则无所谓（多余条目闲置）。所以录制用例与回放用例
保持"同样的用户路径"是纪律，不是巧合。

**Q：3 秒慢接口注入会不会让套件变慢？**
只会慢这一条用例（4.5s），且慢得有价值——它验证的是"延迟窗口内 loading 可见"这个
真实产品行为。不设延迟上限的话，`expect.timeout`（5s）会先超时把问题暴露出来，
这也是一种保护。

**Q：注入会不会影响其他用例？**
不会。`page.route` 注册在当前 page 上，用例结束即销毁；
跨用例想共享注入规则，用 `context.route` 或 config 的 `use.serviceWorkers` 同级的
全局钩子。本系列约定：注入规则随用例走，可读性优先。
