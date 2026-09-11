# 07 · 快照测试（syrupy）：一行断言守住整个大对象

> 断言一个 30 个字段的 API 响应要写 30 行 assert？改一个字段就维护到崩溃。
> 快照测试换个问法："**输出和上次认可的版本一模一样吗？**"——一行断言守全场，
> 变更必须经人审 diff 后有意更新。本实验走完 破坏→红→更新→绿 的完整闭环。

## 1. 为什么需要它

- 大而稳定的输出（API JSON、渲染 HTML、编译产物）逐字段断言成本高、漏断言风险大。
- 快照是"回归基线"：默认**任何变化都红**，把"变更是否合法"强制变成人工决策。
- syrupy 是 pytest 生态的快照标准件：可读的 diff 报告 + 单文件存储。

## 2. 总览：输出、快照与审查流的关系

<!-- 图: images/snapshot.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/07_snapshot/images/snapshot.html)
> （或本地打开 [`images/snapshot.html`](images/snapshot.html)）。

测试输出与 `.ambr` 快照比对：不一致 → 红并展示双向 diff；
人审后确认合法 → `--snapshot-update` 换基线 → 绿。循环往复。

## 3. 快速开始

```bash
./snapshot_lab.sh            # 全流程：拍照 → 改坏变红 → 有意更新变绿 → 恢复基线
cat tests/__snapshots__/*.ambr   # 亲眼看快照长什么样（人审的对象）
```

## 4. 核心概念

### 4.1 首跑生成，此后比对

`--snapshot-update` 生成基线（observe 前的 apply 步骤）；之后每次运行都是
"现输出 vs 基线"的精确比对。**快照文件要提交进版本库**——它是基线本体。

### 4.2 破坏→红：diff 就是审查界面

`SNAP_BREAK=1` 模拟输出被改（金额 +1、td→th），快照测试立即红，
报告以 `+ received / - snapshot` 双列展示每个变化点——比人眼 diff HTML 靠谱。

### 4.3 更新是"有意行为"，不是条件反射

流程：看 diff → 判断"这变化合法吗"→ 合法才 `-u`。**禁止无脑 -u**：
那等于把所有回归都自动赦免，快照测试沦为摆设。脚本 ② 步演示了"确认后更新"。

### 4.4 快照适合什么、不适合什么

- 适合：结构稳定的大对象、整段 HTML/文本、序列化格式。
- 不适合：含时间戳/UUID/随机数——要么 mock 掉不稳定源（lab 04 的 freezegun），
  要么用 syrupy 的 matcher 钩子归一化。

### 4.5 易错点

- 快照炸弹：一条用例输出 500 行 diff 不可读——大对象先归一化/裁剪再拍。
- 参数化用例的快照按参数自动分名，改名参数=换快照，注意 diff 报告里的 orphan 提示。

## 5. 关键命令

```bash
pytest -q                          # 比对模式（日常）
pytest --snapshot-update -q        # 生成/更新基线（人审后）
pytest --snapshot-details -q       # 详细报告
```

## 6. 文件结构

```
07_snapshot/
├── README.md
├── snapshot_lab.sh             # 主演示脚本（破坏→红→更新→绿闭环）
├── configs/pytest.ini
├── renderer.py                 # 被测对象：API 载荷构造 + HTML 行渲染
├── tests/
│   ├── test_snapshot.py        # 两条快照用例（JSON + HTML 各一）
│   └── __snapshots__/test_snapshot.ambr   # 基线本体（应提交）
└── images/
```

## 7. 深入要点

- **Q: 快照测试和普通断言的边界？** 普通断言表达"业务规则"，快照表达"整体形态没意外漂移"。
- **Q: 怎么防止"无脑更新快照"泛滥？** CR 时盯 .ambr 文件的 diff；CI 里拆两步
  （先只读跑、更新必须单独提交）；更新说明写进 commit message。
- **Q: 输出里有时间戳怎么办？** 冻结时钟、注入 clock，或 syrupy 自定义 matcher
  在比对前归一化——不稳定源进不了快照。

## 8. 总结

大对象的回归从此一行断言。下一篇 [08_async](../08_async/README.md)：
异步代码与时间的确定性测试——重试用例怎么做到 <1s 跑完。
