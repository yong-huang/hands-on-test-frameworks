# 06 · 契约生成挡板：provider 还没写，消费方先开发

> 对接方等后端排期，是集成阶段最常见的空转。本实验从项目 5 的契约**动态生成**
> 挡板（替身服务）：5 条消费方测试打挡板全绿——provider 全程不存在；停掉挡板
> 同样测试全红，证明挡板是唯一依赖；挡板响应逐操作过契约 schema 校验零错误；
> 真 provider 就位后，消费方测试零改动接真服务。

## Background

之前的做法：前端和下游服务排期等后端，「接口长什么样」其实契约早就定了
（项目 5），但没人在契约上先把消费方做出来——等的是可以不等的那部分。

痛点的核心还是集成贵（项目 1 漏斗里最右的关卡）：消费方的联调问题（字段
理解错、容错分支没写）全堆到 provider 就位之后才暴露。

本实验把顺序倒过来：契约一签，从契约机器生成挡板，消费方当天开工；provider
就位后按同一契约验收（项目 5 的契约测试），消费方代码原样切换。

## What

契约生成挡板是从 OpenAPI 契约自动构造的替身服务：按契约返回**结构合法**的
示例响应——字段齐全、类型正确、状态码在契约内，由 jsonschema 逐操作校验背书；
无业务逻辑、无状态。

可以把挡板想成售楼处样板间：户型（结构）与合同图纸（契约）一致，装修（业务
逻辑）没有。但和样板间不同的是它完全无记忆——删除后照样能「查到」，所以
消费方测试只能断言结构，业务断言要等 provider。

与录制回放式挡板（architect 08）的方向相反：08 从真实流量后向生成（服务
先行），本实验从契约前向生成（provider 还没生）。

![契约动态生成挡板，消费方先行，provider 换装透明](images/mock_first.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/06_mock_first/images/mock_first.html)
> （或本地打开 [`images/mock_first.html`](images/mock_first.html)）。
> 契约是唯一输入；挡板与真 provider 在消费方眼里可互换是本实验的题眼。

## When to Use

- 前端/下游等后端排期：契约一签挡板当天可用，联调问题提前到消费方开发期。
- 容错演练：注入 500 与延迟，把消费方的重试、降级分支当靶子练。
- 何时不用：需要真实状态语义的联调（挡板无记忆）；契约还没定的接口——先定契约。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 手写 mock | 路由硬编码，契约改了要人跟 | 一次性单接口 |
| 本实验（契约动态生成） | 契约改，挡板自动跟上 | 契约已定的并行开发 |
| 录制回放挡板 | 从真实流量生成，语义最真 | 已有服务做集成替身（architect 08） |

## Quick Start

前置：仓库根 `.venv`（fastapi/uvicorn/pyyaml/httpx/jsonschema）；契约复制自
项目 5。一条命令跑完整动线：

```bash
./mock_first.sh   # apply → observe（全绿/校验/注入/全红/换装）→ clean
```

provider 不存在，挡板就位后消费方测试全绿；挡板响应逐操作过契约 schema：

```text
挡板就绪：http://127.0.0.1:8934（provider 从未启动）
5 passed in 0.22s
✅ GET /api/health → 200：响应符合契约 schema
✅ GET /api/items → 200：响应符合契约 schema
✅ POST /api/items → 201：响应符合契约 schema
✅ GET /api/items/{id} → 200：响应符合契约 schema
✅ DELETE /api/items/{id} → 204：204 无响应体，无需校验
校验结论：零错误，挡板结构合法（exit 0）
```

错误与延迟注入（消费方容错分支的靶子）：

```text
注入 500 → HTTP 500
注入 1s 延迟 → 耗时 1.005965s
```

停掉挡板——同样 5 条测试全红；换上真 provider（项目 5 的忠实实现）——零改动全绿：

```text
5 failed in 16.30s            # 挡板停了，无处可打（预期失败）
>>> 已按预期全红：没有挡板也没有 provider，消费方测试无处可打
5 passed in 0.20s             # MOCK_BASE_URL 指向真 provider，测试零改动
>>> 挡板与真 provider 对消费方透明——这就是契约消费方先行的意义
```

诚实预期：挡板无状态无记忆——删除后 GET 仍返回 200（结构对、语义无），
所以消费方测试只断言契约保证的结构；业务断言是 provider 就位后的事。

## How It Works

**「从契约生成」是字面意思**：mock_server.py 不写死任何业务路由——启动时
解析契约，注册一个 catch-all 路由接住所有请求，按「方法 + 路径模板正则」
匹配到契约操作，再从该操作成功响应的 schema 递归生成示例。契约加接口，
挡板自动跟上：

```python
def gen_example(schema):                                    # 节选：省略类型标注
    schema = resolve_ref(schema)                 # $ref → components 里的定义
    if schema.get("type") == "object":
        return {k: gen_example(s) for k, s in schema.get("properties", {}).items()
                if k in schema.get("required", []) or len(schema.get("required", [])) == 0}
    ...                       # enum/array/integer/number/boolean/string 各有生成规则
```

**结构合法由独立校验背书**：validate_mock.py 对每个操作真实发请求，用
jsonschema（JSON Schema 2020-12 版规范的校验器）按契约声明的响应 schema 校验——它的示例生成是
独立实现的，防「自己校验自己」；$ref 用 RefResolver 挂整份契约解析。

**注入是演练容错的钩子**：请求头 `X-Mock-Fault: 500` 返回该状态码、
`X-Mock-Delay: 2` 睡 2 秒——消费方的重试/超时/降级分支在挡板期就能打真。

**provider 换装是零改动的**：消费方测试只认识 `MOCK_BASE_URL` 与契约结构，
指向挡板绿、指向真 provider 也绿——中间隔着的正是「双方都符合契约」这层保证。

## Pitfalls & Q&A

常见故障与解法：

- **在挡板期写了业务断言**：「DELETE 后 GET 应 404」在无记忆挡板上必挂。
  断言分层是纪律：结构断言在挡板期写，业务断言等 provider 就位补。
- **catch-all 路由的参数**：handler 声明 `api_path: str` 即可拿到通配路径；
  别做逐路由动态签名（exec 造函数、`__signature__` 都是多余复杂度）。
- **lsof 双端口一次调用**：本机 lsof 不支持 `lsof -ti :8934 :8935`，
  清理脚本分两次调用。

Q&A：

- **挡板会不会被误当真服务？** 挡板只保证结构合法；provider 是否符合契约由
  项目 5 的契约测试管——同一份契约把两边钉住，谁偏了测试说话。
- **示例生成会漏可选字段吗？** 无 required 约束时全量生成，有 required 时只
  出必填——两者都 schema 合法（OpenAPI 默认允许 additionalProperties）。
- **消费方测试太「结构化」还有价值吗？** 有：字段理解错、类型搞错、漏容错
  分支这些最贵的联调问题，恰恰都是结构层面的——挡板期就拦下。
