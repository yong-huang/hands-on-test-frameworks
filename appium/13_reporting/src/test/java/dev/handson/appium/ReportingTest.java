package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.testng.annotations.Test;

import java.util.LinkedHashSet;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * 报告与失败诊断演示：2 条成功 + 1 条故意失败。
 * 故意失败的用例（断言一个必然错误的期望值）用于触发诊断监听器，
 * 生成截图、page source、syslog 与录屏四类证据。
 */
public class ReportingTest extends BaseTest {

    @Test
    public void catalogListsAllProductsSortedByName() {
        LinkedHashSet<String> seen = new LinkedHashSet<>(allProductNames());
        int idle = 0;
        while (idle < 3) {
            var list = driver.findElement(
                    AppiumBy.className("XCUIElementTypeCollectionView"));
            driver.executeScript("mobile: scroll", java.util.Map.of(
                    "elementId", ((org.openqa.selenium.remote.RemoteWebElement) list).getId(),
                    "direction", "down"));
            int before = seen.size();
            seen.addAll(allProductNames());
            idle = seen.size() > before ? 0 : idle + 1;
        }
        List<String> actual = new ArrayList<>(seen);
        List<String> expected = new ArrayList<>(actual);
        expected.sort(Comparator.naturalOrder());
        assertEquals(actual, expected, "默认顺序应为名称升序");
        System.out.printf("✅ 目录 %d 件商品，默认名称升序%n", actual.size());
    }

    private List<String> allProductNames() {
        return driver.findElements(AppiumBy.accessibilityId("Product Name"))
                .stream().map(e -> e.getAttribute("label")).toList();
    }

    /** 故意失败演示：断言加购后角标为 2（实际是 1），触发证据链采集。 */
    @Test
    public void deliberatelyFailingDemo() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        Thread.sleep(1200);
        driver.findElement(AppiumBy.accessibilityId("AddToCart")).click();
        Thread.sleep(800);
        String badge = driver.findElement(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND name == '1'")).getAttribute("name");
        // 故意断言错误值：本用例的价值在失败后的证据链，不在通过
        assertEquals(badge, "2", "故意失败：演示诊断监听器的证据采集");
    }

    @Test
    public void loginSuggestionSucceeds() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Login Button")).click();
        Thread.sleep(1500);
        driver.findElement(AppiumBy.accessibilityId("bob@example.com")).click();
        Thread.sleep(800);
        var logins = driver.findElements(AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeButton' AND name == 'Login'"));
        logins.get(logins.size() - 1).click();
        Thread.sleep(1500);
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        assertTrue(driver.getPageSource().contains("LogOut-menu-item"),
                "登录成功后 More 页应出现 LogOut");
        System.out.println("✅ 建议登录成功：More 页 LogOut 可见");
    }
}
