# 16 · Playwright 入门：自动等待的现代 E2E，从三条用例开始

> Selenium 时代写 E2E，一半代码在处理"等"。Playwright 把等待变成默认：
> **操作自动等元素可交互，断言自动等结果成立**。本篇用 SUT 首页的
> 下单→查询→删除三部曲，建立现代 E2E 的第一直觉。

## 1. 为什么需要它

- pytest-playwright 提供 `page` fixture：每条用例全新页面、失败自动截图。
- web-first 断言（`expect`）把"等多久"从脚本里赶出去——flaky 的头号来源就此消失。

## 2. 总览：一次 E2E 用例的执行链路

<!-- 图: images/pw_basics.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/16_pw_basics/images/pw_basics.html)
> （或本地打开 [`images/pw_basics.html`](images/pw_basics.html)）。

pytest → page fixture（新页面）→ 定位器解析 → 自动等待 → 动作/断言 →
trace/截图落盘（可选）→ 页面销毁。

## 3. 快速开始

```bash
./pw_basics.sh            # 起 SUT(8916) → 三条用例 → trace 演示 → 清理
$PY -m playwright show-trace test-results/*/trace.zip   # 回放执行过程（GUI）
$PY -m playwright codegen http://127.0.0.1:8916          # 录制器：操作即生成代码
```

## 4. 核心概念

### 4.1 定位器优先级

`get_by_role` > `get_by_placeholder/get_by_text` > `locator("css")`。
语义定位对样式重构免疫（lab 17 的 role 用例即验证），CSS 是最后的手段。

### 4.2 自动等待 vs web-first 断言

动作（click/fill）自动等"可交互"；断言要用 `expect(locator).to_be_visible()`
这类 **web-first** 断言——它们持续重试到条件成立或超时。
**本实验踩过的坑**：`is_visible()` 立即返回不等待——用它断言"将出现的元素"必挂。
一句话：断言过去用 expect，不用 is_*()。

### 4.3 trace 回放

`--tracing on` 记录每一步的 DOM 快照、网络、控制台；`show-trace` 打开时间旅行式
调试器——比看视频找问题快得多。CI 里用 `--tracing retain-on-failure` 只留失败。

### 4.4 codegen 录制

`playwright codegen <url>` 打开浏览器实时生成代码——起点是录制，终点是
手工整理成语义化定位器（lab 18 的 POM）。

## 5. 关键命令

```bash
pytest --base-url http://... --browser chromium --tracing retain-on-failure
pytest --trace on     # 出错即进入 Playwright inspector
```

## 6. 文件结构

```
16_pw_basics/
├── README.md
├── pw_basics.sh              # SUT 生命周期 + 三步观察
├── configs/pytest.ini
├── tests/test_orders_e2e.py  # 下单/查询/删除 三条用例
└── images/
```

## 7. 面试要点

- **Q: Playwright 的自动等待覆盖什么？** 元素可见、稳定、可接收事件、启用状态；
  断言层面要主动用 web-first expect 才有重试语义。
- **Q: trace 里能看什么？** 每步前后的 DOM 快照、网络请求、console、
  源码定位——一次录制替代"复跑加 print"。
- **Q: 为什么 selector 要语义化？** 抗重构、可读、可访问性双赢——
  role 定位器本身就要求页面可访问性达标。

## 8. 总结

现代 E2E 的手感已经建立。下一篇 [17_pw_locators](../17_pw_locators/README.md)：
专治各种"等不到"——竞态、延迟渲染与稳定性连跑。
