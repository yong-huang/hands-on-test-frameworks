# 📱 appium/：iOS Appium 自动化 14 实验（Java 17 + Maven + TestNG + Appium 3.8）

> 把 [../docs/appium.md](../docs/appium.md) 清单落成的可真实跑通系列：
> 首会话 → 定位策略 → 登录/目录/购物车/结算 → 手势/WebView/Face ID/生命周期 → 数据驱动/POM/报告 → 🏁 双模拟器终极套件。
> 全系列测同一个真实 App：SauceLabs My Demo App（bundleId `com.saucelabs.mydemo.app.ios`，2.3.0），
> 跑在 iPhone 17（iOS 26.5）模拟器上——元素歧义、弹窗吞点击、context 不出现，都是这个真实 App 教的第一手坑。
> 与 labs/28 互补：那边把「移动端测试」当 labs 主线的一站（环境受阻时 Playwright 移动视口 fallback 也算完成），这边是 macOS 上完整的 iOS 原生栈。
> 01-13 同一脚本生命周期：apply 装环境 → observe 出证据 → clean 清残留（00 为环境安装脚本、14 为套件运行器，入口见各自章节）。
> 全程免费本机：Xcode 模拟器 + Appium 开源版 + SauceLabs 免费 Demo App，零云真机依赖。

进度：**14/14 (100%)** ██████████████

## 🚀 快速开始

前置条件：macOS + 完整 Xcode（本系列实测 Xcode 26.6）、iPhone 17 / iOS 26.5 模拟器、Java 17+、Maven 3.9+、Node 20+、4723 端口空闲。

```bash
cd appium/00_env && ./setup.sh              # 安装 Appium 3.8.0 + XCUITest driver 并跑 doctor 体检
cd ../01_ios_session && ./ios_session.sh    # 首会话：建立 session → 启动 App → 断言 Catalog tab
```

01 首次运行会自动安装 Appium 3.8 与 XCUITest driver、下载约 6 MB 的 My Demo App；WDA（WebDriverAgent，Appium 驱动 iOS 的自动化代理）第一次编译要 2-5 分钟，
有缓存后全流程实测 5.4 秒。

02-13 各实验复用 01 的 `apply`/`clean`，不重复装环境；每次 `apply` 会**强制重装**被测 App——
App 容器/Keychain 的陈旧状态 `clearApp` 清不掉，多轮 `noReset` 会话累积后会让生物识别等依赖持久状态的流程失效（重装即愈）。

## 📚 实验总表

| 实验 | 主题 | 一句话产出 | 验收亮点 |
|:---|:---|:---|:---|
| [00](00_env/README.md) | 共享环境 | 幂等安装 Appium 3.8.0 + XCUITest 12.19.1 并跑 doctor 体检 | 「Diagnostic completed, 0 required fixes needed…」 |
| [01](01_ios_session/README.md) | 首会话 | Java 17 + TestNG + Appium Java Client 9.4 建立首条 session 并断言 Catalog tab | 「找到 Catalog-tab-item，App 已启动」；有缓存全流程 5.4 秒 |
| [02](02_locators/README.md) | 定位策略 | 6 类元素各用两种定位共 12 次查找，确立 id→predicate→class chain 优先级、XPath 挡在主套件外 | 「商品名：id 命中 6 个（有歧义）/ predicate 锁定 Black」 |
| [03](03_login/README.md) | 登录矩阵 | Page Object + DataProvider 压 5 条登录场景，断言 iOS 原生 alert | 「Tests run: 5, Failures: 0」（Validation Error! / Username is required） |
| [04](04_catalog/README.md) | 目录排序 | `mobile: scroll` 拿全 25 件商品全序并断言四种排序，识破价格排序键缺陷 | 「✅ 商品总数：25（验收下限 20）」；「首=$15.99 尾=$9.99」疑似字符串排序 |
| [05](05_cart/README.md) | 购物车 | 角标/数量/总价三者同步断言，BigDecimal 校验金额 | 「✅ 购物车总价同步：$59.98 = $29.99 × 2（2 Items）」；角标统计总件数陷阱 |
| [06](06_checkout/README.md) | 结算 E2E | CheckoutFlow 编排登录到下单 8 步，含空姓名/空卡号负向校验 | 「✅ Review 总价一致：$35.98 = $29.99 + $5.99 运费」 |
| [07](07_gestures/README.md) | 手势像素断言 | W3C Actions 驱动画线/长按/swipe/Reset，用截图像素差给画布结果写断言 | 「✅ 画布墨迹像素变化：11400」「Clear 后残留差异像素：0」 |
| [08](08_webview/README.md) | WebView 混合 | native→Webview→native 往返；WKWebView 未开 inspectable，用 native 树诚实降级断言 | 「⚠️ 30 秒内未出现 WEBVIEW context」「Hello WebView 可见」（本地页 :8923） |
| [09](09_biometrics/README.md) | Face ID 模拟 | enrollBiometric + sendBiometricMatch 模拟匹配成功/失败/失败后重试 | 「第二次尝试：match=true，登录成功——弹窗无残留阻塞」 |
| [10](10_lifecycle/README.md) | 生命周期 | 后台/terminate/Reset 驱动状态迁移，queryAppState 断言状态值 | 「queryAppState 3→4」「全程 4 → 1 → 4」（4=前台 3=后台 1=未运行） |
| [11](11_data_driven/README.md) | 数据驱动 | DataProvider + Jackson 读 JSON 5 组国际地址，唯一毫秒后缀证明数据生效 | 「收件人=李雷-mvkeq6wm」「步骤 40：下单成功」 |
| [12](12_pom/README.md) | POM 分层（Page Object Model，页面对象模型） | 把 03-06 重构为 Page + Flow + 测试三层，测试类零 findElement | 「Tests run: 6, Failures: 0」；硬规则「findElement 出现次数为 0」 |
| [13](13_reporting/README.md) | Allure 报告 | 失败用例自动附截图 + page source + syslog + 录屏四类证据进 Allure | 「[diag] 失败证据已附加」（1 条故意失败）；Allure CLI 2.46.1 |
| [14](14_final_suite/README.md) | 🏁 终极套件 | 双模拟器并行 smoke + regression 共 29 条，RetryAnalyzer 重试，N 连跑统计 | 「Tests run: 29, Failures: 0」；「🏁 1 轮连续全绿」；wdaLocalPort 8100/8101 |

## 🧭 学习路线

按编号 00 → 14 即路线：

1. **00-01 打地基**：环境体检 → 首会话（WDA 编译、能力矩阵，Appium Server 挂在脱离终端的包装壳下防误杀——细节见 01 的 ios_session.sh）
2. **02-06 业务流四件套**：定位策略 → 登录 → 目录 → 购物车 → 结算，每层都踩真实 App 的元素坑
3. **07-10 进阶交互**：手势像素断言 → WebView 降级 → Face ID 模拟 → 生命周期状态机
4. **11-14 工程化收官**：数据驱动 → POM 分层 → 失败取证与报告 → 🏁 双模拟器并行终极套件

## 🖼️ 架构图

除 00（纯环境实验）外，各实验 images/ 下有图：多数为三件套——`NN_name.html`（双击打开，可交互）· `.svg`（静态图）· `.workflow.json`（数据源）；01/03 为 html+svg 两件。

## ⚠️ 预期失败诚实标注

- 04 的价格排序缺陷（首件 $15.99 > 尾件 $9.99）是**被测 App 的疑似缺陷**，断言只写「缺陷存在也成立」的性质
- 08 的 WEBVIEW context 永远不出现——该构建 WKWebView 未开 inspectable（iOS 16.4+ 是 App 侧代码的事），实验教的是 native 树降级断言
- 09 的人脸提示弹出后 App 像「死」了是正常现象——必须先 `sendBiometricMatch` 应答才能继续；且这套命令仅模拟器有效
- 13 的「Tests run: 3, Failures: 1」有 1 条故意失败——它是取证演示的素材
- 14 首轮特别慢（两台设备各要编译一份 WDA，每台 2-5 分钟）；并行 session 必须各用独立 `wdaLocalPort` 与
  `derivedDataPath`，共用会随机超时

## 🔧 环境要求

macOS + 完整 Xcode（`xcode-select` 不能指向 Command Line Tools，否则 WDA 编译必失败）/ iPhone 17 / iOS 26.5 模拟器 / Java 17+ / Maven 3.9+ / Node 20+。

可选：`applesimutils`（仅权限类命令用，00 体检不依赖它；`brew tap wix/brew && brew install applesimutils`）、Allure CLI（13，`brew install allure`）。

无独立 load_resources：环境随 00_env 的 `setup.sh` 与各实验 `apply` 就绪，`clean` 后 Appium 停、App 与下载缓存保留（供下次秒开）。
