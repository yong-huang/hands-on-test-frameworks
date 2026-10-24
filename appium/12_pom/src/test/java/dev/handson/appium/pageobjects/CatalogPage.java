package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;

import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

/** Catalog 页：商品列表滚动累计与排序菜单。 */
public class CatalogPage extends BasePage {

    private static final By PRODUCT_NAMES = AppiumBy.accessibilityId("Product Name");
    private static final By COLLECTION_VIEW = By.className("XCUIElementTypeCollectionView");
    private static final By SORT_BUTTON = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'Button'");

    public CatalogPage(io.appium.java_client.ios.IOSDriver driver,
                       org.openqa.selenium.support.ui.WebDriverWait wait) {
        super(driver, wait);
    }

    /** 当前可见商品名（cell 复用，一屏约 6 个）。 */
    public List<String> visibleNames() {
        return all(PRODUCT_NAMES).stream()
                .map(e -> e.getAttribute("label"))
                .toList();
    }

    /** 滚动累计全部商品，返回首次出现顺序（即列表全序）。 */
    public LinkedHashSet<String> accumulateAll() {
        LinkedHashSet<String> seen = new LinkedHashSet<>(visibleNames());
        int idle = 0;
        while (idle < 3) {
            var list = driver.findElement(COLLECTION_VIEW);
            driver.executeScript("mobile: scroll", Map.of(
                    "elementId", ((org.openqa.selenium.remote.RemoteWebElement) list).getId(),
                    "direction", "down"));
            int before = seen.size();
            seen.addAll(visibleNames());
            idle = seen.size() > before ? 0 : idle + 1;
        }
        return seen;
    }

    /** 打开排序菜单并选择一个选项（如 Name - Descending）。 */
    public void sortBy(String optionLabel) {
        click(SORT_BUTTON);
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Sort by:'")));
        click(AppiumBy.iOSNsPredicateString("label == '" + optionLabel + "'"));
        wait.until(ExpectedConditions.invisibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'Sort by:'")));
    }
}
