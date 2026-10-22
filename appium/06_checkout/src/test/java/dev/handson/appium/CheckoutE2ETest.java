package dev.handson.appium;

import dev.handson.appium.flows.CheckoutFlow;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.math.BigDecimal;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertFalse;
import static org.testng.Assert.assertTrue;

/**
 * 结算全链路：登录 → 加购 → 地址 → 支付 → Review → Place Order。
 * 三条用例共用 CheckoutFlow；每个用例前 clearApp，登录态可能残留由
 * flow 内的条件门处理。
 */
public class CheckoutE2ETest extends BaseTest {

    private CheckoutFlow checkout;

    @BeforeClass(alwaysRun = true)
    public void initFlow() {
        checkout = new CheckoutFlow(this);
    }

    /** 端到端：加购 1 件 → 填地址支付 → Review 总价 → 下单到完成页。 */
    @Test
    public void checkoutEndToEndPlacesOrder() throws Exception {
        checkout.addItemToCart();
        BigDecimal cartTotal = checkout.openCheckout();
        System.out.printf("（购物车总价 $%s，Review 页还会加 $%s 运费）%n",
                cartTotal, CheckoutFlow.DELIVERY_FEE);

        checkout.fillShipping("Rebecca Winter", "Mandorley 112", "Truro", "89750", "United Kingdom");
        checkout.toPayment();
        checkout.fillPayment("Maxim Winter", "3258 1265 7568 7896", "03/25", "123");

        assertFalse(checkout.reviewOrder(), "字段齐全时 Review 不应弹校验 alert");
        BigDecimal reviewTotal = checkout.reviewTotal();
        assertEquals(reviewTotal, cartTotal.add(CheckoutFlow.DELIVERY_FEE),
                "Review 总价应等于购物车总价 + 运费");
        System.out.printf("✅ Review 总价一致：$%s = $%s + $%s 运费%n",
                reviewTotal, cartTotal, CheckoutFlow.DELIVERY_FEE);

        checkout.placeOrder();
        System.out.println("✅ 端到端下单完成");
    }

    /** 负向：Full Name 留空时地址步被拦下。 */
    @Test
    public void emptyFullNameBlocksShippingStep() throws Exception {
        checkout.addItemToCart();
        checkout.openCheckout();

        checkout.fillShipping("", "Mandorley 112", "Truro", "89750", "United Kingdom");
        boolean blocked = checkout.toPayment();
        assertTrue(blocked, "空姓名应触发校验 alert");
        assertEquals(checkout.alertMessage(), "Please provide your full name.",
                "alert 正文应指向 Full Name");
        System.out.println("✅ 空姓名被拦截：" + checkout.alertMessage());
        checkout.dismissAlert();
    }

    /** 负向：卡号留空时 Review 步被拦下。 */
    @Test
    public void emptyCardNumberBlocksReviewStep() throws Exception {
        checkout.addItemToCart();
        checkout.openCheckout();
        checkout.fillShipping("Rebecca Winter", "Mandorley 112", "Truro", "89750", "United Kingdom");
        checkout.toPayment();
        checkout.fillPayment("Maxim Winter", "", "03/25", "123");

        boolean alertShown = checkout.reviewOrder();
        assertTrue(alertShown, "空卡号应触发校验 alert");
        assertEquals(checkout.alertMessage(), "Value looks invalid.",
                "alert 正文应为 Value looks invalid.");
        System.out.println("✅ 空卡号被拦截：" + checkout.alertMessage());
        checkout.dismissAlert();
    }
}
