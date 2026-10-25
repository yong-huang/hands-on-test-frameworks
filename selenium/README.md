# 🧜 selenium/：Selenium Web 自动化 18 实验（Python + Java 双栈）

> 把 [../docs/selenium.md](../docs/selenium.md) 清单落成的可真实跑通系列：
> 地基（靶场/定位/等待/表单）→ 高级交互（窗口/iframe/JS/Actions）→ 工程化（证据链/POM/数据驱动/Java 对照）
> → 规模与现代化（Grid 并行/多浏览器矩阵/CDP/flaky 治理）→ 🏁 双栈终极套件。
> 全系列打同一个**带病靶场**（`shop/`：慢元素/三层 iframe/原生 alert/懒加载四类陷阱，答案锁 SECRET_DEFS.md），
> 每个坑都在后续实验里有一个对应的解法用例。
> 与 labs/23-25 互补（那边是入门与对比）、与 playwright/ 线流派对照；与 appium/（Java 工程化）、
> mocking/（CDP 网络替身 vs 服务端替身）双向复用经验。

进度：**18/18 (100%)** ██████████████████

## 🚀 快速开始

前置条件：仓库 venv（selenium 4.48 ✅）/ Chrome ✅ / Safari+safaridriver ✅ / Firefox 158 + geckodriver 0.37.1 ✅。

项目 12/18 另需 Java 17 + Maven（✅）。Firefox/geckodriver 的国内镜像装法见 docs/selenium.md 项目 1。

```bash
cd selenium/01_shop_first_session
./01_shop_first_session.sh        # 建靶场 + 三浏览器首会话（第一个实验）
./01_shop_first_session.sh clean  # 实验产物清理（靶场为公共设施，clean 不代停）
bash ../shop/shop.sh clean        # 显式停靶场归零
```

每实验同构：`apply` 幂等拉靶场 → `observe` 跑用例出证据 → `clean` 清产物。
共享夹具在 [conftest.py](conftest.py)：`make_driver(name)` 工厂 + `SELENIUM_BROWSER`/`HEADLESS` 环境变量。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [01](01_shop_first_session/README.md) | 靶场与首会话 | 带病靶场落成 + 三浏览器首会话 | Chrome 156/Firefox 158/Safari 26.5 全通（5.47s） |
| [02](02_locators/README.md) | 八种定位策略 | 定位器健壮性打分表 CSV | 购买按钮（iframe 内）6 策略全命中；XPath 锁在对比实验 |
| [03](03_waits/README.md) | 等待机制全集 | sleep/显式/Fluent + 隐式叠加陷阱 | sleep(1s/2s) 0/3 vs 显式 10/10；陷阱实测 5.0s vs 显式 2s |
| [04](04_forms/README.md) | 表单控件全集 | 8 类控件回读逐字段断言 | 1 passed；日期控件 locale 坑 → JS 设值 + change 派发 |
| [05](05_windows/README.md) | 窗口与标签 | 句柄往返 / newWindow / 尺寸 | 3 passed；chromedriver newWindow 返回 null 的坑 |
| [06](06_iframes/README.md) | iframe 嵌套 | 三层 frame 购买支付 + API 复核 | status=paid 双证据（ORD-e966ab54）；alert 阻塞演示 |
| [07](07_js_lazyload/README.md) | JS 执行与懒加载 | 懒加载 30 件全载 + 事件陷阱实测 | JS 直改 value 读空 vs sendKeys 正常；靶场修大屏懒加载缺陷 |
| [08](08_actions/README.md) | Actions 交互链 | 拖拽/hover/Ctrl+S/画布像素断言 | 墨迹 0 → >500 → 清空归 0（对照 appium/07） |
| [09](09_evidence/README.md) | 截图证据链 | 失败自动留截图+page source | 恰好 1 组证据、通过零附件（核验脚本把关） |
| [10](10_pom/README.md) | POM 分层 | pages/flows/tests 三层 | tests/ 零 find_element 硬规则（grep=0） |
| [11](11_data_driven/README.md) | 数据驱动 | orders.json 5 组国际地址 | 毫秒后缀自证数据生效；空地址负向拦截 |
| [12](12_java_parity/README.md) | ⛓️ Java 双栈对照 | Maven+TestNG 等价迁移 | Tests run: 1 Failures: 0；≥10 行双栈差异表 |
| [13](13_grid/README.md) | Grid 并行 | standalone Grid + xdist | 串行 38s → 并行 11s，**提速 71%** |
| [14](14_browser_matrix/README.md) | 多浏览器矩阵 | 冒烟 × Chrome/Firefox/Safari | 6 passed + COMPAT_NOTES 6 条实测差异 |
| [15](15_cdp/README.md) | CDP 拦截与性能 | 接口拦截/弱网/指标采集 | 1208ms → 2922ms（×2.4）；Nodes=127 全采到 |
| [16](16_flaky/README.md) | flaky 治理 | 检出-隔离-复验闭环 | 20 轮检出 2 条植入 → 隔离 → 10 轮全绿 |
| [17](17_final_python/README.md) | 🏁 终极套件 | POM+数据驱动+矩阵+留证+HTML 报告 | 双浏览器全绿 + 注入失败证据链核验 ✅ |
| [18](18_final_java/README.md) | 🏁 终极对照 | TestNG×Grid 并行 + RetryAnalyzer | Tests run: 3 Failures: 0；重试链路在案；12 行终版差异表 |

## 🧭 学习路线

按编号 01 → 18 即路线：

1. **01-04 地基**：靶场与三浏览器 → 定位 → 等待 → 控件（自动化两大翻车点在此排雷）
2. **05-08 高级交互**：窗口 → iframe → JS/懒加载 → Actions（「页面不止一层」四难）
3. **09-12 工程化**：证据链 → POM 三层 → 数据驱动 → ⛓️ Java 双栈对照
4. **13-16 规格上探**：Grid 并行 → 多浏览器矩阵 → CDP → flaky 闭环
5. **17-18 🏁 收官**：Python 终极套件 + Java×Grid 终极对照（12 行差异表）

## ⚠️ 预期失败诚实标注

- 02：XPath 只出现在对比实验；相对定位器锚必须 `{By: 值}` 字典且**可见**（元组/隐藏锚 → chromedriver 神秘崩溃）
- 03：sleep 版用例**设计为必挂**（0/3、0/3），这是数据不是事故
- 09：`1 failed` 是注入的取证素材；证据核验脚本把关「恰好 1 组、通过零附件」
- 14：Safari 原生 click 在非前台不产生事件（JS click 兜底）；safaridriver 单会话配对，僵尸会话需 pkill
- 16：`1 passed` 的前置是 hunt 子流程的 20+10 轮重跑；猎物池由子进程驱动，外层不收集

## 🔧 环境要求

macOS（Apple Silicon 实测）/ 仓库 venv（selenium 4.48）/ Chrome、Safari、Firefox（+geckodriver，npmmirror 装法见 docs/selenium.md）。

Java 17 + Maven（仅 12/18）；Docker（仅 13/18 的 Grid——arm64 用 standalone-chrome 替代 node 镜像，实测 node-chrome 无 arm64 manifest）。
