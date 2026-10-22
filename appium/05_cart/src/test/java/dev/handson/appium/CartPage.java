package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;

/**
 * 商品详情页与购物车页的页面对象。
 * 实测事实（2026-10-22，App 2.3.0）：
 * - 详情页数量控件是 AddPlus Icons / SubtractMinus Icons，数量文本叫 Amount；
 * - 列表页和购物车行的单价带空格（"$ 29.99"），购物车总价没有空格（"$29.99"）；
 * - 购物车角标是 name 为纯数字、visible=false 的 StaticText，断言存在与文本，
 *   不能用 isDisplayed；
 * - 详情页没有返回按钮，切页面靠底部 tab。
 */
public class CartPage {

    private static final By DETAIL_PRICE = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeStaticText' AND name == 'Price'");
    private static final By DETAIL_AMOUNT = AppiumBy.accessibilityId("Amount");
    private static final By ADD_TO_CART = AppiumBy.accessibilityId("AddToCart");
    private static final By ADD_PLUS = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'AddPlus Icons'");
    private static final By SUBTRACT_MINUS = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'SubtractMinus Icons'");
    private static final By REMOVE_ITEM = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'Remove Item'");
    private static final By NO_ITEMS = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeStaticText' AND name == 'No Items'");
    private static final By CART_TAB = AppiumBy.accessibilityId("Cart-tab-item");

    private final BaseTest owner;

    public CartPage(BaseTest owner) {
        this.owner = owner;
    }

    /** 在目录页点第一个商品进详情。 */
    public void openFirstProduct() {
        owner.driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(ADD_TO_CART));
    }

    /** 详情页单价（label 形如 "$ 29.99"）。 */
    public BigDecimal detailUnitPrice() {
        return parseAmount(owner.wait.until(
                ExpectedConditions.visibilityOfElementLocated(DETAIL_PRICE)).getAttribute("label"));
    }

    /** 详情页当前数量（Amount 文本）。 */
    public int detailQuantity() {
        return Integer.parseInt(owner.wait.until(
                        ExpectedConditions.visibilityOfElementLocated(DETAIL_AMOUNT))
                .getAttribute("label"));
    }

    public void tapAddPlusOnDetail() {
        owner.waitForClickable(ADD_PLUS).click();
    }

    /** 点加购并等角标出现指定数字（角标 visible=false，只能断言存在）。 */
    public void addToCartAndWaitBadge(String expectedBadge) {
        owner.waitForClickable(ADD_TO_CART).click();
        owner.wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeStaticText' AND name == '" + expectedBadge + "'")));
    }

    /** 角标文本：详情页上 name 为纯数字的 StaticText（排除名为 Amount 的数量文本）。 */
    public String badgeText() {
        List<WebElement> candidates = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND name MATCHES '[0-9]+' AND name != 'Amount'"));
        if (candidates.isEmpty()) {
            throw new NoSuchElementException("页面上没有数字角标");
        }
        return candidates.get(0).getAttribute("name");
    }

    public void openCart() {
        owner.waitForClickable(CART_TAB).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("name == 'My Cart'")));
    }

    /** 购物车总价：label 形如 "$29.99"（无空格，区别于行内单价的 "$ 29.99"）。 */
    public BigDecimal cartTotal() {
        List<WebElement> amounts = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND label CONTAINS '$'"));
        for (WebElement el : amounts) {
            String label = el.getAttribute("label");
            if (label.matches("\\$[0-9.]+")) {
                return parseAmount(label);
            }
        }
        throw new NoSuchElementException("购物车里没找到总价（形如 $29.99 的无空格金额）");
    }

    /** 购物车行内单价（带空格的 "$ 29.99"）。 */
    public BigDecimal cartUnitPrice() {
        List<WebElement> amounts = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND label CONTAINS '$'"));
        for (WebElement el : amounts) {
            String label = el.getAttribute("label");
            if (label.matches("\\$ [0-9.]+")) {
                return parseAmount(label);
            }
        }
        throw new NoSuchElementException("购物车里没找到行内单价（形如 $ 29.99 的带空格金额）");
    }

    /** "N Items" 文本，如 "2 Items"；购物车为空时返回空串。 */
    public String itemCountLabel() {
        List<WebElement> labels = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND name MATCHES '[0-9]+ Items'"));
        return labels.isEmpty() ? "" : labels.get(0).getAttribute("name");
    }

    /** 购物车行内的数量文本（数字），加减少后用它确认同步。 */
    public String cartRowQuantity() {
        List<WebElement> qty = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND name MATCHES '[0-9]+'"));
        return qty.isEmpty() ? "" : qty.get(0).getAttribute("name");
    }

    public void tapAddPlusInCart() {
        int before = Integer.parseInt(cartRowQuantityOrZero());
        owner.waitForClickable(ADD_PLUS).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeStaticText' AND name == '"
                                + (before + 1) + " Items'")));
    }

    private String cartRowQuantityOrZero() {
        String label = itemCountLabel();
        return label.replaceAll("[^0-9]", "").isEmpty() ? "0" : label.replaceAll("[^0-9]", "");
    }

    public void tapSubtractMinusInCart() {
        int before = Integer.parseInt(cartRowQuantityOrZero());
        owner.waitForClickable(SUBTRACT_MINUS).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeStaticText' AND name == '"
                                + (before - 1) + " Items'")));
    }

    /** 删除行内商品并等空态出现。 */
    public void removeItemAndWaitEmptyState() {
        owner.waitForClickable(REMOVE_ITEM).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(NO_ITEMS));
    }

    /** 空态文案是否可见（有商品时该元素在树上但 visible=false）。 */
    public boolean emptyStateVisible() {
        return owner.isVisible(NO_ITEMS);
    }

    /** 把 "$ 29.99" / "$29.99" 清洗成 BigDecimal。 */
    static BigDecimal parseAmount(String raw) {
        return new BigDecimal(raw.replaceAll("[^0-9.]", ""));
    }
}
