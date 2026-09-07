# 06 · property-based 测试（Hypothesis）：让机器替你发明用例

> 手写用例是"编剧"——你只能想到自己想得到的输入。Hypothesis 是"轰炸机"：
> 你声明**性质**（无论输入是什么都该成立的规律），它随机生成成百上千组输入去炸，
> 炸出问题还会**自动收缩**成最小复现。本实验的真实战果：它当场挖出了
> 实验代码里两个作者自己都没料到的 bug（见 4.6）。

## 1. 为什么需要它

- 手写用例覆盖"想到的"，性质测试覆盖"没想到的"——边界、组合、序列。
- 不变量思维：与其枚举输入，不如声明"输出必须满足什么关系"。
- 挖到的失败会被收缩成最小样例 + 存进 `.hypothesis/` 数据库永久回归。

## 2. 总览：given → 生成 → 断言 → 收缩 → 数据库

<!-- 图: images/hypothesis.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/06_hypothesis/images/hypothesis.html)
> （或本地打开 [`images/hypothesis.html`](images/hypothesis.html)）。

一次 `@given` 用例的完整生命周期：策略生成输入 → 执行断言 → 失败则逐位简化输入
（shrink）→ 报告最小复现 → 存库下次必重放。

## 3. 快速开始

```bash
./hypothesis_lab.sh            # 全流程：埋雷失败 + 收缩输出 + 修复版双跑
./hypothesis_lab.sh observe    # 重点看 ① 的 Falsifying 输出
```

## 4. 核心概念

### 4.1 性质的三种经典形态

- **往返（roundtrip）**：`decode(encode(x)) == x`——编解码器的天条。
- **不变量**：排序后"有序 + 是置换 + 幂等"，三断言锁死一个 sort。
- **等价对拍**：新实现 vs 简单参照实现（本实验 buggy_mean vs fsum 版）。

### 4.2 策略（strategies）与偏向

`st.text() / st.integers() / st.lists(...)` 是基础；`st.one_of` 混抽可制造
"大数吞小数"这类需要特定组合才触发的精度 bug——**策略设计决定挖雷概率**。

### 4.3 收缩（shrink）

失败输入被逐位简化到极简：`[1e300, 1.0, -1e300]` 一眼看懂，而不是一屏乱数。
`Falsifying example` 段落就是收缩产物（脚本 observe ① 已抓取展示）。

### 4.4 @example：把意外收获钉成永久回归

随机发现是惊喜，`@example([1e300, 1.0, -1e300])` 是契约——无论策略怎么改，
这个输入每次必跑。修复后它自动变成回归锚点。

### 4.5 RuleBasedStateMachine：有状态轰炸

对队列类声明 `@rule`（push/pop）与 `@invariant`（长度与模型一致），
框架随机执行几百步规则并随时校验不变量——比手写操作序列便宜一个数量级。

### 4.6 实验撰写时的真实战果（诚实记录）

1. `decode(encode([]))` 返回 `['']` 而非 `[]`——空输入边界 bug，已修复。
2. `encode([''])` 与 `encode([])` 同为 `""`——格式天生无法区分空串元素，
   已把策略约束为非空字符串并作为格式限制写进 `props.py`。
   这两个 case 手写用例都很难想到，正是 property-based 的价值实证。

## 5. 关键字段

```python
@settings(max_examples=200, deadline=None)   # 次数与超时（CI 友好）
@given(st.lists(...), @example([...]))       # 随机生成 + 固定回归
suppress_health_check=[HealthCheck.too_slow] # 慢策略静默（谨慎使用）
```

坑清单：`deadline` 默认 200ms，I/O 或慢机器会误报 Flaky；`.hypothesis/` 数据库
要进版本库还是清理？——团队项目进库（共享回归），教学仓库 clean 掉。

## 6. 文件结构

```
06_hypothesis/
├── README.md
├── hypothesis_lab.sh          # 主演示脚本（埋雷演示是重头戏）
├── configs/pytest.ini
├── props.py                   # 被测对象：编解码器 + 排序 + 埋雷均值
├── tests/
│   ├── test_props.py          # 往返/不变量/@example/埋雷收缩
│   └── test_stateful.py       # RuleBasedStateMachine 队列轰炸
└── images/
```

## 7. 面试要点

- **Q: property-based 能替代手写用例吗？** 不能替代，是互补：手写锁"已知关键样本"，
  性质锁"全输入域规律"，@example 负责把战果固化。
- **Q: 什么叫收缩，为什么重要？** 失败样例最小化，把"调试两小时"压缩成"看一行"。
- **Q: 怎么测有状态组件？** RuleBasedStateMachine：规则=操作，不变量=随时断言，
  模型=简单参照实现（model-based testing 思想）。

## 8. 总结

机器已经开始替你发明用例。下一篇 [07_snapshot](../07_snapshot/README.md)：
把"大对象该长什么样"拍成快照，一行断言守住整个输出。
