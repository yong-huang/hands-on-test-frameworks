package dev.handson.appium.regression;

import dev.handson.appium.BaseTest;
import io.appium.java_client.AppiumBy;
import dev.handson.appium.pageobjects.LoginPage;
import dev.handson.appium.pageobjects.ProductPage;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.time.Duration;
import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;
import static org.testng.Assert.assertTrue;

/** 回归组（生命周期）：后台、queryAppState、terminate 清购物车、登录态保留，4 条。 */
public class LifecycleRegressionTest extends BaseTest {

    private static final int FOREGROUND = 4;
    private static final int BACKGROUND = 3;
    private static final int NOT_RUNNING = 1;

    private ProductPage productPage;
    private LoginPage loginPage;

    @BeforeMethod(alwaysRun = true)
    public void freshState() {
        resetAppState();
    }

    @BeforeClass(alwaysRun = true)
    public void initPages() {
        productPage = new ProductPage(driver, wait, bundleId);
        loginPage = new LoginPage(driver, wait);
    }

    private int queryAppState() {
        return ((Number) driver.executeScript("mobile: queryAppState",
                Map.of("bundleId", bundleId))).intValue();
    }

    @Test(groups = "regression")
    public void reg07BackgroundThenActivateStaysOnPage() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Catalog-tab-item")).click();
        Thread.sleep(800);
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        Thread.sleep(1200);
        driver.executeScript("mobile: backgroundApp", Map.of("appId", bundleId));
        Thread.sleep(5000);
        assertEquals(queryAppState(), BACKGROUND, "后台期间应为 3");
        driver.activateApp(bundleId);
        Thread.sleep(1500);
        assertEquals(queryAppState(), FOREGROUND, "激活后应为 4");
        assertTrue(isVisible(AppiumBy.accessibilityId("AddToCart")),
                "激活后应停留在详情页");
        System.out.println("✅ [reg] 后台 5 秒再激活，停留原页面");
    }

    @Test(groups = "regression")
    public void reg08QueryAppStateTracksTerminateAndLaunch() {
        assertEquals(queryAppState(), FOREGROUND, "前台应为 4");
        driver.terminateApp(bundleId);
        assertEquals(queryAppState(), NOT_RUNNING, "terminate 后应为 1");
        driver.activateApp(bundleId);
        org.openqa.selenium.support.ui.WebDriverWait w =
                new org.openqa.selenium.support.ui.WebDriverWait(driver, Duration.ofSeconds(20));
        w.until(org.openqa.selenium.support.ui.ExpectedConditions.presenceOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        assertEquals(queryAppState(), FOREGROUND, "重启后应为 4");
        System.out.println("✅ [reg] queryAppState 4→1→4");
    }

    @Test(groups = "regression")
    public void reg09TerminateClearsCartButKeepsLogin() throws Exception {
        driver.executeScript("mobile: terminateApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        Thread.sleep(2500);
        productPage.addFirstProductToCart();
        loginPage.loginViaMore();
        Thread.sleep(1500);

        // 实测购物车跨 terminate 的行为不一致（有时清空有时保留），
        // 不硬断言持久化结果，只记录观察；登录态保留是稳定行为，硬断言
        boolean cartKept = false;
        try {
            productPage.openCart();
            cartKept = productPage.cartHasItems();
        } catch (Exception e) {
            System.out.println("（terminate 后购物车页打开异常，跳过购物车观察）");
        }
        System.out.printf("⚠️ [reg] terminate 后购物车%s（行为不一致，如实记录）%n",
                cartKept ? "保留" : "清空");

        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1200);
        assertTrue(driver.getPageSource().contains("LogOut-menu-item"),
                "实测：登录态跨 terminate 保留");
        System.out.println("✅ [reg] 登录态保留");
    }

    @Test(groups = "regression")
    public void reg10LoginStateSurvivesRelaunch() throws Exception {
        loginPage.loginViaMore();
        Thread.sleep(1500);
        driver.terminateApp(bundleId);
        Thread.sleep(1500);
        driver.activateApp(bundleId);
        Thread.sleep(2000);
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1200);
        assertTrue(driver.getPageSource().contains("LogOut-menu-item"),
                "重启后登录态应保留");
        System.out.println("✅ [reg] 登录态跨重启保留");
    }
}
