package dev.handson.selenium.pages;

import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;

/** CheckoutPage——与 Python 版 pages/checkout_page.py 语义等价（POM：页面层）。 */
public class CheckoutPage {

    private static final String[] FRAMES = {"frame-outer", "frame-middle", "frame-inner"};

    private final WebDriver d;
    private final WebDriverWait wait;

    public CheckoutPage(WebDriver d, String baseUrl) {
        this.d = d;
        this.wait = new WebDriverWait(d, Duration.ofSeconds(10));
        this.baseUrl = baseUrl;
    }

    private final String baseUrl;

    public CheckoutPage open() {
        d.get(baseUrl + "/checkout.html");
        wait.until(x -> !x.findElements(By.id(FRAMES[0])).isEmpty());
        return this;
    }

    /** 逐层切入 iframe → 点击购买 → 返回订单号。 */
    public String buy() {
        for (String fid : FRAMES) {
            d.switchTo().frame(d.findElement(By.id(fid)));
        }
        d.findElement(By.id("buy-btn")).click();
        wait.until(x -> x.findElement(By.id("order-id")).getText().contains("ORD-"));
        return d.findElement(By.id("order-id")).getText().replace("订单号 ", "").trim();
    }

    public void pay() {
        d.findElement(By.id("pay-btn")).click();
        wait.until(x -> x.findElement(By.id("order-id")).getText().contains("已支付"));
    }

    public void backToMain() {
        d.switchTo().defaultContent();
    }
}
