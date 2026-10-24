package dev.handson.appium;

import io.appium.java_client.AppiumBy;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.testng.annotations.Test;

import java.util.Map;

import static org.testng.Assert.assertTrue;

/**
 * 生物识别登录：Face ID 模拟（仅 iOS Simulator 有效）。
 * 流程：Biometrics 页打开开关 → Login 页出现 FaceId Icons 按钮 →
 * enrollBiometric 登记 → 点击按钮弹系统 Face ID 提示 →
 * sendBiometricMatch 决定匹配结果。
 * 实测事实（2026-10-23，App 2.3.0）：
 * - 开关是图标按钮 SwitchUnselected Icons，拨后图标名不变，
 *   功能断言用"Login 页出现 FaceId Icons 按钮"；
 * - 系统人脸提示不在应用源码里，解析它的唯一方式是 sendBiometricMatch；
 * - match=true 登录成功后落到 Checkout 地址页（该 App 的登录表单
 *   就是结算流程的登录门）。
 */
public class BiometricLoginTest extends BaseTest {

    private static final By LOGIN_FORM_HINT = AppiumBy.iOSNsPredicateString(
            "label == 'Select a username from the list below'");
    private static final By FACE_ID_BUTTON = AppiumBy.accessibilityId("FaceId Icons");
    private static final By CHECKOUT_REACHED = AppiumBy.iOSNsPredicateString(
            "label == 'Enter a shipping address'");

    /** 打开 Face ID 登录开关并进入 Login 页（功能断言：FaceId 按钮出现）。 */
    private void enableFaceIdAndOpenLogin() throws Exception {
        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("Biometrics-menu-item")).click();
        driver.findElement(AppiumBy.accessibilityId("SwitchUnselected Icons")).click();
        Thread.sleep(600);

        driver.findElement(AppiumBy.accessibilityId("More-tab-item")).click();
        waitForClickable(AppiumBy.accessibilityId("Login Button")).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(FACE_ID_BUTTON));
        System.out.println("✅ Face ID 登录已开启，Login 页出现 FaceId Icons 按钮");
    }

    private void enrollBiometric() {
        driver.executeScript("mobile: enrollBiometric", Map.of("enroll", true));
        System.out.println("✅ 模拟器已登记生物特征（enrollBiometric）");
    }

    private void tapFaceIdButton() throws Exception {
        WebElement button = wait.until(ExpectedConditions.visibilityOfElementLocated(FACE_ID_BUTTON));
        button.click();
        Thread.sleep(1500);
    }

    /** 模拟系统 Face ID 弹窗的匹配结果。 */
    private void sendBiometricMatch(boolean match) {
        driver.executeScript("mobile: sendBiometricMatch",
                Map.of("type", "faceId", "match", match));
        System.out.println("✅ sendBiometricMatch：match=" + match);
    }

    /** 手势一（真用例一）：match=true 走完 Face ID 登录。 */
    @Test
    public void faceIdMatchTrueLogsIn() throws Exception {
        enableFaceIdAndOpenLogin();
        enrollBiometric();

        tapFaceIdButton();
        sendBiometricMatch(true);

        // 登录成功：该 App 的登录表单就是结算流程的登录门，成功后进地址页
        wait.until(ExpectedConditions.visibilityOfElementLocated(CHECKOUT_REACHED));
        System.out.println("✅ Face ID 匹配成功：已登录并进入结算地址页");
    }

    /** 手势二（真用例二）：match=false 拒绝匹配，停留登录页且应用不崩。 */
    @Test
    public void faceIdMatchFalseStaysOnLogin() throws Exception {
        enableFaceIdAndOpenLogin();
        enrollBiometric();

        tapFaceIdButton();
        sendBiometricMatch(false);
        Thread.sleep(1500);

        assertTrue(isVisible(LOGIN_FORM_HINT),
                "匹配失败后应停留登录页（用户名建议列表仍可见）");
        assertTrue(!driver.findElements(FACE_ID_BUTTON).isEmpty(),
                "FaceId 按钮应仍在，应用未崩溃");
        System.out.println("✅ 匹配失败：停留登录页，应用未崩溃");
    }

    /**
     * 手势三（链路）：失败不阻塞下一次尝试——match=false 之后紧接着
     * match=true 仍能正常登录（系统弹窗被逐次解析，无残留阻塞）。
     */
    @Test
    public void failedMatchDoesNotBlockNextAttempt() throws Exception {
        enableFaceIdAndOpenLogin();
        enrollBiometric();

        tapFaceIdButton();
        sendBiometricMatch(false);
        Thread.sleep(1200);
        assertTrue(isVisible(LOGIN_FORM_HINT), "失败后应停留登录页");
        System.out.println("✅ 第一次尝试：match=false，停留登录页");

        tapFaceIdButton();
        sendBiometricMatch(true);
        wait.until(ExpectedConditions.visibilityOfElementLocated(CHECKOUT_REACHED));
        System.out.println("✅ 第二次尝试：match=true，登录成功——弹窗无残留阻塞");
    }
}
