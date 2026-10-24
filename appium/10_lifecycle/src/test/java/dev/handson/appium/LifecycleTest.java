package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.annotations.Test;

import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * 应用生命周期与状态恢复：background / activate / terminate / launch /
 * queryAppState / Reset App State。
 * 实测事实（2026-10-23，App 2.3.0 + iOS 26.5 模拟器）：
 * - queryAppState：前台=4、后台=3、terminate 后=1（未运行）；
 * - 后台 5 秒再激活，停留原页面；
 * - 购物车不跨 terminate 保留（重启后清空），登录态跨 terminate 保留；
 * - 该 App 未注册自定义 URL scheme，深链接不作为断言（仅 README 说明）。
 */
public class LifecycleTest extends BaseTest {

    private static final int FOREGROUND = 4;
    private static final int BACKGROUND = 3;
    private static final int NOT_RUNNING = 1;

    private int queryAppState() {
        return ((Number) driver.executeScript("mobile: queryAppState",
                Map.of("bundleId", bundleId))).intValue();
    }

    private void addOneToCart() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        Thread.sleep(1200);
        waitForClickable(AppiumBy.accessibilityId("AddToCart")).click();
        wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "type == 'XCUIElementTypeStaticText' AND name == '1'")));
    }

    private void openCart() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Cart-tab-item")).click();
        Thread.sleep(1200);
    }

    private boolean cartHasItems() {
        String src = driver.getPageSource();
        return src.contains("Items") && !src.contains("No Items");
    }

    private void loginViaMore() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("Login Button")).click();
        Thread.sleep(1500);
        driver.findElements(AppiumBy.accessibilityId("bob@example.com"))
                .stream().findFirst().ifPresent(WebElement::click);
        Thread.sleep(800);
        var logins = driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeButton' AND name == 'Login'"));
        logins.get(logins.size() - 1).click();
        Thread.sleep(2000);
    }

    /** 生命周期一：后台 5 秒再激活，停留原页面。 */
    @Test
    public void backgroundThenActivateStaysOnSamePage() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        Thread.sleep(1500);
        assertTrue(hasAddToCartLocator(), "应已进入商品详情页");

        // 不带 duration：立即后台并保持，由测试控制"后台 5 秒"的节奏
        driver.executeScript("mobile: backgroundApp", Map.of("appId", bundleId));
        Thread.sleep(5000);
        assertEquals(queryAppState(), BACKGROUND,
                "后台期间 queryAppState 应为 3");

        driver.activateApp(bundleId);
        Thread.sleep(1500);
        assertEquals(queryAppState(), FOREGROUND, "激活后应回到前台（4）");
        assertTrue(hasAddToCartLocator(), "激活后应停留在商品详情页");
        System.out.println("✅ 后台 5 秒再激活：queryAppState 3→4，停留原页面");
    }

    /** 生命周期二：queryAppState 贯穿 terminate / launch 的状态值。 */
    @Test
    public void queryAppStateTracksTerminateAndLaunch() {
        assertEquals(queryAppState(), FOREGROUND, "前台应为 4");

        driver.terminateApp(bundleId);
        assertEquals(queryAppState(), NOT_RUNNING,
                "terminate 后应为 1（未运行）");

        driver.activateApp(bundleId);
        wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        assertEquals(queryAppState(), FOREGROUND, "重新启动后应为 4");
        System.out.println("✅ queryAppState 全程 4 → 1 → 4");
    }

    /**
     * 生命周期三：terminate 后重启，购物车清空但登录态保留——
     * 两个事实都是实测行为，断言按实际写。
     */
    @Test
    public void terminateRelaunchClearsCartButKeepsLogin() throws Exception {
        addOneToCart();
        loginViaMore();

        driver.terminateApp(bundleId);
        Thread.sleep(1500);
        driver.activateApp(bundleId);
        Thread.sleep(2000);

        openCart();
        assertTrue(!cartHasItems(), "实测购物车不跨 terminate 保留（重启后清空）");
        System.out.println("✅ terminate 后购物车清空（该 App 未持久化购物车）");

        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1200);
        assertTrue(driver.getPageSource().contains("LogOut-menu-item"),
                "实测登录态跨 terminate 保留（More 页 LogOut 可见）");
        System.out.println("✅ 登录态保留：More 页 LogOut 可见");
    }

    /** 生命周期四：Reset App State 清空购物车（带确认框的菜单入口）。 */
    @Test
    public void resetAppStateEmptiesCart() throws Exception {
        addOneToCart();
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("ResetAppState-menu-item")).click();
        waitForClickable(AppiumBy.accessibilityId("RESET APP")).click();

        // 07 教训：reset 后 tab 栏粘滞，重启应用再验证
        driver.executeScript("mobile: terminateApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        Thread.sleep(2500);

        openCart();
        assertTrue(driver.getPageSource().contains("No Items"),
                "Reset App State 后购物车应为 No Items 空态");
        System.out.println("✅ Reset App State 后购物车回到 No Items 空态");
    }

    private boolean hasAddToCartLocator() {
        By addToCart = AppiumBy.accessibilityId("AddToCart");
        wait.until(ExpectedConditions.presenceOfElementLocated(addToCart));
        return !driver.findElements(addToCart).isEmpty();
    }
}
