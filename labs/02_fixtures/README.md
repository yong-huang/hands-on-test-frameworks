# 02 · fixture 与 conftest：用例的准备与清理，测试的依赖注入

> 十条用例都要同一个数据库连接：每条用例里连十遍？还是用全局变量传着用？
> pytest 的答案是 fixture——声明式地"需要什么"，而不是命令式地"怎么造"。
> 读完本篇你能用作用域控制资源生命周期、用 yield 写清理、用 conftest.py 跨文件共享、
> 用工厂 fixture 批量造数据。

## Background

没有 fixture 时的两个极端：要么每条用例自己在 `setUp` 里准备资源——数据库连接这种昂贵
资源被重复创建十遍，套件变慢；要么用全局变量共享——一条用例改了表数据，下一条用例莫名
失败，用例之间从此不敢乱序执行。

痛点在于测试代码的大头本来就是准备与清理（行数占比常到八成），这部分写得越糟，
测试套件越慢、越脆。重复准备拖慢速度，全局共享让失败传染——两者还会互相催生：
为了绕开脏状态，团队开始给用例规定执行顺序，顺序依赖又让并行化无从谈起。

pytest 的 fixture 把"需要什么"与"怎么造"解耦：用例在参数表里声明名字，
pytest 负责按约定创建资源、在合适的时机清理。本实验用"昂贵连接 + 干净表 + 数据工厂"
三件套把这套机制讲透。

## What

fixture 是 pytest 的资源提供机制：一个带 `@pytest.fixture` 装饰器的函数，
用例把它的函数名写进参数表，pytest 就在用例运行前执行它、把返回值注入用例，
并在约定时机执行清理。

可以把 fixture 想象成酒店房务：住客（用例）只声明"要一间干净的房"，退房后的打扫（teardown，清理步骤）由酒店负责。

但和酒店不同的是，fixture 的服务粒度由作用域（scope）精确控制——整场会议（session 作用域）只建一次的资源，和每位住客（function 作用域）都要换新的资源，可以并存。


fixture 之间也能互相依赖：一个 fixture 的参数表里写另一个 fixture 的名字，
pytest 会自动先造好后者——用例由此只关心"断言什么"，形成**测试的依赖注入**
（依赖由框架按声明自动装配，用例不去主动获取）。

## When to Use

典型场景：

- 多个用例共享昂贵资源（数据库连接、启动服务）：session 级 fixture，建一次用到底。
- 每条用例需要干净状态（清空表、临时目录）：function 级 fixture，逐条清理。
- 批量造测试数据：工厂 fixture 返回造数据的函数，一条用例造 3 个还是 10 个用户自己定。

何时不用：只有一条用例用一个资源时，直接在用例里写更直白；fixture 层层依赖深到
读不懂时，是抽象过度的信号，该收敛了。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| unittest setUp/tearDown | 固定 function 级、必须写成类 | 已有 unittest 代码库 |
| pytest fixture | 多作用域、无需类、conftest 共享 | pytest 项目的默认做法 |
| 用例内手写 try/finally | 每条重复、容易漏清理 | 只有一条用例时 |

## Quick Start

前置条件：labs/00 体检通过；本实验无外部服务，`FakeDB` 是内存假数据库
（带实例计数器，用来证明"建了几次"）。

```bash
cd labs/02_fixtures
./fixtures.sh            # 全流程
./fixtures.sh observe    # 重点看 ② --setup-show 的 SETUP/TEARDOWN 幕后
```

全量运行的真实输出（2026-09-28 实测，节选）：

```
collected 12 items

tests/test_fixtures.py ............                                      [100%]

============================== 12 passed in 0.27s ==============================
```

`--setup-show` 打开某条用例的 setup/teardown 幕后（同一次 observe，节选）：

```
SETUP    S db
        SETUP    F clean_db (fixtures used: db)
        TEARDOWN F clean_db
TEARDOWN S db
```

诚实预期：12 条用例全绿是正常态。

`--setup-show` 输出里 `S` 前缀是 session 级 fixture、`F` 前缀是 function 级；`SETUP S db` 与 `TEARDOWN S db` 首尾成对，中间夹着每条用例自己的 `clean_db`——session 连接只建一次，表清理逐条发生。

作用域证据还可以看 `FakeDB.instances` 计数器：session 级 `db` 连接（约 0.2s）在整个运行里只发生一次，四条用例共用。


本实验的三个共享 fixture（`db` / `clean_db` / `user_factory`）都在
`tests/conftest.py` 里，用例只管在参数表里报名字。

## How It Works

**栈式装配**：pytest 像栈一样装配 fixture——session 级最先建、最后拆；function 级每条用例一对 setup/teardown。

Quick Start 节选输出里的先后顺序（`SETUP S db` → `SETUP F clean_db` → `TEARDOWN F clean_db` → `TEARDOWN S db`）就是这张栈的实况。


**yield 式 setup/teardown** 是最核心的写法：

```python
@pytest.fixture(scope="session")   # 作用域：function < module < package < session
def db():
    conn = FakeDB(...)             # setup：建昂贵连接
    yield conn                     # 把资源交给用例
    conn.close()                   # teardown：即使用例失败也执行
```

为什么这样写：`yield` 之前的代码是 setup，之后的是 teardown，一个函数写完生命周期，
不需要像 unittest 那样拆成两个方法。teardown 的执行保证与 try/finally 相同——
用例失败也执行，脏状态不会泄漏给下一条用例。

**conftest.py 共享**：放在 `tests/conftest.py` 里的 fixture 对整个目录的用例可见，
不需要 import。层级规则是就近优先：子目录的 conftest 可以覆盖父目录同名 fixture，
天然支持"项目级默认 + 目录级特化"（monorepo 多包各自动态定制时有用）。

**依赖解析**：用例签名声明参数 → pytest 按名字解析 fixture → fixture 自身的参数
又解析其他 fixture，层层展开成一张依赖图（DAG）。`clean_db(db)` 这一个签名就表达了
"先有 session 连接，再清表"。

**工厂 fixture**：`user_factory(n=10)` 返回的不是数据而是**造数据的函数**——
用例里调用几次、造几份，自己说了算。

## Pitfalls & Q&A

踩坑清单：

- **测试套件莫名变慢**。原因：`scope="function"` 是默认值，昂贵资源忘了改作用域，
  每条用例重建一遍。解法：连接类贵而不脏的资源上 session 级。
- **报 ScopeMismatch**。现象：fixture 创建时报作用域不匹配。原因：function 级
  fixture 被 session 级依赖——作用域只能"就大不就小"。解法：调大被依赖者的作用域。
- **autouse=True 满天飞**。autouse 会把 fixture 强加给所有用例，隐式依赖难排查。
  解法：显式写在参数表里，可读性优先。
- **用例之间有顺序依赖**。现象：单独跑全绿、合跑就挂。原因：脏状态没清理。
  解法：function 级 teardown 保证"谁先跑都干净"——这也是 lab 09 并行化的前提。
- **自己造 tempfile 管临时目录**。pytest 内置 `tmp_path` fixture：每条用例唯一
  临时目录、自动清理，不需要手写 tempfile 逻辑。

深入问答：

- **Q：session 和 function 作用域怎么选？** 按"建一次的成本 × 脏的风险"权衡：
  连接类贵而不脏的上 session；数据类易脏的留 function，并在 teardown 里复位。
- **Q：yield fixture 和 addfinalizer 的区别？** 语义等价，yield 更线性可读。
  多个 finalizer 的执行顺序是注册的逆序，与多层 yield 的行为一致。
- **Q：conftest 能被子目录覆盖吗？** 能，就近优先，适合 monorepo 里多个包各自定制。
