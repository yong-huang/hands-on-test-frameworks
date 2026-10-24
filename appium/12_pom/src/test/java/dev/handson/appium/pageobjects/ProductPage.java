package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import org.openqa.selenium.support.ui.ExpectedConditions;

import java.math.BigDecimal;
import java.util.List;

/** 商品详情页与购物车（Component Object：详情和购物车共享角标逻辑）。 */
public class ProductPage extends BasePage {

    private static final By FIRST_PRODUCT = AppiumBy.accessibilityId("Product Name");
    private static final By ADD_TO_CART = AppiumBy.accessibilityId("AddToCart");
    private static final By BADGE = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeStaticText' AND name == '1'");
    private static final By CART_TAB = AppiumBy.accessibilityId("Cart-tab-item");
    private static final By REMOVE_ITEM = AppiumBy.accessibilityId("Remove Item");
    private static final By NO_ITEMS = AppiumBy.accessibilityId("No Items");

    public ProductPage(io.appium.java_client.ios.IOSDriver driver,
                       org.openqa.selenium.support.ui.WebDriverWait wait) {
        super(driver, wait);
    }

    /** 打开第一个商品详情并加购一件。 */
    public void addFirstProductToCart() {
        presenceOf(FIRST_PRODUCT).click();
        click(ADD_TO_CART);
        wait.until(ExpectedConditions.presenceOfElementLocated(BADGE));
    }

    /** 角标数字（加购后出现）。 */
    public String badgeText() {
        return labelOf(BADGE);
    }

    public void openCart() throws InterruptedException {
        click(CART_TAB);
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'My Cart'")));
        Thread.sleep(1000);
    }

    /** 购物车里是否还有商品（No Items 未出现）。 */
    public boolean cartHasItems() {
        // "No Items" 空态元素常驻源码（无商品时才 visible），按可见性判断
        return !isVisible(NO_ITEMS);
    }

    /** 删除购物车中的商品：同名还有 StaticText，只点按钮类型，删到按钮消失。 */
    public void removeItems() {
        By removeButton = AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeButton' AND name == 'Remove Item'");
        while (!all(removeButton).isEmpty()) {
            all(removeButton).get(0).click();
            wait.until(ExpectedConditions.invisibilityOfElementLocated(removeButton));
        }
    }

    /** 购物车是否为空态（No Items 可见）。 */
    public boolean cartIsEmpty() {
        return isVisible(NO_ITEMS);
    }
}
