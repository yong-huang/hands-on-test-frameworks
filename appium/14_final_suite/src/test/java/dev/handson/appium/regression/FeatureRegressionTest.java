package dev.handson.appium.regression;

import dev.handson.appium.BaseTest;
import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.interactions.Pause;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.interactions.PointerInput;
import org.openqa.selenium.interactions.Sequence;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static org.testng.Assert.assertTrue;

/** 回归组（专项能力）：WebView、手势、生物识别，6 条。 */
public class FeatureRegressionTest extends BaseTest {

    private static final By CANVAS = AppiumBy.accessibilityId("DrawingBackground Icons");
    private static final By LAST_PRODUCT = AppiumBy.iOSNsPredicateString(
            "label == 'Test.allTheThings() T-Shirt - Yellow'");

    @BeforeClass(alwaysRun = true)
    public void init() {
        // 无共享状态
    }

    @Test(groups = "regression")
    public void reg11WebviewLoadsLocalPage() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Webview-menu-item")).click();
        Thread.sleep(1200);
        var field = driver.findElement(By.className("XCUIElementTypeTextField"));
        field.click();
        ((org.openqa.selenium.remote.RemoteWebElement) field).clear();
        field.sendKeys("http://127.0.0.1:8923/");
        Thread.sleep(400);
        driver.executeScript("mobile: keys", Map.of("keys", List.of("\uE004")));
        Thread.sleep(400);
        driver.findElement(AppiumBy.accessibilityId("Go To Site")).click();
        Thread.sleep(3000);
        boolean visible = !driver.findElements(AppiumBy.iOSNsPredicateString(
                "label == 'Hello WebView'")).isEmpty();
        assertTrue(visible, "本地页内容应在 native 树可见");
        System.out.println("✅ [reg] WebView 本地页加载（需 ./run_suite.sh 起本地服务）");
    }

    /** 从任意页面回到目录页：webview 先返回，再切 Catalog tab。 */
    private void ensureCatalog() throws Exception {
        // 无论当前在哪一屏（webview/绘图/完成页都没有 tab 栏），
        // 重启应用必回目录页，比逐页返回可靠
        driver.executeScript("mobile: terminateApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        Thread.sleep(800);
    }

    @Test(groups = "regression")
    public void reg12DrawPolylineLeavesInk() throws Exception {
        ensureCatalog();
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Drawing-menu-item")).click();
        Thread.sleep(1200);
        var canvas = driver.findElement(CANVAS);
        var r = canvas.getRect();
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");
        Sequence draw = new Sequence(finger, 0);
        int[][] pts = {{20, 30}, {50, 70}, {80, 20}};
        draw.addAction(finger.createPointerMove(Duration.ofMillis(0),
                PointerInput.Origin.viewport(),
                r.getX() + r.getWidth() * pts[0][0] / 100,
                r.getY() + r.getHeight() * pts[0][1] / 100));
        draw.addAction(finger.createPointerDown(PointerInput.MouseButton.LEFT.asArg()));
        for (int i = 1; i < pts.length; i++) {
            draw.addAction(finger.createPointerMove(Duration.ofMillis(250),
                    PointerInput.Origin.viewport(),
                    r.getX() + r.getWidth() * pts[i][0] / 100,
                    r.getY() + r.getHeight() * pts[i][1] / 100));
        }
        draw.addAction(finger.createPointerUp(PointerInput.MouseButton.LEFT.asArg()));
        driver.perform(List.of(draw));
        System.out.println("✅ [reg] 画布画折线（W3C Actions）");
    }

    @Test(groups = "regression")
    public void reg13LongPressDrawsDot() throws Exception {
        ensureCatalog();
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Drawing-menu-item")).click();
        Thread.sleep(1200);
        var canvas = driver.findElement(CANVAS);
        var r = canvas.getRect();
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");
        Sequence press = new Sequence(finger, 1);
        press.addAction(finger.createPointerMove(Duration.ofMillis(0),
                PointerInput.Origin.viewport(),
                r.getX() + r.getWidth() / 2, r.getY() + r.getHeight() / 2));
        press.addAction(finger.createPointerDown(PointerInput.MouseButton.LEFT.asArg()));
        press.addAction(new Pause(finger, Duration.ofMillis(1200)));
        press.addAction(finger.createPointerUp(PointerInput.MouseButton.LEFT.asArg()));
        driver.perform(List.of(press));
        System.out.println("✅ [reg] 长按画布出墨点");
    }

    @Test(groups = "regression")
    public void reg14SwipeReachesLastProduct() throws Exception {
        ensureCatalog();
        driver.findElement(AppiumBy.accessibilityId("Catalog-tab-item")).click();
        Thread.sleep(1200);
        int w = driver.manage().window().getSize().width;
        int h = driver.manage().window().getSize().height;
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");
        boolean found = false;
        for (int i = 0; i < 15 && !found; i++) {
            found = !driver.findElements(LAST_PRODUCT).isEmpty();
            if (found) break;
            Sequence swipe = new Sequence(finger, i);
            swipe.addAction(finger.createPointerMove(Duration.ofMillis(0),
                    PointerInput.Origin.viewport(), w / 2, (int) (h * 0.72)));
            swipe.addAction(finger.createPointerDown(PointerInput.MouseButton.LEFT.asArg()));
            swipe.addAction(finger.createPointerMove(Duration.ofMillis(500),
                    PointerInput.Origin.viewport(), w / 2, (int) (h * 0.22)));
            swipe.addAction(finger.createPointerUp(PointerInput.MouseButton.LEFT.asArg()));
            driver.perform(List.of(swipe));
            Thread.sleep(700);
        }
        assertTrue(found, "swipe 后应看到最后一件商品");
        System.out.println("✅ [reg] swipe 到达最后一件商品");
    }

    @Test(groups = "regression")
    public void reg15BiometricMatchTrueLogsIn() throws Exception {
        ensureCatalog();
        driver.executeScript("mobile: enrollBiometric", Map.of("enroll", true));
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Biometrics-menu-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("SwitchUnselected Icons")).click();
        Thread.sleep(800);
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Login Button")).click();
        Thread.sleep(1500);
        driver.findElement(AppiumBy.accessibilityId("FaceId Icons")).click();
        Thread.sleep(1500);
        driver.executeScript("mobile: sendBiometricMatch",
                Map.of("type", "faceId", "match", true));
        Thread.sleep(2000);
        assertTrue(driver.getPageSource().contains("Enter a shipping address"),
                "match=true 应登录并进入结算地址页");
        System.out.println("✅ [reg] Face ID match=true 登录成功");
    }

    @Test(groups = "regression")
    public void reg16BiometricMatchFalseStaysOnLogin() throws Exception {
        ensureCatalog();
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Biometrics-menu-item")).click();
        Thread.sleep(1000);
        // 幂等开开关：上一位测试可能已开（图标名拨后不变），未选才点
        var off = driver.findElements(AppiumBy.accessibilityId("SwitchUnselected Icons"));
        if (!off.isEmpty()) {
            off.get(0).click();
            Thread.sleep(600);
        }
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        Thread.sleep(1000);
        driver.findElement(AppiumBy.accessibilityId("Login Button")).click();
        Thread.sleep(1500);
        driver.findElement(AppiumBy.accessibilityId("FaceId Icons")).click();
        Thread.sleep(1500);
        driver.executeScript("mobile: sendBiometricMatch",
                Map.of("type", "faceId", "match", false));
        Thread.sleep(1500);
        assertTrue(!driver.findElements(AppiumBy.iOSNsPredicateString(
                        "label == 'Select a username from the list below'")).isEmpty(),
                "match=false 应停留登录页");
        System.out.println("✅ [reg] Face ID match=false 停留登录页");
    }
}
