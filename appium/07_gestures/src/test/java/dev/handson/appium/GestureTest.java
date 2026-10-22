package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Pause;
import org.openqa.selenium.interactions.PointerInput;
import org.openqa.selenium.interactions.Sequence;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.annotations.Test;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.util.List;
import java.util.Map;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * 手势与滚动：W3C Actions 画布签名、长按、swipe、Reset App State。
 * 坐标一律基于元素 rect 的相对百分比，不写死设备像素。
 * 实测事实（2026-10-23，App 2.3.0）：
 * - Drawing 画布是 DrawingBackground Icons（x=16 y=201 w=361 h=402）；
 * - Save 无任何可见反馈，且首次触发系统照片权限弹窗（会吞掉后续所有点击），
 *   需要提前 simctl privacy grant photos；
 * - 长按 Header / 商品都不会触发任何交互（规划中的"长按重置"不存在，
 *   长按改为在画布上按出墨点演示），Reset App State 走 More 页菜单。
 */
public class GestureTest extends BaseTest {

    private static final By CANVAS = AppiumBy.accessibilityId("DrawingBackground Icons");
    private static final By LAST_PRODUCT = AppiumBy.iOSNsPredicateString(
            "label == 'Test.allTheThings() T-Shirt - Yellow'");

    /** 手势一：W3C Actions 在画布画折线，画布区域出现墨迹。 */
    @Test
    public void drawPolylineLeavesInkOnCanvas() throws IOException, InterruptedException {
        openDrawing();
        File baseline = screenshot();

        WebElement canvas = driver.findElement(CANVAS);
        org.openqa.selenium.Rectangle r = canvas.getRect();
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");
        Sequence draw = new Sequence(finger, 0);
        int[][] pts = {{20, 30}, {50, 70}, {80, 20}, {50, 50}};
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

        File after = screenshot();
        long ink = diffPixels(canvas, baseline, after);
        System.out.printf("✅ 画布墨迹像素变化：%d%n", ink);
        assertTrue(ink > 500, "画折线后画布区域应有墨迹（变化像素 " + ink + "）");

        // Save 无可见反馈（实测），断言点击后没有错误 alert
        driver.findElement(AppiumBy.accessibilityId("SaveButton Icons")).click();
        Thread.sleep(500);
        List<WebElement> alerts = driver.findElements(By.className("XCUIElementTypeAlert"));
        assertTrue(alerts.isEmpty(), "Save 后不应有错误 alert");
        System.out.println("✅ Save 已点击（该 App 无保存成功反馈，实测无 alert）");
    }

    /** 手势二：长按画布按出墨点，Clear 后画布复原。 */
    @Test
    public void longPressDrawsDotAndClearRestores() throws IOException, InterruptedException {
        openDrawing();
        File baseline = screenshot();

        WebElement canvas = driver.findElement(CANVAS);
        org.openqa.selenium.Rectangle r = canvas.getRect();
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");
        Sequence press = new Sequence(finger, 1);
        press.addAction(finger.createPointerMove(Duration.ofMillis(0),
                PointerInput.Origin.viewport(),
                r.getX() + r.getWidth() / 2, r.getY() + r.getHeight() / 2));
        press.addAction(finger.createPointerDown(PointerInput.MouseButton.LEFT.asArg()));
        press.addAction(new Pause(finger, Duration.ofMillis(1200)));
        press.addAction(finger.createPointerUp(PointerInput.MouseButton.LEFT.asArg()));
        driver.perform(List.of(press));

        File after = screenshot();
        long ink = diffPixels(canvas, baseline, after);
        System.out.printf("✅ 长按墨点像素变化：%d%n", ink);
        assertTrue(ink > 10, "长按后画布中心应有墨点（变化像素 " + ink + "）");

        driver.findElement(AppiumBy.accessibilityId("ClearButton Icons")).click();
        Thread.sleep(800);
        File cleared = screenshot();
        long restored = diffPixels(canvas, baseline, cleared);
        System.out.printf("✅ Clear 后残留差异像素：%d%n", restored);
        assertTrue(restored < ink / 10,
                "Clear 后画布应复原（残留 " + restored + "，墨迹 " + ink + "）");
    }

    /** 手势三：W3C swipe 把目录滑到最后一件商品。 */
    @Test
    public void swipeReachesLastCatalogProduct() throws InterruptedException {
        int w = driver.manage().window().getSize().width;
        int h = driver.manage().window().getSize().height;
        int x = w / 2;
        PointerInput finger = new PointerInput(PointerInput.Kind.TOUCH, "finger");

        boolean found = false;
        for (int i = 0; i < 15 && !found; i++) {
            found = !driver.findElements(LAST_PRODUCT).isEmpty();
            if (found) {
                break;
            }
            Sequence swipe = new Sequence(finger, i);
            swipe.addAction(finger.createPointerMove(Duration.ofMillis(0),
                    PointerInput.Origin.viewport(), x, (int) (h * 0.72)));
            swipe.addAction(finger.createPointerDown(PointerInput.MouseButton.LEFT.asArg()));
            swipe.addAction(finger.createPointerMove(Duration.ofMillis(500),
                    PointerInput.Origin.viewport(), x, (int) (h * 0.22)));
            swipe.addAction(finger.createPointerUp(PointerInput.MouseButton.LEFT.asArg()));
            driver.perform(List.of(swipe));
            Thread.sleep(700);
        }
        assertTrue(found, "滑动后应能看到最后一件商品 Test.allTheThings() T-Shirt - Yellow");
        System.out.println("✅ swipe 到达目录最后一件商品");
    }

    /** 手势四（菜单操作）：Reset App State 后购物车回空态。 */
    @Test
    public void resetAppStateEmptiesCart() {
        // 先加购一件，让"重置"有东西可清
        driver.findElement(AppiumBy.accessibilityId("Product Name")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("AddToCart")));
        driver.findElement(AppiumBy.accessibilityId("AddToCart")).click();

        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("ResetAppState-menu-item")).click();
        WebElement dialog = wait.until(ExpectedConditions
                .visibilityOfElementLocated(By.className("XCUIElementTypeAlert")));
        assertEquals(dialog.getAttribute("name"), "Reset App State",
                "应弹出 Reset App State 确认框");
        System.out.println("✅ 确认框出现：Are you sure you want to reset the app state");

        waitForClickable(AppiumBy.accessibilityId("RESET APP")).click();
        // 实测 RESET APP 后 tab 栏 visible=false 且停在 More 页（粘滞状态），
        // 重启应用绕开，干净回到 Catalog
        driver.executeScript("mobile: terminateApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        // 重启后可能恢复到任意主页面；重启后 'Products' 文本的 presence 不可靠
        //（实测三次点击都"未见"但应用正常），真正的断言在购物车空态
        wait.until(ExpectedConditions.presenceOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
        driver.findElement(AppiumBy.accessibilityId("Cart-tab-item")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.iOSNsPredicateString("label == 'No Items'")));
        System.out.println("✅ 重置后购物车回到 No Items 空态");
    }

    private void openDrawing() throws InterruptedException {
        // resetAppState 后首次点击可能被吞，点 + 验证 + 重试最多 3 次
        for (int i = 0; i < 3; i++) {
            try {
                driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
                waitForClickable(AppiumBy.accessibilityId("Drawing-menu-item")).click();
                // DrawingBackground 的 visible 标志不稳定（实测 visible=false 也正常可画），
                // 等存在即可，坐标交互不受影响
                WebDriverWait shortWait = new WebDriverWait(driver, Duration.ofSeconds(8));
                shortWait.until(ExpectedConditions.presenceOfElementLocated(CANVAS));
                return;
            } catch (org.openqa.selenium.TimeoutException e) {
                try {
                    java.io.File shot = driver.getScreenshotAs(OutputType.FILE);
                    java.nio.file.Files.copy(shot.toPath(),
                            java.nio.file.Path.of("/tmp/p7-retry-" + i + ".png"),
                            java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                    String src = driver.getPageSource();
                    System.out.println("（第 " + (i + 1) + " 次未生效：source 含 Drawing-menu="
                            + src.contains("Drawing-menu-item") + " 含 DrawingBackground="
                            + src.contains("DrawingBackground") + "，截图 /tmp/p7-retry-" + i + ".png）");
                } catch (Exception ignore) { }
            }
        }
        throw new AssertionError("3 次尝试后 Drawing 画布仍未出现");
    }

    private File screenshot() throws IOException {
        File shot = driver.getScreenshotAs(OutputType.FILE);
        File kept = File.createTempFile("gesture", ".png");
        java.nio.file.Files.copy(shot.toPath(), kept.toPath(),
                StandardCopyOption.REPLACE_EXISTING);
        return kept;
    }

    /** 画布区域内两帧截图的差异像素数（截图为 2x 视网膜，按比例换算）。 */
    private long diffPixels(WebElement canvas, File before, File after) throws IOException {
        BufferedImage bi = ImageIO.read(before);
        BufferedImage ai = ImageIO.read(after);
        org.openqa.selenium.Rectangle r = canvas.getRect();
        double scale = (double) bi.getWidth() / driver.manage().window().getSize().width;
        int x0 = (int) (r.getX() * scale);
        int y0 = (int) (r.getY() * scale);
        int x1 = (int) ((r.getX() + r.getWidth()) * scale);
        int y1 = (int) ((r.getY() + r.getHeight()) * scale);
        long diff = 0;
        for (int y = y0; y < Math.min(y1, bi.getHeight()); y++) {
            for (int x = x0; x < Math.min(x1, bi.getWidth()); x++) {
                int p1 = bi.getRGB(x, y);
                int p2 = ai.getRGB(x, y);
                int d = Math.abs(((p1 >> 16) & 0xFF) - ((p2 >> 16) & 0xFF))
                        + Math.abs(((p1 >> 8) & 0xFF) - ((p2 >> 8) & 0xFF))
                        + Math.abs((p1 & 0xFF) - (p2 & 0xFF));
                if (d > 90) {
                    diff++;
                }
            }
        }
        return diff;
    }
}
