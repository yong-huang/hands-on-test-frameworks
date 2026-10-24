package dev.handson.appium;

import dev.handson.appium.flows.PurchaseFlow;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

/** 结算端到端（POM 版）：Flow 编排 + 测试层断言。 */
public class CheckoutPomTest extends BaseTest {

    private PurchaseFlow purchase;

    @BeforeClass(alwaysRun = true)
    public void initFlow() {
        purchase = new PurchaseFlow(driver, wait);
    }

    @Test
    public void checkoutEndToEndReachesCompleteScreen() throws Exception {
        purchase.addItemToCart();
        purchase.openCheckout();
        purchase.fillShipping("Rebecca Winter", "Mandorley 112", "Truro",
                "89750", "United Kingdom");
        purchase.fillPaymentAndReview("Maxim Winter", "3258 1265 7568 7896",
                "03/25", "123");
        purchase.placeOrder();
        System.out.println("✅ POM 结算端到端：到达 CheckoutComplete-screen");
    }
}
