# 28 · 移动端测试（Appium）：完整链路 + Playwright fallback 双路径

> Appium 的环境链是全系列最长的（Xcode + Simulator + server + driver）。
> 本篇按清单约定做"双路径"：完整 Appium 链路给出可运行的参考实现与补齐清单；
> 环境受阻时 fallback 到 Playwright 移动视口 + 触屏——**fallback 也算完成，
> 且如实记录**。

## 1. 为什么需要它

- 移动端测试的特殊性：触屏语义（tap≠click）、真机/模拟器矩阵、设备描述符。
- 识别"链路中哪一环断了、断了对验收意味着什么"——是工程判断力的体现。

## 2. 总览：双路径架构

<!-- 图: images/appium.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/28_appium/images/appium.html)
> （或本地打开 [`images/appium.html`](images/appium.html)）。

理想路径（Appium 2 → XCUITest → Simulator）在本机受阻于 simctl；
fallback 路径（Playwright 设备描述符 + tap）在真触屏语义下完成同等用例。

## 3. 快速开始

```bash
./mobile_lab.sh    # ① 环境探测（诚实打印断点）② fallback 三用例全绿
```

实测：探测输出 `simctl 不可用（xcode-select 指向 CommandLineTools）`；
fallback 3 条用例（触屏下单/小屏布局/竞态按钮）全绿。

## 4. 核心概念

### 4.1 Appium 链路与补齐清单

本机探测结果（2026-09）：Appium server 未装、simctl 不可用。
补齐三步（完成后 `appium_reference.py` 可直接跑）：

```bash
sudo xcode-select -s /Applications/Xcode.app        # 启用完整工具链
npm install -g appium && appium driver install xcuitest
appium --base-path /wd/hub                          # 起 server
pip install Appium-Python-Client
```

参考实现演示了 capabilities（device_name/platform_version/automation_name）、
`accessibility id` 定位首选、启动→定位→断言的最小闭环。

### 4.2 fallback 的等价性：tap 是触屏不是鼠标

Playwright 设备描述符（`playwright.devices["iPhone 14"]`）带来 390×843 视口、
`hasTouch`、移动 UA——用例里的 `.tap()` 走的是**触摸事件**而非鼠标点击。
移动端的三个验收点全部覆盖：触屏下单、无横向滚动、触屏竞态按钮。

### 4.3 小屏布局断言

`scrollWidth <= innerWidth + 2`——移动端基本盘是不出横向滚动条。
这类断言成本极低、价值极高，值得进每条移动用例。

### 4.4 诚实记录的意义

清单原文允许 fallback 算完成，但前提是"如实记录"。脚本的探测段会明确打印
链路断在哪一环——**环境受阻不可耻，假装跑通才可耻**。

## 5. 关键片段

```python
device = playwright.devices["iPhone 14"]
context = browser.new_context(**device)         # 视口+触屏+UA 一次到位
page.get_by_role("button", name="创建订单").tap()
assert page.evaluate("document.documentElement.scrollWidth") <= page.evaluate("window.innerWidth") + 2
```

## 6. 文件结构

```
28_appium/
├── README.md
├── mobile_lab.sh                 # 探测 + fallback 执行
├── appium_reference.py           # Appium 2 参考实现（补齐环境即可跑）
├── configs/pytest.ini
├── tests/
│   ├── conftest.py               # iPhone 14 设备描述符 fixture
│   └── test_mobile_fallback.py   # 触屏下单/布局/竞态 三条
└── images/
```

## 7. 深入要点

- **Q: Appium 和 Espresso/XCUITest 的关系？** Appium 是协议层翻译官，
  底层仍驱动 XCUITest/uiautomator2——多语言通用，但多一层延迟。
- **Q: accessibility id 为什么是定位首选？** 与视觉实现解耦、双语种稳定、
  本身就是可访问性要求——一举三得。
- **Q: 移动 Web 和原生 App 测试的边界？** 移动 Web 用 Playwright 移动视口
  已覆盖大半；原生能力（相机/推送）必须真机+原生框架。

## 8. 总结

移动端有了务实的落地路径。下一篇 [29_a11y_security](../29_a11y_security/README.md)：
无障碍与安全双基线——把"该做的事"变成可回归的门禁。
