package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import io.appium.java_client.ios.IOSDriver;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.remote.RemoteWebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.util.List;
import java.util.Map;

public class LoginPage {

    private static final By USERNAME = AppiumBy.iOSClassChain("**/XCUIElementTypeTextField");
    private static final By PASSWORD = AppiumBy.iOSClassChain("**/XCUIElementTypeSecureTextField");
    private static final By LOGIN = AppiumBy.iOSClassChain("**/XCUIElementTypeButton[`name == \"Login\"`]");
    private static final By ALERT = AppiumBy.iOSClassChain("**/XCUIElementTypeAlert");
    private static final By KEYBOARD = By.className("XCUIElementTypeKeyboard");

    private final IOSDriver driver;
    private final WebDriverWait wait;

    public LoginPage(IOSDriver driver, WebDriverWait wait) {
        this.driver = driver;
        this.wait = wait;
    }

    public void waitUntilLoaded() {
        wait.until(ExpectedConditions.visibilityOfElementLocated(USERNAME));
        wait.until(ExpectedConditions.visibilityOfElementLocated(PASSWORD));
    }

    public boolean isDisplayed() {
        return !driver.findElements(USERNAME).isEmpty()
                && driver.findElement(USERNAME).isDisplayed();
    }

    public void selectSuggestion(String email) {
        wait.until(ExpectedConditions.elementToBeClickable(
                AppiumBy.accessibilityId(email))).click();
        wait.until(ExpectedConditions.attributeContains(USERNAME, "value", email));
    }

    public String username() {
        return driver.findElement(USERNAME).getAttribute("value");
    }

    public String password() {
        return driver.findElement(PASSWORD).getAttribute("value");
    }

    public void clearPassword() {
        WebElement field = wait.until(ExpectedConditions.elementToBeClickable(PASSWORD));
        field.click();
        field.clear();
        wait.until(d -> {
            String value = d.findElement(PASSWORD).getAttribute("value");
            return value == null || value.isBlank();
        });
    }

    public void submit() {
        wait.until(ExpectedConditions.elementToBeClickable(LOGIN)).click();
    }

    public void submitWithKeyboardCoveringButton() {
        if (isKeyboardVisible()) {
            dismissKeyboardWithTab();
        }
        WebElement login = wait.until(ExpectedConditions.elementToBeClickable(LOGIN));
        String elementId = ((RemoteWebElement) login).getId();
        driver.executeScript("mobile: doubleTap", Map.of("elementId", elementId));
    }

    public void dismissKeyboardWithTab() {
        driver.executeScript("mobile: keys", Map.of("keys", List.of("\uE004")));
        wait.until(d -> !isKeyboardVisible());
    }

    public boolean isKeyboardVisible() {
        return driver.findElements(KEYBOARD).stream()
                .anyMatch(element -> "true".equals(element.getAttribute("visible")));
    }

    public String alertTitle() {
        return alertTexts().get(0).getAttribute("name");
    }

    public String alertMessage() {
        return alertTexts().get(1).getAttribute("name");
    }

    public void acceptAlert() {
        WebElement alert = wait.until(ExpectedConditions.visibilityOfElementLocated(ALERT));
        alert.findElement(By.className("XCUIElementTypeButton")).click();
        wait.until(ExpectedConditions.invisibilityOfElementLocated(ALERT));
    }

    private List<WebElement> alertTexts() {
        WebElement alert = wait.until(ExpectedConditions.visibilityOfElementLocated(ALERT));
        return alert.findElements(By.className("XCUIElementTypeStaticText"));
    }
}
