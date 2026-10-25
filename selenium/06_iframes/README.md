# 06 · iframe 嵌套作战

## Background

iframe 把页面切成多个独立文档，driver 的「眼睛」一次只能在一个文档里——这是新手
NoSuchElementException 的第二大来源（第一大是等待）。靶场把购买按钮包了三层 iframe，
还塞了一个原生 alert，一次把两类阻塞练透。

## What

- 三层 frame（outer→middle→inner）内完成 购买 → 支付 → 切回主文档 → **API 侧复核** status=paid
- frame 按序号（index）切换的等价写法
- 原生 alert 阻塞演示：不 accept，后续操作全部卡死；accept 后状态才更新
- 反例注释保留：不切 frame 直接找内层按钮 → NoSuchElementException

## When to Use

- 支付网关、富文本编辑器、客服组件、广告位——一切第三方嵌入场景
- 页面弹 alert 的流程（权限提示、确认框）

## Quick Start

```bash
cd selenium/06_iframes
./06_iframes.sh            # 3 passed
```

实测输出（2026-10-26，节选）：

```text
三层 iframe 内完成购买+支付，API 复核 status=paid（ORD-e966ab54, $15.98）
3 passed in 2.37s
```

## How It Works

- `switch_to.frame(id/index/WebElement)` 进入，`switch_to.default_content()` 回到最外层——
  嵌套切换是「逐层进入」，回退是「一键到顶」，没有「回上一层」
- 每层切换前先等下一层 frame 元素出现（frame 标签在父文档里，可以被显式等待）
- 断言不只看页面自说自话：切回主文档后用 API 复核订单状态，双证据

## Pitfalls & Q&A

- **坑：不切 frame 直接找 iframe 里的元素** → NoSuchElement（元素在另一个文档里）
- **坑：切进内层后又 `switch_to.frame("frame-middle")`** → 找不到，因为 middle 在父文档——
  回退只能 `default_content()` 重新逐层进
- **坑：alert 没处理就点别的** → `UnexpectedAlertPresentException` 或操作静默失效；先 `switch_to.alert.accept()`
- **Q：frame 按 index 切什么时候用？** frame 无 id/name 时按出现序号（0 起），可读性差，注释里写清哪个是哪个
