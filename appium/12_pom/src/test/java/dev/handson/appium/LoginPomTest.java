package dev.handson.appium;

import dev.handson.appium.pageobjects.LoginPage;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import static org.testng.Assert.assertTrue;

/** 登录（POM 版）：测试层只有业务断言，没有定位器。 */
public class LoginPomTest extends BaseTest {

    private LoginPage loginPage;

    @BeforeClass(alwaysRun = true)
    public void initPage() {
        loginPage = new LoginPage(driver, wait);
    }

    @Test
    public void suggestionLoginSucceeds() throws Exception {
        loginPage.loginViaMore();
        Thread.sleep(1500);
        assertTrue(loginPage.isLoggedIn(), "登录成功后 More 页应出现 LogOut");
        System.out.println("✅ 建议登录成功：More 页 LogOut 可见");
    }
}
