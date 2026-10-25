package dev.handson.finalsuite;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.Test;

/** 购买支付全流程（与 Python 终极套件的 test_purchase_roundtrip 同用例集）。 */
public class PurchaseTest extends GridBase {

    private static final String BASE = System.getenv().getOrDefault("SHOP_URL_BROWSER", "http://host.docker.internal:8946");

    @Test
    public void purchaseRoundtrip() throws Exception {
        d.get(BASE + "/checkout.html");
        WebDriverWait wait = new WebDriverWait(d, Duration.ofSeconds(10));
        for (String fid : new String[]{"frame-outer", "frame-middle", "frame-inner"}) {
            d.switchTo().frame(d.findElement(By.id(fid)));
        }
        d.findElement(By.id("buy-btn")).click();
        wait.until(x -> x.findElement(By.id("order-id")).getText().contains("ORD-"));
        String orderId = d.findElement(By.id("order-id")).getText().replace("订单号 ", "").trim();
        d.findElement(By.id("pay-btn")).click();
        wait.until(x -> x.findElement(By.id("order-id")).getText().contains("已支付"));
        d.switchTo().defaultContent();

        HttpRequest req = HttpRequest.newBuilder(URI.create(
                BASE.replace("host.docker.internal", "127.0.0.1") + "/api/orders/" + orderId)).GET().build();
        HttpResponse<String> res = HttpClient.newHttpClient().send(req, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(res.statusCode(), 200);
        Assert.assertTrue(res.body().contains("\"status\": \"paid\""), res.body());
    }
}
