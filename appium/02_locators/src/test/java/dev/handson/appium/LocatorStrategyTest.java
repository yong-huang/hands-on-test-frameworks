package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.util.List;

public class LocatorStrategyTest extends BaseTest {

    @BeforeClass(alwaysRun = true)
    public void seedCart() {
        resetAppState();
        addFirstProductToCart();
        System.out.println("已重置 App 状态并加入 1 件商品（角标 = 1）");
    }

    @BeforeMethod(alwaysRun = true)
    public void ensureCatalog() {
        goToCatalog();
    }

    @Test
    public void catalogTabLocators() {
        WebElement byAccessibilityId = wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        WebElement byPredicate = wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("name == 'Catalog-tab-item'")));

        assertVisible(byAccessibilityId, "Catalog tab（accessibility id）");
        assertVisible(byPredicate, "Catalog tab（predicate）");
        System.out.println("✅ Catalog tab：accessibility id / predicate");
    }

    @Test
    public void loginButtonLocators() {
        try {
            driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
            WebElement byAccessibilityId = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    AppiumBy.accessibilityId("Login Button")));
            WebElement byPredicate = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    AppiumBy.iOSNsPredicateString("name == 'Login Button'")));

            assertVisible(byAccessibilityId, "Login Button（accessibility id）");
            assertVisible(byPredicate, "Login Button（predicate）");
            System.out.println("✅ Login Button：accessibility id / predicate（容器名稳定，子按钮 id 不可靠）");
        } finally {
            goToCatalog();
        }
    }

    @Test
    public void productNameLocators() {
        List<WebElement> byAccessibilityId = driver.findElements(
                AppiumBy.accessibilityId("Product Name"));
        Assert.assertEquals(byAccessibilityId.size(), 6,
                "Catalog 应渲染 6 个商品，Product Name 不是唯一 id");

        WebElement blackBackpack = wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Sauce Labs Backpack - Black'")));
        Assert.assertEquals(blackBackpack.getText(), "Sauce Labs Backpack - Black");
        System.out.println("✅ 商品名：id 命中 6 个（有歧义）/ predicate 锁定 Black");
    }

    @Test
    public void productPriceLocators() {
        List<WebElement> byAccessibilityId = driver.findElements(
                AppiumBy.accessibilityId("Product Price"));
        Assert.assertEquals(byAccessibilityId.size(), 6,
                "Catalog 的 Product Price 也不是唯一 id");

        WebElement firstPrice = wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSClassChain(
                        "**/XCUIElementTypeStaticText[`name == \"Product Price\"`][1]")));
        Assert.assertTrue(firstPrice.isDisplayed(), "class chain 应能锁定第一个价格元素");

        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        try {
            WebElement detailPrice = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    AppiumBy.accessibilityId("Price")));
            WebElement detailPriceByPredicate = driver.findElement(
                    AppiumBy.iOSNsPredicateString("name == 'Price'"));

            Assert.assertEquals(detailPrice.getText(), "$ 29.99");
            Assert.assertEquals(detailPriceByPredicate.getText(), "$ 29.99");
            System.out.println("✅ 价格：列表 id/class chain + 详情页 id/predicate（$ 29.99）");
        } finally {
            goToCatalog();
        }
    }

    @Test
    public void cartBadgeLocators() {
        WebElement byPredicate = wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.iOSNsPredicateString(
                        "name == '1' AND type == 'XCUIElementTypeStaticText'")));
        WebElement byClassChain = wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.iOSClassChain("**/XCUIElementTypeStaticText[`name == \"1\"`]")));

        Assert.assertEquals(byPredicate.getText(), "1");
        Assert.assertEquals(byClassChain.getText(), "1");
        System.out.println("✅ 购物车角标：predicate / class chain（visible 属性不可靠，断言存在与文本）");
    }

    @Test
    public void checkoutButtonLocators() {
        driver.findElement(AppiumBy.accessibilityId("Cart-tab-item")).click();
        try {
            WebElement byAccessibilityId = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    AppiumBy.accessibilityId("ProceedToCheckout")));
            WebElement byPredicate = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    AppiumBy.iOSNsPredicateString("name == 'ProceedToCheckout'")));

            assertVisible(byAccessibilityId, "结算按钮（accessibility id）");
            assertVisible(byPredicate, "结算按钮（predicate）");
            System.out.println("✅ 结算按钮：accessibility id / predicate");
        } finally {
            goToCatalog();
        }
    }

    private void assertVisible(WebElement element, String label) {
        Assert.assertTrue(element.isDisplayed(), label + " 应该可见");
    }
}
