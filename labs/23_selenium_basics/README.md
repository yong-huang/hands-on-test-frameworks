# 23 · Selenium 基础：WebDriver 协议直感，无等待必挂 vs 显式等待

> Selenium 没有"自动等待"的魔法：每个动作都是一次 WebDriver HTTP 往返，
> 元素不在就当场报错。读完本篇你能亲手复现"无等待必挂"（真实触发
> `NoSuchElementException`），再用 `WebDriverWait` 写出稳定版——
> 两版对比就是三代框架差异的根源。

## Background

理解 Playwright 和 Cypress 的"自动等待"替你做了什么，最好的办法是用一个没做这件事的框架：Selenium。

它的每个动作（find、click、send_keys）都是一次WebDriver HTTP 命令发给浏览器驱动，同步阻塞、逐条往返——命令返回即结束，没有任何"等元素出现"的默认行为。

元素 2 秒后才渲染？`find_element` 当场抛`NoSuchElementException`。


这正是 2010 年代 E2E flaky 的原型：脚本跑得比页面快，用例时红时绿，团队开始堆固定 sleep。

显式等待（`WebDriverWait` 轮询条件）是那一代的解药——有效但每个条件都要手写，这与后来 Playwright 的 `expect`、Cypress 的`should` 一对照，就看清了"自动等待"到底自动化了什么。


Selenium 至今仍是绕不开的基本功：存量系统、多语言团队（WebDriver 协议
绑定 Java/C#/Python/JS 全家）、老浏览器兼容场景都在用它。

## What

Selenium 是基于 WebDriver 协议（W3C 标准，用 HTTP 命令控制浏览器的规范）
的浏览器自动化框架：测试代码 → driver（如 chromedriver）→ 浏览器，
协议链上每一环都是 HTTP 往返。

可以把 WebDriver 想成对讲机遥控的机械臂：你每喊一个动作（"点这个按钮"）都要完整说一句话、等机械臂做完再回话，中间没有任何预判。

但和机械臂不同的是，驱动还有版本匹配问题——浏览器升级后 driver 也要跟版本，这是 Selenium 的历史包袱，4.x 的 Selenium Manager 自动下载匹配驱动后才大幅缓解。


Selenium Manager 是 4.x 内置的驱动管理器：按已装浏览器自动下载匹配的
chromedriver/geckodriver——本实验零手动配驱动。

## When to Use

典型场景：

- 存量系统的既有 Selenium 套件维护：读懂协议才治得了 flaky。
- 多语言团队统一 E2E 技术栈：WebDriver 协议全语言对等。
- 企业内浏览器矩阵（老版本 IE 模式、特殊渠道 Chrome）：WebDriver 生态最广。

何时不用：新项目从零建 E2E，Playwright 的自动等待 + trace + 多内核
综合体验更好；纯前端团队内部自测，Cypress 的运行器体验更顺手
（完整对照见 lab 25）。

等待能力三代对照：

| 框架 | 等待语义 | 表达形式 |
|:---|:---|:---|
| Selenium | 显式手写条件轮询 | `WebDriverWait().until(EC...)` |
| Cypress | 命令链自动重试 | `cy.get().should()` |
| Playwright | 断言自动重试 | `expect(loc).to_be_visible()` |

## Quick Start

前置条件：labs/00 体检通过（Chrome 就绪；Safari 需手动启用 safaridriver，
见下）；脚本自动起 SUT(8923)。

```bash
cd labs/23_selenium_basics
./selenium_basics.sh    # 起 SUT → Chrome 三用例 → Safari 可用性探测
./selenium_basics.sh observe
```

observe 的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① Chrome 基础用例（Selenium Manager 自动驱动）
======================== 3 passed in 350.93s (0:05:50) =========================

=====> [observe] ② 无等待 vs 显式等待对比（上面已各自演示：一个必挂、一个稳定）
======================= 2 passed, 1 deselected in 3.30s ========================

=====> [observe] ③ Safari 支持探测（macOS 原生 Safari 26）
⚠️  safaridriver 未启用：需要手动执行一次 sudo safaridriver --enable
    （系统会要求在'安全性与隐私'里确认——这是 Safari 自动化的唯一门槛，诚实标注）
```

诚实预期：三条基础用例全过——**首轮 350s 是 Selenium Manager 现场下载
chromedriver 的环境成本**（后续运行秒级，对照 labs/14 首跑拉镜像的道理相同）。

`test_no_wait_fails_on_delayed_page` 真实触发 `NoSuchElementException`
（预期失败演示，被标记处理），`test_explicit_wait_survives_delayed_page` 稳定通过。

Safari 探测在未启用 safaridriver 时给出指引，而不是替你执行 sudo。

关键 API（这段在做什么：驱动获取、显式等待、元素操作三个入口）：

```python
d = webdriver.Chrome(options=opts)          # Manager 自动配驱动
WebDriverWait(d, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), txt))
d.find_element(By.ID, "customer").send_keys("...")
```

## How It Works

**协议链的同步往返**：`find_element` 发一次 HTTP 命令、拿一次响应——
元素不存在就抛 `NoSuchElementException`，没有重试、没有等待。
"无等待必挂"的机制就在这：点击"加载延迟列表"后立刻 find，
元素 2 秒后才渲染，往返早于渲染完成。

**显式等待的轮询**：`WebDriverWait(d, 10).until(lambda d: len(d.find_elements(...)) == 3)`内部是"每 0.5s 执行一次条件、直到成立或超时"的循环。

与 PW `expect` /CY `should` 语义相同，但要**手写每个条件**——expected_conditions（EC）覆盖常见场景，复杂条件写 lambda。

等待条件用 `find_elements`（返回空列表）而不是 `find_element`（找不到立即抛错）——轮询需要的是"查一次"不是"炸一次"。


**隐式等待为什么被显式归零**：`implicitly_wait` 是全局 find 超时（找不到
元素时最多等多久），与显式等待混用会叠加等待，失败时间变得不可预测——
本实验显式 `implicitly_wait(0)`，把等待完全交给显式条件。

**Safari 的特殊通道**：macOS 的 Safari 由系统自带 safaridriver 驱动，
默认禁用——手动 `sudo safaridriver --enable` 一次（在"安全性与隐私"确认）
才能自动化。脚本只探测并给指引，不替你执行 sudo；未启用时 Chrome 路径
不受影响。

## Pitfalls & Q&A

踩坑清单：

- **隐式等待与显式等待混用**。现象：失败时间忽长忽短不可解释。
  原因：两种等待叠加。解法：统一显式等待，隐式归零。
- **用 `find_element` 写等待条件**。现象：轮询第一步就抛错退出。
  解法：条件用 `find_elements` 判长度。
- **驱动版本不匹配**。现象：`session not created` 类报错。
  解法：交给 Selenium Manager（4.x），别手动下载指定版本。
- **Safari 探测误判为环境坏了**。现象：observe ③ 的 ⚠️ 让人以为套件有问题。
  事实：safaridriver 默认禁用是 macOS 的出厂状态，手动启用一次即可。

深入问答：

- **Q：隐式等待与显式等待的区别？** 隐式是全局 find 超时，显式是条件轮询；
  混用会叠加等待，失败时间难解释——统一用显式。
- **Q：为什么 Selenium 的 flaky 名声更重？** 等待全靠人写、取证全靠自建、
  协议同步往返慢——三代框架的自动等待正是在消这三项。
- **Q：Selenium Manager 解决了什么？** 驱动-浏览器版本匹配的自动化；
  剩下的是浏览器安装本身。
