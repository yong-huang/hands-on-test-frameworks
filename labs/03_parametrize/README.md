# 03 · 参数化与异常断言：一条用例打一片，异常也是契约

> 复制粘贴十条只差输入的用例？参数化让"一个函数 × 一张数据表"生成整个用例矩阵，
> `ids` 让每条用例在报告里有名字。另一半功课：`pytest.raises` 把异常行为也锁进契约——
> 类型和消息都要对。读完本篇你能把重复用例压成数据表，并精确断言异常。

## Background

一个解析函数的正常、边界、异常三类输入是它的三张面孔。没有参数化时，覆盖它们的做法是
复制粘贴：`test_parse_int_valid`、`test_parse_int_negative`、`test_parse_int_bool`……
十条用例九成代码相同，只有字面量不同。

复制粘贴的代价在失败时爆发：某个输入改了行为，只有被复制到的那几条用例能抓到；
漏复制的那类输入从此没人管。反过来，报告里 `param0`、`param1` 这样的自动命名
让人挂了都不知道是哪个输入——测试数量上去了，可诊断性却崩了。

pytest 的参数化（parametrize）把"同一段逻辑 × 一张数据表"变成框架原语：
一个测试函数配一个装饰器，收集期就展开成多条独立用例。异常行为同理——
"这个输入应该抛什么错"也是契约，`pytest.raises` 把它锁进断言。

## What

参数化是 pytest 的用例生成机制：在测试函数上叠加 `@pytest.mark.parametrize` 装饰器，
pytest 在收集期把"函数 × 参数组合"展开成多条独立用例，每条独立执行、独立失败。

可以把参数化想成把一张 Excel 数据表直接钉在测试函数上：表有几行，就用例有几条。
但和复制粘贴不同的是，逻辑只存在一份——表里加一行就是加一条用例，改行为只需改一处。

两个配套机制：`ids` 给每一行起可读名字；`indirect` 让某些参数先进 fixture
（pytest 的资源注入机制，见 lab 02）加工后再进用例。

## When to Use

典型场景：

- 纯函数的输入矩阵：解析器、换算、校验规则——每个合法/非法输入一行数据。
- 回归保护网：线上出过的每个 bug，把触发输入加进数据表，一条用例永久看住它。
- 异常契约：错误类型 + 错误消息一起断言，防止"碰巧抛对"。

何时不用：各输入的准备流程差异很大时（不只是数据不同，而是要连不同的服务、
做不同的前置），写多条函数更清楚；参数化是"同逻辑不同数据"，
fixture 解决的才是"同数据不同逻辑"。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 复制粘贴多个测试函数 | 逻辑重复，改行为要改多处 | 几乎不用 |
| 参数化 | 一函数一表，收集期展开 | 输入矩阵类测试 |
| 循环里多次 assert | 一条用例，首个失败即停 | 不推荐——后面的输入测不到 |

## Quick Start

前置条件：labs/00 体检通过。被测对象是 `config_parser.py`——一个 INI 风格
（`key = value` 行式格式）的解析器，带 5 类错误分支。

```bash
cd labs/03_parametrize
./parametrize.sh            # 全流程
./parametrize.sh apply      # 看收集：11 个函数 → 24 条用例
./parametrize.sh observe    # 看报告里的 ids 命名与圈选
```

收集期的真实输出（2026-09-28 实测）：

```
========================= 24 tests collected in 0.05s ==========================
```

ids 命名让 `-k` 能精确圈选一组异常用例（observe ①，节选）：

```
collected 24 items / 20 deselected / 4 selected

tests/test_parametrize.py ....                                           [100%]

======================= 4 passed, 20 deselected in 0.06s =======================
```

报告行名是可读名而不是 `param0`（observe ②，节选）：

```
tests/test_parametrize.py::test_parse_value[int] PASSED                  [ 12%]
tests/test_parametrize.py::test_parse_value[negative-int] PASSED         [ 25%]
tests/test_parametrize.py::test_parse_value[bool-lower] PASSED           [ 37%]
tests/test_parametrize.py::test_parse_value[bool-upper] PASSED           [ 50%]
```

诚实预期：全量 24 条应全绿。11 个测试函数展开成 24 条用例的构成：
一个 6 条的笛卡尔积（3×2）、两组枚举（9 条 + 5 条）、2 条 indirect 用例。

parametrize 装饰器的关键字段（这段在做什么：把"参数名 × 值列表 × 可读名"钉到一个函数上）：

```python
@pytest.mark.parametrize(
    "bad_text,match",            # 多参数用逗号串
    [("just_a_line", "缺少 '='"), ...],
    ids=["no-equals", ...],      # 与 argvalues 一一对应
    indirect=["loaded"],         # 指定哪些参数走 fixture
)
```

## How It Works

**收集期展开**：pytest 收集到带 parametrize 的函数时，对装饰器做笛卡尔积（两组参数的全组合）——同一函数叠两个 `@pytest.mark.parametrize`，就是两组值的逐个配对。

本实验 `prefix(3) × body(2) = 6` 条由此而来。展开发生在收集期，所以 `--collect-only` 里看到的就是最终的用例数。


**异常断言的双重锁**：

```python
with pytest.raises(ConfigError, match="重复键"):
    parse_config("a = 1\na = 2\n")
```

为什么这样写：只写 `raises(ConfigError)` 不断言消息，任何重复键错误都算过——
错误提示可能在重构中被改得面目全非，测试却仍然全绿。`match` 是**正则**不是子串，
它把消息文本也锁进契约。

**indirect 管道**：`indirect=["loaded"]` 让 `loaded` 这一列的值不再直接进用例，
而是先作为参数送进同名 fixture，由 fixture 解析成配置对象后再注入。
适合"参数需要加工"的场景；同一装饰器里其余参数照常直传——一条数据表可以
混合"直传列"和"加工列"。

**个别行打标**：`pytest.param(..., marks=pytest.mark.xfail)` 可以给矩阵中单独一行
打标记（如预期失败），不用为一条特例拆出独立函数。

## Pitfalls & Q&A

踩坑清单：

- **ids 没写，报告全是 param0/param1**。现象：失败报告看不出是哪个输入挂了。
  解法：`ids` 与值列表一一对应地起名；它同时是 `-k` 圈选的锚点。
- **参数值里放可变对象，多条用例共享同一实例**。现象：单独跑绿、合跑挂。
  解法：数据表里放工厂函数（lab 02），每条用例领自己的实例。
- **断言裹进 raises 块被吞掉**。现象：断言从未执行但测试通过。原因：`raises` 块内
  所有代码都在"期待异常"上下文里。解法：块内只放会抛异常的一行；需要断言异常细节时，
  先 `with pytest.raises(...) as excinfo:`，出块后再断言 `excinfo.value`。
- **`match` 当子串用**。它是正则——消息里的 `(`、`[` 等元字符要转义。

深入问答：

- **Q：参数化和 fixture 各自适合什么场景？** 参数化是"同逻辑不同数据"，
  fixture 是"同数据不同逻辑"；需要两者组合时用 `indirect` 桥接。
- **Q：ids 为什么值得花心思？** 报告定位、`-k` 圈选、与非技术同事沟通用例覆盖，
  全都依赖可读名——200 条参数化用例里，`param137` 等于没有名字。
