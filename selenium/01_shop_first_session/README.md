# 01 · 带病靶场 + 三浏览器首会话

## Background

没有自动化靶场时，学 Selenium 只能打公共演示站：网络不可控、页面随时改版、陷阱不可复现。
本系列第一步先自建一个**带病靶场**——一个故意埋了四类经典陷阱的电商站（慢元素/三层 iframe/原生 alert/懒加载），
全部 18 个项目都打它，坑是自己的，结论才可复现。

## What

- **靶场**（`../shop/`，全系列共享公共设施）：
  - `index.html` 商品列表：30 件商品分 3 页滚动懒加载（接口故意慢 1.2s）+ 2.5s 后现身的秒杀横幅（慢元素）
  - `checkout.html` 结账页：三层 iframe 包住的购买按钮 + 原生 alert 弹窗按钮
  - REST：`/api/products?page=N`（慢）、`/api/orders` 创建/查询/支付/取消、`/api/health`
  - 陷阱答案锁在 [../shop/SECRET_DEFS.md](../shop/SECRET_DEFS.md)，破案前别看
- **首会话**（本目录）：Chrome / Firefox（无头）+ Safari（有头，无无头模式）各自
  「打开靶场 → 断言标题 → 打印 browser/driver 版本 → 退出」

## When to Use

- 新机器搭 Selenium 环境后的第一件事：验证 driver 链路（Selenium Manager 自动管 chromedriver/geckodriver）
- 给新系列建「自己的靶场」时，参考这里的陷阱设计套路

## Quick Start

```bash
cd selenium/01_shop_first_session
./01_shop_first_session.sh            # apply 拉靶场 → observe 三浏览器跑通 → clean 清产物
bash ../shop/shop.sh clean            # 显式停靶场（公共设施，clean 不代停）
```

实测输出（2026-10-26，节选）：

```text
[chrome] browser=156.0.8078.47 driver=156.0.8078.47
[firefox] browser=158.0.1 driver=0.37.1
[safari] browser=26.5.2 driver=safaridriver
3 passed in 5.47s
```

## How It Works

- driver 不再手装：Selenium Manager（selenium 4.6+ 内置）按需下载/匹配 chromedriver 与 geckodriver；
  GitHub 不通的环境从 npmmirror 手动装 geckodriver（见 docs/selenium.md 项目 1 风险行）
- `../conftest.py` 提供全系列共享的 `make_driver(name)` 与 `shop` 会话级夹具（幂等拉靶场），
  `SELENIUM_BROWSER`/`HEADLESS` 两个环境变量控制浏览器与无头
- Safari 没有无头模式，恒有头；safaridriver 由 macOS 自带，首次使用需 `sudo safaridriver --enable`（本机已可用）

## Pitfalls & Q&A

- **Q：为什么靶场是"带病"的？** 每个病对应后面一个项目的教学点（等待/iframe/alert/懒加载），答案在 SECRET_DEFS.md
- **Q：Safari 窗口会弹出来吗？** 会——Safari 不支持无头，跑它时屏幕上会闪窗口，属正常
- **坑：geckodriver 自动下载失败**（GitHub 不通）：`curl -sfL` 从 npmmirror 装 0.37.1，注意 0.37 起文件名是 `macos-aarch64`
