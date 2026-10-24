package dev.handson.appium.pageobjects;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;

import java.util.List;

/** More 页的登录表单（建议列表自动填充 + Login 按钮）。 */
public class LoginPage extends BasePage {

    private static final By LOGIN_BUTTON = AppiumBy.accessibilityId("Login Button");
    private static final By SUGGESTION = AppiumBy.accessibilityId("bob@example.com");
    private static final By SUBMIT = AppiumBy.iOSNsPredicateString(
            "type == 'XCUIElementTypeButton' AND name == 'Login'");
    private static final By LOG_OUT = AppiumBy.accessibilityId("LogOut-menu-item");

    public LoginPage(io.appium.java_client.ios.IOSDriver driver,
                     org.openqa.selenium.support.ui.WebDriverWait wait) {
        super(driver, wait);
    }

    /** 完整登录旅程：More → Login 表单 → 建议自动填充 → 提交。 */
    public void loginViaMore() throws Exception {
        click(AppiumBy.accessibilityId("More-tab-item"));
        Thread.sleep(1000);
        click(LOGIN_BUTTON);
        wait.until(ExpectedConditions.visibilityOfElementLocated(SUGGESTION));
        click(SUGGESTION);
        List<WebElement> logins = driver.findElements(SUBMIT);
        logins.get(logins.size() - 1).click();
    }

    /** 登录是否成功：More 页出现 LogOut 菜单项。 */
    public boolean isLoggedIn() {
        openMore();
        return exists(LOG_OUT);
    }

    private void openMore() {
        click(AppiumBy.accessibilityId("More-tab-item"));
        wait.until(ExpectedConditions.visibilityOfElementLocated(LOG_OUT));
    }
}
