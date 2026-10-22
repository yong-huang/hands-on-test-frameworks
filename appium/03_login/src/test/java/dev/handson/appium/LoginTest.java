package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertTrue;

public class LoginTest extends BaseTest {

    @DataProvider(name = "missingFieldCases")
    public Object[][] missingFieldCases() {
        return new Object[][]{
                {null, "Username is required"},
                {"bob@example.com", "Password is required"}
        };
    }

    @Test
    public void successfulLoginShowsCatalogAndLogout() {
        openLogin();
        loginPage.selectSuggestion("alice@example.com");
        loginPage.submit();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        openMore();
        assertTrue(isVisible(AppiumBy.accessibilityId("LogOut-menu-item")),
                "登录成功后 More 页应出现 LogOut-menu-item");
        System.out.println("✅ 成功登录：Catalog 可见，More 页显示 LogOut-menu-item");
    }

    @Test
    public void emailSuggestionFillsBothFields() {
        openLogin();
        loginPage.selectSuggestion("bob@example.com");
        assertEquals(loginPage.username(), "bob@example.com");
        assertFalse(loginPage.password() == null || loginPage.password().isBlank(),
                "点击用户名后密码应自动填充");
        assertFalse(loginPage.isKeyboardVisible(), "用户名建议应避免弹出键盘");
        System.out.println("✅ 邮箱自动填充：用户名和密码均已填充，键盘未弹出");
    }

    @Test(dataProvider = "missingFieldCases")
    public void missingFieldShowsValidation(String suggestion, String expectedMessage) {
        openLogin();
        if (suggestion != null) {
            loginPage.selectSuggestion(suggestion);
            loginPage.clearPassword();
            loginPage.submitWithKeyboardCoveringButton();
        } else {
            loginPage.submit();
        }
        assertEquals(loginPage.alertTitle(), "Validation Error!");
        assertEquals(loginPage.alertMessage(), expectedMessage);
        loginPage.acceptAlert();
        System.out.printf("✅ 空字段校验：%s → Validation Error! / %s%n",
                suggestion == null ? "空用户名" : "空密码", expectedMessage);
    }

    @Test
    public void logoutReturnsToLoginForm() {
        openLogin();
        loginPage.selectSuggestion("bob@example.com");
        loginPage.submit();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        openMore();
        waitForClickable(AppiumBy.accessibilityId("LogOut-menu-item")).click();
        loginPage.waitUntilLoaded();
        assertTrue(loginPage.isDisplayed(), "LogOut 后应回到登录表单");

        resetAppState();
        openMore();
        assertTrue(isVisible(AppiumBy.accessibilityId("Login Button")),
                "清理登录态后应重新看到 Login Button");
        System.out.println("⚠️ Demo App 的 LogOut 未清除登录态；clearApp 后 Login Button 重新可见");
    }
}
