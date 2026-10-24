package dev.handson.appium;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.handson.appium.flows.CheckoutFlow;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertTrue;

/**
 * 数据驱动结算：DataProvider 从 JSON 读 5 组地址/支付数据，
 * 每组生成唯一收件人后独立跑完整结算。
 * 隔离手段：每条数据前 BeforeMethod clearApp 重置应用，
 * 顺序执行与失败重跑都不依赖上一条的状态。
 */
public class CheckoutDataDrivenTest extends BaseTest {

    private static final Path DATA_FILE = Path.of("testdata", "checkout-cases.json");

    private CheckoutFlow checkout;
    private final AtomicInteger caseNo = new AtomicInteger();

    @BeforeClass(alwaysRun = true)
    public void initFlow() {
        checkout = new CheckoutFlow(this);
    }

    /** 从 JSON 数据源读用例；TestNG 会对每行数据各跑一次测试方法。 */
    @DataProvider(name = "checkoutCases")
    public Object[][] checkoutCases() throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, String>> cases = mapper.readValue(
                DATA_FILE.toFile(),
                mapper.getTypeFactory().constructCollectionType(List.class, Map.class));
        Object[][] rows = new Object[cases.size()][1];
        for (int i = 0; i < cases.size(); i++) {
            rows[i][0] = cases.get(i);
        }
        return rows;
    }

    @Test(dataProvider = "checkoutCases")
    public void checkoutWithDataSettlesEndToEnd(Map<String, String> c) throws Exception {
        int no = caseNo.incrementAndGet();
        // 唯一收件人：数据里的姓名 + 毫秒后缀，保证跨用例/跨轮次不重名
        String uniqueName = c.get("fullName") + "-" + Long.toString(System.currentTimeMillis(), 36);
        System.out.printf("▸ 数据组 %d（%s）：收件人=%s%n", no, c.get("caseName"), uniqueName);

        checkout.addItemToCart();
        checkout.openCheckout();
        checkout.fillShipping(uniqueName,
                c.get("address"), c.get("city"), c.get("zip"), c.get("country"));
        checkout.toPayment();
        checkout.fillPayment(c.get("cardName"), c.get("cardNumber"),
                c.get("expiry"), c.get("securityCode"));

        assertFalse(checkout.reviewOrder(), "数据齐全时 Review 不应弹校验 alert");
        assertTrue(reviewPageContains(uniqueName),
                "Review 页收件人应为本组的唯一姓名（数据确实生效）");
        System.out.printf("✅ 数据组 %d：Review 页收件人核验通过%n", no);

        checkout.placeOrder();
        System.out.printf("✅ 数据组 %d：下单完成%n", no);
    }

    /** Review 页源码里是否出现唯一收件人姓名。 */
    private boolean reviewPageContains(String uniqueName) {
        return driver.getPageSource().contains(uniqueName);
    }
}
