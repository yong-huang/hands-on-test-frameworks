# 10 · 并行与隔离：4 workers 抢一个 SUT 的秩序

> cucumber 的 `parallel: 4` 让 10 个场景分布在 4 个 worker 上同时执行——
> 速度换秩序：所有"恰好没撞上"的数据竞争集中爆发。本实验用唯一前缀协议
> 证明零串号（10 场景 4 workers 全绿），并把隔离纪律写进 World 的数据工厂。

## Background

BDD 套件的并行与 lab 10（playwright/ 系列）面临同一道题：SUT 是跨 worker
共享的内存态，并行下"A 刚建的订单"和"B 刚删的订单"交错出现，
按总数断言的用例必然随机红。

解法也与 playwright/10 同源：**唯一前缀协议**——每个场景的数据带
唯一前缀（worker 序号 + 时间戳 + 随机数），断言只认自己的那一笔。
并行自由不靠运气，靠数据协议。

## What

本实验的 World 内置数据工厂：`this.prefix` 字段自动生成唯一前缀，
`apiCreate()` 用 fetch 直打 API（毫秒级）创建订单。10 个场景共享同一组
步骤定义（"管理员创建自己的订单" → "恰好存在自己的那 1 笔"），
靠 World 的前缀字段天然隔离。

可以把并行想成四条流水线同时灌装：瓶子（场景）不同、饮料（数据）不同，
但都进同一个仓库（SUT）。仓库管理员（断言）只核对条码（唯一前缀），
不数总数——总数永远在变，条码永远唯一。

![并行隔离：唯一前缀协议下的 4 worker 执行](images/parallel.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/10_parallel/images/parallel.html)
> （或本地打开 [`images/parallel.html`](images/parallel.html)）。
> 两条 worker 泳道各自"造数 → 只认自己"，虚线 POST 汇入共享 SUT。

## When to Use

| 场景 | parallel: 4 | parallel: 1 |
|:---|:---|:---|
| 唯一前缀协议下的独立场景 | ✅ 主战场 | 慢但可 |
| 断言全局总数/列表顺序 | ❌ 必然漂移 | ✅ 串行才确定 |
| 调试可疑的串号 | ❌ 干扰判断 | ✅ 先降维复现 |

判断口径：**先写对隔离协议再开并行**。protocol 之外的并行收益是碰运气。

## Quick Start

```bash
cd cucumber/10_parallel
./parallel.sh          # apply 起靶场 → observe 10 场景并行全绿 → clean
```

observe ① 10 场景 × 4 workers 全绿：

```
8 hooks (8 passed)
10 scenarios (10 passed)
40 steps (40 passed)
```

验收方式：全绿且无 failed/flaky。串号实验：把步骤里的 `lastTitle`
改成固定标题（如"共享订单"），并行重跑多次——计数断言随机红，
这就是协议缺失的代价。

## How It Works

**唯一前缀是并行场景的数据协议。** World 的 prefix 字段在每次实例化时
生成 `W{workerIndex}-{时间戳}-{随机数}`——跨 worker、跨重跑、
跨场景三重唯一。

步骤里 `apiCreate(`${this.prefix}-订单`)` 创建、
`filter({ hasText: lastTitle })` 断言，数据自产自销互不可见。

**API 造数 + UI 验证的分工。** 创建走 fetch 直打（毫秒级），
浏览器只负责打开页面断言呈现——与 lab 17 的分层一致：
被测交互是"列表正确显示"，不是"表单填得快"。

**parallel 的粒度是 feature 文件。** cucumber 的并行按文件分发到 worker：
同文件场景切给不同 worker，跨文件并行同样成立。

文件是并行的天然边界，也是"按业务域拆 feature"的另一个理由。

**Before 里的 reset 是并行安全的吗？**
不完全——两个 worker 的场景交叠时，A 的 reset 会清掉 B 刚造的数据。

本实验的对策：每个场景的断言只依赖自己创建的行（前缀隔离），
reset 只是把"起点"拉回种子，容忍交叠窗口。
更强的隔离需要数据域命名空间（按 worker 分区），属于规模化课题。

## Pitfalls & Q&A

**Q：为什么在 When 里断言 status === 201？**
API 造数失败时，后面的 UI 断言会以"找不到行"失败——错误信息脱离根因。
在 When 里就地断言 201，失败信息直指"造数失败"，排障路径最短。
这是"每个动作步骤自带前置校验"的实践。

**Q：parallel: 4 但只有 10 个快场景，加速明显吗？**
本实验实测总时长约 1.2s（含浏览器启动）——轻量套件的并行收益被
固定成本稀释（playwright/18 的同结论）。并行是规模化工具：
套件达到分钟级后收益才显现，协议先行是为了将来不返工。

**Q：World 的 prefix 在场景内多次创建订单会重复吗？**
会重复——prefix 只保证跨场景唯一，场景内多次创建需再加序号
（`this.prefix + '-2'`）。本实验每场景一笔所以无此问题；
多笔场景应把序号并入协议（lab 18 的 40 条池就是 `前缀+序号` 形态）。

**Q：SUT 的 /api/reset 在并行下安全吗？**
不安全但有界：reset 清空全部订单，交叠窗口内其他 worker 断言过的行
会被清掉——但前缀协议的断言只认"自己的行是否还存在"，
被清掉时会以"找不到"失败暴露，而不是假绿。

彻底解法是按 worker 分区数据域（规模化课题），
本实验用"断言窗口短 + 前缀唯一"把风险压到概率级。

**Q：cucumber 的并行和 Playwright 的 workers 是一回事吗？**
层级不同：cucumber 的 parallel 决定开多少个"场景执行流"，
每个流内的 Playwright page 是一个浏览器标签页级上下文。

playwright/ 系列的 workers 是测试进程。cucumber 场景里的浏览器
共享同一个 chromium 实例的不同 context——资源占用更低，
但一个浏览器崩溃会影响同 worker 的后续场景。
