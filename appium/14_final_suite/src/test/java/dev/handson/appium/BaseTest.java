package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.ios.IOSDriver;
import io.appium.java_client.ios.options.XCUITestOptions;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.annotations.AfterClass;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Parameters;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.Map;
import java.time.Duration;
import java.util.Map;

public abstract class BaseTest {

    public IOSDriver driver;
    public WebDriverWait wait;
    protected String bundleId;

    private static String setting(String key, String env, String fallback) {
        String value = System.getProperty(key);
        if (value != null && !value.isBlank()) {
            return value;
        }
        value = System.getenv(env);
        return value == null || value.isBlank() ? fallback : value;
    }

    @BeforeClass(alwaysRun = true)
    @Parameters({"appium.url", "device.udid", "device.name",
            "wda.localPort", "derived.dataPath", "bundle.id"})
    public void setUp(String appiumUrl, String udid, String deviceName,
                      String wdaPort, String derivedDataPath, String bundleId)
            throws MalformedURLException {
        this.bundleId = bundleId;

        XCUITestOptions options = new XCUITestOptions()
                .setPlatformName("iOS")
                .setDeviceName(deviceName)
                .setUdid(udid)
                .setPlatformVersion("26.5")
                .setAutomationName("XCUITest")
                .setBundleId(bundleId)
                .setNoReset(true)
                .setNewCommandTimeout(Duration.ofSeconds(180))
                .setWdaLaunchTimeout(Duration.ofSeconds(240))
                // 并行的关键：每个 session 独占一个 WDA 端口和一份构建产物
                .setWdaLocalPort(Integer.parseInt(wdaPort))
                .setDerivedDataPath(derivedDataPath);

        System.out.printf("[session] %s（wdaLocalPort=%s）%n", deviceName, wdaPort);
        driver = new IOSDriver(new URL(appiumUrl), options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(30));
        // noReset 会话会恢复上次退出时的页面（可能是 checkout/More），
        // 先清状态再启动，保证每个类都从目录页开始
        driver.executeScript("mobile: clearApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
    }


    protected boolean isVisible(By locator) {
        return !driver.findElements(locator).isEmpty()
                && driver.findElement(locator).isDisplayed();
    }

    /** 重置应用状态（clearApp + 重启到目录页）。 */
    protected void resetAppState() {
        driver.executeScript("mobile: clearApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
    }

    public WebElement waitForClickable(By locator) {
        return wait.until(ExpectedConditions.elementToBeClickable(locator));
    }

    @AfterClass(alwaysRun = true)
    public void tearDown() {
        if (driver != null) {
            driver.quit();
            System.out.println("Session 已关闭");
        }
    }
}
