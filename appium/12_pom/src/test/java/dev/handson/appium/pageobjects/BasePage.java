package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.util.List;

/**
 * 所有页面对象的基类：统一显式等待与动作封装。
 * 分层边界：Page 只做"动作 + 状态查询"，不做业务断言；
 * 定位器（By）全部留在各 Page 内部，测试层永远接触不到。
 */
public abstract class BasePage {

    protected final io.appium.java_client.ios.IOSDriver driver;
    protected final WebDriverWait wait;

    protected BasePage(io.appium.java_client.ios.IOSDriver driver, WebDriverWait wait) {
        this.driver = driver;
        this.wait = wait;
    }

    /** 元素存在即可（不要求 visible，应对该 App 大量 visible=false 的元素）。 */
    protected WebElement presenceOf(By locator) {
        return wait.until(ExpectedConditions.presenceOfElementLocated(locator));
    }

    protected WebElement visibilityOf(By locator) {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
    }

    protected WebElement clickable(By locator) {
        return wait.until(ExpectedConditions.elementToBeClickable(locator));
    }

    protected void click(By locator) {
        clickable(locator).click();
    }

    protected void clickAll(By locator) {
        for (WebElement el : driver.findElements(locator)) {
            el.click();
        }
    }

    protected void type(By locator, String text) {
        WebElement field = visibilityOf(locator);
        field.click();
        ((org.openqa.selenium.remote.RemoteWebElement) field).clear();
        if (!text.isEmpty()) {
            field.sendKeys(text);
        }
    }

    protected String labelOf(By locator) {
        return presenceOf(locator).getAttribute("label");
    }

    protected boolean exists(By locator) {
        return !driver.findElements(locator).isEmpty();
    }

    /** 存在且可见（该 App 大量元素存在但 visible=false，语义不同）。 */
    protected boolean isVisible(By locator) {
        return exists(locator) && driver.findElement(locator).isDisplayed();
    }

    protected List<WebElement> all(By locator) {
        return driver.findElements(locator);
    }

    /** 通用 Tab 切换（tab 按钮的 accessibility id 形如 xxx-tab-item）。 */
    protected void openTab(String tabName) {
        click(AppiumBy.accessibilityId(tabName + "-tab-item"));
    }
}
