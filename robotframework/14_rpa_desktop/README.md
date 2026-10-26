# 14 · RPA——桌面应用自动化

## Background

桌面自动化是 RPA 的看家本领：驱动没有 API、没有 DOM 的老应用。macOS 上最稳的通道
是 System Events 的辅助功能 API——键盘事件（keystroke）+ UI 树读值（static text 的 value）。
本实验把 macOS 计算器桥成 Robot 关键字，5 道四则运算全键盘驱动、屏显读数断言。

## What

- `CalcBridge.py`：6 个关键字——打开计算器 / 按键序列 / 分步计算 / 读结果层 /
  剪贴板写入 / 读取（osascript 桥，规避 RPA.Desktop 图像定位的分辨率敏感与 RPA.Windows 的平台限制）
- 五道四则（12×3=36 … 144/12=12）键盘逐字发送、读**结果层** static text 断言
- 剪贴板跨应用搬运：写入唯一 token → 读回一致性断言
- apply 步含辅助功能权限自检（无权限直接给出系统设置路径）

## When to Use

- 无 API 的桌面应用（企业内部老系统、财务软件）
- 跨应用的数据搬运（剪贴板是应用间最低成本的桥）

## Quick Start

```bash
cd robotframework/14_rpa_desktop
./14_rpa_desktop.sh            # 2 passed（屏幕上会看到计算器自己动）
```

实测输出（2026-10-27）：`2 tests, 2 passed, 0 failed`

## How It Works

- 键盘流：`keystroke "12*3="`——计算器在收到 `=` 前显示算式层，收到后结果层刷新
- 读数：显示器是两个 scroll area 的 static text，**算式层在 scroll area 1、结果层在
  scroll area 2**——读错层会拿到「12×3」而不是「36」
- 全角空格清洗：macOS 显示层返回值带 U+200E 方向符，断言前 strip

## Pitfalls & Q&A

- **坑：Python import 大小写敏感**——文件命名 `calc_bridge.py` 后按 `CalcBridge.py` 导入，
  macOS 文件系统不区分、Python 区分（实测 ModuleNotFoundError）；库文件名与类名统一
- **坑：RF7 的 `Create Dictionary` 传 key/value 对**——值含 `=` 等符号时必须用
  `Evaluate {dict(...)}` 字面量，否则被按 `name=value` 复合语法解析报 Invalid item
- **坑：`@keyword` 装饰器忘了 import**——`robot.api.deco` 的 `keyword` 不在标准库同名
  builtins 里（NameError: keyword）；file 头的 import 全必查
- **Q：为什么不用 RPA.Desktop？** 图像定位对分辨率敏感（跨机器脆弱）；System Events
  的辅助功能 API 是 macOS 的「原生控件协议」，稳且快——代价是需要辅助功能授权
