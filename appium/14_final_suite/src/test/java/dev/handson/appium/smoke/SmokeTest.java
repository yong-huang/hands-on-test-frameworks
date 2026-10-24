package dev.handson.appium.smoke;

import dev.handson.appium.BaseTest;
import dev.handson.appium.pageobjects.CatalogPage;
import dev.handson.appium.pageobjects.LoginPage;
import dev.handson.appium.pageobjects.ProductPage;
import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/** 冒烟组（smoke）：登录、目录、购物车、后台、重置，8 条快速用例。 */
public class SmokeTest extends BaseTest {

    private CatalogPage catalogPage;
    private LoginPage loginPage;
    private ProductPage productPage;

    @BeforeMethod(alwaysRun = true)
    public void freshState() {
        resetAppState();
    }

    @BeforeClass(alwaysRun = true)
    public void initPages() {
        catalogPage = new CatalogPage(driver, wait);
        loginPage = new LoginPage(driver, wait);
        productPage = new ProductPage(driver, wait, bundleId);
    }

    @Test(groups = "smoke")
    public void smoke01LoginViaSuggestion() throws Exception {
        loginPage.loginViaMore();
        Thread.sleep(1500);
        assertTrue(loginPage.isLoggedIn(), "登录成功后 More 页应出现 LogOut");
        System.out.println("✅ [smoke] 建议登录成功");
    }

    @Test(groups = "smoke")
    public void smoke02CatalogListsAllProducts() {
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        assertTrue(actual.size() >= 20, "商品数应 ≥ 20，实际 " + actual.size());
        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.naturalOrder());
        assertEquals(actual, expected, "默认顺序应为名称升序");
        System.out.printf("✅ [smoke] 目录 %d 件商品，名称升序%n", actual.size());
    }

    @Test(groups = "smoke")
    public void smoke03SortByNameDescending() {
        catalogPage.sortBy("Name - Descending");
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.reverseOrder());
        assertEquals(actual, expected, "降序全序应精确反转");
        System.out.printf("✅ [smoke] 名称降序全序一致：%d 件%n", actual.size());
    }

    @Test(groups = "smoke")
    public void smoke04AddToCartShowsBadge() {
        productPage.addFirstProductToCart();
        assertEquals(productPage.badgeText(), "1", "加购后角标应为 1");
        System.out.println("✅ [smoke] 加购后角标=1");
    }

    @Test(groups = "smoke")
    public void smoke05CartKeepsItem() throws Exception {
        productPage.addFirstProductToCart();
        productPage.openCart();
        assertTrue(productPage.cartHasItems(), "购物车应有商品");
        System.out.println("✅ [smoke] 购物车保留商品");
    }

    @Test(groups = "smoke")
    public void smoke06RemoveItemsReturnsToEmptyState() throws Exception {
        productPage.addFirstProductToCart();
        productPage.openCart();
        productPage.removeItems();
        assertTrue(productPage.cartIsEmpty(), "删除后应为 No Items 空态");
        System.out.println("✅ [smoke] 删除后回到 No Items 空态");
    }

    @Test(groups = "smoke")
    public void smoke07BackgroundFiveSecondsStaysOnPage() throws Exception {
        driver.executeScript("mobile: backgroundApp", Map.of("appId", bundleId));
        Thread.sleep(5000);
        driver.activateApp(bundleId);
        Thread.sleep(1500);
        assertTrue(isVisible(AppiumBy.accessibilityId("Product Name")),
                "激活后应停留在目录页（Product Name 可见）");
        System.out.println("✅ [smoke] 后台 5 秒再激活，停留原页面");
    }

    @Test(groups = "smoke")
    public void smoke08ResetAppStateClearsBadge() throws Exception {
        productPage.addFirstProductToCart();
        assertEquals(productPage.badgeText(), "1", "加购后角标应为 1");

        for (int i = 0; i < 3; i++) {
            try {
                driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
                waitForClickable(AppiumBy.accessibilityId("ResetAppState-menu-item")).click();
                waitForClickable(AppiumBy.accessibilityId("RESET APP")).click();
                break;
            } catch (org.openqa.selenium.TimeoutException e) {
                driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
                Thread.sleep(800);
            }
        }

        // Reset App State 清空购物车：角标消失（避开 reset 后 tab 点击被吞的粘滞状态）
        driver.executeScript("mobile: terminateApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        productPage.waitBadgeGone(15);
        assertTrue(driver.findElements(AppiumBy.accessibilityId("Product Name")).size() > 0,
                "重置后应回到目录页");
        assertTrue(driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND name == '1'")).isEmpty(),
                "Reset App State 后角标应消失（购物车已清空）");
        System.out.println("✅ [smoke] Reset App State 清空购物车（角标消失）");
    }

}
