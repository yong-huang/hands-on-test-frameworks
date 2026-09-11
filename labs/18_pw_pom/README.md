# 18 · 页面对象模型（POM）：选择器收口，新用例只要 10 行

> 十条用例散落着 30 个 `get_by_placeholder`——UI 一改版，改测试比改产品还累。
> POM 的解法：每个页面一个类，**选择器只允许出现在 pages/ 里**，
> 用例只说业务语言。本篇把 16-17 的用例重构为 POM，并验证"新增用例只要 10 行"。

## 1. 为什么需要它

- 可维护性：UI 改版只改一个 page object，几十条用例自动跟上。
- 可读性：用例读起来像需求（"下单然后看见订单"），而不是 DOM 操作手册。
- 复用性：一个业务动作（下单）在十条用例里写十遍？封装一次到处调用。

## 2. 总览：POM 分层与依赖方向

<!-- 图: images/pw_pom.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/18_pw_pom/images/pw_pom.html)
> （或本地打开 [`images/pw_pom.html`](images/pw_pom.html)）。

test（业务断言）→ IndexPage/SlowPage（业务动作 + 收口的选择器）→ page fixture。
依赖永远向下；用例之间、页面之间不互相引用。

## 3. 快速开始

```bash
./pw_pom.sh        # 全绿 + 选择器泄漏检查 + 新用例行数统计
```

脚本 ② 步用 grep 做**纪律检查**：tests/ 里出现任何 `get_by_*` / `locator(`
即失败——POM 靠约定更靠检查。

## 4. 核心概念

### 4.1 Page Object 里放什么

- 选择器（构造器里集中声明）
- 业务动作（`place_order(customer, item, price)`——不是 `fill_三次_再click`）
- 业务断言（`expect_order_visible(customer)`）

不放：业务断言之外的等待参数魔法数、跨页面流程（那是 test 的职责）。

### 4.2 fixture 注入页面对象

`conftest.py` 提供 `index_page(page)` / `slow_page(page)`——用例签名里声明即可。
页面构造只发生在 fixture 里，用例与 Page 的构造解耦。

### 4.3 重构不改断言（等价性验证）

16/17 的用例语义（下单可见、删除消失、竞态完成）在 18 里逐条对应，
用例数量不变——**重构测试的纪律与重构产品一致：行为不变，结构变好**。

### 4.4 新用例成本实测

`tests/test_new_feature.py` 全文 12 行（含空行注释）即新增一条完整用例——
脚本 ③ 步用 `wc -l` 证明。这就是 POM 的回报曲线：前期封装成本，后期线性扩用例。

### 4.5 易错点（本实验真实踩过）

- "连续下两单"的新用例踩中前端刷新竞态：A 单的列表刷新异步覆盖了 B 单的渲染。
  对策是**用例按真实用户节奏走**（等 A 上屏再下 B）——POM 让你更容易写出
  贴近用户的用例，但不豁免等待哲学（lab 17）。

## 5. 关键结构

```python
class IndexPage:
    def __init__(self, page): self.customer = page.get_by_placeholder("客户名")  # 收口
    def place_order(self, customer): ...        # 业务动作
    def expect_order_visible(self, customer): expect(...).to_be_visible()
```

## 6. 文件结构

```
18_pw_pom/
├── README.md
├── pw_pom.sh                 # 全绿 + 泄漏检查 + 行数统计
├── configs/pytest.ini
├── pages/
│   ├── index_page.py         # 首页页面对象（选择器唯一居所）
│   └── slow_page.py          # 慢加载页页面对象
├── tests/
│   ├── conftest.py           # index_page / slow_page fixture
│   ├── test_orders_pom.py    # 重构后的三条等价用例
│   └── test_new_feature.py   # 12 行的新增用例演示
└── images/
```

## 7. 深入要点

- **Q: POM 的边界怎么划？** 页面对象管"单页面的动作与断言"，跨页面用户旅程
  留在 test 层编排——避免 page object 变成上帝类。
- **Q: POM 和 fixture 怎么配合？** fixture 负责"给哪个页面对象"，test 负责
  "用它做什么"；构造参数（如环境 URL）也由 fixture 统一注入。
- **Q: 什么时候 POM 是过度设计？** 一次性验证脚本、纯 API 层测试不需要；
  三条以上用例共享同一页面时就值得封装。

## 8. 总结

测试代码库正式"工程化"。下一篇 [19_pw_network](../19_pw_network/README.md)：
网络拦截与登录态复用——前端测试的"不依赖后端"自由。
