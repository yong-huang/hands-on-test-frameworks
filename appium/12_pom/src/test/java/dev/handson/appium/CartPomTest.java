package dev.handson.appium;

import dev.handson.appium.pageobjects.ProductPage;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/** 购物车（POM 版）：角标与空态。 */
public class CartPomTest extends BaseTest {

    private ProductPage productPage;

    @BeforeClass(alwaysRun = true)
    public void initPage() {
        productPage = new ProductPage(driver, wait);
    }

    @Test
    public void addToCartShowsBadge() throws Exception {
        productPage.addFirstProductToCart();
        assertEquals(productPage.badgeText(), "1", "加购后角标应为 1");
        System.out.println("✅ 加购后角标=1");

        productPage.openCart();
        assertTrue(productPage.cartHasItems(), "购物车应有商品");
        System.out.println("✅ 购物车有商品");
    }

    @Test
    public void removeItemsReturnsToEmptyState() throws Exception {
        productPage.addFirstProductToCart();
        productPage.openCart();
        productPage.removeItems();
        Thread.sleep(1000);
        assertTrue(productPage.cartIsEmpty(), "删除后应为 No Items 空态");
        System.out.println("✅ 删除后回到 No Items 空态");
    }
}
