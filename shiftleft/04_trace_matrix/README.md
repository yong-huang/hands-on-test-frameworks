# 04 · 需求↔测试追溯矩阵：让「哪些需求没人测」机械可查

> 「这条需求谁在测」在多数团队靠人翻目录回答。本实验给 labs/11 订单应用
> （本仓库 labs 主线搭好的 FastAPI 被测系统，即 SUT）建双向追溯矩阵：
> pytest 收集的 12 个测试 = 11 个已映射 + 1 个孤儿，需求覆盖
> 8/8，两个计数等式机械核对；哪条需求的覆盖被删光立即退出码 1——可直接当 CI 卡点。

## Background

之前的做法：需求表在产品经理的文档里，测试在仓库里，两边靠记忆对齐。问
「订单取消有没有测试覆盖」，答案是「应该有吧」；删一条测试前没人问「它原来
挡哪条需求」。

痛点的核心是**两个方向的缺口都不可见**：漏测的需求（没人挡的需求）和孤儿
测试（没人要的测试）同时存在，且只有出事故时才被翻出来。

本实验做需求↔测试双向追溯（RTM，requirements traceability matrix）的自动化：
pytest 收集真实测试节点，外挂映射声明「测试→需求」，三方对账产出矩阵——
缺口与孤儿都变成显式条目，而不是事故后的回忆。

## What

追溯矩阵是一张「每条需求由哪些测试覆盖、每个测试为哪条需求存在」的双向
账本，附两个计数等式的机械核对：收集数 = pytest 报告数 = 已映射 + 孤儿。

可以把矩阵想成考场座位表：每个考生（测试）必须有准考证号（需求），每个
座位号（需求）必须有考生，空座位与无号考生一眼可见。但和座位表不同的是，
它只管「有人坐」不管「答得对不对」——覆盖≠通过，矩阵不替代测试执行。

映射采用**外挂文件**（测试名子串 → 需求 ID）而不是 `@pytest.mark` 内联标注：
labs/11 是共有资产，本实验一个字不改它的测试文件。

![需求、映射、pytest 收集三方对账出双向矩阵](images/trace_matrix.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/04_trace_matrix/images/trace_matrix.html)
> （或本地打开 [`images/trace_matrix.html`](images/trace_matrix.html)）。
> 三方数据在引擎处汇合；孤儿（没人要的测试）、缺口（没人测的需求）、陈旧映射
> （映射指向已改名/已删除的测试）三种异常各自有独立出口。

## When to Use

- 需求评审：新需求进迭代前看矩阵缺口，「谁来测」当场定，而不是上线后补。
- 删改测试前：查上游需求是否还有别的覆盖，防「删测试断需求」。
- CI 卡点：未覆盖需求即退出码 1，放 PR 流水线挡「删测试不删需求」的提交。

何时不用：需求与测试一一对应且团队已强制 `mark` 标注时收益有限；需求粒度
太粗（一条 REQ 挂十几条测试）时先拆需求再谈追溯。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| `@pytest.mark.req` 内联 | 标记跟测试走，但要改共有资产 | 自有测试仓库 |
| 外挂映射（本实验） | 零侵入 + 映射可独立 diff 评审 | 治理存量/共有资产 |
| 手工 RTM 表格 | 零工具成本，必然腐烂 | 一次性审计 |

## Quick Start

前置：仓库根 `.venv`（pyyaml/pytest/httpx/fastapi）；labs/11 全程只读（collect-only），本实验自己的套件用临时数据库。一条命令：

```bash
./trace_matrix.sh   # apply → observe（自证+矩阵+缺口门禁）→ clean
```

第一步自证覆盖套件是真的（8 条需求配的回归测试全绿，输出为 pytest 汇总行）：

```text
10 passed, 2 warnings in 0.58s
```

第二步全量矩阵（表格节选，完整 8 行的 trace_matrix.md 在 clean 前的 reports/；
想留档就跑 `./trace_matrix.sh observe`，all 模式结尾会清掉它）：

```text
收集 12 个测试（pytest 报告 12）= 已映射 11 + 孤儿 1  ✓ 机械一致

REQ      需求                                      覆盖 测试节点
REQ-001  健康检查端点可用（GET /api/health 返回 20… 1    shiftleft/04_trace_matrix/tests/…::test_health_ok
REQ-002  可创建订单（POST /api/orders 返回 201 与… 2    labs/11_sut_app/tests/…::test_create_and_delete_roundtrip 等 2 条
……（REQ-003 ~ REQ-008 同构）

需求覆盖 8/8；孤儿测试 1；陈旧映射 0
  ⚠️ 孤儿 labs/11_sut_app/tests/test_sut_smoke.py::test_health（未挂任何需求映射）
门禁判定：需求全覆盖，放行（exit 0）
```

第三步缺口门禁：换上删掉 REQ-003 唯一覆盖的映射文件（预期失败演示）。
输出节选（只摘 REQ-003 相关行；此时已映射 10 + 孤儿 2、覆盖 7/8，机械一致仍成立）：

```bash
../../.venv/bin/python trace_matrix.py --mapping configs/test_mapping_gap.yaml
```

```text
REQ-003  订单列表支持分页与总数（GET /api/orders … 0 ⛔  ——
  ⛔ 未覆盖需求 REQ-003：订单列表支持分页与总数（GET /api/orders 返回 items/total/limit/offset）
门禁判定：1 条需求漏测，打回（exit 1）
```

诚实预期：映射键是子串匹配——键用完整测试函数名（太短会误命中别的节点）；
改了测试名必须同步改映射，否则进「陈旧映射」告警而不是静默漏报。

## How It Works

**三方对账是唯一事实源**：pytest `--collect-only` 给出真实存在的节点（一条
不多），需求清单给出「要什么」，映射给出「谁挡」。引擎按子串匹配把三方缝成
双向矩阵——参数化测试天然逐实例计数（REQ-005 的 3 个覆盖就是 3 个参数实例）。

**机械一致是两个等式同时成立**：引擎数出的节点数 == pytest 报告的 collected 数 ==
已映射 + 孤儿。任一等式破掉矩阵直接标 ✗，不给「看起来对」的账本留余地。

**共有资产只读靠两个机关**：labs/11 的测试只被 collect 不被执行；本实验
套件用 TestClient 内进程打应用，但 `SUT_DB` 环境变量在 import 前就改写
（conftest.py 是 pytest 约定自动加载的目录级配置）。

改写的时机是生死线：应用在 import 时就冻结数据库路径（conftest.py 里先设
`os.environ` 再 import main），晚设一步测试数据就会写进 labs/11 的 orders.db。
核心匹配循环：

```python
for key, rids in mapping.items():
    hits = [n for n in nodes if key in n]   # 子串匹配，一个键可挂多条需求
    if not hits:
        stale.append(key)                   # 键匹配不到任何节点 → 陈旧映射
    for n in hits:
        for r in rids:
            if r not in node_reqs.setdefault(n, []):
                node_reqs[n].append(r)
```

**三种异常三个出口**：孤儿与陈旧映射是 ⚠️ 告警不挡道，未覆盖需求是 ⛔ 门禁
退出码 1——轻重分明，告警才不会被门禁淹没。

## Pitfalls & Q&A

常见故障与解法：

- **`no such table: orders`**：裸 `TestClient(app)` 不触发 lifespan（启动钩子，
  建表就挂在里面）——必须 `with TestClient(app) as c:` 进上下文。
- **参数化测试签名漏 fixture（client 这类 pytest 注入的夹具参数）**：批量加参数时带参的
  `def test_x(status)` 会被正则漏掉——`AttributeError: no attribute 'post'` 即此症。
- **映射键太短**：`test_health` 会同时命中本实验与 labs/11 两处的健康测试；键用完整函数名，陈旧映射告警会帮你发现改名。

Q&A：

- **为什么外挂映射而不是 mark 标注？** 零侵入是表因；主因是映射可被单独 diff
  评审——需求变更时看一个文件的改动就知道覆盖计划怎么变。
- **覆盖 8/8 还有 1 个孤儿，要处理吗？** 孤儿是治理线索不是故障：要么挂上 REQ-001，要么删除——不可见才是问题。
- **矩阵说覆盖了，测试红着呢？** 矩阵管「存在性」，执行管「正确性」；演示动线
  里先跑 `pytest tests/`（全绿）再看矩阵，顺序本身就是答案。
