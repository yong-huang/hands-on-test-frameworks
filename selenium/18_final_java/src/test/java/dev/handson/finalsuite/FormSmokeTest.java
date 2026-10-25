package dev.handson.finalsuite;

import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

/** 表单冒烟（与 Python 终极套件的表单用例同用例集）。 */
public class FormSmokeTest extends GridBase {

    private static final String BASE = System.getenv().getOrDefault("SHOP_URL_BROWSER", "http://host.docker.internal:8946");

    @Test
    public void formSmoke() {
        d.get(BASE + "/form.html");
        WebDriverWait wait = new WebDriverWait(d, Duration.ofSeconds(10));
        long suffix = System.currentTimeMillis();
        String customer = "🏁Java矩阵-" + suffix;
        d.findElement(By.id("customer")).sendKeys(customer);
        d.findElement(By.id("address")).sendKeys("Java 矩阵测试地址");
        new Select(d.findElement(By.id("channel"))).selectByValue("web");
        d.findElement(By.id("submit-btn")).click();
        String echo = wait.until(x -> x.findElement(By.id("echo")).isDisplayed()
                ? x.findElement(By.id("echo")).getText() : "").trim();
        Assert.assertTrue(echo.contains(customer), "回读应含本轮收件人: " + echo);
        Assert.assertTrue(echo.contains("Java 矩阵测试地址"));
    }
}
