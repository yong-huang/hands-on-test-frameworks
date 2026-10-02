# 11 · Example Mapping：从需求对话到红绿闭环

> BDD 的价值一半在工具，一半在对话。Example Mapping（实例化映射，Cucumber
> 创始人推广的协作方法）用三色卡片把一条模糊的需求("仅 admin 可删单")
> 推演成具体的规则与例子，再落成 .feature 文件——先写场景（全 pending 黄），
> 再实现步骤（收敛绿）。本实验完整走一遍这条红→绿闭环。

## Background

直接写 .feature 的常见困境是"不知道该写哪些场景"——因为需求本身
只有一句话。Example Mapping 是把这句话摊开的协作方法：拿三色便利贴，
规则写卡纸（黄），例子写便签（绿），没答案的问题写红卡（疑问），
一场 15 分钟的对话就能把需求的边界全部铺开。

本实验的需求卡是 pw-store 的真实规则："仅 admin 可删单"。
推演出两条规则（admin 可见可删 / customer 不可见不可删）与一个疑问
（顾客绕过 UI 直接调 API 呢？→ 服务端 403）——疑问的答案直接补进场景。

## What

三色卡的产物是"规则 + 例子"清单：每条规则至少配 2 个例子（正例与反例），
例子进 Examples 表。本实验的场景大纲因此只有 2 行例子——admin 行与
customer 行，每行同时断言 UI 可见性与 API 状态码。

可以把 Example Mapping 想成需求的"摊煎饼"：一句话的面糊倒在三色卡上，
推演过程把它摊成一张覆盖所有边界的薄饼。但和摊煎饼不同，
摊开的结果直接是可执行的 .feature——对话产物零翻译损耗。

![Example Mapping：三色卡到红绿闭环](images/mapping.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/11_example_mapping/images/mapping.html)
> （或本地打开 [`images/mapping.html`](images/mapping.html)）。
> 主链路是"需求卡 → 三色卡推演 → .feature → 红 → 实现 → 绿"。

## When to Use

| 场景 | Example Mapping | 直接写 feature |
|:---|:---|:---|
| 需求只有一句话、边界未明 | ✅ 先摊开再写 | ❌ 漏边界场景 |
| 需求文档已经很细 | ⚠️ 走过场 | ✅ 直接翻译 |
| 多方对"什么算完成"有分歧 | ✅ 例子上桌对齐 | ❌ 分歧进代码 |
| 遗留功能补测试（行为已定） | ⚠️ 从现状反推例子 | 直接写 |

判断口径：**需求越模糊，Example Mapping 的收益越大**。
它花的是对话时间，省的是"做完发现理解错了"的返工。

## Quick Start

```bash
cd cucumber/11_example_mapping
./example_mapping.sh          # apply 起靶场 → observe 需求卡场景 2 组全绿 → clean
```

observe ① 跑需求卡推演出的场景大纲（2 组例子：admin 行与 customer 行）：

```
2 hooks (2 passed)
2 scenarios (2 passed)
10 steps (10 passed)
```

每行断言三件事：删除按钮可见性（admin 见 / customer 不可见）、
直接调删除 API 的状态码（200 / 403）——UI 与 API 双层都钉死。

验收方式：2 组全绿。变异实验：把 customer 行的预期状态码改成 200
（模拟"以为顾客也能删"的错误理解）重跑——customer 行必红，
这正是 Example Mapping 在需求阶段就该拦住的理解偏差。

## How It Works

**红先绿后是工作法的骨架。** 先写 .feature（步骤全 pending，报告黄色），
确认场景覆盖了规则与例子，再逐条实现步骤绑定。pending（黄色）与 failed
（红色）的语义区分是关键：黄 = "还没做"，红 = "做错了"——
先全黄再逐条转绿，进度可见且不会带病通过。

**Example Mapping 的产出直接映射 .feature 结构。** 一条规则 ≈ 一个 Feature，
一个例子 ≈ Examples 表的一行，一个疑问 = 新增的一条断言
（本实验"API 直删"的疑问变成了"状态码"步骤）。

推演记录（三色卡照片）应该与 feature 一起入库——它就是需求的推导过程。

**UI 与 API 双层断言钉死权限语义。** customer 看不到删除按钮（UI 层），
只能证明"入口藏了"；绕过 UI 直接 DELETE 返回 403（API 层）才是授权收口。

双层都绿才能说"权限成立"。

**步骤实现的成本几乎为零。** 页面对象（lab 02）、World 会话（lab 03）、
参数捕获（lab 04）都已就位，本实验的步骤实现只是把已有积木拼起来——
先写场景的成本优势在基建完备的仓库里会持续放大。

## Pitfalls & Q&A

**Q：Example Mapping 一定要开会吗？**
不一定——单人也可以在 issue 里用三色卡的格式自查（规则/例子/疑问三段）。
开会的价值是多方对齐；单人自查的价值是强制自己找反例。
本实验的推演记录就是单人版的演示。

**Q：为什么每个例子都同时断言 UI 和 API？**
UI 断言防"藏入口"（顾客看不到删除按钮），API 断言防"绕过"（直接调
DELETE 返回 403）。只测前者，攻击者或误用的集成方仍能破坏数据——
两层断言各守一道门。

**Q：例子表的值为什么不能带引号？**
lab 04 的结论在这里同样适用：Outline 代入是纯文本替换，
`{string}` 只匹配带引号文本，裸值配 `{}`。本实验的角色列
（admin/customer）是裸值，定义用 `以 {} 打开订单区`。

**Q：customer 用 API 删除时为什么返回 403 而不是 404？**
pw-store 的删除处理先做鉴权（角色检查）再做存在性检查——
customer 的 token 有效但角色不够，403 先于 404 返回。
这个顺序是刻意的安全设计：不向无权者泄露资源是否存在。

**Q：{int} 传入的状态码是字符串还是数字？**
本实验实测踩坑：`{} 匿名参数` 把表格值按**字符串**传入
（"200"/"403"），与 fetch 的数字 status 比较时必须
`toBe(Number(expectedStatus))`——这是 outline+匿名参数组合的固定搭配。
