"""FormPage——表单页对象（终极套件的数据驱动用例使用）。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


class FormPage:
    URL = "/form.html"

    def __init__(self, driver, base_url):
        self.d = driver
        self.base = base_url
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.d.get(self.base + self.URL)
        return self

    def submit_order(self, customer: str, address: str) -> dict:
        import json
        self.d.find_element(By.ID, "customer").clear()
        self.d.find_element(By.ID, "customer").send_keys(customer)
        addr = self.d.find_element(By.ID, "address")
        addr.clear()
        addr.send_keys(address)
        Select(self.d.find_element(By.ID, "channel")).select_by_value("web")
        self.d.find_element(By.ID, "submit-btn").click()
        el = self.wait.until(
            lambda d: d.find_element(By.ID, "echo") if d.find_element(By.ID, "echo").is_displayed() else False)
        return json.loads(el.text)
