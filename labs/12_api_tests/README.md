# 12 · API 测试套件：httpx + pytest 给 SUT 来 30 条真 HTTP 用例

> 单测没法告诉你"HTTP 层接起来对不对"。API 测试在**真端口**上对 SUT 发真请求：
> 状态码、响应头、schema、负向分支一次测全。本篇产出 30 条互相独立的用例——
> 乱序跑、并行跑都绿，因为数据"自造自清"。

## 1. 为什么需要它

- 单测 mock 掉了网络，API 测试把网络请回来：路由、序列化、校验、状态码——
  一条 422 背后是 pydantic、FastAPI、store 三层的合奏。
- session 级 client fixture 复用连接池；order_factory 让"造数-清理"自动化。

## 2. 总览：一条 API 用例的完整生命周期

<!-- 图: images/api_tests.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/12_api_tests/images/api_tests.html)
> （或本地打开 [`images/api_tests.html`](images/api_tests.html)）。

fixture 造数（带唯一标记）→ 发请求 → 断言（状态码/头/模型）→ teardown 删除。
任何一步崩了，teardown 都会跑——测试库不留尸体。

## 3. 快速开始

```bash
./api_tests.sh            # 起独立 SUT（8901 端口+独立空库）→ 全量 → 乱序 → 并行 → 清理
./api_tests.sh observe
```

注意"独立实例"设计：lab 12 用 8901 端口和独立测试库，**不污染** lab 11 的演示数据。

## 4. 核心概念

### 4.1 session 级 client + function 级工厂

`httpx.Client(base_url=...)` 整个会话复用 TCP；`order_factory` 每条用例现造现删
（teardown 里循环 delete）。**用例只经工厂造数**——没人依赖别人的数据，天然可乱序。

### 4.2 响应 schema 校验（pydantic）

`OrderOut.model_validate(response_json)` 一行锁死字段名与类型。契约漂移
（改字段名/类型）当场被抓——这是 lab 15 Pact 的轻量前置体验。

### 4.3 负向用例是半壁江山

30 条里 7 条负向：缺字段 422、负数量 422、非法状态 400、不存在 404（并校验
detail 里带 id）、user 角色打 admin 接口 403。**API 的健壮性藏在 4xx 里**。

### 4.4 测试数据生命周期：自造自清

对比两种反模式：共享"魔法数据"（谁先跑谁写死 ID）与拍屁股走人（垃圾数据堆积）。
工厂 + teardown 注册让清理与用例成败解耦。实测：`-k` 圈一半/另一半、`-n 4`
并行，全绿（脚本 ③④ 步）。

### 4.5 易错点

- conftest.py 放错层级 fixture 不生效（本实验踩过：放根目录遇 `-c configs/` 找不到，
  放 tests/ 稳）。
- 断言 `X-Total-Count` 时注意 httpx 把响应头小写化：`r.headers["x-total-count"]`。
- 依赖"最后一个订单是我造的"必然翻车——总数断言用 `>=` 或限定自己的窗口。

## 5. 关键字段

```python
httpx.Client(base_url=..., timeout=10)      # session 级复用
r.headers["location"]                        # 201 创建后能按图索骥
int(r.headers["x-total-count"])              # 分页总数
OrderOut.model_validate(r.json())            # schema 锁
```

## 6. 文件结构

```
12_api_tests/
├── README.md
├── api_tests.sh                # 独立 SUT 生命周期 + 四组观察
├── configs/pytest.ini
└── tests/
    ├── conftest.py             # client + order_factory（自造自清）
    └── test_api.py             # 30 条：CRUD/分页/负向/登录/慢接口
└── images/
```

## 7. 深入要点

- **Q: API 测试和 E2E 的边界？** API 测试只管接口契约（无 UI）；E2E 管
  用户路径（有浏览器）。同一 SUT，两层互补。
- **Q: 怎么保证用例可乱序？** 不依赖执行顺序、不依赖他例数据、清理挂 teardown。
  判定法：`-k` 随机圈子集都应全绿。
- **Q: 测试环境的数据从哪来？** 自造最优（不依赖种子漂移）；造不了的用
  fixture 预置；绝不共享可变数据。

## 8. 总结

HTTP 契约已被 30 条用例焊死。下一篇 [13_db_tests](../13_db_tests/README.md)：
绕过 HTTP，直接对数据层做集成测试——两种隔离策略正面对决。
