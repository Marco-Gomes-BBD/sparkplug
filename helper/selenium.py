from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def bring_to_front(driver):
    position = driver.get_window_position()
    driver.minimize_window()
    driver.set_window_position(position["x"], position["y"])


def get_children(element):
    return element.find_elements(By.XPATH, "./*")


def find_element_safe(element, by, value):
    res = None
    try:
        res = element.find_element(by, value)
    except Exception:
        res = None
    return res


def select_item_in_elements(elements, selector):
    by, value = selector
    for element in elements:
        user_field = find_element_safe(element, by, value)
        if user_field is not None:
            return user_field
    return None


def await_element(driver, selector, time=10):
    return WebDriverWait(driver, time).until(EC.presence_of_element_located(selector))


def await_element_stale(driver, selector, time=10, stale_time=10):
    element = await_element(driver, selector, time)
    WebDriverWait(driver, stale_time).until(EC.staleness_of(element))
    element = await_element(driver, selector, time)
    return element


def await_text_in_element(driver, selector, text, time=10):
    return WebDriverWait(driver, time).until(
        EC.text_to_be_present_in_element(selector, text)
    )
