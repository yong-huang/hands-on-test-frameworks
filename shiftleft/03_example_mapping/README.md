# 03 · Example Mapping 工作台：把三色卡片变成合法的 Gherkin 骨架

> Example Mapping（三 amigos 协作法：需求、开发、测试三方围桌拆故事）开完会，
> 产出往往是三色便利贴的照片——规则和例子散在图片里没人再碰。本实验把卡片
> 数字化：蓝卡规则→场景大纲、绿卡例子→Examples 表、红卡疑问→待认领清单，
> 生成的 feature 过官方 gherkin 解析器零错误，空规则与缺例子的卡片当场告警。

## Background

三 amigos 会议的结论本来就该是测试：每条规则配几个具体例子，天然就是
Given/When/Then（Gherkin 的三种步骤关键词，中文写法即后文的 假如/当/那么）。但卡片到 Gherkin 的最后一公里靠手工——例子抄错行、
疑问丢在照片里、写出来的 feature 语法错了要等跑测试才炸。

痛点的核心是**协作产物没有结构闭环**：会议产物进不了工具链，下次迭代
没人对得上号。坏需求最便宜的拦截点（系列实验 01「缺陷成本漏斗」里需求评审这一关）就这样又退回人肉。

本实验把会议产物录成 YAML（键值对文本格式）：规则、例子、疑问三段式，一键转成结构合法的
feature 骨架与疑问清单，官方解析器当场校验——卡片没画完，工具立刻指出来。

## What

Example Mapping 工作台把三色卡片的数字记录转化为结构合法的 Gherkin 骨架与
待认领疑问清单——Gherkin 是用接近自然语言的关键词（功能/场景大纲/假如/当/那么）
写验收测试的文本格式，一个功能对应一个 .feature 文件。

三色映射：蓝卡（业务规则）→ 场景大纲，绿卡（每条规则的具体例子）→ Examples
表，红卡（答不上来的疑问）→ 逐条带 owner 与状态的清单。

可以把工作台想成卡片扫描仪：把桌面便利贴拍成结构化文件。但和扫描仪不同的是
它检查「卡片画完没有」——空规则（蓝卡没写字）、无例子（绿卡缺失）当场告警。

术语：规则就是「业务上必须成立的约束」（如「每单限用一张券」）；例子是该规则
的具体化数据点；疑问是会上答不出、需要会后认领的问题。它们翻译成 Gherkin 的
场景大纲（带 <占位符> 的模板场景）和 Examples 表（模板下面逐行填数的例子表）。

![Example Mapping 三色卡片到 Gherkin 骨架与疑问清单的转化](images/example_mapping.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/03_example_mapping/images/example_mapping.html)
> （或本地打开 [`images/example_mapping.html`](images/example_mapping.html)）。
> 引擎节点与三类卡片一一对应；告警节点是「卡片没画完」的检测出口。

## When to Use

- 三 amigos 会中：YAML 当白板记录，边聊边转骨架，疑问当场进清单认领。
- 会后补录：把便利贴照片录成 YAML，用告警找出漏画的规则与例子。

何时不用：故事只有一两句、无规则可拆时直接写场景更快；本工具解决的是
「多规则多例子的故事」的翻译与追漏。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 手写 Gherkin | 直接但容易抄漏例子、语法后置暴露 | 单场景小故事 |
| 本工具 | 结构保证 + 缺卡告警 + 疑问清单 | 多规则故事的评审会 |
| LLM 直接生成 | 语义流畅但结构无保证 | 生成后仍需本类工具校验兜底 |

## Quick Start

前置：仓库根 `.venv`（pyyaml）与 node（gherkin 解析器复用 `cucumber/` 共享依赖）。
一条命令跑完整动线，核心是干净故事的转化与校验：

```bash
./example_mapping.sh   # apply → observe（转化+校验+告警）→ clean
```

```text
=====> [observe] ① 干净故事（3 规则 6 例子）→ feature + 疑问清单 → 官方解析器校验
[Example Mapping] US-201 订单满减：3 条规则 / 6 个例子 / 2 个疑问
产物：reports/US-201.feature（待 gherkin 解析校验）、reports/US-201-questions.md
✅ gherkin 解析零错误：功能「订单满减」，3 个场景（含大纲），6 条例子
```

生成的骨架长这样（节选；文件开头还有 `# language: zh-CN` 与 `功能:` 两行）：

```text
  场景大纲: R1 小计满 100 元才可用满减
    假如 <小计>
    当 <动作>
    那么 <预期>

    例子:
      | 小计 | 动作 | 预期 |
      | 150.00 | 提交满减 | 应付 130.00 |
      | 100.00 | 提交满减 | 应付 80.00（恰在门槛可用） |
      | 99.99 | 提交满减 | 拒绝用券，应付 99.99 |
……（R2/R3 同构；疑问清单 2 条，逐条带 Owner「待定」与状态 open）
```

脏故事演示（空规则 + 无例子 → 告警，strict 模式退出码 1，预期失败）：

```text
  ⚠️ 空规则 [R1]：蓝卡没写字，已跳过不进 feature——先回 Example Mapping 把规则写出来
  ⚠️ 无例子 [R2 券叠加数量不超过 3 张]：绿卡缺失——没有例子的规则无法翻译成测试，场景骨架里留了待补占位
产物：reports/US-202.feature（待 gherkin 解析校验）、reports/US-202-questions.md
strict 模式：存在未完成卡片，故事不能进迭代（exit 1）
>>> 已按预期退出非零：卡片没画完的故事不能进迭代
✅ gherkin 解析零错误：功能「优惠券叠加（半成品）」，2 个场景（含大纲），1 条例子
```

诚实预期：骨架的步骤关键词（假如/当/那么）按列循环生成，语义需要三 amigos
精修——本工具保证结构合法、例子不丢、疑问不漏，不代替人的语义确认。

## How It Works

**转化是三层一一映射**：每条蓝卡规则生成一个「场景大纲」，其绿卡例子聚合成
该大纲的 Examples 表（表头 = 第一条例子的键），红卡疑问逐行进 markdown 清单。
核心十几行：

```python
cols = list(examples[0].keys())          # 表头取自第一条例子的键
lines.append(f"  场景大纲: {rid} {text}")
for i, col in enumerate(cols):
    lines.append(f"    {STEP_KEYWORDS[i % len(STEP_KEYWORDS)]} <{esc(col)}>")
lines += ["", "    例子:", "      | " + " | ".join(esc(c) for c in cols) + " |"]
```

**表格转义是正确性关键**：竖线与换行是 Gherkin 表格的结构字符，单元格内容
必须转义（`esc` 把 `|` 换成 `\|`、压平换行），否则一条例子里的竖线会拆碎整表。

**校验器复用官方解析器**（cucumber 13 的依赖 gherkin 42，按相对路径 import）：
`new Parser(new AstBuilder(…), new GherkinClassicTokenMatcher())` 对产物全文解析。

`# language: zh-CN` 头让中文关键词（功能/场景大纲/例子）被方言表自动识别——
语法错误在生成后一秒内暴露，而不是等 CI 跑测试。

**strict 模式是需求关的门禁牙口**：`--strict` 下任何告警（空规则/无例子/列名
不一致）都以退出码 1 收场——卡片没画完的故事进不了迭代。

## Pitfalls & Q&A

常见故障与解法：

- **同一规则的例子列名不一致**：Examples 表必须共享表头。工具以第一条例子为准
  并告警丢弃不一致的键——补录照片卡片时最常见。
- **gherkin 42 的 Parser 必须双参构造**：`new Parser(builder, tokenMatcher)` 缺
  tokenMatcher 会报 `Cannot read properties of undefined (reading 'reset')`。
- **AST（抽象语法树，解析器把 feature 文本拆成的结构化对象）属性名是 `scenario` 不是 `scenarioOutline`**：gherkin 42 文档树里两者
  同键，靠 `keyword`（场景 / 场景大纲）区分——数例子时别找错属性。

Q&A：

- **骨架步骤为什么是假如/当/那么循环？** 列名即占位符（`<小计>`），语义精修是
  三 amigos 的事；工具的边界是结构合法与信息不丢，越界反而替人做了决定。
- **产物能直接跑吗？** 步骤实现与执行在 cucumber 线（14 项已练完）；本实验
  交付的是「结构合法的待精修骨架 + 待认领疑问」，属于需求关而非执行关。
- **疑问清单的 owner「待定」怎么消费？** 评审会逐条认领、改状态，全部 closed
  才进迭代——清单就是需求关的退出条件。
