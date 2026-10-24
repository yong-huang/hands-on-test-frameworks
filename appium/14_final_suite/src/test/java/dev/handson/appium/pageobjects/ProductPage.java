package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.List;
import java.util.Map;

/** 商品详情页与购物车（Component Object：详情和购物车共享角标逻辑）。 */
public class ProductPage extends BasePage {

    private static final By FIRST_PRODUCT = AppiumBy.accessibilityId("Product Name");
    private static final By ADD_TO_CART = AppiumBy.accessibilityId("AddToCart");
    private static final By BADGE = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeStaticText' AND name == '1'");
    private static final By CART_TAB = AppiumBy.accessibilityId("Cart-tab-item");
    private static final By REMOVE_ITEM = AppiumBy.accessibilityId("Remove Item");
    private static final By NO_ITEMS = AppiumBy.accessibilityId("No Items");

    private final String bundleId;

    public ProductPage(io.appium.java_client.ios.IOSDriver driver,
                       org.openqa.selenium.support.ui.WebDriverWait wait,
                       String bundleId) {
        super(driver, wait);
        this.bundleId = bundleId;
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

    /** 等待角标消失（Reset App State 清空购物车的可见信号）。 */
    public void waitBadgeGone(int seconds) throws InterruptedException {
        long deadline = System.currentTimeMillis() + seconds * 1000L;
        while (System.currentTimeMillis() < deadline) {
            if (driver.findElements(BADGE).isEmpty()) {
                return;
            }
            Thread.sleep(500);
        }
    }

    public void openCart() throws InterruptedException {
        // 先直接点 Cart tab；被吞时 clearApp + launch 兜底（必回目录页）再点
        for (int i = 0; i < 4; i++) {
            try {
                click(CART_TAB);
                WebDriverWait shortWait = new WebDriverWait(driver, Duration.ofSeconds(15));
                shortWait.until(ExpectedConditions.visibilityOfElementLocated(
                        AppiumBy.iOSNsPredicateString("label == 'My Cart'")));
                Thread.sleep(800);
                return;
            } catch (Exception e) {
                System.out.println("（打开购物车第 " + (i + 1) + " 次未生效，clearApp 兜底）");
                driver.executeScript("mobile: clearApp", Map.of("bundleId", bundleId));
                driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
                Thread.sleep(3000);
            }
        }
        try {
            java.io.File shot = driver.getScreenshotAs(OutputType.FILE);
            java.nio.file.Files.copy(shot.toPath(),
                    java.nio.file.Path.of("target", "opencart-failure.png"),
                    java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            String src = driver.getPageSource();
            java.nio.file.Files.writeString(
                    java.nio.file.Path.of("target", "opencart-failure.html"), src);
        } catch (Exception ignore) { }
        throw new org.openqa.selenium.NoSuchElementException("4 次尝试后 My Cart 仍未出现");
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
