# SECRET_DEFS.md — 靶场陷阱答案（破案前别看）

| # | 陷阱 | 位置 | 破解要点 |
|:--|:---|:---|:---|
| ① | 慢元素：秒杀横幅页面打开 2.5s 后才 `hidden=false` | index.html | 显式等待 `visibilityOfElementLocated(#flash-banner)`，sleep 版会翻车或浪费 |
| ② | 三层 iframe：购买按钮 #buy-btn 包在 outer→middle→inner 三层里 | checkout.html + frame_outer/middle/inner.html | 逐层 `switch_to.frame`，操作完 `switch_to.default_content`；不切 frame 必 NoSuchFrameException |
| ③ | 原生 alert：点「开启促销提醒」弹 alert，不处理会阻塞后续一切操作 | checkout.html #promo-btn | `driver.switch_to.alert.accept()`；alert 期间页面元素不可见 |
| ④ | 懒加载：30 件商品分 3 页，滚动到底才 fetch 下一页；接口本身还慢 1.2s | index.html + /api/products | 滚动到底（JS 或键 End）→ 等待卡片数增长 → 重复至 30 |

另有接口级慢响应：/api/products 固定 1.2s 延迟（server.py），供等待/性能类实验复用。
