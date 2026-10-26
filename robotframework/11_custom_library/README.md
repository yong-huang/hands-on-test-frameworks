# 11 · 自定义 Python 关键字库

## Background

通用关键字不够用时，就该造自己的轮子了：Python 写类、方法即关键字、docstring 即文档、
抛 AssertionError 即用例红。Robot 的库机制让 Python 工程能力全部进入关键字宇宙。

## What

- `ShopLibrary.py`：5 个关键字——生成订单号前缀 / 校验金额（两位小数正数）/ 生成测试数据
  （唯一毫秒后缀）/ 计算签名（sha256 规范化序列化 + 盐）/ 断言签名一致
- `robot.libdoc` 生成 HTML API 文档（造的轮子要有说明书）
- 套件 4 条用例：每个关键字都有 正向 + 反向（非法输入必须红）双向验证

## When to Use

- 领域断言（金额/签名/业务规则）需要复用 ≥2 个套件时
- 测试数据工厂需要跨用例唯一性保证时

## Quick Start

```bash
cd robotframework/11_custom_library
./11_custom_library.sh            # libdoc ✅ + 4 tests, 4 passed
```

实测输出（2026-10-27，节选）：`✅ API 文档已生成` + `4 tests, 4 passed, 0 failed`

## How It Works

- `@keyword` 装饰器定中文名（用例里写中文关键字）、`@library(scope="GLOBAL")` 定实例域
- 断言失败抛 AssertionError → 该关键字红 → 用例红；`Run Keyword And Return Status`
  把红绿捕获成布尔供反向用例
- libdoc 直接吃 .py 文件，docstring 就是文档正文

## Pitfalls & Q&A

- **坑：PythonLibCore 不是 robotframework 的传递依赖**——纯 robot.api 装饰器就能建库，
  不装 PLC 会 ModuleNotFoundError（实测）；需要动态库关键字等高级特性时再引入
- **坑：同一毫秒连调数据工厂会撞后缀**——机器太快，`int(time.time()*1000)` 两次相等
  （实测 `李雷-1793033819564 == 李雷-1793033819564`）；加进程内计数器兜底递增
- **Q：为什么断言放库里而不是用例里？** 业务规则（金额两位小数）只有一个定义处；
  用例里复述规则=规则改了要改 N 处
