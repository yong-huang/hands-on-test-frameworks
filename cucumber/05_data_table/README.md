# 05 · DataTable：When 携输入表，Then 携期望表

> 一个步骤一行数据是 Outline 的形态；一个步骤**一张表**的数据是 DataTable 的形态。
> 本实验用两种消费形态（rows 数组、hashes 对象）驱动批量建单，并确立双表分工：
> When 表携输入、Then 表携期望——顺带踩一个"无表的 Then"的经典坑。

## Background

批量场景的 Gherkin 有两种写法：5 个"并且 创建…"步骤（重复爆炸），或一个步骤
挂一张表格。DataTable 让步骤声明接收一张结构化表，步骤内按行消费——
数据规模变化只改表行数，不碰代码。

表格的进阶用法是**双表分工**：When 携"输入表"（要创建什么），Then 携"期望表"
（应该看到什么）。两表都由业务可读的字段名作表头，整个场景读起来就是
"给这些输入 → 应有这些输出"的规约。

## What

DataTable 是 cucumber 传给步骤的表格对象，两种消费形态：`rows()` 返回
字符串二维数组（按列位置取值），`hashes()` 返回以首行为键的对象数组
（按字段名取值）。字段可能增删的表用 hashes，列位置固定的简单表用 rows。

可以把两种形态想成通讯录的两种录入法：rows 是"第 1 列姓名、第 2 列电话"
的按位置念法，hashes 是"姓名：张三、电话：138…"的按标签念法。
标签念法啰嗦但谁念都不出错；位置念法快，但插一列全乱。

![DataTable 双表分工与两种消费形态](images/table.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/cucumber/05_data_table/images/table.html)
> （或本地打开 [`images/table.html`](images/table.html)）。
> 上排是 When 表驱动的批量创建，下排是 Then 表驱动的逐字段核对。

## When to Use

| 形态 | 适用 | 本实验靶点 |
|:---|:---|:---|
| `rows()` | 列少且位置稳定（单列表格） | 批量建单 5 行 |
| `hashes()` | 字段多、可能增删（标题+状态） | 期望表逐字段核对 |
| `rowsHash()` | 单记录键值对（配置类） | 未演示，机制同源 |

判断口径：**表头是业务字段的用 hashes**——列可以重排、可以增删，
步骤代码不用动。位置语义的表（第 1 列就是标题本身）用 rows 更简洁。

## Quick Start

```bash
cd cucumber/05_data_table
./data_table.sh          # apply 起靶场 → observe 双表场景 → clean
```

observe ① 两个表格场景全绿：

```
2 hooks (2 passed)
2 scenarios (2 passed)
10 steps (10 passed)
```

场景 1 用 `rows()` 逐行创建 5 笔订单并全部断言可见；场景 2 的 When 表
创建 2 笔、Then 表声明期望（标题 + 预期状态"已创建"），逐字段核对。

验收方式：双场景全绿。变异实验：把 Then 期望表里一行改成
`| 对象核对-支架 | 已发货 |`（实际状态是已创建）——断言即红，
证明"逐字段核对"核对的是**值**而不只是行存在。

## How It Works

**hashes() 把表头变成对象的键。** 表格

```gherkin
      | 商品标题       | 状态   |
      | 对象核对-键盘   | 已创建   |
```

经 `table.hashes()` 变成 `[{ 商品标题: '对象核对-键盘', 状态: '已创建' }]`。

步骤里 `row['商品标题']`、`row['状态']` 语义自解释——增删列只改表和消费处，
行序与列序都不再敏感。`rows()` 则保留原始二维数组，适合"列就是数据"的场景。

**Then 表是期望的载体。** "When 表是输入、Then 表是期望"是表格场景的
标准分工：输入表驱动被测系统，期望表声明可观察结果。

两表字段同名时（本实验的商品标题），核对逻辑就是逐行匹配——
读者一眼看出每个输入对应的期望。

**动作边界等待 POST。** 与 lab 02 相同，`create()` 在点击后等待
POST /api/orders 响应才返回——批量创建 5 笔时，每笔都确定性落库后
再创建下一笔，断言阶段不再有竞态。

## Pitfalls & Q&A

**Q：Then 步骤没带表时报"callback and promise"是什么错？**
本实验实测踩过：Then 步骤签名写了 `table: DataTable`，但 feature 里
该步骤**没有挂表**——cucumber 只传进来回调函数，`table.hashes()` 调用的
其实是回调。

报 "function uses multiple asynchronous interfaces" 是
"签名与实际参数不匹配"的名片：签名里的 DataTable 位置收到了别的东西。

**Q：rows() 和 hashes() 能混用吗？**
同一张表在同一个步骤里可以两种方式各读一遍（它们都是纯函数视图），
但一个步骤通常只需要一种。

混用的常见场景：rows() 先校验表形状（行数、列数），
hashes() 再做业务消费——形状不对时报更友好的错误。

**Q：表格里的空单元格会变成什么？**
hashes() 里空单元格的值是 `''`（空字符串）而非 undefined/null。

断言"必填字段非空"时用 `expect(v).not.toBe('')`，别写 `toBeFalsy()`——
空串恰好是 falsy，会误伤合法的 `'0'` 吗？不会，'0' 是 truthy；
但 `toBeFalsy` 的语义模糊性不值得引入。

**Q：批量创建后每行断言 count=1，为什么不用 toHaveCount(5)？**
列表里可能还有种子数据或其他场景的残留——按标题精确断言每一笔
（唯一标题 + count=1）才是隔离纪律（lab 10 的协议）的落点。
总数断言会把这些历史一起算进去，脆弱且无定位能力。
