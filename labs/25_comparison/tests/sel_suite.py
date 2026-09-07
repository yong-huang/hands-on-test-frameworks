"""Selenium 版统一场景套件：同语义 5 条（显式等待）。"""
import uuid

from playwright.sync_api import expect  # noqa: F401（仅占位提醒语义对齐）
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _wait(driver):
    return WebDriverWait(driver, 15)


def test_1_home_loads(driver, sut_url):
    driver.get(f"{sut_url}/")
    _wait(driver).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))


def test_2_create_order(driver, sut_url):
    uniq = uuid.uuid4().hex[:6]
    driver.get(f"{sut_url}/")
    driver.find_element(By.ID, "customer").send_keys(f"对比-{uniq}")
    driver.find_element(By.ID, "item").send_keys("对比商品")
    driver.find_element(By.ID, "price").send_keys("5.5")
    driver.find_element(By.XPATH, "//button[text()='创建订单']").click()
    _wait(driver).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), f"对比-{uniq}"))


def test_3_list_has_rows(driver, sut_url):
    driver.get(f"{sut_url}/")
    _wait(driver).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#orders tr")) >= 1)


def test_4_delete_created(driver, sut_url):
    uniq = uuid.uuid4().hex[:6]
    driver.get(f"{sut_url}/")
    driver.find_element(By.ID, "customer").send_keys(f"删除-{uniq}")
    driver.find_element(By.ID, "item").send_keys("x")
    driver.find_element(By.ID, "price").send_keys("1")
    driver.find_element(By.XPATH, "//button[text()='创建订单']").click()
    _wait(driver).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"), f"删除-{uniq}"))
    driver.find_element(
        By.XPATH, f"//tr[contains(., '删除-{uniq}')]//button[@class='delete-btn']").click()
    _wait(driver).until(lambda d: f"删除-{uniq}" not in d.page_source)


def test_5_slow_banner(driver, sut_url):
    driver.get(f"{sut_url}/")
    _wait(driver).until(
        EC.text_to_be_present_in_element((By.ID, "banner"), "Banner:"))
