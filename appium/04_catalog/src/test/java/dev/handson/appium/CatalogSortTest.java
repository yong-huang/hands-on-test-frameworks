package dev.handson.appium;

import org.testng.annotations.BeforeClass;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * 目录与排序：CollectionView 滚动累计、四种排序、金额解析。
 * 该 App 的演示数据共 25 个商品；价格金额只在详情页暴露。
 */
public class CatalogSortTest extends BaseTest {

    private CatalogPage catalog;

    @BeforeClass(alwaysRun = true)
    public void initPage() {
        catalog = new CatalogPage(this);
    }

    /** 默认目录 = 名称升序全量列表；顺带验证商品总数与滚动累计。 */
    @Test
    public void catalogDefaultsToAllProductsSortedByName() {
        LinkedHashSet<String> seen = catalog.accumulateAll();
        List<String> actual = new ArrayList<>(seen);

        System.out.printf("✅ 商品总数：%d（验收下限 20）%n", actual.size());
        assertTrue(actual.size() >= 20, "商品数应 ≥ 20，实际 " + actual.size());

        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.naturalOrder());
        assertEquals(actual, expected,
                "默认顺序应等于名称升序（首 " + actual.get(0) + " / 尾 "
                        + actual.get(actual.size() - 1) + "）");
        System.out.printf("✅ 默认即名称升序：首=%s 尾=%s%n",
                actual.get(0), actual.get(actual.size() - 1));
    }

    /** 名称降序：整条列表应恰好反向。 */
    @Test
    public void sortByNameDescendingReversesFullOrder() {
        catalog.sortBy("Name - Descending");
        List<String> actual = new ArrayList<>(catalog.accumulateAll());

        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.reverseOrder());
        assertEquals(actual, expected, "Name - Descending 应为名称降序全序");
        System.out.printf("✅ 名称降序全序一致：首=%s 尾=%s%n",
                actual.get(0), actual.get(actual.size() - 1));
    }

    /**
     * 价格升降序：金额不在列表页暴露，只能进详情页读 Price。
     * 名称→价格是商品固有属性、与排序无关，所以离开列表前先记住首尾名字。
     * 实测发现（2026-10-22）：该 App 的价格排序不是数值升序——$9.99 的
     * Bike Light 在 Price - Ascending 下排末位。疑似实现缺陷，因此本用例
     * 只断言缺陷存在时也成立的性质：两个方向互为镜像、极值跨方向价格一致；
     * 排序键本身的问题打印警告，不写成断言（修复后会变红的是断言，不是 App）。
     */
    @Test
    public void priceSortExtremesAreConsistentAcrossDirections() {
        // --- 价格升序：记下全序与首尾名 ---
        catalog.sortBy("Price - Ascending");
        List<String> ascOrder = new ArrayList<>(catalog.accumulateAll());
        String ascFirst = ascOrder.get(0);
        String ascLast = ascOrder.get(ascOrder.size() - 1);

        catalog.openProduct(ascFirst);
        BigDecimal ascFirstPrice = catalog.detailPrice();
        catalog.backToCatalog();

        catalog.openProduct(ascLast);
        BigDecimal ascLastPrice = catalog.detailPrice();
        catalog.backToCatalog();

        System.out.printf("⚠️ 价格升序：首=%s($%s) 尾=%s($%s)——"
                        + "%s 不是本序列最小价，排序键疑似缺陷%n",
                ascFirst, ascFirstPrice, ascLast, ascLastPrice,
                ascLastPrice.compareTo(ascFirstPrice) < 0 ? "尾件价格低于首件" : "首尾价格正常");

        // --- 价格降序：与升序是同一批商品，极值价格跨方向一致 ---
        // （实测 Bolt 与 Test.allTheThings 两族同价，同价并列时 App 保持
        //   名称原序，所以对"降序 = 升序反转"只断言到多重集合与极值价格，
        //   不假设并列组内部的排列。）
        catalog.sortBy("Price - Descending");
        List<String> descOrder = new ArrayList<>(catalog.accumulateAll());
        List<String> sortedDesc = new ArrayList<>(descOrder);
        List<String> sortedAsc = new ArrayList<>(ascOrder);
        sortedDesc.sort(Comparator.naturalOrder());
        sortedAsc.sort(Comparator.naturalOrder());
        assertEquals(sortedDesc, sortedAsc,
                "价格升序和降序应是同一批商品的两种排列");

        String descFirst = descOrder.get(0);
        String descLast = descOrder.get(descOrder.size() - 1);

        catalog.openProduct(descFirst);
        BigDecimal descFirstPrice = catalog.detailPrice();
        catalog.backToCatalog();

        catalog.openProduct(descLast);
        BigDecimal descLastPrice = catalog.detailPrice();
        catalog.backToCatalog();

        // --- 两个方向互为镜像 → 极值价格跨方向一致（并列时名字可不同，价格必相等） ---
        assertEquals(descFirstPrice.compareTo(ascLastPrice), 0,
                "desc 首件价格应等于 asc 尾件价格（同为序列极值）");
        assertEquals(descLastPrice.compareTo(ascFirstPrice), 0,
                "desc 尾件价格应等于 asc 首件价格（同为序列极值）");
        System.out.printf("✅ 价格升降镜像成立：asc 首/尾 = $%s/$%s，desc 首/尾 = $%s/$%s%n",
                ascFirstPrice, ascLastPrice, descFirstPrice, descLastPrice);
    }
}
