# 15 · CDP 网络拦截与性能采集

## Background

Selenium 的 W3C 协议管「页面交互」，页面底下的网络与性能要靠 Chrome DevTools Protocol（CDP）。
chromedriver 把 CDP 暴露成 `execute_cdp_cmd`——本实验用三条命令打开前端性能与容错测试的门：
拦截接口、模拟弱网、采集指标。**全是 Chromium 内核专属**，非 Chrome 直接 skip。

## What

- `Network.setBlockedURLs` 拦截商品接口：页面停在加载态、零卡片渲染；解除后恢复
- `Network.emulateNetworkConditions` 弱网模拟（512B/s + 2s 延迟）：同一接口实测
  **1208ms → 2922ms（×2.4）**
- `Performance.getMetrics` + DOM 时序：Nodes=127、Listeners、DCL 时间戳全采到
- 三条用例都带 Chromium-only 守卫（非 Chrome skip 并指向 14 的 COMPAT_NOTES）

## When to Use

- 前端容错验证：接口挂了页面应该「优雅降级」而不是白屏
- 弱网体验回归：关键接口在 3G 档位下的耗时预算
- 性能基线采集：节点数/监听器数/DCL 进回归报告

## Quick Start

```bash
cd selenium/15_cdp
./15_cdp.sh            # 3 passed
```

实测输出（2026-10-26，节选）：

```text
接口耗时：正常 1208ms → 弱网 2922ms（×2.4）
指标采集 OK：Nodes=127 Listeners=2 DCL=...
3 passed in 20.12s
```

## How It Works

- `execute_cdp_cmd(域名.方法, 参数)` 直通 CDP；`Network.enable` 是网络域命令的前置
- 弱网档位要跟响应体大小匹配：接口响应只有几百字节，50KB/s 的「经典档位」实测只拉高 36%，
  512B/s 才拉出 ×2.4 的差距——**弱网档位是实验参数，不是常识参数**
- 拦截用 `setBlockedURLs`（拒绝请求），要「改写响应」需 BiDi/Fetch 域事件流，超出本实验范围

## Pitfalls & Q&A

- **坑：非 Chromium 内核跑 CDP**——safaridriver/geckodriver 没有 execute_cdp_cmd 通道；
  用例必须有浏览器守卫（skip + 指向兼容性清单）
- **坑：弱网档位想当然**——「3G 档位」抄来的吞吐值在小响应体上拉不开差距；
  先测基线，再选能把差距放大到验收线以上的档位
- **Q：Safari/Firefox 怎么办？** 各有自家协议（Safari Automation inspector / BiDi），
  跨内核的网络测试建议交给代理层（如 mocking 线的替身），浏览器侧只做行为断言
