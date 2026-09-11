# 11 · 造被测应用 SUT：FastAPI 订单管理，后面 19 个实验都测它

> 测什么？从本篇起不再"玩具函数"——我们造一个**真被测应用**：FastAPI + SQLite +
> 静态前端页的订单管理小应用。API 契约从此冻结，API 测试、DB 集成、Playwright、
> Cypress、Selenium、Locust、k6……全部对着**同一个 SUT**，同目标才好对比。

## 1. 为什么需要它

- 没有稳定 SUT，E2E 教程只能"each tutorial its own todo-app"——没法横向对比。
- 本 SUT 特意包含教学需要的"事故现场"：慢接口（等 waits）、登录态（练会话）、
  4xx 分支（练负向用例）、迁移表（练集成隔离）。

## 2. 总览：SUT 的组件与依赖关系

<!-- 图: images/sut.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/11_sut_app/images/sut.html)
> （或本地打开 [`images/sut.html`](images/sut.html)）。

静态页（下单表单/慢加载页/登录页/Admin 页）走 HTTP 调 API；API 层校验后进
SQLite 数据层；`/api/slow-config` 故意睡 1.5s，是 lab 17 等待训练的靶子。

## 3. 快速开始

```bash
./sut_app.sh            # 全流程：种子数据 → 起服务 → API 走查 → 自测冒烟 → 清理
./sut_app.sh observe    # 起服务并验证（服务保留运行，方便手动探索）
open http://127.0.0.1:8899
./sut_app.sh clean      # 停服务、删库——回到实验前状态
```

端口默认 8899，`SUT_PORT=xxxx ./sut_app.sh` 覆盖。

## 4. 核心概念（API 契约速查）

| 方法 | 路径 | 成功 | 失败 |
|:---|:---|:---|:---|
| POST | /api/orders | 201 + Location | 422（缺字段/负数） |
| GET | /api/orders?status&limit&offset | 200 + X-Total-Count | 400（非法状态） |
| GET | /api/orders/{id} | 200 | 404 |
| PATCH | /api/orders/{id} | 200 | 400 非法状态 / 404 |
| DELETE | /api/orders/{id} | 204 | 404 |
| POST | /api/login | 200 {token, role} | 401 |
| GET | /api/admin/stats | 200（仅 admin） | 403 |
| GET | /api/slow-config | 200（睡 1.5s） | — |

- **登录态**：admin/admin123、user/user123，token 写 localStorage（lab 19/22 复用）。
- **状态机**：created → paid → shipped / cancelled，四个合法值。

### 4.1 易错点（本实验真实踩过）

- SQLite `with conn:` 只管提交不关连接；**提交前开新连接读不到刚写的数据**。
- 后台起 uvicorn 要 `nohup + </dev/null + disown`，否则脚本退出会被拖住。
- bash 里 `$OID；`（后面跟全角标点）会把多字节字符并进变量名——用 `${OID}`。

## 5. 关键字段（为什么这么设计）

- `X-Total-Count` 响应头：分页总数的通用约定，lab 12 直接断言它。
- `schema_migrations` 表：lab 13 迁移测试的靶子。
- `store.py` 独立成数据层：lab 13/14 能绕过 API 直接测库、切 Postgres。
- 种子脚本幂等可重跑：`rm -f orders.db && python seed.py` 是脚本 clean/apply 的组合。

## 6. 文件结构

```
11_sut_app/
├── README.md
├── sut_app.sh            # apply 种子 / observe 起服+走查+自测 / clean 停服删库
├── configs/pytest.ini
├── app/
│   ├── main.py           # FastAPI 路由 + 静态页挂载（契约在上表）
│   ├── store.py          # SQLite 数据层（后续集成测试的对象）
│   ├── seed.py           # 10 条演示订单
│   └── static/
│       ├── index.html    # 下单表单 + 列表 + 删除按钮（E2E 主页面）
│       ├── slow.html     # 延迟渲染/竞态按钮（lab 17）
│       ├── login.html    # 写 localStorage（lab 19/22）
│       └── admin.html    # admin 角色专属页（lab 19/22）
├── tests/test_sut_smoke.py   # SUT 自测：起不来后面全白搭
└── images/
```

## 7. 深入要点

- **Q: 被测应用的"测试友好设计"指什么？** 依赖可注入（DB 路径环境变量）、
  状态可重置（幂等种子/删库）、行为可加速或可故意放慢、契约稳定。
- **Q: 健康检查为什么重要？** 脚本/CI 里"等就绪"的唯一可靠方式是轮询健康端点，
  裸 sleep 是 flaky 之源。
- **Q: 为什么数据层独立成模块？** API 测试走 HTTP、集成测试直打数据层——
  分层让"同一逻辑"能被两层测试夹击。

## 8. 总结

SUT 就绪、契约冻结。下一篇 [12_api_tests](../12_api_tests/README.md)：
给它写第一套 30 条的 API 测试。
