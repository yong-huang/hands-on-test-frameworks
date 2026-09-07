# 05 · 覆盖率与质量门禁：让"没测到"变成会被拦截的事

> 用例全绿就安全了吗？不——绿只说明你写的用例过了，**没写的用例悄悄溜走了**。
> 覆盖率把"测了什么"变成数字，门禁把这个数字变成 CI 的生死线。
> 本实验亲手把分支覆盖率从 ~78% 补到 100%，并看门禁如何拦下不合格提交。

## 1. 为什么需要它

- 覆盖率回答"哪里没测"，不回答"测得好不好"——它是**发现盲区的探测器**，不是质量分。
- 分支覆盖率（branch）比行覆盖严格：`if` 只跑了真分支，行覆盖 100% 也会漏一半逻辑。
- `--cov-fail-under` 让覆盖率低于阈值时**退出码非 0**——CI 拦截的开关就在这。

## 2. 总览：从代码到门禁的数据流

<!-- 图: images/coverage.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/05_coverage/images/coverage.html)
> （或本地打开 [`images/coverage.html`](images/coverage.html)）。

coverage.py 在字节码层插桩 → 记录每行/每分支是否执行 → 汇总报告 →
门禁比较阈值决定退出码 → HTML/XML 报告供人审读。

## 3. 快速开始

```bash
./coverage_lab.sh              # 全流程：门禁失败演示 → 补漏通过 → HTML 报告
open reports/htmlcov/index.html   # 逐行着色查看（绿=测到，红=漏网）
```

## 4. 核心概念

### 4.1 行覆盖 vs 分支覆盖

实验数据：只跑基础用例集时，行覆盖已不低但**分支覆盖 78%**——`weekend`、
国际运费、未知券码这些分支全在裸奔。补漏用例每条注释了对准哪个分支。

### 4.2 门禁语义：测试全绿 ≠ 提交通过

observe ① 里 5 条用例全过，但覆盖率 78% < 90%，**退出码 1**——CI 照样拦截。
"测试通过"与"质量门禁"是两道独立的闸门。

### 4.3 排除规则：别为胶水代码凑数

`.coveragerc` 的 `exclude_lines` 把 `if TYPE_CHECKING:`、`raise NotImplementedError`
等模式排除在度量外——**门禁衡量业务逻辑，不逼你为类型桩写测试**。

### 4.4 易错点

- 追求 100% 覆盖会催生"为覆盖率而写"的空断言用例——阈值设在 85-95%，留一点呼吸感。
- `--cov` 与 `coverage run` 别混用，插桩两次数据会怪。
- 没开 `branch = True` 的覆盖率报告会给你虚假的安全感。

## 5. 配置关键字段

```ini
[run]
branch = True          # 分支覆盖率开关
source = discount      # 度量范围圈定被测模块，排除测试自身
[report]
exclude_lines = ...    # 排除模式：pragma: no cover 等
```

坑清单：`COVERAGE_RCFILE` 环境变量可指定非默认位置的配置（coverage CLI 不认 `-c`）；
报告落 `reports/` 目录取代默认 `htmlcov/`，与 .gitignore 配合。

## 6. 文件结构

```
05_coverage/
├── README.md
├── coverage_lab.sh              # 主演示脚本（①门禁失败 ②门禁通过 ③HTML 报告）
├── configs/
│   ├── pytest.ini
│   └── .coveragerc              # 分支开关 + 排除规则
├── discount.py                  # 被测对象：分支密集的折扣引擎
├── tests/
│   ├── test_discount.py         # 基础用例集（~78% 分支）
│   └── test_discount_extra.py   # 补漏用例（→100%，每条注明补哪个分支）
├── reports/                     # 运行后生成：htmlcov/ + coverage.xml
└── images/
```

## 7. 面试要点

- **Q: 覆盖率 100% 意味着什么？** 只意味着代码都被执行过一次，不保证断言有效、
  不保证组合覆盖。它是必要不充分条件。
- **Q: 门禁阈值怎么定？** 现状 +5% 起步，防止一次性大重写；每次只升不降（棘轮）。
- **Q: 分支覆盖为什么更严格？** 短路表达式 `a and b` 只测 a=True 路径时行覆盖已满，
  分支覆盖仍会揪出 b 从未求值。

## 8. 总结

单测四件套（fixture/参数化/mock/覆盖率）已集齐，阶段一毕业。下一篇进入阶段二：
[06_hypothesis](../06_hypothesis/README.md)——让机器替你发明用例的 property-based 测试。
