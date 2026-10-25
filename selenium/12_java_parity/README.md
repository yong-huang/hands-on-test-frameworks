# 12 · ⛓️ Java 双栈对照

## Background

国内测试团队的现状常是「Python 跑得快、Java 家底厚」并存。同一套 POM 用例在双栈各写一遍，
差异表就是技术选型与团队分工的第一手依据。本项目把项目 10 的结账购买套件原样迁到
Maven + TestNG + Selenium Java，断言语义逐条等价。

## What

- `pom.xml`：selenium-java 4.27 + testng 7.10 + surefire，Java 17
- `pages/CheckoutPage` + `flows/PurchaseFlow` + `PurchaseTest` 三层等价迁移
- 用例：三层 iframe 购买 → 支付 → HTTP 客户端复核 `status=paid` 与金额字段
- 产物：双栈差异表（下方，≥8 行）

## When to Use

- 团队双栈并存时的迁移/对照评估
- 面试讲「同一套件两种语言写法的差别」时的实证材料

## Quick Start

```bash
cd selenium/12_java_parity
./12_java_parity.sh            # apply → mvn test → clean（清理会删 target，结果见 observe 输出）
# 只重跑：./12_java_parity.sh observe
```

实测输出（2026-10-26）：`Tests run: 1, Failures: 0, Errors: 0, Skipped: 0`（另有一条 CDP 版本告警，不影响）

## 双栈差异表（≥8 行，实证）

| 维度 | Python（项目 10/17） | Java（本项目） |
|:---|:---|:---|
| 运行入口 | `pytest 目录` 按收集器扫 | `mvn test` 走 surefire（`*Test` 命名约定） |
| 依赖管理 | venv + pip（秒级） | Maven Central（首跑下载分钟级） |
| 生命周期 | pytest fixture（yield 后销毁） | TestNG `@BeforeMethod/@AfterMethod` |
| 显式等待 | `WebDriverWait(d, 10)`（秒） | `new WebDriverWait(d, Duration.ofSeconds(10))`（必须 Duration） |
| 断言 | 裸 `assert` + 比较 | `Assert.assertTrue/assertEquals` |
| 参数化/数据驱动 | `pytest.mark.parametrize` | `@DataProvider` + `@Test(dataProvider=...)` |
| 并行 | pytest-xdist 按进程 | TestNG `parallel="tests"` 按线程（或 Grid） |
| 失败报告 | pytest 输出 + junit xml | surefire-reports txt/xml + Allure 生态 |
| JSON 断言 | `json.loads` 后字典取值（服务端空格无关） | 字符串包含断言（**空格敏感**，见踩坑） |
| POM 习惯 | 轻量类 + fixture 注入 | PageFactory 传承 + 显式构造注入 |

## Pitfalls & Q&A

- **坑：Python `json.dumps` 键值间带空格**（`"status": "paid"`）——Java 侧字符串包含断言
  不留空格必挂（实测第一次就翻车）；双栈对照先对齐序列化空格口径
- **坑：surefire 默认只扫 `*Test` 命名**——类名不带 Test 后缀会静默 0 条（appium/13 同款教训）
- **Q：CDP 版本告警要处理吗？** 不影响本实验；要消除需按浏览器版本显式引入 selenium-devtools 构件
