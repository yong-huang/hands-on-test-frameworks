# 09 · 报告体系：一次失败，三路产物，一份活文档

> 测试跑完只留一个退出码是浪费——失败现场（截图、上下文）、CI 数据（JUnit）、
> 业务可读的功能清单（活文档）都应该自动产出。本实验给 BDD 套件配三路
> formatter（json/junit/summary），用一条人为失败标本验证报告的完整形态。

## Background

lab 02 的踩坑已经证明 BDD 报告自带"功能清单"属性——但 cucumber 默认只在
终端打 summary，跑完什么都不留。CI 需要机器可解析的结果（JUnit XML），业务侧需要可读的活文档，
排障需要失败现场（截图附件）——三种消费者，三种格式。

reporter（报告器）是把执行结果转换成特定格式的插件。
cucumber 的 json formatter 输出全量结构化结果，HTML 渲染器
（multiple-cucumber-html-reporter）消费 json 生成交互报告。

json 是中间货币，报告是它的一个视图。

## What

reporter（报告器）是把执行结果转换成特定格式的插件。
cucumber 的 json formatter 输出全量结构化结果，供下游渲染器消费。

HTML 渲染器（multiple-cucumber-html-reporter）把 json 变成交互报告。
json 是中间货币，报告是它的一个视图。

可以把报告体系想成体检中心：验完血（跑批）同时出三份东西——化验单
（JUnit 给"平台"读）、体检报告（HTML 给"人"读）、血样留档（截图附件给"复查"）。
但和体检不同，失败标本的截图是自动采集的——After 钩子读到 FAILED 状态才挂。

![报告体系：失败场景的附件流经三路 formatter](images/reports.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/09_reports/images/reports.html)
> （或本地打开 [`images/reports.html`](images/reports.html)）。
> 主链路是"失败场景挂附件 → json formatter → HTML 渲染"；JUnit 与终端是并行出口。

## When to Use

| 消费者 | 产物 | 打开方式 |
|:---|:---|:---|
| 本地排障 | HTML 报告 | 浏览器打开 reports/html/index.html |
| CI 平台 | junit.xml | 平台自动解析聚合 |
| 业务侧功能清单 | HTML 活文档 | 同 HTML 报告（场景即功能） |
| 开发循环 | summary 终端 | 跑批即见 |

判断口径：**报告的形态由最远的消费者决定**。CI 需要 JUnit 就必须配
junit formatter；业务侧要读活文档就必须留 json——缺一路就断一类消费者。

## Quick Start

```bash
cd cucumber/09_reports
./reports.sh          # apply 起靶场 → observe 跑批 + 产物核验 + 活文档生成 → clean
```

observe ① 跑 3 个场景（2 绿 + 1 条人为失败标本，脚本显式容忍红）：

```
2 hooks (2 passed)
3 scenarios (2 passed, 1 failed)
15 steps (14 passed, 1 failed)
```

observe ②③ 是产物核验：JUnit 过 xmllint 合法性检查，HTML 活文档生成：

```
>>> cucumber.json ✓ (24900 bytes)
>>> junit.xml 合法 ✓
>>> reports/html/index.html ✓  （open 查看活文档）
```

验收方式：junit.xml 过 xmllint 零输出；打开 HTML 报告能看到失败场景
内嵌的截图附件与上下文文本。变异实验：把失败标本改回有效断言——
报告变全绿，活文档里该场景的标记从红转绿。

## How It Works

**attach 是"给报告喂字节"的通用通道。** World 的 `this.attach(data, opts)`
把任意字节挂进当前场景的结果流——截图（Buffer）、文本（string）都行，
`fileName` 与 `mediaType` 决定报告里的呈现形态。

本实验挂在 After 钩子里，以 `scenario.result.status === 'FAILED'` 为守卫：
失败场景才产截图，成功零噪声。

**formatter 传参的两条路，宽严不同。** CLI 的 `--format json:reports/xxx.json`
是 name:path 简写（本实验采用）；配置文件的 format 数组校验更严——
对象形式的 outputFile 键实测被 schema 拒绝。

经验法则：路径类的 formatter 参数走 CLI，行为类的配置走配置文件。

**失败标本是报告的验收器。** 一条稳定失败的人为用例（断言不存在的元素）
让报告每次都有"失败详情"可查：内嵌截图、上下文文本、错误信息三位一体。

报告体系没有失败标本就像消防演练没有火——流程通了一遍，但没人见过烟。

## Pitfalls & Q&A

**Q：Then 步骤没带表时报"callback and promise"是什么错？**
本实验实测踩过：Then 步骤签名写了 `table: DataTable`，但 feature 里
该步骤没有挂表——cucumber 只传进来回调函数，`table.hashes()` 调用的
其实是回调。

报 "function uses multiple asynchronous interfaces" 是
"签名与实际参数不匹配"的名片：签名里的 DataTable 位置收到了别的东西。

**Q：scenario.attach 报不存在，attach 不是钩子参数的属性吗？**
cucumber 13 里 attach 是 World 的方法（`this.attach`），不是钩子参数的
属性——钩子参数带的是 pickle 与 result。

实测 `this.attach(...)` 是正确调用点。
类型报错时优先查 API 归属，别靠猜。

**Q：attach 的选项键是 filename 还是 fileName？**
cucumber 13 的 ICreateAttachmentOptions 用 `fileName`（驼峰）——
`filename` 会被类型检查拒绝。

这类键名差异以本地 node_modules 的类型定义为准
（tsc 报错信息里甚至会提示正确拼法）。

**Q：formatter 写在配置文件里为什么会报错？**
配置文件的 format 数组元素要求是字符串或 `[string, 对象]`，
对象形式的 outputFile 键被 schema 拒绝。

而 `name:path` 字符串简写在配置文件里会被当作
formatter 名去 import（junit: 被当成 ESM 模块名）——两条路都不通时，
CLI 传参是可靠出口：路径类参数留在脚本里，随调用而变是合理形态。

**Q：rows() 和 hashes() 能混用吗？**
同一张表在同一个步骤里可以两种方式各读一遍（它们都是纯函数视图），
但一个步骤通常只需要一种。

混用的常见场景：rows() 先校验表形状（行数、列数），
hashes() 再做业务消费——形状不对时报更友好的错误。

**Q：报告里能看到步骤参数吗？**
能。json 与 HTML 报告都记录每个步骤的参数（本实验的登录步骤带
用户名/密码参数）——但注意敏感信息会原样出现在报告里。

生产套件应避免在参数里传明文密码（环境变量注入 + 报告脱敏），
测试数据用假数据集是更稳的默认。

**Q：HTML 渲染器与 cucumber 13 的 json 兼容吗？**
multiple-cucumber-html-reporter 3.x 对 cucumber 13 的 json 实测兼容
（本 lab 的清单文档曾标 ⚠️ 待验证，实测通过）。

风险在于大版本升级后 json schema 变化——
若渲染报错，fallback 是 cucumber 官方的 html formatter。

**Q：表格里的空单元格会变成什么？**
hashes() 里空单元格的值是 `''`（空字符串）而非 undefined/null。

断言"必填字段非空"时用 `expect(v).not.toBe('')`，别写 `toBeFalsy()`——
空串恰好是 falsy，会误伤合法的 `'0'` 吗？不会，'0' 是 truthy；
但 `toBeFalsy` 的语义模糊性不值得引入。
