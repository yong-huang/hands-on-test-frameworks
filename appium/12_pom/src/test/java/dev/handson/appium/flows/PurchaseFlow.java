package dev.handson.appium.flows;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.remote.RemoteWebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.WebDriverException;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * 跨页业务流（Flow 层）：组合多个 Page 的编排器，
 * 每个动作一个方法、每个方法打一行日志，业务断言留在测试层。
 */
public class PurchaseFlow {

    private static final By URL_FIELD = By.className("XCUIElementTypeTextField");

    private final io.appium.java_client.ios.IOSDriver driver;
    private final org.openqa.selenium.support.ui.WebDriverWait wait;
    private int stepNo = 0;

    public PurchaseFlow(io.appium.java_client.ios.IOSDriver driver,
                        org.openqa.selenium.support.ui.WebDriverWait wait) {
        this.driver = driver;
        this.wait = wait;
    }

    private void log(String message) {
        stepNo++;
        System.out.printf("▸ 步骤 %d：%s%n", stepNo, message);
    }

    /** 详情页加购一件。 */
    public void addItemToCart() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("AddToCart")));
        driver.findElement(AppiumBy.accessibilityId("AddToCart")).click();
        log("详情页加购一件");
    }

    /** 进购物车并点结算，穿过登录门（有建议登录，无建议直达表单）。 */
    public void openCheckout() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Cart-tab-item")).click();
        Thread.sleep(1200);
        driver.findElement(AppiumBy.accessibilityId("ProceedToCheckout")).click();
        for (int i = 0; i < 20; i++) {
            if (!driver.findElements(AppiumBy.accessibilityId("bob@example.com")).isEmpty()) {
                log("登录门出现，建议自动填充后 Login");
                driver.findElements(AppiumBy.accessibilityId("bob@example.com")).get(0).click();
                Thread.sleep(800);
                var logins = driver.findElements(AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeButton' AND name == 'Login'"));
                logins.get(logins.size() - 1).click();
                Thread.sleep(2000);
                waitShippingForm();
                return;
            }
            if (!driver.findElements(AppiumBy.iOSNsPredicateString(
                    "label == 'Enter a shipping address'")).isEmpty()) {
                log("登录态残留，直达表单");
                waitShippingForm();
                return;
            }
            Thread.sleep(500);
        }
        throw new IllegalStateException("点 Proceed 后既没有登录门也没有地址表单");
    }

    private void waitShippingForm() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Enter a shipping address'")));
    }

    /** 填地址并进支付页（预填值不被认账，逐字段清空重填）。 */
    public void fillShipping(String fullName, String address, String city,
                             String zip, String country) throws Exception {
        typeAt(0, fullName);
        typeAt(1, address);
        typeAt(3, city);
        typeAt(4, zip);
        typeAt(6, country);
        driver.findElement(AppiumBy.accessibilityId("To Payment")).click();
        Thread.sleep(1200);
        log("地址已填并通过校验");
    }

    /** 填支付表单并进 Review。 */
    public void fillPaymentAndReview(String cardName, String cardNumber,
                                     String expiry, String securityCode) throws Exception {
        typeAt(0, cardName);
        typeAt(1, cardNumber);
        typeAt(2, expiry);
        typeAt(3, securityCode);
        driver.findElement(AppiumBy.accessibilityId("Review Order")).click();
        Thread.sleep(1500);
        wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.accessibilityId("Place Order")));
        log("支付已填，Review 页就绪");
    }

    /** 下单并等完成页。 */
    public void placeOrder() {
        driver.findElement(AppiumBy.accessibilityId("Place Order")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("CheckoutComplete-screen")));
        log("下单成功，CheckoutComplete-screen 出现");
    }

    private void typeAt(int index, String value) throws Exception {
        WebElement field = driver.findElements(
                By.className("XCUIElementTypeTextField")).get(index);
        field.click();
        ((RemoteWebElement) field).clear();
        if (!value.isEmpty()) {
            field.sendKeys(value);
        }
        try {
            driver.executeScript("mobile: keys",
                    Map.of("keys", List.of("\uE004")));
        } catch (WebDriverException ignore) {
            // 无键盘时 Tab 可能失败，不影响后续字段定位
        }
        Thread.sleep(400);
    }
}
