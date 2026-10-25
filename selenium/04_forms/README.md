# 04 · 表单控件全集

## Background

真实业务的自动化八成在跟表单打交道：文本框谁都会填，日期控件、多选下拉、滑块、文件上传
每一类都有自己的脾气。本实验把 8 类控件一网打尽，并用「服务端回读 vs 输入」的逐字段断言
证明不是"看起来填上了"，而是真的填对了。

## What

- 靶场新增 `form.html`：文本 / 单选下拉 / 多选下拉 / 复选框 / 单选组 / 日期 / 滑块 / 文件上传
- 新增 `/api/feedback` 回读接口：原样回显提交 payload，供逐字段断言
- 用例：8 类控件全操作 → 提交 → 断言回读 JSON 与输入逐字段一致（含中文「李雷 ⚡<testing>」与特殊字符）

## When to Use

- 新表单页面写用例时的控件操作速查
- 验证「输入真的到达服务端」——回读断言比截图断言可信

## Quick Start

```bash
cd selenium/04_forms
./04_forms.sh            # apply（重启靶场加载新接口）→ observe → clean
```

实测输出（2026-10-26）：

```text
1 passed in 1.47s
```

## How It Works

- 单选/多选下拉走 `Select` 类；文件上传不需要点开文件对话框——`send_keys(绝对路径)` 直接投递
- 滑块：点选聚焦后按方向键（step=1），提交前 `get_attribute("value")` 预校验
- 提交后等待 `<pre id=echo>` 可见再解析 JSON，回读断言逐字段比对

## Pitfalls & Q&A

- **坑：日期控件键入受 locale 段位顺序摆布**。实测本机 Chrome 按 年/月/日 消化键入，
  `"11012026"` 被解析成 `110120-02-06` 这种鬼日期；en-US 机器又是另一种错法。
  键入法要跟 locale 赌博，**确定性做法是 JS 设值 + 派发 change 事件**（表单读 `.value`，监听也同步）
- **坑：多选下拉忘记 `multiple` 属性时 `Select` 会抛 NotImplementedError**——`select_by_visible_text` 只对多选/单选各有一套
- **Q：文件上传能绕过系统文件对话框吗？** 能，且必须绕过——`input[type=file]` 上 `send_keys` 路径是 WebDriver 的官方通道
