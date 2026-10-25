"""CheckoutPage——结账页唯一的定位器与操作住址（POM：页面三层之一）。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class CheckoutPage:
    URL = "/checkout.html"
    FRAMES = ("frame-outer", "frame-middle", "frame-inner")

    def __init__(self, driver, base_url):
        self.d = driver
        self.base = base_url
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.d.get(self.base + self.URL)
        self.wait.until(lambda d: d.find_elements(By.ID, self.FRAMES[0]))
        return self

    def buy(self) -> str:
        """逐层切入 iframe → 点击购买 → 返回订单号。"""
        for fid in self.FRAMES:
            self.d.switch_to.frame(self.d.find_element(By.ID, fid))
        self.d.find_element(By.ID, "buy-btn").click()
        self.wait.until(lambda d: "ORD-" in d.find_element(By.ID, "order-id").text)
        oid = self.d.find_element(By.ID, "order-id").text.replace("订单号 ", "").strip()
        return oid

    def pay(self):
        self.d.find_element(By.ID, "pay-btn").click()
        self.wait.until(lambda d: "已支付" in d.find_element(By.ID, "order-id").text)

    def back_to_main(self):
        self.d.switch_to.default_content()
