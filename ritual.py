import os
import json
from time import sleep
from dotenv_flow import dotenv_flow

import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


# Get environment
dotenv_flow("")
email = os.getenv("STDB_EMAIL")
password = os.getenv("STDB_PASSWORD")

# Get config file
config = {}
with open("config.json", "r") as file:
    config = json.load(file)

accounts = config.get("accounts", None)
censor = config.get("censor", False)


def bring_to_front(driver):
    position = driver.get_window_position()
    driver.minimize_window()
    driver.set_window_position(position["x"], position["y"])


def get_children(element):
    return element.find_elements(By.XPATH, "./*")


def select_item_in_elements(elements, selector):
    by, value = selector
    for element in elements:
        user_field = find_element_safe(element, by, value)
        if user_field is not None:
            return user_field
    return None


def find_element_safe(element, by, value):
    res = None
    try:
        res = element.find_element(by, value)
    except Exception:
        res = None
    return res


def await_element(driver, selector, time=10):
    return WebDriverWait(driver, time).until(EC.presence_of_element_located(selector))


def await_text_in_element(driver, selector, text, time=10):
    return WebDriverWait(driver, time).until(
        EC.text_to_be_present_in_element(selector, text)
    )


driver = webdriver.Chrome()
bring_to_front(driver)

driver.get("https://epvs.za.sbicdirectory.com/PasswordVault/logon.aspx")
elem_user = await_element(driver, (By.ID, "user_pass_form_username_field"))
elem_pass = await_element(driver, (By.ID, "user_pass_form_password_field"))
elem_user.clear()
elem_pass.clear()
elem_user.send_keys(email)
elem_pass.send_keys(password, Keys.RETURN)

# Wait for the next page to load
WebDriverWait(driver, 60).until(EC.title_is("Accounts"))

# Get the login table
driver.switch_to.frame("frame-epv")
elem_results = await_text_in_element(
    driver, (By.CSS_SELECTOR, ".grid-title__title__filter__results"), "results", 20
)

elem_fav = await_element(driver, (By.CSS_SELECTOR, "[ref=eLeftContainer]"))
elem_logins = await_element(driver, (By.CSS_SELECTOR, "[ref=eBodyContainer]"))
elem_actions = await_element(driver, (By.CSS_SELECTOR, "[ref=eRightContainer]"))

# Get table elements
children_fav = get_children(elem_fav)
children_logins = get_children(elem_logins)
children_actions = get_children(elem_actions)
rows = zip(children_fav, children_logins, children_actions)

# Get the logins
print("Logins:")
for row in rows:
    sel = By.CSS_SELECTOR
    ele_fav = select_item_in_elements(row, (sel, '[col-id="isFavorite"]'))
    ele_user = select_item_in_elements(row, (sel, '[col-id="UserName"]'))
    ele_name = find_element_safe(ele_user, sel, '[data-testid="grid-cell-UserName"]')

    padding = " " * 2
    user = ele_name.get_attribute("innerText")
    lookup = accounts[user]
    retrieve = lookup.get("retrieve", False)
    if user not in accounts:
        print(f"{padding}Skipping account: {user} (unknown account)")
        continue
    if "reason" not in lookup:
        print(f"{padding}Skipping account: {user} (no reason provided)")
        continue
    if not retrieve:
        print(f"{padding}Skipping account: {user} (false retrieve)")
        continue

    reason = lookup["reason"]

    ele_act = select_item_in_elements(row, (sel, '[col-id="ActionColumn"]'))
    ele_more = find_element_safe(ele_act, sel, '[data-testid="more-actions-button"]')
    ele_more.click()

    ele_copy = await_element(driver, (sel, '[data-testid="action-menu-item-2"]'))
    ele_copy.click()

    ele_reason = await_element(driver, (sel, '[formcontrolname="ReasonFreeText"]'))
    ele_reason.send_keys(reason, Keys.TAB, Keys.ENTER)
    sleep(1)

    clipboard = pyperclip.paste()
    censor_local = censor or lookup.get("censor", False)
    if censor_local:
        clipboard = len(clipboard) * "█"

    print(f"{padding}{user}: {clipboard}")
    sleep(3)

driver.close()
input()
