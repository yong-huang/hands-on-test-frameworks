package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;

import java.util.Map;

/** 结算漏斗：地址表单、支付表单、Review 与完成页。 */
public class CheckoutPage extends BasePage {

    private static final By PROCEED = AppiumBy.accessibilityId("ProceedToCheckout");
    private static final By URL_FIELD = By.className("XCUIElementTypeTextField");
    private static final By GO_TO_SITE = AppiumBy.accessibilityId("Go To Site");

    public CheckoutPage(io.appium.java_client.ios.IOSDriver driver,
                        org.openqa.selenium.support.ui.WebDriverWait wait) {
        super(driver, wait);
    }

    /** 打开 Webview 演示页并加载本地 URL（用于 context 演示）。 */
    public void openWebviewDemo(String url) throws InterruptedException {
        click(AppiumBy.accessibilityId("More-tab-item"));
        click(AppiumBy.accessibilityId("Webview-menu-item"));
        type(URL_FIELD, url);
        Thread.sleep(400);
        driver.executeScript("mobile: keys",
                Map.of("keys", java.util.List.of("\uE004")));
        Thread.sleep(400);
        click(GO_TO_SITE);
        Thread.sleep(2500);
    }

    /** Web 内容在 native 树的可见性断言数据。 */
    public boolean nativeTextVisible(String label) {
        return !driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND label == '" + label + "'")).isEmpty();
    }

    /** 结算入口是否可点（购物车页）。 */
    public void proceedToCheckout() {
        click(PROCEED);
    }
}
