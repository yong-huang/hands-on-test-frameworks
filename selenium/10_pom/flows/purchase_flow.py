"""PurchaseFlow——业务编排层（POM：页面三层之二）。组合页面动作成完整业务。"""
from pages.checkout_page import CheckoutPage


class PurchaseFlow:
    def __init__(self, driver, base_url):
        self.page = CheckoutPage(driver, base_url)

    def buy_and_pay(self) -> str:
        """完整下单支付流：开页 → 购买 → 支付 → 回主文档。返回订单号。"""
        self.page.open()
        oid = self.page.buy()
        self.page.pay()
        self.page.back_to_main()
        return oid
