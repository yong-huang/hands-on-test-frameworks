# 定位策略实测笔记

> 在 iPhone 17 / iOS 26.5、SauceLabs My Demo App 2.3.0 上实测。
> 目标不是背 API，而是知道"这个元素的哪种定位最抗改版"。

## 优先级

1. **accessibility id**：最稳，语义明确，改版通常不动它。
2. **iOS predicate**：id 不唯一或需要条件组合时使用，可读性好。
3. **iOS class chain**：需要层级/索引时使用，比 XPath 快，但索引脆弱。
4. **XPath**：最后手段。遍历整棵 UI 树，慢且容易随层级变化失效。

## 六类元素对照

| 元素 | 实测 accessibility id | 第二策略 | 实测结果 | 结论 |
|:---|:---|:---|:---|:---|
| Catalog tab | `Catalog-tab-item` | predicate `name == 'Catalog-tab-item'` | 两种各命中 1 个 | 首选 id |
| Login Button | `Login Button` | predicate `name == 'Login Button'` | 容器各命中 1 个 | 定位容器，不定位子按钮 |
| 商品名 | `Product Name` | predicate `label == 'Sauce Labs Backpack - Black'` | id 命中 6 个；predicate 命中 1 个 | id 有歧义，用 label 收窄 |
| 商品价格（列表） | `Product Price` | class chain ``**/XCUIElementTypeStaticText[`name == "Product Price"`][1]`` | id 命中 6 个；class chain 命中第 1 个 | 列表金额未暴露，详情页看金额 |
| 购物车角标 | 无稳定 id | predicate `name == '1' AND type == 'XCUIElementTypeStaticText'` | predicate / class chain 各命中 1 个 | 断言存在与文本，不依赖 visible |
| 结算按钮 | `ProceedToCheckout` | predicate `name == 'ProceedToCheckout'` | 两种各命中 1 个 | 首选 id |

## 四个真实坑

### 1. `Product Name` / `Product Price` 不是唯一 id

Catalog 一次渲染 6 个商品，每个商品的名称和价格都复用同一个 accessibility
identifier。`findElement` 只返回第一个，`findElements` 才能看到 6 个。

要锁定具体商品，用 predicate 的 `label`：

```java
AppiumBy.iOSNsPredicateString("label == 'Sauce Labs Backpack - Black'")
```

### 2. 列表价格没有暴露金额

Catalog 的 `Product Price` 元素 `value`、`name`、`label` 都是
`Product Price`，具体金额没有出现在 page source 里；进入商品详情页后，
`Price` 元素才暴露 `$ 29.99`。

所以价格断言分两层：列表页验证"价格元素存在"，详情页验证"金额正确"。

### 3. 角标的 `visible` 不可靠

购物车角标在截图里可见，但 page source 里 `visible="false"`。此时
`isDisplayed()` 可能返回 false，不能拿它当断言；正确做法是断言元素存在，
并校验文本为 `1`。

### 4. Login Button 的子按钮 id 会骗人

`Login Button` 容器的 accessibility id 稳定；它下面的子按钮 id 是
`LogOut-menu-item`，即使界面显示的是 "Login"。定位容器即可，不要依赖
子按钮的名字去判断登录状态。

## XPath 演示

`XPathDemoTest` 只演示"能定位"，不进入主套件：

```java
AppiumBy.xpath("//XCUIElementTypeButton[@name='Catalog-tab-item']")
```

主用例 `LocatorStrategyTest` 中 XPath 出现次数必须为 0，脚本会用 grep 检查。
