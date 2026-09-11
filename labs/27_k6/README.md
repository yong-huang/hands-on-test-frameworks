# 27 · 负载与阈值（k6）：场景即代码，阈值即门禁

> Locust 擅长"用 Python 探索容量"，k6 擅长"把性能塞进 CI"：
> 场景用 JS 声明、thresholds 不达标就退出码非 0——性能回归和功能回归
> 用同一套红绿语言。本篇跑 smoke/ramping/spike 三场景，并演示门禁拦截。

## 1. 为什么需要它

- 部署后 15 秒 smoke、夜间 ramping、发版前 spike——一份脚本三种负载形态。
- thresholds 让"性能变差"变成可拦截的 CI 事件，而不是上线后的工单。

## 2. 总览：场景选择 → 执行 → 阈值判定

<!-- 图: images/k6.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/27_k6/images/k6.html)
> （或本地打开 [`images/k6.html`](images/k6.html)）。

`SCENARIO` 环境变量选场景；请求打 `endpoint:fast` 标签，thresholds 只约束
快接口；p95<500ms 且错误率<1% 不达标 → 退出码非 0。

## 3. 快速开始

```bash
./k6_run.sh                  # 起 SUT(8927) → 三场景全跑 + 门禁失败演示
BASE_URL=... k6 run -e SCENARIO=smoke load.js   # 单场景
```

## 4. 核心概念

### 4.1 三种场景形态（一份脚本）

| 场景 | executor | 形态 | 用途 |
|:---|:---|:---|:---|
| smoke | constant-vus (1 VU/15s) | 单用户验活 | 部署后秒级检查 |
| ramping | ramping-vus (0→20→0) | 爬坡-稳态-收尾 | 找拐点 |
| spike | ramping-arrival-rate (5→60/s) | 到达率突刺 | 复现突发流量 |

实测：ramping 稳态 148 checks/s、P95 7.7ms；spike 复现突刺下延迟抬升。

### 4.2 thresholds 的标签过滤

慢接口 1.5s 是 SUT 的已知设计，不能让它的 P95 污染全局阈值——
`http.get(url, { tags: { endpoint: 'fast' } })` + `http_req_duration{endpoint:fast}`
让阈值只约束该管的端点。**性能门禁的精度来自打标**。

### 4.3 门禁失败演示（真实触发）

对慢接口直接设 `p(95)<500` → threshold 违例 → k6 退出码非 0。
脚本 ④ 步展示了这条红线的完整输出——CI 里接上就是自动拦截。

### 4.4 与 Locust 的取舍

k6：JS 单文件、thresholds 语义原生、CI 友好；Locust：Python 场景逻辑
更自由、生态里并发模型更直观。容量探索用 Locust，CI 门禁用 k6——本系列两者都要。

## 5. 关键配置

```js
export const options = {
  scenarios: { main: scenarios[__ENV.SCENARIO] },
  thresholds: {
    'http_req_duration{endpoint:fast}': ['p(95)<500'],
    'http_req_failed': ['rate<0.01'],
  },
};
```

## 6. 文件结构

```
27_k6/
├── README.md
├── k6_run.sh                  # SUT 生命周期 + 三场景 + 门禁演示
├── load.js                    # 三场景 + 阈值（SCENARIO 切换）
├── slow_threshold_demo.js     # 门禁失败的"靶子"
└── images/
```

## 7. 深入要点

- **Q: thresholds 和断言（checks）的区别？** checks 统计成功率不决定退出码；
  thresholds 决定退出码——CI 门禁必须用后者。
- **Q: VU 和 arrival-rate 两种模型怎么选？** VU 模型受响应时间影响（慢则吞吐降）；
  arrival-rate 固定到达率、复现"流量不等人"的真实突刺。
- **Q: 性能门禁的阈值怎么定？** 现状基线 + 业务 SLO 取严者；随容量治理棘轮式收紧。

## 8. 总结

性能进了 CI。下一篇 [28_appium](../28_appium/README.md)：移动端——
Appium 链路与 Playwright fallback 的双路径。
