# 05 · Web 表单与控件全集

## Background

Robot 的表单关键字族是「一句话一个动作」：`Select From List By Value`、`Select Checkbox`、
`Choose File`……本实验把多选/复选/单选组/文件上传一次练熟，并用页面汇总区做端到端断言。

## What

- 靶场表单升级：多选下拉（增值服务）/ 复选（贺卡）/ 单选组（快递）/ 文件上传（凭证）+ 提交后汇总回显
- 一条用例覆盖：多选断言 `List Selection Should Be`、`Checkbox Should Be Selected`、
  `Radio Button Should Be Set To`、`Choose File` 投递绝对路径、汇总四段逐项断言、订单号 ROB- 前缀

## When to Use

- 电商/后台的复杂表单页接入自动化
- 文件上传类流程（凭证、附件、头像）

## Quick Start

```bash
cd robotframework/05_web_widgets
./05_web_widgets.sh            # PASS
```

实测输出（2026-10-27）：`控件全集操作与汇总断言 | PASS`

## How It Works

- 多选下拉连选两次 `Select From List By Value` 即多选；`List Selection Should Be` 接多值校验
- 文件上传不走系统对话框：OperatingSystem 库 `Create File` 造临时凭证，`Choose File` 投绝对路径
- 汇总回显是页面把选择拼成一句话——断言逐段 contains，等价于「服务端回读」的 UI 版

## Pitfalls & Q&A

- **坑：关键字名凭印象写**——`Radio Button Should Be Set` 不存在，正名是
  `Radio Button Should Be Set To`（实测报错自带 Did you mean 提示，按提示改即可）
- **Q：为什么要断言 `Checkbox Should Be Selected`？** 勾选动作成功 ≠ 状态生效；
  状态断言把「点了」和「选上了」分开验证
