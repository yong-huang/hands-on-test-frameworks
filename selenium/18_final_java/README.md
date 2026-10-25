# 18 · 🏁 终极对照（Java + Grid）

## Background

收官之作：把项目 17 的回归集搬到 **TestNG × Grid 并行** 上，加 RetryAnalyzer 重试演示，
并产出双栈终版差异报告。跑完这一篇，「同一回归集、两种语言、两种基础设施」的对照闭环就完整了。

## What

- `testng.xml`：`parallel="methods" thread-count="2"`，全量 @Test 打向 Grid 的 Remote driver
- 三条用例：购买支付（iframe 三层）、表单冒烟、**重试演示**（首试必失败 → RetryAnalyzer 接管 → 二次通过）
- 验收三项：Tests run: N Failures: 0 ＋ 首试失败记录在案 ＋ 重试成功案例在案

## When to Use

- Java 团队要接手 Python 原型套件时的迁移样板
- 评估 Grid 基础设施 + TestNG 并行/重试的组合成本

## Quick Start

```bash
cd selenium/18_final_java
./18_final_java.sh            # apply（靶场+Grid）→ observe（mvn test）→ clean
```

实测输出（2026-10-26，节选）：

```text
[WARNING] Tests run: 4, Failures: 0, ... Skipped: 1 -- in TestSuite   ← 含重试轮次记账
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
✅ 并行 + 重试演示 + 全绿 三项验收通过
```

## 双栈终版差异报告（≥10 行，全程实证）

| # | 维度 | Python 终极套件（17） | Java 终极套件（18） |
|:--|:---|:---|:---|
| 1 | 并行模型 | pytest-xdist 多进程（-n 4） | TestNG `parallel="methods"` 多线程 |
| 2 | 基础设施 | 本地浏览器（SELENIUM_BROWSER 切换） | Remote 打 Grid（会话槽位限并行上限） |
| 3 | 失败重试 | 无内建（插件 pytest-rerunfailures） | RetryAnalyzer + IAnnotationTransformer 全局挂载 |
| 4 | 报告 | pytest-html 单文件 | surefire-reports + TestNG 内建报告 |
| 5 | driver 生命周期 | fixture yield/quit | @BeforeMethod/@AfterMethod(alwaysRun) |
| 6 | POM 形态 | 轻量类 + sys.path 复用 | PageFactory 传承 + 显式构造注入 |
| 7 | 数据驱动 | orders.json + parametrize | @DataProvider（本套件未用，见项目 12） |
| 8 | JSON 断言口径 | json.loads 字典取值（空格无关） | 字符串包含（空格敏感，见项目 12 踩坑） |
| 9 | 显式等待超时 | 秒数直传 | 必须 `Duration.ofSeconds()` |
| 10 | 重试语义 | 重跑整个用例（xdist 无感） | 同一实例重试，类状态（AtomicBoolean）跨重试保留 |
| 11 | 环境准备成本 | pip 秒级 | Maven Central 首跑分钟级 |
| 12 | 已知坑 | 相对定位器锚要字典形式 | is_displayed/isDisplayed 手滑即编译错（双栈互写必踩） |

## Pitfalls & Q&A

- **坑：`parallel="methods"` 下类状态共享**——AtomicBoolean 的「首试失败」在并行线程间是
  类级静态，若同类多测试会互相干扰；重试演示类保持单测试
- **坑：surefire 对重试的记账**——`Tests run: 4 ... Skipped: 1` 是含重试轮次的告警行，
  最终以 `Tests run: 3, Failures: 0` 的 INFO 行为准
- **Q：为什么 Grid 用 standalone 而不是 hub+node？** arm64 无 node 镜像（项目 13 实测），standalone 调大
  会话槽即等价
