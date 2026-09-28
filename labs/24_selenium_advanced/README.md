# 24 · Selenium 进阶：POM + ActionChains + 本地 Grid 并行

> Selenium 的工程化三件套：页面对象稳住结构、ActionChains 覆盖鼠标语义、
> Docker Grid 把并行做真。读完本篇你能写出 Selenium 版 POM、用 ActionChains
> 完成拖拽、并把"多浏览器并行"从口号变成一条 docker-compose
> （实测：Grid 串行 12.2s → 双会话并行 6.8s，加速 1.8x）。

## Background

lab 23 复现了"无等待必挂"，但 Selenium 的工程化差距不止等待一处：
定位器散落在用例里（没有 POM 就没有可维护性）、鼠标语义交互
（拖拽/悬停）没有原生表达、多浏览器并行要靠多台机器或手工起多个浏览器。
这三个缺口在真实团队里都以"套件长到没人维护"的方式爆雷。

Grid 是 Selenium 生态的并行答案：一个 hub（调度中心）接若干 node
（浏览器容器），用例把命令发到 hub，hub 分配给空闲 node——
"多浏览器并行"从此是一条 docker-compose 的事。

本实验的拓扑：pytest-xdist 双进程 → Grid(:4444, maxSession=2) →
两个容器内 Chrome → 访问宿主机 SUT（host.docker.internal）。

## What

三个机制：**POM**（页面对象——lab 18 的思想在 Selenium 上的等价实现）、
**ActionChains**（动作链——把一串鼠标事件攒成一次原生驱动）、
**Grid**（远程浏览器调度）。

可以把 Grid 想成租车行的调度台：客人（用例）只说"我要一辆车"，
调度台（hub）把空闲车（node 容器里的浏览器）派给他，还车后立刻可派给别人。
但和租车行不同的是，派车有并发上限（maxSession）——超了要排队，
排队的开销在套件太快时反而吃掉全部收益（本实验真实踩过，见 Pitfalls）。

ActionChains 的表达：`click_and_hold(src).move_to_element(dst).release()`
一串动作攒起来 `perform()` 一次执行——原生鼠标事件驱动，
不是"设值"而是"真点"。

## When to Use

典型场景：

- 拖拽/悬停/右键等鼠标语义交互：ActionChains 用原生事件驱动。
- 存量 Selenium 套件的并行化改造：Docker Grid + pytest-xdist 两层并行。
- 跨浏览器矩阵：Grid 上挂 Chrome/Firefox node，用例指定 browserName 分发。

何时不用：新项目无历史包袱时，Playwright 自带并行（进程内多 worker）
不需要外部 Grid；容器内跑浏览器需要 Docker 资源（每个 Chrome 吃 0.5-1GB
内存），资源紧张的 CI 节点要掂量。

关键命令（这段在做什么：起 Grid、切远程执行的两个入口）：

```bash
docker compose -f docker-compose.grid.yml up -d     # Grid :4444
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub pytest -n 2
```

```python
webdriver.Remote(command_executor=URL, options=opts)   # 切到 Grid
ActionChains(d).click_and_hold(a).move_to_element(b).release().perform()
```

## Quick Start

前置条件：**Docker 是 Grid 部分的硬前置**（labs/00 体检项；
Docker 不可用时本地部分仍可跑，Grid 对比无法演示——本机实测即此状态，
下方 Grid 数字来自实验作者的 Docker 环境实测）。

```bash
cd labs/24_selenium_advanced
./selenium_grid.sh    # 本地执行 → 起 Grid → 串行 vs ×2 并行对比 → 清理
```

本地段的真实输出（2026-09-29 实测，本机 Chrome 无需 Docker；脚本该步只打印汇总行）：

```
=====> [observe] ① 本地执行：POM + ActionChains + JS 执行器
============================== 7 passed in 14.32s ==============================
```

7 条 = 3 条 POM/ActionChains/JS 用例 + 4 条 1.5s 工作量用例（与下表 Grid 段同一套）。
再起 Grid、先串行后 `pytest -n 2` 双会话并行，最后清理容器。
Grid 段在本机 Docker 未启动时不执行，其数字来自实验作者的 Docker 环境实测
（见下表）。

实验作者实测数据（Docker 环境，7 条用例含 4×1.5s 工作量）：

| 模式 | 耗时 |
|:---|:---|
| Grid 串行 | 12.2s |
| Grid 双会话并行 | 6.8s（加速比 1.8x） |

诚实预期：加速比不是"核数 = 加速"——maxSession=2 决定了上限是 2 倍，
实际 1.8x 是调度与启动开销后的真实值。**度量的前提是负载真实**：
第一版套件太快时（串行 1.8s / 并行 1.9s）并行反而更慢，
加入 4×1.5s 的工作量用例后加速才显形。

## How It Works

**Selenium 版 POM**：`pages/order_page.py` 与 lab 18 的 IndexPage 同语义——选择器集中在类里、动作方法说业务语言。

对照阅读能看出两代框架 POM 的差异只在驱动层 API（`find_element(By.ID, ...)` vs `get_by_role`），结构思想完全一致：**分层与收口是框架无关的工程常识**。


**ActionChains 与 HTML5 拖拽的坑**：`click_and_hold(src).move_to_element(dst).release()`发的是原生鼠标事件序列。

HTML5 的 DnD API（drag and drop，浏览器内置拖拽接口）不吃合成的鼠标事件——本实验的自定义页面用 mousemove/mouseup 监听实现拖放语义，ActionChains 才能驱动；真 HTML5 拖拽要用 JS 注入 dispatchEvent。


**JS 执行器**：`execute_script("arguments[0].scrollIntoView(...)", el)`——
协议做不到的事直接执行 JS；也是读取页面状态（title、变量）的万能后门。
能力大、滥用也多：能断言的优先走协议，JS 是逃生舱不是主干道。

**Grid 的两个经典坑（本实验真实踩过）**：

1. **容器内 127.0.0.1 是容器自己**：Chrome 在容器里，访问宿主机 SUT 必须
   `host.docker.internal`——写 localhost 会连接拒绝。
2. **data: URL 的 `#` 是 fragment 分隔符**：内联 HTML 里的十六进制颜色
   （`#ff0000`）会把页面截断——必须 `urllib.parse.quote` 编码。

## Pitfalls & Q&A

踩坑清单：

- **套件太快时上并行**。现象：串行 1.8s、并行 1.9s，越并越慢。
  原因：Grid 会话建立开销吃掉全部收益。解法：并行度量的前提是负载真实，
  套件要先有足够的真实工作量。
- **Grid 里访问宿主机写 localhost**。现象：容器内浏览器连接拒绝。
  解法：`host.docker.internal`（容器视角的宿主机名）。
- **maxSession 与资源不匹配**。现象：node 崩溃或 Chrome 段错误。
  解法：maxSession 与机器核/内存匹配；`shm_size` 给足（2g 起）。
- **Selenium 套件没有失败取证**。现象：CI 红了没有现场。
  原因：框架不管取证。解法：自建钩子——pytest hookimpl 里
  `driver.get_screenshot_as_file`，工程补位。

深入问答：

- **Q：Grid 并行度怎么定？** maxSession 与机器核/内存匹配；每个 Chrome 吃
  0.5-1GB，shm_size 要给足（2g 起）。
- **Q：HTML5 拖拽怎么测？** ActionChains 驱动不了 DnD API——用 JS 注入事件，
  或让被测页面同时响应鼠标事件（本实验做法）。
- **Q：Selenium 套件的失败取证怎么做？** 自建钩子：pytest hookimpl 里
  driver.get_screenshot_as_file——框架不管，工程补位。
