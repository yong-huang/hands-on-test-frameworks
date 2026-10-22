package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * XPath 演示：只用于说明"能定位"和"该不该用"是两件事。
 * 不进入主套件；生产用例的定位纪律见 locator-notes.md。
 */
public class XPathDemoTest extends BaseTest {

    @Test
    public void xpathWorksButIsLastResort() {
        WebElement catalogTab = wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.xpath("//XCUIElementTypeButton[@name='Catalog-tab-item']")));

        Assert.assertTrue(catalogTab.isDisplayed());
        System.out.println("⚠️ XPath 演示：能定位，但遍历整棵 UI 树，只作最后手段");
    }
}
