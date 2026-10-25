# 12 · SAST 自定义规则：给 semgrep 写自己的安检画像

> 用别人写好的扫描规则，永远只防别人想到的攻击。本实验给 semgrep 写三条
> 面向 FastAPI 服务的自定义规则（SQL f-string 拼接 / eval / 硬编码密钥）：
> validate 零错误、靶场 5 个埋点检出 4 个、干净对照零误报；再用社区规则集
> 对真实 SUT（System Under Test，被测系统——即 labs/11 的 FastAPI 订单应用）
> 跑基线留档——安全左移到「规则自己写、自己评审」这一层。

## Background

之前的做法：安全扫描等于装个扫描器跑默认配置，报什么看什么——报告成了
黑盒，误报没法自己修，团队特有的危险模式（自研包装的 execute、口口相传的
密钥约定）更是无人跟进。

痛点的核心是**通用规则不认识团队的业务形状**：漏报的是最贴身的风险，
留下的是最泛泛的告警。规则不可读、不可评审，安全左移就停在「装工具」。

semgrep 把规则做成了可读的 YAML 模式匹配——本实验写三条自定义规则并
全流程验证：合法性校验 → 靶场实测 → 干净对照 → 社区基线对照留档。

## What

SAST（Static Application Security Testing，静态应用安全测试：不运行程序、
扫源码找漏洞模式）规则是对「危险代码形状」的声明式描述；semgrep 把 YAML
里的模式直接对源码结构匹配，命中即报。

可以把规则想成海关的违禁品画像——「圆柱形金属罐」（模式）比「某品牌可乐」
（具体某行代码）覆盖面广。但和海关画像不同的是，形状抓不到内容：变量名叫
`fallback` 的真密钥（本实验埋点 5）就漏了——按值匹配是另一类工具的领地。

| 自定义规则 | 模式 | severity |
|:--|:--|:--|
| sql-fstring | `$CURSOR.execute(f"...")`（f-string 拼 SQL） | ERROR |
| eval-call | `eval(...)`（动态执行任意字符串） | ERROR |
| hardcoded-secret | 变量名含 key/token/secret/password 且赋值为字符串字面量 | WARNING |

![自定义规则经校验后对靶场、对照与真实 SUT 的三路扫描](images/sast_rules.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/12_sast_rules/images/sast_rules.html)
> （或本地打开 [`images/sast_rules.html`](images/sast_rules.html)）。
> 规则 YAML 是唯一产出物：validate、靶场、基线都是对它的三路验证。

## When to Use

- 团队安全基线落地：把代码评审的口头约定（「SQL 不许拼字符串」）变成
  机器规则，评审规则 diff 就是评审安全策略。
- 框架专属模式：社区规则不认识你的自研 DB 包装、内部加密约定。
- 何时不用：通用 CVE（公开编号的已知漏洞）/框架漏洞直接用社区规则集（别重造轮子）。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 社区规则集（--config auto） | 广覆盖、零维护、需联网 | 通用漏洞基线（本实验第③步） |
| 自定义规则（本实验） | 贴合团队模式，可评审 | 团队安全约定固化 |
| 按值匹配扫描（gitleaks） | 抓密钥内容而非变量名 | 凭据泄漏专查（项目 13） |

## Quick Start

前置：仓库根 `.venv`（semgrep 已装入，缺则 `pip install semgrep`）。
一条命令跑完整动线：

```bash
./sast_rules.sh   # apply → observe（校验/靶场/对照/盲区/基线）→ clean
```

规则合法性校验与靶场扫描（5 埋点检出 4，≥4/5 达标；输出为节选，
已省略步骤横幅与行尾截断注释）：

```text
Configuration is valid - found 0 configuration error(s), and 3 rule(s).
  ⛔ hardcoded-secret  L8   API_KEY = "sk-live-9527-console"
  ⛔ sql-fstring        L14  cur.execute(f"SELECT * FROM users WHERE id = {user_id}")
  ⛔ sql-fstring        L21  cur.execute(f"SELECT * FROM orders WHERE owner = '{user_id}'")
  ⛔ eval-call          L26  return eval(code)
  检出 4 / 5
```

干净对照零误报；盲区披露与社区基线：

```text
  误报 0 条
>>> 按变量名匹配是白名单式规则；值为密钥但名字无关的，交给 gitleaks 按值匹配（项目 13）
  基线发现 2 条（已留档 baseline/community_baseline.json）
```

诚实预期：检出 4/5 不是引擎故障——埋点 5 是「变量名无关的真密钥」，按变量
名匹配的规则天然看不见它；这正是分层防御的理由（见 Q&A 第三条）。

## How It Works

**一条规则三要素**：`id`（唯一名）、`severity`（ERROR/WARNING 报告分级）、
模式（单 `pattern` 或 `patterns` 组合）。组合用 metavariable 提取变量再做
二级约束——hardcoded-secret 的写法：

```yaml
patterns:
  - pattern: $KEY = "..."        # "..." 匹配任意字符串字面量
  - metavariable-regex:
      metavariable: $KEY
      regex: (?i)^(.*_)?(key|token|secret|password)(_.*)?$
```

**`"..."` 与 `f"..."` 是通配语法**：前者匹配任意字符串字面量（所以
`API_KEY = os.environ[...]` 不命中——那是下标访问不是字面量），后者匹配
任意 f-string。两条 SQL 埋点（单引号内插、直接内插）都被同一个 `f"..."`
模式覆盖，规则不用写两遍。

**validate 先于实战**：`semgrep --validate` 校验 YAML 语法与模式合法性
（本实验规则 0 error）；基线用 `--config auto` 联网拉社区规则集，对
labs/11 实扫出 2 条 sqlalchemy 裸查询告警——JSON 已留档作对照起点。

## Pitfalls & Q&A

常见故障与解法：

- **想匹配「字符串字面量」却写 `metavariable-pattern: pattern: str`**：
  那匹配的是名为 `str` 的表达式（一个引用），不是字面量——hardcoded-secret
  因此全空。任意字符串字面量就用 semgrep 的 `"..."` 通配。
- **只按变量名匹配密钥**：值为密钥、名字无关（`fallback = "..."`）的案例
  必漏。按名规则 + 按值工具（gitleaks）互补，别让一条规则包打天下。
- **报告取行别信 `extra.lines`**：它偶发不等于源码行；用 `start.line` 回
  源文件取行打印，展示永远以真实源码为准。

Q&A：

- **和 architect 22 什么关系？** 22 用现成规则搭安全门禁「流程」；本实验
  学写规则「本身」——先会写规则，门禁里的规则才评审得动。
- **severity 有什么用？** 报告分级之外，配 `semgrep --error` 可让 ERROR 级
  变非零退出码——门禁化路径接项目 14 的 pre-commit 链。
- **埋点 5 的盲区怎么治？** 分层防御：按名匹配（本实验）+ 按值匹配
  （gitleaks，项目 13）+ 运行时监控（右移）——每一层抓自己的形状。
