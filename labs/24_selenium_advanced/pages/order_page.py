"""Selenium 版页面对象：与 lab 18（Playwright POM）同一套业务语义。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class OrderPage:
    def __init__(self, driver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def open(self) -> "OrderPage":
        self.driver.get(f"{self.base_url}/")
        return self

    def place_order(self, customer: str, item: str = "标准商品", price: str = "9.9") -> None:
        d = self.driver
        d.find_element(By.ID, "customer").send_keys(customer)
        d.find_element(By.ID, "item").send_keys(item)
        d.find_element(By.ID, "price").send_keys(price)
        d.find_element(By.XPATH, "//button[text()='创建订单']").click()
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), customer))

    def order_visible(self, customer: str) -> bool:
        return customer in self.driver.find_element(By.TAG_NAME, "tbody").text

    def delete_order(self, customer: str) -> None:
        row = self.driver.find_element(By.XPATH, f"//tr[contains(., '{customer}')]")
        row.find_element(By.CLASS_NAME, "delete-btn").click()
        self.wait.until(EC.invisibility_of_element_located(
            (By.XPATH, f"//tr[contains(., '{customer}')]")))
