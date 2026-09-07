# 02 · fixture 与 conftest：用例的准备与清理，测试的依赖注入

> 十条用例都要一个数据库连接：在每条用例里连十遍？还是搞全局变量传着用？
> pytest 的答案是 fixture——**声明式地"需要什么"，而不是命令式地"怎么造"**。
> 本实验用"昂贵连接 + 干净表 + 数据工厂"三件套讲透作用域。

## 1. 为什么需要它

- 测试 80% 的代码是准备与清理；fixture 把它们从用例里抽走，用例只剩"断言什么"。
- 作用域（scope）决定资源生命周期：造一次用到底，还是每条用例换新——写错就是慢和脏。
- conftest.py 让 fixture 跨文件共享，不用 import。

## 2. 总览：一次用例执行背后，fixture 的入栈出栈

<!-- 图: images/fixtures.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/02_fixtures/images/fixtures.html)
> （或本地打开 [`images/fixtures.html`](images/fixtures.html)）。

pytest 像栈一样装配 fixture：session 级最先建、最后拆；function 级每条用例
一对 setup/teardown。`--setup-show` 能把这张图打印出来，本实验脚本就是这么做的。

## 3. 快速开始

```bash
./fixtures.sh            # 全流程
./fixtures.sh observe    # 重点看 ② --setup-show 的 SETUP/TEARDOWN 幕后
```

## 4. 核心概念

### 4.1 作用域：session / module / function

实验证据：`FakeDB.instances` 计数器。session 级 `db` 连接 0.2s 只发生一次，
四条用例共用；function 级 `clean_db` 每条用例把表清空。**贵的共享，脏的换新**。

### 4.2 yield 式 setup/teardown

`yield` 前是 setup，之后是 teardown；即使用例失败 teardown 也执行（类似 try/finally）。
验证：`--setup-show` 输出里 `SETUP S db … TEARDOWN S db` 成对出现。

### 4.3 conftest.py 共享

放 `tests/conftest.py` 的 fixture 对整个目录可见，用例参数表里直接写名字即可。
层级规则：子目录的 conftest 可覆盖父目录同名 fixture——天然的"项目级默认 + 目录级特化"。

### 4.4 fixture 工厂

工厂 fixture 返回**造数据的函数**而不是数据：一条用例造 3 个用户还是 10 个，自己说了算。
本实验 `user_factory(n=10)` 造出 10 份不重名数据，只需一行。

### 4.5 易错点

- 作用域只能"就大不就小"：function fixture 不能被 session fixture 依赖（会报 ScopeMismatch）。
- fixture 之间有依赖时写参数即可（`clean_db(db)`），pytest 自动解析——这就是**测试的依赖注入**。
- 用例之间别互相依赖顺序；靠 function 级 teardown 保证"谁先跑都干净"（lab 09 并行的前提）。

## 5. 关键字段

```python
@pytest.fixture(scope="session")   # 作用域：function < module < package < session
def db():
    conn = FakeDB(...)             # setup
    yield conn                     # 把资源交给用例
    conn.close()                   # teardown
```

坑清单：
- `scope="function"` 是默认值，忘了改 scope 是"测试变慢"的头号原因。
- autouse=True 会强加给所有用例——慎用，显式声明依赖更可读。
- tmp_path 是内置 fixture（每用例唯一临时目录，自动清理），别自己造 tempfile。

## 6. 文件结构

```
02_fixtures/
├── README.md
├── fixtures.sh            # 主演示脚本（--setup-show 是隐藏好戏）
├── configs/pytest.ini
├── fake_db.py             # 被测"昂贵"资源（带实例计数器）
├── tests/
│   ├── conftest.py        # db / clean_db / user_factory 三个共享 fixture
│   └── test_fixtures.py   # 13 条用例：作用域证据 + 工厂 + tmp_path
└── images/
```

## 7. 面试要点

- **Q: session 和 function 作用域怎么选？** 按"建一次的成本 × 脏的风险"权衡；
  连接类贵而不脏的上 session，数据类易脏的留 function 并在 teardown 复位。
- **Q: yield fixture 和 addfinalizer 的区别？** 语义等价；yield 更线性可读，
  多个 finalizer 出栈顺序为注册的逆序——与多层 yield 行为一致。
- **Q: conftest 能被子目录覆盖吗？** 能，就近优先；适合 monorepo 多包各自定制。
- **Q: fixture 如何做依赖注入？** 用例签名声明参数 → pytest 按名字解析 fixture →
  fixture 自身参数又解析其他 fixture，形成 DAG。

## 8. 总结

你现在能让"贵的只建一次、脏的自动清理、数据按需批量造"。下一篇
[03_parametrize](../03_parametrize/README.md)：一条用例变二十条——参数化。
