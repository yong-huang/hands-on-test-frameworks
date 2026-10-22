package dev.handson.appium;

import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.time.Duration;

public class FirstSessionTest extends BaseTest {

    @Test
    public void appLaunchesToCatalog() {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(30));
        WebElement catalogTab = wait.until(
                ExpectedConditions.presenceOfElementLocated(By.id("Catalog-tab-item"))
        );

        Assert.assertTrue(catalogTab.isDisplayed(), "Catalog-tab-item 应该可见");
        System.out.println("找到 Catalog-tab-item，App 已启动");
    }
}
