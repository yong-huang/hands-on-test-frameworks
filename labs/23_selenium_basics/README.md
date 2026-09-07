# 23 · Selenium 基础：WebDriver 协议直感，无等待必挂 vs 显式等待

> Selenium 没有"自动等待"的魔法：每个动作都是一次 WebDriver HTTP 往返，
> 元素不在就当场报错。本篇亲手复现"无等待必挂"，再用 `WebDriverWait` 写出
> 稳定版——两版对比就是三代框架差异的根源。

## 1. 为什么需要它

- 读懂 WebDriver 协议，才能理解 Playwright/Cypress 的自动等待到底替你做了什么。
- 存量系统、多语言团队、老浏览器兼容——Selenium 仍是绕不开的基本功。

## 2. 总览：脚本 → driver → 浏览器的协议链

<!-- 图: images/selenium_basics.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/23_selenium_basics/images/selenium_basics.html)
> （或本地打开 [`images/selenium_basics.html`](images/selenium_basics.html)）。

用例发 HTTP 命令给 chromedriver（Selenium Manager 自动下载），driver 驱动
Chrome；同步阻塞、逐条往返——"等"只能靠用例自己安排。

## 3. 快速开始

```bash
./selenium_basics.sh    # 起 SUT(8923) → Chrome 三用例 → Safari 可用性探测
```

实测：3 条用例全过；`test_no_wait_fails_on_delayed_page` 真实触发
NoSuchElementException，`test_explicit_wait_survives_delayed_page` 稳定通过。

## 4. 核心概念

### 4.1 Selenium Manager

驱动与浏览器版本匹配是 Selenium 的历史包袱；4.x 的 Selenium Manager 自动
下载匹配的 chromedriver——环境准备成本大幅下降（本实验零手动配驱动）。

### 4.2 无等待必挂（预期失败演示）

点击"加载延迟列表"后立刻 `find_element`——元素 2 秒后才渲染，
`NoSuchElementException` 当场抛出。这就是 2010 年代 E2E flaky 的原型。

### 4.3 显式等待：WebDriverWait + expected_conditions

`WebDriverWait(10).until(lambda d: len(d.find_elements(...)) == 3)`——
轮询直到条件成立。与 PW `expect` / CY `should` 语义相同，但要**手写每个条件**。

### 4.4 Safari 支持（macOS 原生，诚实标注）

Safari 由系统自带 `safaridriver` 驱动，但默认禁用——需要手动执行一次
`sudo safaridriver --enable`（脚本 ③ 步自动探测并给出指引，不替你执行 sudo）。
未启用时 Chrome 路径不受影响。

### 4.5 易错点

- `implicitly_wait` 与显式等待混用会让失败时间不可预测——本实验显式 `implicitly_wait(0)`。
- `find_element` 找不到立即抛错；`find_elements` 返回空列表——等待条件用后者。

## 5. 关键 API

```python
d = webdriver.Chrome(options=opts)          # Manager 自动配驱动
WebDriverWait(d, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), txt))
d.find_element(By.ID, "customer").send_keys("...")
```

## 6. 文件结构

```
23_selenium_basics/
├── README.md
├── selenium_basics.sh        # SUT 生命周期 + 对比演示 + Safari 探测
├── configs/pytest.ini
├── tests/test_selenium_basics.py   # 基础流 + 无等待必挂 + 显式等待稳定
└── images/
```

## 7. 面试要点

- **Q: 隐式等待与显式等待的区别？** 隐式是全局 find 超时，显式是条件轮询；
  混用会叠加等待，失败时间难解释——统一用显式。
- **Q: 为什么 Selenium 的 flaky 名声更重？** 等待全靠人写、取证全靠自建、
  协议同步往返慢——三代框架的自动等待正是在消这三项。
- **Q: Selenium Manager 解决了什么？** 驱动-浏览器版本匹配的自动化；
  剩下的是浏览器安装本身。

## 8. 总结

协议直感建立。下一篇 [24_selenium_advanced](../24_selenium_advanced/README.md)：
POM、ActionChains 与本地 Grid 并行——Selenium 的完整工程化。
