package dev.handson.appium.regression;

import dev.handson.appium.BaseTest;
import dev.handson.appium.pageobjects.CatalogPage;
import dev.handson.appium.pageobjects.ProductPage;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/** 回归组（核心）：目录累计、排序、角标、购物车保留与清理，5 条。 */
public class CoreRegressionTest extends BaseTest {

    private CatalogPage catalogPage;
    private ProductPage productPage;

    @BeforeMethod(alwaysRun = true)
    public void freshState() {
        resetAppState();
    }

    @BeforeClass(alwaysRun = true)
    public void initPages() {
        catalogPage = new CatalogPage(driver, wait);
        productPage = new ProductPage(driver, wait, bundleId);
    }

    @Test(groups = "regression")
    public void reg01CatalogAccumulatesAllProducts() {
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        assertTrue(actual.size() >= 20, "商品数应 ≥ 20，实际 " + actual.size());
        System.out.printf("✅ [reg] 目录累计 %d 件%n", actual.size());
    }

    @Test(groups = "regression")
    public void reg02DefaultOrderIsNameAscending() {
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.naturalOrder());
        assertEquals(actual, expected, "默认顺序应为名称升序");
        System.out.println("✅ [reg] 默认名称升序");
    }

    @Test(groups = "regression")
    public void reg03SortByNameDescendingReverses() {
        catalogPage.sortBy("Name - Descending");
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.reverseOrder());
        assertEquals(actual, expected, "降序应为精确反转");
        System.out.println("✅ [reg] 降序全序反转");
    }

    @Test(groups = "regression")
    public void reg04BadgeShowsOneAfterAdd() {
        productPage.addFirstProductToCart();
        assertEquals(productPage.badgeText(), "1", "加购后角标应为 1");
        System.out.println("✅ [reg] 角标=1");
    }

    @Test(groups = "regression")
    public void reg05CartKeepsItemAcrossNavigation() throws Exception {
        productPage.addFirstProductToCart();
        productPage.openCart();
        assertTrue(productPage.cartHasItems(), "购物车应保留商品");
        System.out.println("✅ [reg] 购物车保留商品");
    }

    @Test(groups = "regression")
    public void reg06RemoveItemsReturnsToEmptyState() throws Exception {
        productPage.addFirstProductToCart();
        productPage.openCart();
        productPage.removeItems();
        assertTrue(productPage.cartIsEmpty(), "删除后应为 No Items 空态");
        System.out.println("✅ [reg] 删除后空态");
    }
}
