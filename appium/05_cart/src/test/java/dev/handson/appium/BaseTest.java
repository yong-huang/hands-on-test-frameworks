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
import org.testng.annotations.BeforeMethod;

import java.net.MalformedURLException;
import java.net.URL;
import java.time.Duration;
import java.util.Map;

public abstract class BaseTest {

    protected IOSDriver driver;
    protected WebDriverWait wait;
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
    public void setUp() throws MalformedURLException {
        String appiumUrl = setting("appium.url", "APPIUM_URL", "http://127.0.0.1:4723/wd/hub");
        String deviceName = setting("device.name", "DEVICE_NAME", "iPhone 17");
        String platformVersion = setting("platform.version", "PLATFORM_VERSION", "26.5");
        bundleId = setting("bundle.id", "BUNDLE_ID", "com.saucelabs.mydemo.app.ios");

        XCUITestOptions options = new XCUITestOptions()
                .setPlatformName("iOS")
                .setDeviceName(deviceName)
                .setPlatformVersion(platformVersion)
                .setAutomationName("XCUITest")
                .setBundleId(bundleId)
                .setNoReset(true)
                .setNewCommandTimeout(Duration.ofSeconds(180))
                .setWdaLaunchTimeout(Duration.ofSeconds(240));

        System.out.printf("连接 Appium: %s%n", appiumUrl);
        System.out.printf("设备: %s / iOS %s%n", deviceName, platformVersion);
        driver = new IOSDriver(new URL(appiumUrl), options);
        wait = new WebDriverWait(driver, Duration.ofSeconds(30));
        System.out.printf("Session ID: %s%n", driver.getSessionId());
    }

    @BeforeMethod(alwaysRun = true)
    public void resetAppState() {
        driver.executeScript("mobile: clearApp", Map.of("bundleId", bundleId));
        driver.executeScript("mobile: launchApp", Map.of("bundleId", bundleId));
        wait.until(ExpectedConditions.visibilityOfElementLocated(
                AppiumBy.accessibilityId("Catalog-tab-item")));
    }

    protected boolean isVisible(By locator) {
        return !driver.findElements(locator).isEmpty()
                && driver.findElement(locator).isDisplayed();
    }

    protected WebElement waitForClickable(By locator) {
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
