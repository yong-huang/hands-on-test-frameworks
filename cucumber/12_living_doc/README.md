# 12 · 活文档与 pending：场景即规格，黄绿有别

> 测试报告通常只有工程师看，BDD 的报告却是给业务侧的"功能清单"——
> 前提是场景用业务语言写。本实验演示 pending 的正确语义（黄 = 规划中，
> 不是失败）、docstring 传递多行业务数据，以及从报告自动抽取功能清单。

## Background

需求文档与测试代码的脱节是老问题：文档说"30 天内可退货"，
代码里可能已经改成 15 天——没人发现。活文档（Living Documentation）
的解法：把规格直接写成可执行的 Gherkin，文档随代码一起验证——
规格错了测试红，代码错了也是测试红，两份永远一致。

pending 是这套体系里的重要状态：业务上已确认、实现还没排期的规则，
写成场景并标记 pending——它出现在报告里（黄色"规划中"），
提醒团队"这是承诺过的行为，还没实现"。

## What

本实验的退货规则特性有三种场景状态：两条已实现（绿）、一条 pending
（黄，已拆封电子产品的换新规则尚未实现）。报告生成后自动抽取
功能清单（reports/features.md）——业务侧可读的 markdown 文档。

可以把活文档想成餐厅墙上的菜单：绿菜是今天能上的，黄菜是"敬请期待"。
菜单随厨房能力实时更新——因为菜单就是从厨房系统生成的。
但和菜单不同，Gherkin 的每道"菜"都附带验证——pending 转绿的那一刻
意味着实现被自动验证过了。

![活文档：场景的三种状态与功能清单抽取](images/living.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/12_living_doc/images/living.html)
> （或本地打开 [`images/living.html`](images/living.html)）。
> 主链路是".feature 规格源 → 执行 → 绿"；黄与红是另两种可能状态。

## When to Use

| 实践 | 活文档价值 | 前提 |
|:---|:---|:---|
| 业务规则写成 Gherkin | ✅ 报告即功能清单 | 场景用业务语言 |
| 未排期规则标 pending | ✅ 承诺可见 | 团队理解黄 ≠ 红 |
| docstring 传多行数据 | ✅ 表单类数据的标准通道 | 步骤解析约定清晰 |
| 把 UI 操作写成场景 | ❌ 回到命令式老路 | lab 06 的门禁仍然适用 |

判断口径：**进活文档的场景必须用业务语言**——技术细节进代码注释，
业务语义进 Gherkin，两者混写会毁掉文档的可读性。

## Quick Start

```bash
cd cucumber/12_living_doc
./living_doc.sh          # apply 起靶场 → observe 2 绿 1 pending + 清单抽取 → clean
```

observe ① 跑批：两条退货规则绿、一条换新规则 pending（步骤返回 pending
字符串，cucumber 标黄而非红）：

```
2 hooks (2 passed)
3 scenarios (2 passed, 1 pending)
15 steps (13 passed, 1 skipped, 1 pending)
```

observe ② 生成 HTML 活文档与功能清单：

```
>>> 活文档: reports/html/index.html（业务可读）
>>> 功能清单: reports/features.md（抽取的场景列表）
```

验收方式：features.md 列出全部 3 个场景且状态标注正确（✅/🟡）；
pending 场景不红（脚本显式容忍黄）；变异实验：给 pending 步骤返回
`'failed'` 字符串重跑——状态变红，证明黄红有别。

## How It Works

**docstring 是多行业务数据的标准通道。** 步骤行之后跟三引号块，
整块文本原样传入步骤函数——退货申请的三行数据按行解析。

比 5 列 Examples 表更适合字段随规则变化的数据：
加一个字段只改 docstring 与解析，不动表结构。

**pending 的实现是一行字符串返回值。** 步骤函数 `return 'pending'`，
cucumber 将该步骤标记为 pending（黄）并继续执行后续场景——
与 failed 的区别是语义：pending = 还没做，failed = 做错了。
报告中两者分色呈现，混为一谈就会掩盖真实缺陷。

**功能清单从 json 抽取。** cucumber.json 记录每个 feature 的描述、
每个场景的名称与状态——`extract_features.mjs` 把它转成 markdown
功能清单（状态图标 + 场景名）。这份清单与 HTML 报告同源（同一个 json），
永远一致。

## Pitfalls & Q&A

**Q：pending 步骤后面的步骤为什么是 skipped？**
pending 发生在步骤执行中，cucumber 视为"该步骤未完成"并跳过同场景
剩余步骤——场景本身记 pending 而非 failed。要让"后续断言仍执行"，
应把未实现部分改成 `test.skip` 语义的独立场景，而不是共享场景体。

**Q：pending 和 skip 有什么区别？**
skip（如 `@wip` 排除）是"本次不跑"，报告里根本不出现；
pending 是"跑了但未实现"，以黄色出现在报告里。活文档只收录
pending（规划中的承诺），skip 的内容不进文档。

**Q：docstring 与 DataTable 怎么选？**
多行长文本（错误消息模板、SQL、配置块）用 docstring，
字段化记录（列名固定的表）用 DataTable。

本实验的退货申请三行数据用 docstring + 手工解析演示了通道；
若字段稳定，DataTable + hashes() 是更结构化的选择（lab 05）。

**Q：功能清单的"状态"会骗人吗？**
会，如果场景名与实际行为脱节。清单的状态来自执行（真实），
但场景名是人写的——"名称叫退货、实际测下单"的场景会让清单
看起来对其实错。命名评审（lab 06 的业务语言纪律）是清单可信的前提。

**Q：pending 的规则实现后，要改几处？**
两处：实现业务代码 + 把步骤的 `return 'pending'` 换成真实实现。
然后黄转绿。如果业务代码与测试步骤同时就绪，直接删掉 pending 返回值
即可——活文档的更新是零成本的，这正是它"活"的含义。
