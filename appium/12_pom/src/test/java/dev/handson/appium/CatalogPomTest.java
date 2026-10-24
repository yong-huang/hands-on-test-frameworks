package dev.handson.appium;

import dev.handson.appium.pageobjects.CatalogPage;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/** 目录与排序（POM 版）：滚动累计与全序断言。 */
public class CatalogPomTest extends BaseTest {

    private CatalogPage catalogPage;

    @BeforeClass(alwaysRun = true)
    public void initPage() {
        catalogPage = new CatalogPage(driver, wait);
    }

    @Test
    public void catalogListsAllProductsSortedByName() {
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());
        assertTrue(actual.size() >= 20, "商品数应 ≥ 20，实际 " + actual.size());

        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.naturalOrder());
        assertEquals(actual, expected, "默认顺序应为名称升序");
        System.out.printf("✅ 目录 %d 件商品，默认名称升序%n", actual.size());
    }

    @Test
    public void sortByNameDescendingReversesFullOrder() {
        catalogPage.sortBy("Name - Descending");
        List<String> actual = new ArrayList<>(catalogPage.accumulateAll());

        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.reverseOrder());
        assertEquals(actual, expected, "Name - Descending 应为名称降序全序");
        System.out.printf("✅ 名称降序全序一致：%d 件%n", actual.size());
    }
}
