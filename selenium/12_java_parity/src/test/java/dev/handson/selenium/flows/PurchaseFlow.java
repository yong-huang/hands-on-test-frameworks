package dev.handson.selenium.flows;

import dev.handson.selenium.pages.CheckoutPage;
import org.openqa.selenium.WebDriver;

/** PurchaseFlow——业务编排层（与 Python 版 flows/purchase_flow.py 语义等价）。 */
public class PurchaseFlow {

    private final CheckoutPage page;

    public PurchaseFlow(WebDriver d, String baseUrl) {
        this.page = new CheckoutPage(d, baseUrl);
    }

    /** 完整下单支付流：开页 → 购买 → 支付 → 回主文档。返回订单号。 */
    public String buyAndPay() {
        page.open();
        String oid = page.buy();
        page.pay();
        page.backToMain();
        return oid;
    }
}
