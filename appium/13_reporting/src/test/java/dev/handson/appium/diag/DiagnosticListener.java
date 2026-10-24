package dev.handson.appium.diag;

import io.appium.java_client.ios.IOSDriver;
import org.openqa.selenium.OutputType;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;

import static io.qameta.allure.Allure.addAttachment;

/**
 * 失败诊断监听器：用例失败时自动附截图、page source、设备日志与录屏；
 * 成功用例只停录、不产生任何附件。
 * 录屏每条用例独立一段，避免长会话产生超大文件。
 */
public class DiagnosticListener implements ITestListener {

    /** BaseTest 在会话建立时注册 driver（TestNG 监听器先于测试类实例化）。 */
    public static IOSDriver driver;

    @Override
    public void onTestStart(ITestResult result) {
        if (driver == null) {
            return;
        }
        try {
            driver.startRecordingScreen();
        } catch (Exception e) {
            System.out.println("[diag] 录屏启动失败（不影响用例）：" + e.getMessage());
        }
    }

    @Override
    public void onTestSuccess(ITestResult result) {
        stopRecordingQuietly();
    }

    @Override
    public void onTestFailure(ITestResult result) {
        if (driver == null) {
            return;
        }
        String name = result.getMethod().getMethodName();
        attachScreenshot(name);
        attachPageSource(name);
        attachSyslog(name);
        attachRecording(name);
        System.out.println("[diag] 失败证据已附加：截图 + page source + syslog + 录屏");
    }

    private void attachScreenshot(String name) {
        try {
            byte[] png = driver.getScreenshotAs(OutputType.BYTES);
            addAttachment(name + "-screenshot", "image/png",
                    new ByteArrayInputStream(png), "png");
        } catch (Exception e) {
            addAttachment(name + "-screenshot", "截图失败：" + e.getMessage());
        }
    }

    private void attachPageSource(String name) {
        try {
            addAttachment(name + "-page-source", "text/html",
                    new ByteArrayInputStream(driver.getPageSource().getBytes(StandardCharsets.UTF_8)),
                    "html");
        } catch (Exception e) {
            addAttachment(name + "-page-source", "page source 失败：" + e.getMessage());
        }
    }

    /** 设备日志：XCUITest 的 syslog；不可用时降级为 Appium 会话提示。 */
    private void attachSyslog(String name) {
        try {
            var entries = driver.manage().logs().get("syslog").getAll();
            StringBuilder sb = new StringBuilder();
            entries.forEach(e -> sb.append(e.getMessage()).append('\n'));
            addAttachment(name + "-syslog", "text/plain",
                    new ByteArrayInputStream(sb.toString().getBytes(StandardCharsets.UTF_8)), "txt");
        } catch (Exception e) {
            addAttachment(name + "-syslog", "syslog 不可用：" + e.getMessage());
        }
    }

    /** 停录并把录像作为附件（仅失败时调用，mp4 base64 解码）。 */
    private void attachRecording(String name) {
        try {
            String b64 = driver.stopRecordingScreen();
            byte[] mp4 = Base64.getDecoder().decode(b64);
            Path file = Path.of("target", "evidence", name + ".mp4");
            Files.createDirectories(file.getParent());
            Files.write(file, mp4);
            addAttachment(name + "-recording", "video/mp4",
                    new ByteArrayInputStream(mp4), "mp4");
        } catch (Exception e) {
            addAttachment(name + "-recording", "录屏失败：" + e.getMessage());
        }
    }

    private void stopRecordingQuietly() {
        if (driver == null) {
            return;
        }
        try {
            driver.stopRecordingScreen();
        } catch (Exception ignore) {
            // 成功用例的录像按需求丢弃
        }
    }
}
