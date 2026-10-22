package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.math.BigDecimal;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

/**
 * Catalog 页面与商品详情页的页面对象。
 * 实测事实（2026-10-22，App 2.3.0）：
 * - 排序图标无障碍标注缺失，只能按 type + name=='Button' + 导航栏位置定位；
 * - 排序菜单四个选项是 XCUIElementTypeStaticText，label 即选项文案；
 * - 列表页 Product Price 不暴露金额，金额只在详情页 Price 元素（"$ 15.99"）；
 * - 详情页没有返回按钮，回列表靠底部 Catalog tab；
 * - 进入详情或切换 tab 后，排序态重置为默认（名称升序）。
 */
public class CatalogPage {

    private static final By PRODUCT_NAMES = AppiumBy.accessibilityId("Product Name");
    private static final By SORT_BUTTON = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'Button'");
    private static final By DETAIL_PRICE = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeStaticText' AND name == 'Price'");

    private final BaseTest owner;

    public CatalogPage(BaseTest owner) {
        this.owner = owner;
    }

    /** 点导航栏右上角的排序图标，打开 Sort by: 菜单。 */
    public void openSortMenu() {
        owner.waitForClickable(SORT_BUTTON).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Sort by:'")));
    }

    /** 在菜单里点一个选项（Name - Descending / Price - Ascending 等），菜单自动关闭。 */
    public void sortBy(String optionLabel) {
        openSortMenu();
        owner.waitForClickable(AppiumBy.iOSNsPredicateString(
                        "label == '" + optionLabel + "'"))
                .click();
        owner.wait.until(ExpectedConditions.invisibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Sort by:'")));
    }

    /** 当前可见商品名（cell 复用，iOS 一屏只渲染约 6 个）。 */
    public List<String> visibleNames() {
        return owner.driver.findElements(PRODUCT_NAMES).stream()
                .map(e -> e.getAttribute("label"))
                .toList();
    }

    /** 向下滚动一屏；返回 false 表示到底（这一屏没有出现新商品）。 */
    public boolean scrollOneDown(LinkedHashSet<String> seen) {
        WebElement list = owner.driver.findElement(
                By.className("XCUIElementTypeCollectionView"));
        owner.driver.executeScript("mobile: scroll",
                Map.of("elementId",
                        ((org.openqa.selenium.remote.RemoteWebElement) list).getId(),
                        "direction", "down"));
        int before = seen.size();
        seen.addAll(visibleNames());
        return seen.size() > before;
    }

    /** 从当前页开始滚动累计全部商品，返回首次出现顺序（即列表全序）。 */
    public LinkedHashSet<String> accumulateAll() {
        LinkedHashSet<String> seen = new LinkedHashSet<>(visibleNames());
        int idle = 0;
        while (idle < 3) {
            boolean grew = scrollOneDown(seen);
            idle = grew ? 0 : idle + 1;
        }
        return seen;
    }

    /** 滚回列表顶部：向上滚动直到连续 3 次画面不再变化。 */
    public void scrollToTop() {
        int stable = 0;
        String prev = String.join("|", visibleNames());
        while (stable < 3) {
            WebElement list = owner.driver.findElement(
                    By.className("XCUIElementTypeCollectionView"));
            owner.driver.executeScript("mobile: scroll",
                    Map.of("elementId",
                            ((org.openqa.selenium.remote.RemoteWebElement) list).getId(),
                            "direction", "up"));
            String cur = String.join("|", visibleNames());
            if (cur.equals(prev)) {
                stable++;
            } else {
                stable = 0;
                prev = cur;
            }
        }
    }

    /**
     * 滚动直到目标商品可见并点它，进入详情页。
     * 用于排序态重置后重新定位列表尾部的商品。
     * 单次滚动可能落在已看过的一屏（回弹或惯性停住），连续 3 次无新增才判定到底。
     */
    public void openProduct(String productLabel) {
        scrollToTop();
        LinkedHashSet<String> seen = new LinkedHashSet<>(visibleNames());
        int idle = 0;
        while (!seen.contains(productLabel)) {
            if (!scrollOneDown(seen)) {
                if (++idle >= 3) {
                    throw new NoSuchElementException("连续 3 次滚动无新增，未找到商品: " + productLabel);
                }
            } else {
                idle = 0;
            }
        }
        owner.driver.findElement(AppiumBy.iOSNsPredicateString(
                        "label == '" + productLabel + "'"))
                .click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(DETAIL_PRICE));
    }

    /** 读详情页价格并解析成 BigDecimal（label 形如 "$ 15.99"）。 */
    public BigDecimal detailPrice() {
        String raw = owner.wait.until(ExpectedConditions.visibilityOfElementLocated(
                        DETAIL_PRICE))
                .getAttribute("label");
        return new BigDecimal(raw.replaceAll("[^0-9.]", ""));
    }

    /** 从详情页回列表（详情页没有返回按钮，用底部 tab；排序态会重置）。 */
    public void backToCatalog() {
        owner.driver.findElement(AppiumBy.accessibilityId("Catalog-tab-item")).click();
        owner.wait.until(ExpectedConditions.visibilityOfElementLocated(PRODUCT_NAMES));
    }
}
