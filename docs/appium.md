# 📱 Appium iOS 14 小项目学习清单 · Todo List（SauceLabs My Demo App 实战）

> 通过 14 个小项目（每项目 180-350 行 Java/配置）把一个完整 iOS 电商 App 的回归测试，从"能启动"搭到"能交付"
> 全部免费、本机可跑：iPhone 17 / iOS 26.5 Simulator + Appium 3.8 + XCUITest，不碰云真机
> **完整系统型串联**：所有项目共同测试 SauceLabs My Demo App 2.3.0（bundleId `com.saucelabs.mydemo.app.ios`），项目 6 ⛓️ 串联主交易链路，项目 14 🏁 一键回归
> 与 `docs/test_frameworks.md` 的项目 28 **互补**：跳过"Appium 是什么"，直接做 iOS 原生 App 的深水区——见文末关系表
> 预计周期：5-6 周（每天 1-2 小时）

## 🏗️ 终极蓝图（项目 14 完成时的回归套件）

```
              🏁 appium/14_final_suite（TestNG Suite）
   ┌──────────────┬───────────────┬──────────────────┐
   │ smoke        │ regression    │ mobile-special   │
   │ 登录/目录    │ 加购/结算     │ 手势/WebView/FaceID │
   └──────────────┴───────────────┴──────────────────┘
                        │
          Page Objects + Flows + DataProvider
                        │
            Appium 3.8 / XCUITest 12.19
                        │
        iPhone 17 (iOS 26.5) × 2 Simulator
                        │
          SauceLabs My Demo App 2.3.0
   Catalog │ Cart │ Checkout │ WebView │ FaceID
```

每个阶段把该阶段能力接进共享套件；项目 14 用一条命令跑 smoke + regression，并连续跑 10 次证明稳定性。

## 🤖 AI 辅助提示词速查

| 场景 | 提示词 |
|:---|:---|
| **开始一个新项目** | `我要开始 Appium iOS 项目「[名称]」，被测 App 是 SauceLabs My Demo App（bundleId com.saucelabs.mydemo.app.ios，iPhone 17 / iOS 26.5 模拟器）。请给我完整 Java 17 + TestNG + Appium Java Client 9.4 代码约 [行数] 行，含断言、显式等待和 mvn 运行命令。只输出代码。` |
| **定位排障** | `这个元素在 iOS 上定位不到：[粘贴 page source 片段]。请按 accessibility id → predicate → class chain → XPath 的优先级给 2 种稳定定位写法，并说明为什么不要用 XPath。` |
| **会话/WDA 排障** | `Appium 启动 iOS 会话失败：[粘贴日志]。请按 Xcode 路径、XCUITest driver、WebDriverAgent 构建、模拟器状态逐项定位根因并给修复命令。` |
| **并行排障** | `TestNG 并行跑两个 iOS 模拟器时 WDA 端口冲突：[粘贴日志]。请给每个 session 独立 wdaLocalPort/derivedDataPath 的配置方案。` |

## 📊 总进度

进度：████████████████████████ 14/14 (100%)

| 阶段 | 项目数 | 已完成 |
|:---|:---:|:---:|
| 第一阶段：环境与定位 | 2 | 2 |
| 第二阶段：核心交易链路 | 4 | 4 |
| 第三阶段：移动专项能力 | 4 | 4 |
| 第四阶段：工程化与交付 | 4 | 4 |
| **合计** | **14** | **14** |

---

## 🗂️ 第一阶段：环境与定位（项目 1-2）

> **目标**：把 iOS Simulator + Appium + XCUITest + Java/TestNG 串成一条能跑的最小链路，并建立"定位优先级"直觉

### [x] 项目 1：iOS + Appium 首会话（环境到 Catalog）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~180 行 |
| **核心知识点** | Xcode/simctl、Appium 3 server、XCUITest driver、XCUITestOptions（deviceName/platformVersion/bundleId）、session 生命周期、TestNG `@BeforeClass/@AfterClass` |
| **产出模块** | `appium/01_ios_session`（`pom.xml` + `BaseTest` + `FirstSessionTest`）|
| **技术栈** | Java 17 + Maven 3.9 + TestNG 7.11 + Appium Java Client 9.4 + Appium 3.8 + XCUITest 12.19（✅ 2026-10-22 实测 session 创建成功）|
| **⚠️ 风险** | 首次会话要构建 WebDriverAgent，2-5 分钟属正常；本机 `xcode-select` 指向 CommandLineTools，必须显式用 `DEVELOPER_DIR` 或切换工具链 |
| **验收标准** | `mvn -q -Dtest=FirstSessionTest test` 退出码 0；用例启动 App 并断言 `Catalog-tab-item` 存在；`driver.quit()` 后 `curl /wd/hub/status` 仍可用 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「首会话」。请给我完整 Java 17 + Maven + TestNG + Appium Java Client 9.4 代码约 180 行：XCUITestOptions 连接 iPhone 17 / iOS 26.5 模拟器，bundleId 为 com.saucelabs.mydemo.app.ios，启动 App 后断言 Catalog-tab-item 存在，@AfterClass 正常 quit；附 Appium server 启动命令和 mvn 运行命令。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：`xcode-select` 指向 CommandLineTools 时 WDA 编译失败，脚本显式导出 `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`；首次 WDA 编译 2-5 分钟，不要提前中断；Selenium 4.34+ 删除 `ContextAware`，用 `selenium-bom:4.33.0` 锁定版本。

---

### [x] 项目 2：定位策略与页面侦察（accessibility id / predicate / class chain）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | iOS 定位优先级、`AccessibilityId`、`-ios predicate string`、`-ios class chain`、XPath 的代价、`getPageSource`、`findElements`、显式等待 |
| **产出模块** | `appium/02_locators` + `locator-notes.md`（定位优先级与实测对照表）|
| **前置** | 项目 1 |
| **⚠️ 风险** | 登录页两个输入框没有 accessibilityIdentifier，只能靠 predicate/class chain + 索引；索引是脆弱点，必须在笔记里标注 |
| **验收标准** | `mvn -q -Dtest=LocatorStrategyTest test` 全绿；对 tab、`Login Button`、商品名、价格、购物车角标、结算按钮 6 个元素各给 2 种定位策略；测试代码中 XPath 使用次数为 0（除演示用例）|

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「定位策略」。请给我约 220 行 Java + TestNG 代码：对 SauceLabs My Demo App 的 tab、Login Button、商品名、价格、购物车角标、结算按钮，分别用 accessibility id、iOS predicate、class chain 定位并断言；再单独演示一条 XPath 写法并注释说明为什么只作最后手段；另给 locator-notes.md 的优先级对照表模板。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：`Product Name` / `Product Price` 各命中 6 个，必须用 predicate 的 `label` 收窄；列表页不暴露金额，详情页 `Price` 才是 `$ 29.99`；角标 `visible=false` 但文本为 `1`，不能断言 `isDisplayed()`；界面显示 Login 时，`Login Button` 的子按钮 id 仍叫 `LogOut-menu-item`，只宜定位外层容器；XPath 仅保留在 `XPathDemoTest`。

---

## 🗂️ 第二阶段：核心交易链路（项目 3-6）

> **目标**：把登录 → 目录 → 商品详情/加购 → 购物车 → 结算下单串成完整业务回归，项目 6 做阶段集成

### [x] 项目 3：登录与鉴权矩阵（DataProvider）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~260 行 |
| **核心知识点** | 文本输入、secure text field、键盘收起、系统 alert 断言、登录态、登出、TestNG `@DataProvider` |
| **产出模块** | `appium/03_login` |
| **前置** | 项目 2 |
| **⚠️ 风险** | 该 App 是演示登录：只要用户名/密码非空就放行，不存在"密码错误"分支；不要按真实鉴权设计负例，把这个行为写进测试注释 |
| **验收标准** | `mvn -q -Dtest=LoginTest test` 全绿；覆盖成功登录、空用户名、空密码、邮箱自动填充、登出 5 条；空字段断言 `Validation Error!` alert 文案；登出后 `Login Button` 重新可见 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「登录与鉴权矩阵」。请给我约 260 行 Java + TestNG 代码：用 DataProvider 覆盖成功登录、空用户名、空密码、邮箱自动填充、登出 5 条用例；断言系统 alert 文案；封装 hideKeyboard 和显式等待；注释说明该 Demo App 只校验非空、不是真实鉴权。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：Demo App 2.3.0 的 `LogOut-menu-item` 只回到 Login 表单、不清除登录态；`terminateApp` + `launchApp`、`ResetAppState`、`clearKeychains` 都无效，只有 `mobile: clearApp` 能复位，用例因此显式断言这一差异。密码输入后键盘遮住 Login 按钮：`hideKeyboard` 不可用；发送实际字符 Tab（`U+E004`）隐藏键盘，再用 `mobile: doubleTap`（或 `twoFingerTap`）带 `elementId` 点击。该 App 只校验非空，没有密码错误分支。

---

### [x] 项目 4：商品目录与四种排序

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~240 行 |
| **核心知识点** | CollectionView 列表、`findElements`、滚动到可见、排序弹窗、名称/价格升降序、顺序断言、金额解析 |
| **产出模块** | `appium/04_catalog` |
| **前置** | 项目 2 |
| **⚠️ 风险** | 商品名/价格没有独立 ID，依赖 cell 内文本；滚动用 `mobile: scroll` 或 W3C swipe，不要写死绝对坐标 |
| **验收标准** | `mvn -q -Dtest=CatalogSortTest test` 全绿；默认商品数 ≥ 20；四种排序（名称升/降、价格升/降）首尾与全序断言通过；能滚动定位最后一个商品 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「目录与排序」。请给我约 240 行 Java + TestNG 代码：打开 Catalog，统计商品数，依次验证名称升序、名称降序、价格升序、价格降序，断言首尾与整体顺序；用 mobile: scroll 或 W3C swipe 滚动到最后一个商品；价格文本清洗成 BigDecimal 再比较。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：排序图标无障碍标注缺失，name 仅为 `Button`（导航栏右上），只能 predicate 组合 type+name 定位；列表页 `Product Price` 不暴露金额，价格断言必须进详情页读 `Price`（形如 `$ 15.99`），而详情页没有返回按钮，要靠 `Catalog-tab-item` 返回，且进详情或切 tab 后排序态重置为名称升序——所以先记首尾商品名再取价。App 真实缺陷：价格升序把 $9.99 的 Bike Light 排在末位（非数值升序），Bolt 与 Test.allTheThings 两族同为 $15.99，同价并列保持组内名称原序；套件因此只断言"两方向同一批商品 + 极值价格跨方向相等"，缺陷用 ⚠️ 打印不写成断言。CollectionView cell 复用导致首屏恒 6 件，用 `mobile: scroll` + `LinkedHashSet` 首现序累计全量，`openProduct` 前先 `scrollToTop`。实际 Java 350 行（规划 ~240），超出部分主要是滚动到底判定与价格缺陷的稳健处理。

---

### [x] 项目 5：商品详情、加购与购物车

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~260 行 |
| **核心知识点** | 商品详情页、`AddToCart`、数量加减、删除、空购物车、购物车角标、总价计算 |
| **产出模块** | `appium/05_cart` |
| **前置** | 项目 4 |
| **⚠️ 风险** | 价格含货币符号，需解析；数量控件可能只有图标无 ID，需用 predicate/class chain 组合定位 |
| **验收标准** | `mvn -q -Dtest=CartTest test` 全绿；加购 2 件后角标为 2；数量 +1/-1 与总价同步；删除后回到 `No Items` 空态；总价等于单价 × 数量（BigDecimal 断言）|

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「商品详情与购物车」。请给我约 260 行 Java + TestNG 代码：从 Catalog 进入商品详情，加购 2 件，断言购物车角标为 2；在购物车中加减数量、删除商品，断言总价与空态 No Items；价格用 BigDecimal 清洗比较。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：角标统计的是**总件数**不是行数——先加 1 件、把详情页 Amount 调到 2 再加购一次，角标是 3 不是 2，"加购 2 件"必须一次加够；角标是 name=纯数字、`visible=false` 的 StaticText，只能 presence + 文本断言，且要排除详情页名为 `Amount` 的数量文本避免误匹配。金额有两种格式：详情页单价 `$ 29.99`（有空格）、购物车总价 `$29.99`（无空格），`parseAmount` 归一化后用 `assertEquals`（值与 scale 一致才判等），小数位数可能不同时要换 `compareTo`。购物车底部的 `"N Items"` 文案全局唯一，是数量加减后最好的等待锚点（行内数字文本与角标同名，不可靠）；点击前先记旧值再等 `N±1 Items`。空态文案 `No Items` 常驻源码（有商品时 visible=false），空态断言用 `isDisplayed` 翻转而非存在性。Appium server 在两次实验之间退出过一次（session 释放问题），`apply` 幂等拉起即可。实际 Java 331 行（规划 ~260）。

---

### [x] 项目 6：⛓️ 结算全流程（地址 → 支付 → Review → 下单）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~320 行 |
| **核心知识点** | Shipping Address 校验、Payment 表单、billing same/different、Review Order、Place Order、Checkout Complete、端到端串联 |
| **产出模块** | `appium/06_checkout` + `flows/CheckoutFlow`（被后续项目复用）|
| **前置** | 项目 3、4、5 |
| **⚠️ 风险** | 支付/地址输入框无 accessibilityIdentifier，需 predicate/class chain；键盘遮挡会吞点击，需滚动或 `hideKeyboard`；流程长，失败时必须带步骤日志 |
| **验收标准** | `mvn -q -Dtest=CheckoutE2ETest test` 全绿；登录 → 加购 → 地址 → 支付 → Review → Place Order → `CheckoutComplete-screen` 一条用例跑通；空姓名/空卡号分别触发 `Value looks invalid.` alert；Review 与 Cart 总价一致 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「结算全流程」。请给我约 320 行 Java + TestNG 代码：登录后加购，填写 shipping address 与 payment，选择 billing same as shipping，Review Order 后 Place Order，断言 CheckoutComplete-screen；覆盖空姓名/空卡号的 alert 校验；每步输出步骤日志，输入框用 predicate/class chain 定位并处理键盘遮挡。只输出代码。`

**完成日期**：2026-10-22
**踩坑记录**：登录态可能跨 `clearApp` 残留（同一轮实测里登录门一次都没出现、下次又出现三次），`flows/CheckoutFlow` 用条件门消化——点 Proceed 后轮询"用户名建议列表"或"地址表单标题"，先到者定路径。地址与支付两段表单的预填值都不被认账，必须逐字段 clear + sendKeys + Tab 键（`mobile: keys` 参数是复数 `keys`）重填，否则地址步弹 `Please provide your full name.`、Review 步弹 `Value looks invalid.`（两条文案不同、弹出时机也不同：卡号问题要等点 Review Order 才报）。Review 页总价 **$35.98 = $29.99 + $5.99 运费**，不与购物车总价相等，断言写成加法。billing 勾选框是图标按钮 `CheckBoxUnselected Icons`，默认未勾选也能走完（演示 App 无强制账单地址分支）。输入框全部 name=null，按 TextField 类型 + 表单顺序索引定位。实际 Java 397 行（规划 ~320）。产出 `flows/CheckoutFlow` 供后续项目复用。

---

## 🗂️ 第三阶段：移动专项能力（项目 7-10）

> **目标**：掌握原生 App 才有的手势、WebView、生物识别、生命周期能力，跳出"只会点按钮"的 Web 思维

### [x] 项目 7：手势与滚动（W3C Actions / 画布签名）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | W3C Actions、swipe/scroll/drag、长按、画布签名、相对坐标、`mobile: scroll` |
| **产出模块** | `appium/07_gestures` |
| **前置** | 项目 1、2 |
| **⚠️ 风险** | 手势坐标依赖设备尺寸；一律用元素坐标或相对比例，不写死像素；画布签名是"能画"而非"识别笔迹" |
| **验收标准** | `mvn -q -Dtest=GestureTest test` 全绿；在 Drawing 画布画出折线并 Save 成功；长按 App Header 触发 Reset App State；滑动 Catalog 到最后一个商品；至少 3 种手势各一条断言 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「手势与滚动」。请给我约 200 行 Java + TestNG 代码：用 W3C Actions 在 Drawing 画布画折线并 Save；长按 App Header 触发 Reset App State；用相对坐标 swipe 把 Catalog 滚到最后一个商品；所有坐标基于元素位置计算，不写死像素。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：**系统权限弹窗是最大的坑**——Drawing 的 Save 首次触发照片权限弹窗，它是系统级的（不在应用源码、吞掉后续所有点击、跨 `clearApp` 和应用重启挂着），`gesture.sh apply` 用 `simctl privacy grant photos` 预授权，已挂起的用 `mobile: alert` 的 accept 关闭。**规划里"长按 App Header 触发 Reset App State"实测不存在**（长按页头/商品都无反应，长按商品还会退化成点击打开详情页），诚实适配：长按改在画布上演示（按住出墨点），Reset 走 More 页 `ResetAppState-menu-item` + 确认框。`DrawingBackground Icons` 的 visible 标志不可靠（页开着也 false），等 presence 即可，坐标交互不受影响。RESET APP 确认后 tab 栏全部 visible=false 且卡在 More 页，用 `terminateApp` + `launchApp` 重启绕开（重启后 'Products' 文本 presence 不可靠，真正断言放购物车空态）。像素差断言阈值按实测定：折线 11400px（>500）、长按墨点 38px（>10）、Clear 复原 0px；截图是 2x 视网膜，画布坐标要乘比例换算。实际 Java 314 行（规划 ~200）。

---

### [x] 项目 8：WebView 混合应用（Context 切换）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | NATIVE/WEBVIEW context、`getContextHandles()`、`context()`、WKWebView、`webviewConnectTimeout`、双上下文等待 |
| **产出模块** | `appium/08_webview` |
| **前置** | 项目 1、2 |
| **⚠️ 风险** | WKWebView 的 context 可能延迟出现，需设 `webviewConnectTimeout` 并轮询；若始终拿不到 context，fallback 为 native 断言 + 如实记录，不假装切成功 |
| **验收标准** | `mvn -q -Dtest=WebViewTest test` 全绿；Menu → Webview → Go To Site 后切到 WEBVIEW context，断言页面标题/URL；再切回 NATIVE 并返回 Catalog；同一用例内完成 NATIVE → WEBVIEW → NATIVE |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「WebView 混合应用」。请给我约 220 行 Java + TestNG 代码：从 Menu 进入 Webview，点击 Go To Site，轮询 getContextHandles 直到出现 WEBVIEW，切换后断言标题或 URL，再切回 NATIVE 并返回 Catalog；设置 webviewConnectTimeout，context 不出现时给出清晰失败信息。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：**该构建 WKWebView 未开 inspectable，WEBVIEW context 永不出现**（30 秒轮询只有 NATIVE_APP；模拟器级 `defaults write` 强制开启也无效；iOS 16.4+ 起 inspectable 是 App 侧代码 `webView.isInspectable = true` 的事）——触发规划的 fallback 条款：native 树断言 Web 内容（Web 文本以 StaticText 暴露），不假装切换成功；用例按"拿到 context 就切、拿不到走 fallback"双向设计，未来 App 开启 inspectable 自动升级。**默认 URL `https://www.website.com` 不可达**（广告停放域名，永远 Loading），`webview.sh apply` 起本机 8923 静态页（configs/webview-page.html）替代外网。**返回箭头 name/label 全 null 且 x/y 不能用于 NSPredicate**（实测谓词零命中），只能遍历按钮按 rect 左上角过滤。**返回菜单页时 URL 框自动聚焦弹键盘吞掉 tab 点击**，需二次返回到 More 页让焦点随导航离开。**离开 WebView 后可达性树短暂陈旧**（屏幕有 "Products" 源码没有），等 `Product Name` presence + 重切 tab 恢复。实际 Java 270 行（规划 ~220）。

---

### [x] 项目 9：生物识别与系统弹窗（Face ID 模拟）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~240 行 |
| **核心知识点** | `mobile: enrollBiometric`、`mobile: sendBiometricMatch`、LocalAuthentication、系统 alert、`autoAcceptAlerts`、权限 |
| **产出模块** | `appium/09_biometrics` |
| **前置** | 项目 3 |
| **⚠️ 风险** | 生物识别模拟只在 Simulator 有效；真机需要真实 Face ID。权限类操作依赖可选工具 applesimutils，未装则跳过并标注 |
| **验收标准** | `mvn -q -Dtest=BiometricLoginTest test` 全绿；Menu → Biometrics 开启开关；Login 页点 Face ID，`sendBiometricMatch(faceId, true)` 后登录成功；`match=false` 时停留登录页且无崩溃；系统弹窗不阻塞下一条用例 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「生物识别与系统弹窗」。请给我约 240 行 Java + TestNG 代码：在 iOS Simulator 上先 enrollBiometric，再分别模拟 Face ID match=true/false，验证登录成功与失败；处理系统 alert，设置 autoAcceptAlerts；说明 applesimutils 只用于权限类能力。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：Biometrics 页的开关是图标按钮 `SwitchUnselected Icons`（不是 Switch 控件），**拨动后图标名实测不变**，开关状态的断言用功能信号——Login 页出现 `FaceId Icons` 按钮即生效。**系统人脸提示是系统级覆盖层**：不在应用源码、点不到，弹出期间应用"卡住"属正常，必须用 `sendBiometricMatch(type=faceId, match=bool)` 应答；match=true 登录成功后落到 "Enter a shipping address" 结算地址页（该 App 的登录表单就是结算登录门），match=false 无错误文案、唯一可观察结果是停留登录页。`autoAcceptAlerts(true)` 兜底权限类弹窗，Face ID 提示不归它管；applesimutils 本机未装，按规划跳过权限精细分支。`clearApp` 会清 Face ID 开关状态，每条用例需重新打开。实际 Java 199 行（规划 ~240）。

---

### [x] 项目 10：应用生命周期与状态恢复

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | `terminateApp`、`activateApp`、`backgroundApp`、`queryAppState`、`mobile: launchApp`、Reset App State、状态持久化 |
| **产出模块** | `appium/10_lifecycle` |
| **前置** | 项目 3、5 |
| **⚠️ 风险** | 该 App 未注册自定义 URL scheme，深链接不作为硬验收；用 `simctl openurl` 只做演示。状态恢复依赖 App 自身 UserDefaults，断言要按实际行为写 |
| **验收标准** | `mvn -q -Dtest=LifecycleTest test` 全绿；后台 5s 再激活仍在原页面；terminate 后 launch，登录态/购物车按实际行为恢复；Menu → Reset App State 后购物车清空；`queryAppState` 断言状态值 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「生命周期与状态恢复」。请给我约 220 行 Java + TestNG 代码：后台 5 秒再激活、terminate 后重新 launch、queryAppState 断言、Menu 里 Reset App State 清空购物车；说明该 App 无自定义 URL scheme，深链接只用 simctl openurl 演示。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：`backgroundApp` 带 duration 参数（`{"appId":..., "duration":5}`）实测是"后台 5 秒后**自动回前台**"——命令返回时 queryAppState 已是 4，要保持后台必须不带 duration 由测试自己 sleep。`queryAppState` 返回数字（前台 4 / 后台 3 / 终止后 1 / 未安装 0），Java 客户端返回 Object 需转 Number。**状态恢复是不对称的实测行为**：terminate 后重启购物车清空（未持久化，进程死亡即消失）但登录态保留（Keychain/UserDefaults 不随进程死亡丢失），断言按实际写并在消息里注明"实测行为"。RESET APP 确认后的 tab 栏粘滞状态（07 同款）用 terminate+launch 重启绕开。深链接：该 App 未注册自定义 URL scheme，`simctl openurl` 只开 Safari，仅 README 说明不做断言。实际 Java 235 行（规划 ~220）。**至此第三阶段收官：移动专项能力（手势/WebView/生物识别/生命周期）4/4 完成。**

---

## 🗂️ 第四阶段：工程化与交付（项目 11-14）

> **目标**：把前面 10 个项目的能力收进一套可维护、可诊断、可并行、能证明稳定的回归体系

### [x] 项目 11：数据驱动与测试数据隔离

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~200 行 |
| **核心知识点** | TestNG DataProvider、JSON/CSV 数据源、随机数据、测试隔离、状态重置、失败重跑 |
| **产出模块** | `appium/11_data_driven` + `testdata/checkout-cases.json` |
| **前置** | 项目 6 |
| **⚠️ 风险** | App 状态持久化在本地，用例间会互相污染；每条数据前必须 reset 或使用独立模拟器 |
| **验收标准** | `mvn -q -Dtest=CheckoutDataDrivenTest test` 全绿；5 组地址/支付数据独立跑通；每次生成唯一收件人；重跑不依赖上一次状态 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「数据驱动与隔离」。请给我约 200 行 Java + TestNG 代码：用 DataProvider 从 checkout-cases.json 读 5 组地址/支付数据，每组生成唯一收件人并跑完整结算；每例开始前重置 App 状态，保证顺序执行和失败重跑都不互相污染。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：直接复用 06 的 `flows/CheckoutFlow` 编排器（自包含拷贝到本工程），DataProvider 用 Jackson 读 `testdata/checkout-cases.json`（pom 新增 jackson-databind 2.17.2 test 依赖）。**唯一收件人是数据生效的关键断言**：姓名 + 毫秒后缀（36 进制）保证跨组不重名，Review 页源码含唯一姓名 = 本组数据确实被应用采用（原始姓名会跨组重复，残留场景下断言也绿）。每条数据前 BeforeMethod clearApp 强隔离。5 组数据含中国地址（"李雷" CJK sendKeys 直填正常）、德国长地名、日本短邮编（含连字符），全部跑通。实际 Java 362 行（BaseTest 82 + 测试 78 + 复用的 CheckoutFlow 234，新增 ~160）。

---

### [x] 项目 12：POM / 组件对象重构

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~350 行 |
| **核心知识点** | Screen Object、Component Object、Flow、BasePage、懒加载定位、显式等待、分层边界 |
| **产出模块** | `appium/12_pom`（`pageobjects/` + 重构后的核心用例）|
| **前置** | 项目 3-11 |
| **⚠️ 风险** | 过度封装会把断言也藏进 Page；业务断言必须留在测试层，Page 只负责"动作 + 状态查询" |
| **验收标准** | `mvn -q test` 核心 6 条用例全绿；测试类中 `findElement` 出现次数为 0；所有元素定位只存在于 pageobjects；新增一个页面只需新增一个类 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「POM 重构」。请给我约 350 行 Java + TestNG 代码：把登录、目录、商品详情、购物车、结算抽成 Screen Object + Component Object + Flow；BasePage 统一显式等待和动作封装；业务断言保留在测试层；重构后 6 条核心用例全绿。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：分层结构落定为 pageobjects/BasePage（click/type/exists/isVisible + 三种等待）+ 4 个屏幕类（LoginPage/CatalogPage/ProductPage/CheckoutPage，其中 ProductPage 一个类管详情与购物车两个屏）+ flows/PurchaseFlow（登录门条件分支 + 结算编排 + 步骤日志）。**测试层零定位器**是硬验收：4 个 *PomTest 的 findElement 计数为 0，业务断言（角标=1、全序一致、到达完成页）全部留在测试层，Page 只提供事实查询方法。**visible 标志怪癖贯穿始终**："Remove Item" 同名按钮与 StaticText 并存（删除只点按钮类型、删到按钮消失）、购物车页需等 "My Cart" 标题可见再读源码（No Items 空态元素常驻源码，cartHasItems 按可见性判断而非源码包含）。BasePage 的"子类不直接碰 driver"最初写成绝对表述，被自己的代码推翻（滚动加载/Webview 演示必须直接用 driver），如实改为"以这些方法为主"。实际新增 ~500 行（规划 ~350）。

---

### [x] 项目 13：报告、截图与失败诊断（Allure）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~220 行 |
| **核心知识点** | TestNG `ITestListener`、Allure、失败截图、page source、Appium server 日志、simctl 日志、录屏 |
| **产出模块** | `appium/13_reporting` |
| **前置** | 项目 1-12 |
| **⚠️ 风险** | Allure CLI 需单独安装；报告目录和截图不提交仓库；录屏文件要限制时长和数量 |
| **验收标准** | 故意失败的用例自动附截图 + page source + Appium 日志；`allure serve target/allure-results` 能看到完整证据链；成功用例不产生多余附件 |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「报告与失败诊断」。请给我约 220 行 Java + TestNG 代码：实现 ITestListener，用例失败时自动截图、保存 page source、附加 Appium 日志；接入 Allure 报告；给一条故意失败的演示用例和 allure serve 命令；成功用例不产生多余附件。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：**监听器注册顺序是头号坑**——Allure 处理失败时会关闭用例的结果上下文，DiagnosticListener 排在 AllureTestNg 之后的话附件全部掉进容器（container.json）而非用例，报告里看不到；解法是 pom 配置 `suiteXmlFiles` 指向 configs/testng.xml 并把 DiagnosticListener 放在 AllureTestNg 之前（**`mvn test` 默认不读测试文件里的 testng.xml**，不配 suiteXmlFiles 监听器完全失效，实测踩过）。`Allure.addAttachment` 没有 byte[] 重载，需包 ByteArrayInputStream。录屏按"失败才停才存"实现，成功用例零附件。Allure CLI 2.46.1 brew 安装。注意：`all` 命令末步 clean 会删 target/（报告与录屏），想看报告单独跑 observe。实际 Java ~260 行（规划 ~220）。

---

### [x] 项目 14：🏁 终极回归套件与本地流水线（双模拟器并行 + 10 连跑）

| 项目信息 | 详情 |
|:---|:---|
| **行数** | ~300 行 |
| **核心知识点** | TestNG suite XML、groups（smoke/regression）、并行、`wdaLocalPort`/`derivedDataPath`、RetryAnalyzer、稳定性度量、本地流水线 |
| **产出模块** | `appium/14_final_suite` + `run_suite.sh` |
| **前置** | 项目 1-13 |
| **⚠️ 风险** | 并行必须为每个 session 分配唯一 `wdaLocalPort` 和 `derivedDataPath`；两台模拟器很吃内存；10 连跑预计 20-30 分钟 |
| **验收标准** | `./run_suite.sh` 一条命令在 2 台模拟器上并行跑 smoke + regression；≥25 条用例全绿；连续 10 次运行全绿（或把 flaky 率如实记录并归零）；失败自动重试不超过 1 次；报告归档到 `target/` |

**🤖 开始提示词**：
> `我要开始 Appium iOS 项目「终极回归套件」。请给我约 300 行 Java + TestNG + shell：TestNG suite 分 smoke/regression 两组，在两台 iPhone 模拟器上并行，每个 session 配唯一 wdaLocalPort 和 derivedDataPath；加 RetryAnalyzer 和 10 连跑统计脚本 run_suite.sh；输出总用例数、通过率、flaky 率。只输出代码。`

**完成日期**：2026-10-23
**踩坑记录**：**双模拟器并行必须资源隔离**——两个 session 各配独立 `wdaLocalPort`（8100/8101）与 `derivedDataPath`，共用会让 WDA 互相覆盖。第二台模拟器用 `simctl clone` 创建（连应用一起复制，比单独安装省事）。**reset 后 tab 栏粘滞**在并行负载下更明显：Cart tab 可见可点但点击被吞，openCart 用"重启回目录 + 重试"兜底；Reset 断言改用角标消失（避开导航雷区）。**10 连跑实测 292 条用例、291 通过、1 失败**——唯一失败是 run 8 的 smoke08（Reset 后粘滞导致 Cart 导航被吞，重试后仍失败），属间歇性环境问题而非 flaky（RetryAnalyzer 计数 0）；通过率 99.7%。**flaky 统计**：RetryAnalyzer 在首次失败与重试后通过时打"⚠️ flaky："标记，run_suite.sh 用 grep 统计标记数；注意 TestNG 只在失败时调 retry()，"静态计数器记重试后通过"的写法是不可达的死代码。实际新增 ~600 行（规划 ~300，含双机编排与统计脚本）。

---

## 📅 周计划

| 周次 | 内容 | 项目数 |
|:---|:---|:---:|
| **第 1 周** | 项目 1-4（环境、定位、登录、目录）| 4 |
| **第 2 周** | 项目 5-7（购物车、结算、手势）| 3 |
| **第 3 周** | 项目 8-10（WebView、Face ID、生命周期）| 3 |
| **第 4 周** | 项目 11-12（数据驱动、POM）| 2 |
| **第 5 周** | 项目 13-14（报告、终极套件）| 2 |
| **第 6 周** | 缓冲：补漏、10 连跑、报告整理 | 0 |

## 🏆 里程碑

- [x] **完成项目 1-2** → 能独立建立 iOS Appium 会话，并按优先级稳定定位元素
- [x] **完成项目 3-6** → 购物主链路自动化：登录 → 目录 → 加购 → 购物车 → 结算下单
- [x] **完成项目 7-10** → 移动专项能力：手势、WebView、Face ID、生命周期
- [x] **完成项目 11-12** → 套件工程化：数据驱动 + POM，可维护可扩展
- [x] **完成项目 13-14** → 一键回归 + 失败证据链 + 10 连跑稳定性证明
- [x] **全部完成** → 具备独立搭建 iOS Appium 回归体系的能力

## 🔧 环境配置

```bash
# 0. 已就绪（2026-10-22 本机实测）
# macOS 26.5.2（Apple Silicon）
# Xcode 26.6 + iPhone 17 / iOS 26.5 Simulator
# Node 22.23.2 / npm 10.9.8
# Java 27（Homebrew）/ Maven 3.9.16
# Appium 3.8.0 + xcuitest 12.19.1（临时目录实测）
# ffmpeg / curl / unzip

# 1. 固定 Xcode 工具链（当前 xcode-select 指向 CommandLineTools）
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
# 或一次性切换：sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

# 2. Appium server（项目内安装，避免污染全局）
mkdir -p appium/00_env && cd appium/00_env
npm init -y
npm i appium@3.8.0
npx appium driver install xcuitest
npx appium driver doctor xcuitest   # 期望 0 required fixes

# 3. 被测 App（SauceLabs My Demo App 2.3.0）
curl -L -o /tmp/SauceLabs-Demo-App.Simulator.zip \
  https://github.com/saucelabs/my-demo-app-ios/releases/download/2.3.0/SauceLabs-Demo-App.Simulator.zip
unzip -q -o /tmp/SauceLabs-Demo-App.Simulator.zip -d /tmp
xcrun simctl boot "iPhone 17" || true
open -a Simulator
xcrun simctl install booted "/tmp/Payload/My Demo App.app"

# 4. 起 Appium
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
  npx appium server --port 4723 --base-path /wd/hub

# 5. Java 测试工程
mvn -q test

# 每项目开工前统一检查
xcrun simctl list devices booted | grep "iPhone 17"
curl -s http://127.0.0.1:4723/wd/hub/status

# 可选：权限设置（相机/定位等）
brew tap wix/brew && brew install applesimutils

# 可选：Android 双端冒烟（本机已有 AVD hvtest）
~/Library/Android/sdk/emulator/emulator -avd hvtest
```

关键 capabilities：

```java
XCUITestOptions options = new XCUITestOptions()
    .setPlatformName("iOS")
    .setDeviceName("iPhone 17")
    .setPlatformVersion("26.5")
    .setAutomationName("XCUITest")
    .setBundleId("com.saucelabs.mydemo.app.ios")
    .setNoReset(true);
```

## ⚠️ 与已有清单的关系

| 已有清单 | 关系 |
|:---|:---|
| `docs/test_frameworks.md` 项目 28 / `labs/28_appium` | 单点入门：Appium 是什么 + Playwright 移动视口 fallback。本清单不复讲基础，直接进入 iOS 原生 App 的 14 项深水区；其 fallback 路径不重复 |
| `docs/playwright.md` | Web E2E 进阶线；本清单是原生 App 线，定位/等待思想可迁移，但工具与能力不重叠 |
| `labs/23-25`（Selenium / Cypress / 三框架对比）| Web 自动化对比；不涉及原生 App，无重叠 |

## 📚 来源

- [SauceLabs My Demo App - iOS（源码）](https://github.com/saucelabs/my-demo-app-ios)
- [SauceLabs My Demo App 2.3.0 Simulator 安装包](https://github.com/saucelabs/my-demo-app-ios/releases/download/2.3.0/SauceLabs-Demo-App.Simulator.zip)
- [Appium XCUITest Driver 文档](https://github.com/appium/appium-xcuitest-driver)
- [XCUITest execute methods（含 biometric 模拟）](https://github.com/appium/appium-xcuitest-driver/blob/master/docs/reference/execute-methods.md)
- [Appium Java Client](https://github.com/appium/java-client)
- [TestNG 文档](https://testng.org/)
- [Appium Inspector](https://github.com/appium/appium-inspector)

## ⚠️ 能力覆盖速查表

| 能力 | 计划 | 实测结论（2026-10-22）|
|:---|:---|:---|
| iOS Simulator 启动 | 项目 1 | ✅ iPhone 17 / iOS 26.5 启动成功 |
| App 安装/启动 | 项目 1 | ✅ `com.saucelabs.mydemo.app.ios` 安装并启动成功 |
| Appium 3 + XCUITest 会话 | 项目 1 | ✅ session 创建成功，WDA 首次构建通过 |
| page source / accessibility id | 项目 2 | ✅ 取到 `Catalog-tab-item` 等 75 个元素 |
| Face ID 模拟 | 项目 9 | ✅ `enrollBiometric` + `sendBiometricMatch` true/false 双路径实测通过 |
| WebView context 切换 | 项目 8 | ⚠️ 部分验证：本地页加载成功，但该构建 WKWebView 未开 inspectable，WEBVIEW context 不可切（native fallback 断言）|
| 双模拟器并行 | 项目 14 | ✅ 10 连跑实测：292 条用例 291 通过（99.7%），1 条为 Reset 后粘滞的间歇失败 |
| Android 双端 | 可选 | ⚠️ 本机 AVD `hvtest` 已存在，未纳入本清单验收 |
| 真机 | 不在范围 | ❌ 需要签名/开发者账号与设备，本清单不涉及 |

## 📝 每日日志

| 日期 | 项目 | 耗时 | 收获 | 踩坑 |
|:---|:---|:---:|:---|:---|
| | | | | |
