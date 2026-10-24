package dev.handson.appium.flows;

import dev.handson.appium.BaseTest;
import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.remote.RemoteWebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

/**
 * 结算全链路的可复用编排器（页面定位 + 步骤动作 + 每步日志）。
 * 实测事实（2026-10-22，App 2.3.0）：
 * - 登录态可能跨 clearApp 残留：点 Proceed 后可能有登录门、也可能直达表单；
 * - 地址与支付表单的预填值不被认账，必须逐字段清空重填，否则弹校验 alert；
 * - 输入框全部 name=null，只能按 TextField 类型 + 索引定位（顺序即表单顺序）；
 * - Review 总价 = 购物车总价 + $5.99 运费，不与购物车总价相等。
 */
public class CheckoutFlow {

    /** Review 页固定收取的运费（实测 $35.98 = $29.99 + $5.99）。 */
    public static final BigDecimal DELIVERY_FEE = new BigDecimal("5.99");

    private static final By TEXT_FIELDS = By.className("XCUIElementTypeTextField");
    private static final By ALERT_OK = AppiumBy.accessibilityId("OK");

    private final BaseTest owner;
    private int stepNo = 0;

    public CheckoutFlow(BaseTest owner) {
        this.owner = owner;
    }

    private void log(String message) {
        stepNo++;
        System.out.printf("▸ 步骤 %d：%s%n", stepNo, message);
    }

    /** 目录第一件商品加购一件。 */
    public void addItemToCart() {
        owner.driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("AddToCart")));
        owner.driver.findElement(AppiumBy.accessibilityId("AddToCart")).click();
        owner.wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeStaticText' AND name == '1'")));
        log("已加购 1 件到购物车");
    }

    /** 进购物车 → 读总价 → 点 Proceed To Checkout 穿过登录门。返回购物车总价。 */
    public BigDecimal openCheckout() throws Exception {
        owner.driver.findElement(AppiumBy.accessibilityId("Cart-tab-item")).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Total:'")));
        BigDecimal total = cartTotal();
        log("进入购物车页，总价 $" + total);
        owner.waitForClickable(AppiumBy.accessibilityId("ProceedToCheckout")).click();
        for (int i = 0; i < 20; i++) {
            if (!owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                    "label == 'bob@example.com'")).isEmpty()) {
                log("登录门出现：点用户名建议自动填充后 Login");
                owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                                "label == 'bob@example.com'")).get(0).click();
                Thread.sleep(800);
                List<WebElement> logins = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeButton' AND name == 'Login'"));
                logins.get(logins.size() - 1).click();
                Thread.sleep(2000);
                waitShippingForm();
                return total;
            }
            if (!owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                    "label == 'Enter a shipping address'")).isEmpty()) {
                log("登录态残留：直达 Checkout 表单");
                waitShippingForm();
                return total;
            }
            Thread.sleep(500);
        }
        throw new IllegalStateException("点 Proceed 后既没有登录门也没有地址表单");
    }

    private void waitShippingForm() {
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Enter a shipping address'")));
    }

    /**
     * 清空重填地址表单的必填字段（索引按表单顺序：
     * 0 Full Name、1 Address Line 1、3 City、4 Zip Code、6 Country）。
     * 传入空串表示故意留空，用于触发校验。
     */
    public void fillShipping(String fullName, String address, String city,
                             String zip, String country) {
        typeIntoField(0, fullName);
        typeIntoField(1, address);
        typeIntoField(3, city);
        typeIntoField(4, zip);
        typeIntoField(6, country);
        log("地址表单已填写（姓名=" + (fullName.isEmpty() ? "空" : fullName) + "）");
    }

    /** 点 To Payment。返回是否弹了校验 alert（true=被拦下，可读 alertMessage）。 */
    public boolean toPayment() {
        owner.waitForClickable(AppiumBy.accessibilityId("To Payment")).click();
        for (int i = 0; i < 20; i++) {
            if (!owner.driver.findElements(ALERT_OK).isEmpty()) {
                log("地址校验 alert 弹出");
                return true;
            }
            if (!owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                    "label == 'Enter a payment method'")).isEmpty()) {
                log("通过地址校验，进入支付页");
                return false;
            }
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("等待支付页被中断", e);
            }
        }
        throw new IllegalStateException("点 To Payment 后既没有 alert 也没有支付页");
    }

    /**
     * 清空重填支付表单（索引 0 卡姓名、1 卡号、2 有效期、3 安全码）。
     * cardNumber 传空串用于触发 Review 步的校验。
     */
    public void fillPayment(String cardName, String cardNumber,
                            String expiry, String securityCode) {
        typeIntoField(0, cardName);
        typeIntoField(1, cardNumber);
        typeIntoField(2, expiry);
        typeIntoField(3, securityCode);
        log("支付表单已填写（卡号=" + (cardNumber.isEmpty() ? "空" : "****") + "）");
    }

    /**
     * 点 Review Order。支付字段没填好时 App 弹 Value looks invalid.，
     * 返回是否弹了 alert，供负向用例断言；正向流程会自动重试一次。
     */
    public boolean reviewOrder() {
        owner.waitForClickable(AppiumBy.accessibilityId("Review Order")).click();
        owner.wait.until(d -> !owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                        "label == 'Review your order'")).isEmpty()
                || !owner.driver.findElements(ALERT_OK).isEmpty());
        boolean alertShown = !owner.driver.findElements(ALERT_OK).isEmpty();
        if (alertShown) {
            log("Review 弹校验 alert");
        } else {
            log("进入 Review Order 页");
        }
        return alertShown;
    }

    /** 读 alert 正文（标题固定为 Validation Error!）。 */
    public String alertMessage() {
        List<WebElement> texts = owner.driver.findElements(By.className("XCUIElementTypeStaticText"));
        for (WebElement t : texts) {
            String label = t.getAttribute("label");
            if (label != null && !"Validation Error!".equals(label)) {
                return label;
            }
        }
        throw new NoSuchElementException("页面上没有 alert 正文");
    }

    public void dismissAlert() {
        owner.waitForClickable(ALERT_OK).click();
    }

    /** Review 页总价（含 $5.99 运费，label 形如 $35.98）。 */
    public BigDecimal reviewTotal() {
        List<WebElement> texts = owner.driver.findElements(By.className("XCUIElementTypeStaticText"));
        for (WebElement t : texts) {
            String label = t.getAttribute("label");
            if (label != null && label.matches("\\$[0-9.]+")) {
                return new BigDecimal(label.replaceAll("[^0-9.]", ""));
            }
        }
        throw new NoSuchElementException("Review 页没找到总价");
    }

    /** 点 Place Order 并等 Checkout Complete 页出现。 */
    public void placeOrder() {
        owner.waitForClickable(AppiumBy.accessibilityId("Place Order")).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("CheckoutComplete-screen")));
        log("下单成功，出现 CheckoutComplete-screen");
    }

    /** 勾选 billing same as shipping（图标按钮，勾选后名字翻转）。 */
    public String billingCheckboxName() {
        List<WebElement> cb = owner.driver.findElements(AppiumBy.iOSNsPredicateString(
                "name == 'CheckBoxUnselected Icons' OR name == 'CheckBoxSelected Icons'"));
        if (cb.isEmpty()) {
            throw new NoSuchElementException("没找到 billing 勾选框");
        }
        return cb.get(0).getAttribute("name");
    }

    public void toggleBillingCheckbox() {
        owner.waitForClickable(AppiumBy.iOSNsPredicateString(
                "name == 'CheckBoxUnselected Icons' OR name == 'CheckBoxSelected Icons'")).click();
    }

    /** 购物车总价（label 形如 $29.99，无空格）。 */
    public BigDecimal cartTotal() {
        List<WebElement> texts = owner.driver.findElements(By.className("XCUIElementTypeStaticText"));
        for (WebElement t : texts) {
            String label = t.getAttribute("label");
            if (label != null && label.matches("\\$[0-9.]+")) {
                return new BigDecimal(label.replaceAll("[^0-9.]", ""));
            }
        }
        throw new NoSuchElementException("购物车里没找到总价");
    }

    private void typeIntoField(int index, String value) {
        WebElement field = owner.driver.findElements(TEXT_FIELDS).get(index);
        field.click();
        ((RemoteWebElement) field).clear();
        if (!value.isEmpty()) {
            field.sendKeys(value);
        }
        owner.driver.executeScript("mobile: keys", Map.of("keys", List.of("\uE004")));
    }
}
