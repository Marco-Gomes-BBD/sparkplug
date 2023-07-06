import os
import sys
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
def read_config():
    config = {}
    with open("config.json", "r") as file:
        config = json.load(file)

    accounts = config.get("accounts", {})
    censor = config.get("censor", False)
    driver = config.get("driver", None)
    method = config.get("method", None)
    auth_method = config.get("auth_method", None)
    return driver, accounts, censor, method, auth_method


def get_account(accounts, user):
    lookup = accounts[user]
    retrieve = lookup.get("retrieve", False)
    reason = lookup.get("reason", None)
    censor_user = lookup.get("censor", False)

    issue = None
    if user not in accounts:
        issue = "Unknown account"
    elif reason is None:
        issue = "No reason provided"
    elif not retrieve:
        issue = "Account retrieve blacklist"

    return user, reason, censor_user, issue


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


def await_element_stale(driver, selector, time=10, stale_time=10):
    element = await_element(driver, selector, time)
    WebDriverWait(driver, stale_time).until(EC.staleness_of(element))
    element = await_element(driver, selector, time)
    return element


def await_text_in_element(driver, selector, text, time=10):
    return WebDriverWait(driver, time).until(
        EC.text_to_be_present_in_element(selector, text)
    )


def get_secret_show(driver, reason):
    sel = By.CSS_SELECTOR
    ele_show = await_element(driver, (sel, '[data-testid="action-menu-item-1"]'))
    ele_show.click()

    ele_reason = await_element(driver, (sel, '[formcontrolname="ReasonFreeText"]'))
    ele_reason.send_keys(reason, Keys.TAB, Keys.ENTER)

    ele_secret = await_element(driver, (sel, '[formcontrolname="secret"]'))
    secret = ele_secret.get_attribute("value")

    ele_close = await_element(driver, (sel, ".timer-button"))
    ele_close.click()
    return secret


def get_secret_copy(driver, reason):
    sel = By.CSS_SELECTOR
    ele_copy = await_element(driver, (sel, '[data-testid="action-menu-item-2"]'))
    ele_copy.click()

    ele_reason = await_element(driver, (sel, '[formcontrolname="ReasonFreeText"]'))
    ele_reason.send_keys(reason, Keys.TAB, Keys.ENTER)

    sleep(1)
    secret = pyperclip.paste()
    return secret


def authenticate_radius():
    driver.get("https://epvs.za.sbicdirectory.com/PasswordVault/v10/logon/radius")
    elem_user = await_element(driver, (By.ID, "user_pass_form_username_field"))
    elem_user.clear()
    elem_user.send_keys(email)

    elem_pass = await_element(driver, (By.ID, "user_pass_form_password_field"))
    elem_pass.clear()
    elem_pass.send_keys(password, Keys.RETURN)


def authenticate_saml():
    driver.get("https://epvs.za.sbicdirectory.com/PasswordVault/v10/logon/saml")
    elem_user = await_element(driver, (By.CSS_SELECTOR, '[name="loginfmt"]'))
    elem_user.clear()
    elem_user.send_keys(email, Keys.RETURN)

    elem_pass = await_element_stale(driver, (By.CSS_SELECTOR, '[name="passwd"]'))
    elem_pass.clear()
    elem_pass.send_keys(password, Keys.RETURN)


def dict_lookup(dict, key, lookup_handler, default):
    method = dict.get(key, None)
    if method is None:
        lookup_handler(key)
        method = default
    return method


def get_secret_method(name: str):
    def method_error(name):
        return print(f"Error: {name} not a valid method, falling back to default.")

    default = get_secret_copy
    methods = {
        "copy": get_secret_copy,
        "show": get_secret_show,
    }
    return dict_lookup(methods, name.lower(), method_error, default)


def get_authentication_method(name: str):
    def method_error(name):
        return print(f"Error: {name} not a valid authentication, using default.")

    default = authenticate_radius
    methods = {
        "radius": authenticate_radius,
        "saml": authenticate_saml,
    }
    return dict_lookup(methods, name.lower(), method_error, default)


def select_driver(name: str):
    def driver_error(name):
        print(f"Error: {name} not a valid driver, falling back to default.")

    name = name.lower()

    default = webdriver.Edge
    drivers = {
        "chrome": webdriver.Chrome,
        "chromium_edge": webdriver.ChromiumEdge,
        "firefox": webdriver.Firefox,
        "ie": webdriver.Ie,
        "safari": webdriver.Safari,
    }
    return dict_lookup(drivers, name.lower(), driver_error, default)


driver_name, accounts, censor, method, auth_method = read_config()
driver_class = select_driver(driver_name)
get_secret = get_secret_method(method)
authenticate = get_authentication_method(auth_method)

driver = driver_class()
bring_to_front(driver)

authenticate()

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
    user, reason, censor_user, issue = get_account(accounts, user)
    if issue is not None:
        print(f"{padding}Issue with user: {user} ({issue})")
        continue

    ele_act = select_item_in_elements(row, (sel, '[col-id="ActionColumn"]'))
    ele_more = find_element_safe(ele_act, sel, '[data-testid="more-actions-button"]')
    ele_more.click()

    secret = get_secret(driver, reason)
    censor_local = censor or censor_user
    if censor_local:
        secret = len(secret) * "█"

    print(f"{padding}{user}: {secret}")
    sleep(3)

driver.close()
if getattr(sys, "frozen", False):
    input()
