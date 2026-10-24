package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.remote.RemoteWebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.annotations.Test;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * WebView 混合应用：context 轮询、双向切换、native fallback。
 * 实测事实（2026-10-23，App 2.3.0 + iOS 26.5 模拟器）：
 * - Webview 菜单页默认 URL 是 https://www.website.com（本网络不可达），
 *   URL 输入框可改写为本地页；
 * - 加载本地页后 WKWebView 正常渲染，但 getContextHandles() 始终只返回
 *   NATIVE_APP——该构建的 WKWebView 未开 inspectable，context 切换不可用；
 * - Web 内容在 native 树里以 StaticText 暴露，可作为 fallback 断言；
 * - webview 页没有 tab 栏，返回靠左上角返回箭头。
 */
public class WebViewTest extends BaseTest {

    private static final String LOCAL_URL = "http://127.0.0.1:8923/";
    private static final By URL_FIELD = By.className("XCUIElementTypeTextField");
    private static final By GO_TO_SITE = AppiumBy.accessibilityId("Go To Site");
    /** 返回箭头无任何标注（name/label 为 null），且 x/y 不能用于谓词——按 rect 过滤。 */

    /** 菜单页基线：URL 输入框与 Go To Site 按钮存在，只有 NATIVE context。 */
    @Test
    public void webviewMenuExposesUrlFieldAndGoButton() {
        openWebviewMenu();

        WebElement urlField = driver.findElement(URL_FIELD);
        assertEquals(urlField.getAttribute("value"), "https://www.website.com",
                "URL 输入框默认值应为演示占位域名");
        assertTrue(isVisible(GO_TO_SITE), "Go To Site 按钮应可见");
        Set<String> handles = driver.getContextHandles();
        assertTrue(handles.contains("NATIVE_APP"), "初始应包含 NATIVE_APP context");
        System.out.println("✅ 菜单页基线：URL 输入框 + Go To Site，contexts=" + handles);
    }

    /**
     * 核心链路：输入本地 URL 加载 → 轮询 WEBVIEW context → 内容断言 → 返回。
     * 实测该构建的 WKWebView 未开 inspectable，轮询拿不到 WEBVIEW context；
     * 测试不假装切换成功：拿到 context 就切并断言标题，拿不到就打警告，
     * 两条路径都以 native 树的内容断言收尾（未来 App 开启 inspectable 时
     * 本用例自动升级为真 context 切换）。
     */
    @Test
    public void webviewLoadsLocalPageAndReturnsToCatalog() throws Exception {
        openWebviewMenu();
        typeLocalUrlAndGo();

        String webviewContext = pollForWebviewContext(30);
        if (webviewContext != null) {
            driver.context(webviewContext);
            System.out.println("✅ 切入 " + webviewContext + "，title=" + driver.getTitle());
            assertEquals(driver.getTitle(), "WebView Demo", "WEBVIEW 页标题应为本地页标题");
            driver.context("NATIVE_APP");
        } else {
            System.out.println("⚠️ 30 秒内未出现 WEBVIEW context——"
                    + "该构建 WKWebView 未开 inspectable，context 切换不可用（如实记录）");
        }

        // native fallback 断言：Web 内容以原生元素形式暴露
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                nativeText("Hello WebView")));
        assertTrue(isVisible(nativeText("这是本地测试页，用于 Appium context 切换实验")),
                "本地页正文应在 native 树可见");
        System.out.println("✅ Web 内容断言（native 树）：Hello WebView 可见");

        returnToCatalog();
        System.out.println("✅ 已返回 Catalog");
    }

    /** 本地页重载一次（再次 Go To Site），内容仍可断言。 */
    @Test
    public void reloadLocalPageKeepsContentAccessible() throws Exception {
        openWebviewMenu();
        typeLocalUrlAndGo();
        pollForWebviewContext(10);

        // 再走一遍菜单流程，模拟二次加载
        tapBack();
        Thread.sleep(800);
        typeLocalUrlAndGo();
        pollForWebviewContext(10);

        wait.until(ExpectedConditions.visibilityOfElementLocated(
                nativeText("Hello WebView")));
        System.out.println("✅ 二次加载后内容仍可断言：Hello WebView 可见");

        returnToCatalog();
    }

    // ---------- 辅助 ----------

    private void openWebviewMenu() {
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("Webview-menu-item")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(GO_TO_SITE));
    }

    private void typeLocalUrlAndGo() throws Exception {
        WebElement urlField = driver.findElement(URL_FIELD);
        urlField.click();
        ((RemoteWebElement) urlField).clear();
        urlField.sendKeys(LOCAL_URL);
        Thread.sleep(400);
        driver.executeScript("mobile: keys", Map.of("keys", List.of("\uE004")));
        Thread.sleep(400);
        waitForClickable(GO_TO_SITE).click();
    }

    /** 轮询 context handles，返回 WEBVIEW context 名；超时返回 null。 */
    private String pollForWebviewContext(int seconds) throws Exception {
        String found = null;
        for (int i = 0; i < seconds; i++) {
            Thread.sleep(1000);
            Set<String> handles = driver.getContextHandles();
            if (i % 5 == 0) {
                System.out.println("  … 轮询 " + (i + 1) + "s contexts=" + handles);
            }
            found = handles.stream()
                    .filter(c -> c.contains("WEBVIEW"))
                    .findFirst().orElse(null);
            if (found != null) {
                break;
            }
        }
        return found;
    }

    private By nativeText(String label) {
        return AppiumBy.iOSNsPredicateString(
                "type == 'XCUIElementTypeStaticText' AND label == '" + label + "'");
    }

    /** 点左上角返回箭头：遍历按钮按 rect 特征过滤（左上角、y<150）。 */
    private void tapBack() {
        List<WebElement> buttons = driver.findElements(By.className("XCUIElementTypeButton"));
        for (WebElement b : buttons) {
            var r = ((RemoteWebElement) b).getRect();
            if (r.getX() <= 10 && r.getY() < 150) {
                b.click();
                return;
            }
        }
        throw new org.openqa.selenium.NoSuchElementException("左上角没找到返回箭头");
    }

    /** 从 webview 页回主流程：返回箭头 → Catalog tab。 */
    private void returnToCatalog() throws Exception {
        tapBack();
        Thread.sleep(800);
        // 返回箭头只退到菜单页，URL 输入框会自动聚焦弹键盘（实测吞掉 tab 点击）；
        // 再按一次返回到 More 页，焦点随导航离开，键盘自然消失
        if (!driver.findElements(URL_FIELD).isEmpty()) {
            tapBack();
            Thread.sleep(600);
        }
        // 离开 WebView 后可达性树可能短暂陈旧：等目录页的商品元素，
        // 30 秒没等到就重切一次 tab 再等（实测一次重试内必现）
        for (int i = 0; i < 2; i++) {
            try {
                new WebDriverWait(driver, Duration.ofSeconds(20)).until(
                        ExpectedConditions.presenceOfElementLocated(
                                AppiumBy.accessibilityId("Product Name")));
                return;
            } catch (org.openqa.selenium.TimeoutException e) {
                System.out.println("（返回 Catalog 后商品列表第 " + (i + 1) + " 次未出现，重切 tab）");
                driver.findElement(AppiumBy.accessibilityId("Catalog-tab-item")).click();
            }
        }
        throw new AssertionError("返回 Catalog 后商品列表始终未出现");
    }
}
