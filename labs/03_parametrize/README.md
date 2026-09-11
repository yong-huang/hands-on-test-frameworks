# 03 · 参数化与异常断言：一条用例打一片，异常也是契约

> 复制粘贴十条只差输入的用例？参数化让"一个函数 × 一张数据表"生成整个用例矩阵，
> 而且 ids 让每条用例在报告里有名字。另一半功课：`pytest.raises` 把异常行为
> 也锁进契约——类型和消息都要对。

## 1. 为什么需要它

- 正常/边界/异常三类输入是每个函数的三张面孔；参数化把它们压进一张表。
- 测试报告可读性是被低估的资产：ids 命名让你在 200 条参数化用例里一眼认出谁挂了。
- indirect 参数化打通 fixture 与数据表——预处理管道的官方通道。

## 2. 总览：一个测试函数如何展开成 24 条用例

<!-- 图: images/parametrize.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/03_parametrize/images/parametrize.html)
> （或本地打开 [`images/parametrize.html`](images/parametrize.html)）。

收集期，pytest 对每个参数化装饰器做**笛卡尔积**：本实验 11 个测试函数展开成
24 条用例（6=2×3 的积、9+5 的枚举、indirect 2 条）。运行期每条独立执行、独立失败。

## 3. 快速开始

```bash
./parametrize.sh            # 全流程
./parametrize.sh apply      # 看收集：11 个函数 → 24 条用例
```

## 4. 核心概念

### 4.1 parametrize 三要素

`argnames`（参数名）、`argvalues`（值列表）、`ids`（每行的可读名）。
验证：跑 observe ① 后看报告行名是 `int / negative-int / bool-lower…` 而非 `param0`。

### 4.2 笛卡尔积

同一函数叠两个 `@pytest.mark.parametrize` = 全组合。实验里
`prefix(3) × body(2) = 6` 条——比手写 6 个函数诚实得多。

### 4.3 异常断言：类型 + 消息双重锁

```python
with pytest.raises(ConfigError, match="重复键"):
    parse_config("a = 1\na = 2\n")
```

`match` 是**正则**不是子串；只断言类型不断言消息，错误提示会退化成"碰巧抛对"。

### 4.4 indirect：参数先进 fixture 再进用例

`indirect=["loaded"]` 让 `loaded` 的值走 fixture 管道（先解析成配置对象）。
适合"参数需要加工"的场景；其他参数照常直传。

### 4.5 易错点

- ids 没写，报告就是 param0/param1——挂了都不知道是哪个输入。
- 参数值里放对象实例时，多个用例可能共享同一实例；需要隔离就放工厂函数（lab 02）。
- 异常断言范围要最小化：`raises` 块里只放会抛异常的一行，别把断言也裹进去。

## 5. 关键字段

```python
@pytest.mark.parametrize(
    "bad_text,match",            # 多参数用逗号串
    [("just_a_line", "缺少 '='"), ...],
    ids=["no-equals", ...],      # 与 argvalues 一一对应
    indirect=["loaded"],         # 指定哪些参数走 fixture
)
```

坑清单：`pytest.param(..., marks=pytest.mark.xfail)` 可以给矩阵中个别行打标，
不用为一条特例拆函数。

## 6. 文件结构

```
03_parametrize/
├── README.md
├── parametrize.sh              # 主演示脚本
├── configs/pytest.ini
├── config_parser.py            # 被测对象：INI 风格解析器（含 5 类错误分支）
├── tests/test_parametrize.py   # 11 函数 → 24 条用例
└── images/
```

## 7. 深入要点

- **Q: 参数化和 fixture 各自适合什么场景？** 参数化是"同逻辑不同数据"；
  fixture 是"同数据不同逻辑"。需要两者时用 indirect 桥接。
- **Q: ids 为什么重要？** 报告定位、-k 圈选、与 PM 沟通用例覆盖，全都靠可读名。
- **Q: pytest.raises 会吞掉断言吗？** 会——raises 块内所有代码都在"期待异常"上下文，
  断言放进去等于从未执行。先 `raises` 拿到 excinfo，出块后再断言细节。

## 8. 总结

你会用一张数据表打一片输入，也会把异常锁进契约。下一篇
[04_mock](../04_mock/README.md)：把"外部世界"请出测试——mock 与替身。
