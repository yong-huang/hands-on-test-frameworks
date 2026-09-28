# 27 · 负载与阈值（k6）：场景即代码，阈值即门禁

> Locust 擅长"用 Python 探索容量"，k6 擅长"把性能塞进 CI"：场景用 JS 声明、
> thresholds 不达标就退出码非 0——性能回归和功能回归用同一套红绿语言。
> 读完本篇你能用一份脚本跑 smoke/ramping/spike 三种负载形态，
> 并亲手触发一次性能门禁拦截。

## Background

性能测试做完一次报告就归档，是它最大的浪费：容量会随代码演进漂移，
上次压测的结论三个月后可能已不成立。性能要"保持"，就得像功能测试一样
进 CI——每次发版自动验一遍，性能变差变成可拦截的事件，而不是上线后的工单。

把性能塞进 CI 需要三种负载形态配合：部署后的**秒级验活**（smoke，
1 个用户 15 秒确认服务活着）、**找拐点的爬坡**（ramping）、
**复现突发流量的突刺**（spike）。以及一个决定性的机制：**阈值即退出码**——
P95、错误率不达标就非 0 退出，CI 的红绿语言对性能同样生效。

k6（Go 编写的负载测试工具，场景用 JS 声明）把这四件事做成了原生语义。

## What

k6 的两个核心概念：**场景（scenario）**声明负载形态（多少虚拟用户、
怎么爬坡、按到达率还是按用户数），**阈值（thresholds）**声明性能红线
（不达标退出码非 0）。

可以把 thresholds 想成高速的区间测速：不拦你怎么开，只在你超过限速
（P95 超 500ms、错误率超 1%）时拍下违规记录并计入处罚（CI 红灯）。
但和测速不同的是，限速可以**按车道设置**——给请求打标签
（`endpoint:fast`），阈值只约束该管的端点，慢接口的已知设计不污染全局。

三种场景形态（一份脚本，`SCENARIO` 环境变量切换）：

| 场景 | executor（执行器：k6 里声明"怎么施压"的配置块） | 形态 | 用途 |
|:---|:---|:---|:---|
| smoke | constant-vus (1 VU——虚拟用户/15s) | 单用户验活 | 部署后秒级检查 |
| ramping | ramping-vus (0→20→0) | 爬坡-稳态-收尾 | 找拐点 |
| spike | ramping-arrival-rate (5→60/s) | 到达率突刺 | 复现突发流量 |

## When to Use

典型场景：

- 部署后冒烟：15 秒 smoke 确认性能基线没塌，塌了流水线当场红。
- 夜间容量回归：ramping 场景跑拐点，与上次基线对比。
- 发版前突刺演练：spike 场景复现"整点抢购"式到达率冲击。

何时不用：探索期调优用 Locust 更顺手（Python 场景逻辑更自由、并发模型
更直观）；一次性容量探索也不必配门禁——thresholds 的价值在"持续"，
不持续就不值得维护阈值。

本机实测（2026-09-28，节选）：

- ramping 稳态 13092 checks、checks 成功率 100%，快接口
  `p(95)=5.74ms`（avg 2.38ms）；
- spike 到达率 5→60/s 突刺下 `p(95)=1.68ms`，延迟未抬升（本机余量大）；
- 门禁演示：对 1.5s 慢接口设 `p(95)<500` → `p(95)=1.51s` 违例 →
  **退出码 99**。

## Quick Start

前置条件：labs/00 体检通过（k6 CLI 就绪）。

```bash
cd labs/27_k6
./k6_run.sh                  # 起 SUT(8927) → 三场景全跑 + 门禁失败演示
BASE_URL=... k6 run -e SCENARIO=smoke load.js   # 单场景
```

smoke 与门禁演示的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① smoke 场景（1 VU 15s）：部署后秒级验活
     scenarios: (100.00%) 1 scenario, 1 max VUs, 45s max duration (incl. graceful stop):
    http_req_duration{endpoint:fast}
    ✓ 'p(95)<500' p(95)=1.93ms
    ✓ 'rate<0.01' rate=0.00%
    checks_total.......: 222     14.635736/s
    checks_succeeded...: 100.00% 222 out of 222

=====> [observe] ④ thresholds 门禁演示：对 1.5s 慢接口设 p95<500 → 不达标退出码非 0（预期失败）
    ✗ 'p(95)<500' p(95)=1.51s
time="2026-09-28T21:51:16+08:00" level=error msg="thresholds on metrics 'http_req_duration' have been crossed"
>>> 退出码 = 99（非 0：thresholds 不达标即 CI 门禁红线）
```

诚实预期：smoke/ramping/spike 三场景应全绿（checks 100%）；④ 的门禁违例是
**故意把阈值设到慢接口头上**的演示（`slow_threshold_demo.js`），退出码 99
正是预期产物——k6 用 99 这个退出码表示"阈值被突破"，区别于其他错误。

关键配置（这段在做什么：场景选择与带标签的阈值红线）：

```js
export const options = {
  scenarios: { main: scenarios[__ENV.SCENARIO] },
  thresholds: {
    'http_req_duration{endpoint:fast}': ['p(95)<500'],
    'http_req_failed': ['rate<0.01'],
  },
};
```

## How It Works

**标签过滤的精度**：慢接口 1.5s 是 SUT 的已知设计（lab 11 预埋的等待训练靶），
不能让它的 P95 污染全局阈值。

`http.get(url, { tags: { endpoint: 'fast' } })` 给请求打标，
`http_req_duration{endpoint:fast}` 让阈值只约束快接口。

**性能门禁的精度来自打标**：不打标的阈值要么误伤已知慢端点，要么被迫放宽到无意义。


**checks 与 thresholds 的分工**：checks（`✓ health 200`）统计业务断言的
成功率，是观测；thresholds 决定退出码，是门禁。CI 里两者都要——
checks 告诉你"功能还对不对"，thresholds 告诉你"性能还够不够"，
但只有后者能拦下发。

**两种负载模型的取舍**：VU 模型（constant-vus/ramping-vus）固定"多少人在线"，吞吐受响应时间影响——变慢则 RPS 自己掉；arrival-rate 模型（ramping-arrival-rate）固定"每秒来多少请求"，复现"流量不等人"的真实突刺。

spike 场景必须用后者，否则突刺会被 VU 模型的自适应抹平。


**与 Locust 的分工**：k6 的 JS 单文件 + thresholds 原生语义 + 退出码，
天生适合 CI 门禁；Locust 的 Python 场景逻辑更自由，适合容量探索。
本系列两者都要：lab 26 探索容量，lab 27 把性能钉进 CI。

## Pitfalls & Q&A

踩坑清单：

- **用 checks 当门禁**。现象：功能断言挂了 CI 却绿。
  原因：checks 不决定退出码。解法：门禁一律 thresholds。
- **阈值不打标**。现象：慢接口把 P95 拉爆，全场景永远红。
  解法：按端点打 tag，阈值只约束该管的端点。
- **spike 用 VU 模型**。现象：突刺被"自适应"掉，复现不出真实冲击。
  解法：arrival-rate 执行器才固定到达率。
- **阈值一步到位设过严**。现象：门禁永远红，团队开始无视。
  解法：现状基线 + 业务 SLO（Service Level Objective，服务级性能目标，
  如"P95 ≤ 500ms"的正式要求）取严者，随容量治理棘轮式收紧。

深入问答：

- **Q：thresholds 和断言（checks）的区别？** checks 统计成功率不决定退出码；
  thresholds 决定退出码——CI 门禁必须用后者。
- **Q：VU 和 arrival-rate 两种模型怎么选？** VU 模型受响应时间影响
  （慢则吞吐降）；arrival-rate 固定到达率、复现"流量不等人"的真实突刺。
- **Q：性能门禁的阈值怎么定？** 现状基线 + 业务 SLO 取严者；
  随容量治理棘轮式收紧。
