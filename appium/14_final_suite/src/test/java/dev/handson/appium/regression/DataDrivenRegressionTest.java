package dev.handson.appium.regression;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.handson.appium.BaseTest;
import dev.handson.appium.flows.CheckoutFlow;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertTrue;

/** 回归组（数据驱动）：5 组地址/支付数据各跑一次完整结算。 */
public class DataDrivenRegressionTest extends BaseTest {

    private static final Path DATA_FILE = Path.of("testdata", "checkout-cases.json");

    private CheckoutFlow checkout;

    @BeforeClass(alwaysRun = true)
    public void initFlow() {
        checkout = new CheckoutFlow(this);
    }

    @DataProvider(name = "checkoutCases")
    public Object[][] checkoutCases() throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, String>> cases = mapper.readValue(DATA_FILE.toFile(),
                mapper.getTypeFactory().constructCollectionType(List.class, Map.class));
        Object[][] rows = new Object[cases.size()][1];
        for (int i = 0; i < cases.size(); i++) {
            rows[i][0] = cases.get(i);
        }
        return rows;
    }

    @Test(dataProvider = "checkoutCases")
    public void reg17CheckoutWithDataSettles(Map<String, String> c) throws Exception {
        String uniqueName = c.get("fullName") + "-"
                + Long.toString(System.currentTimeMillis(), 36);
        System.out.printf("▸ [reg] 数据组（%s）：收件人=%s%n", c.get("caseName"), uniqueName);

        resetAppState();
        checkout.addItemToCart();
        checkout.openCheckout();
        checkout.fillShipping(uniqueName, c.get("address"),
                c.get("city"), c.get("zip"), c.get("country"));
        checkout.toPayment();
        checkout.fillPayment(c.get("cardName"), c.get("cardNumber"),
                c.get("expiry"), c.get("securityCode"));
        assertFalse(checkout.reviewOrder());
        assertTrue(reviewPageContains(uniqueName), "Review 页应含唯一收件人");
        checkout.placeOrder();
        System.out.printf("✅ [reg] 数据组（%s）下单完成%n", c.get("caseName"));
    }

    private boolean reviewPageContains(String text) {
        return driver.getPageSource().contains(text);
    }
}
