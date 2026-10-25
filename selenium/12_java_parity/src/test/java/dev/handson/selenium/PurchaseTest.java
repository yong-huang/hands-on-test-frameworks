package dev.handson.selenium;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import dev.handson.selenium.flows.PurchaseFlow;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

/** 测试层（与 Python 版 tests/purchase_test.py 语义等价）——零定位细节。 */
public class PurchaseTest {

    private static final String BASE = System.getenv().getOrDefault("SHOP_URL", "http://127.0.0.1:8946");

    private WebDriver d;

    @BeforeMethod
    public void setUp() {
        ChromeOptions opts = new ChromeOptions();
        if (!"0".equals(System.getenv().getOrDefault("HEADLESS", "1"))) {
            opts.addArguments("--headless=new");
        }
        opts.addArguments("--window-size=1400,1000");
        d = new ChromeDriver(opts);
    }

    @AfterMethod
    public void tearDown() {
        if (d != null) {
            d.quit();
        }
    }

    @Test
    public void buyAndPayRoundtrip() throws Exception {
        String orderId = new PurchaseFlow(d, BASE).buyAndPay();
        Assert.assertTrue(orderId.startsWith("ORD-"), "订单号应以 ORD- 开头: " + orderId);

        HttpRequest req = HttpRequest.newBuilder(URI.create(BASE + "/api/orders/" + orderId)).GET().build();
        HttpResponse<String> res = HttpClient.newHttpClient().send(req, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(res.statusCode(), 200);
        // 注意：靶场服务端是 Python json.dumps，键值间带空格（"status": "paid"）——
        // 双栈对照时最容易踩的就是这类序列化空格差异
        Assert.assertTrue(res.body().contains("\"status\": \"paid\""), "订单应已支付: " + res.body());
        Assert.assertTrue(res.body().contains("\"amount\":"), "订单应含金额字段");
    }
}
