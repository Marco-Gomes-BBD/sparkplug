import copy
import os
import sys
import json
import argparse
from time import sleep
from dotenv_flow import dotenv_flow

import types

import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common import exceptions as seleniumError

from action import run_action_specs
from helper.utils import dict_lookup, frozen_exit
from helper.selenium import (
    await_element,
    await_element_stale,
    select_item_in_elements,
    find_element_safe,
    await_text_in_element,
    get_children,
    bring_to_front,
)

# Get environment
dotenv_flow("")
email = os.getenv("STDB_EMAIL")
password = os.getenv("STDB_PASSWORD")

defaults = {
    "driver": "chrome",
    "censor": True,
    "method": "copy",
    "auth_method": "saml",
    "account": {"reason": None, "retrieve": True, "censor": False},
}

# Global variables
driver = None
config = None
args = None

padding = " " * 2

# App information
version = "1.0.0"


def read_config(file: str):
    config = {}
    try:
        with open(file, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        print("No config file found...")
    except Exception as e:
        raise e

    accounts = config.get("accounts", {})
    censor = config.get("censor", defaults["censor"])
    driver = config.get("driver", defaults["driver"])
    method = config.get("method", defaults["method"])
    auth_method = config.get("auth_method", defaults["auth_method"])

    config = {
        "driver": driver,
        "censor": censor,
        "method": method,
        "auth_method": auth_method,
        "accounts": accounts,
    }
    return types.SimpleNamespace(**config)


def save_config(config, file: str):
    new_config = {
        "driver": config.driver,
        "censor": config.censor,
        "method": config.method,
        "auth_method": config.auth_method,
        "accounts": config.accounts,
    }

    with open(file, "w") as file:
        json.dump(new_config, file, indent=4)


def get_account(accounts, user):
    lookup = accounts.get(user, {})
    retrieve = lookup.get("retrieve", False)
    reason = lookup.get("reason", None)
    censor_user = lookup.get("censor", False)
    actions = lookup.get("actions", [])

    issue = None
    if user not in accounts:
        issue = "Unknown account"
        accounts[user] = defaults["account"]
    elif reason is None:
        issue = "No reason provided"
    elif not retrieve:
        issue = "Account retrieve blacklist"

    return user, reason, censor_user, issue, actions


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


def authenticate_radius(driver):
    driver.get("https://epvs.za.sbicdirectory.com/PasswordVault/v10/logon/radius")
    elem_user = await_element(driver, (By.ID, "user_pass_form_username_field"))
    elem_user.clear()
    elem_user.send_keys(email)

    elem_pass = await_element(driver, (By.ID, "user_pass_form_password_field"))
    elem_pass.clear()
    elem_pass.send_keys(password, Keys.RETURN)


def authenticate_saml(driver):
    driver.get("https://epvs.za.sbicdirectory.com/PasswordVault/v10/logon/saml")
    elem_user = await_element(driver, (By.CSS_SELECTOR, '[name="loginfmt"]'))
    elem_user.clear()
    elem_user.send_keys(email, Keys.RETURN)

    elem_pass = await_element_stale(driver, (By.CSS_SELECTOR, '[name="passwd"]'))
    elem_pass.clear()
    elem_pass.send_keys(password, Keys.RETURN)


def get_secret_method(name: str, default: str = defaults["method"]):
    def method_error(name):
        return print(f"Error: {name} not a valid method, falling back to default.")

    methods = {
        "copy": get_secret_copy,
        "show": get_secret_show,
    }
    default = methods[default]
    return dict_lookup(methods, name.lower(), default, method_error)


def get_authentication_method(name: str, default: str = defaults["auth_method"]):
    def method_error(name):
        return print(f"Error: {name} not a valid authentication, using default.")

    methods = {
        "radius": authenticate_radius,
        "saml": authenticate_saml,
    }
    default = methods[default]
    return dict_lookup(methods, name.lower(), default, method_error)


def select_driver(name: str, default: str = defaults["driver"]):
    def driver_error(name):
        print(f"Error: {name} not a valid driver, falling back to default.")

    drivers = {
        "chrome": webdriver.Chrome,
        "chromium_edge": webdriver.ChromiumEdge,
        "firefox": webdriver.Firefox,
        "safari": webdriver.Safari,
    }
    default = drivers[default]
    return dict_lookup(drivers, name.lower(), default, driver_error)


def get_row_secret(get_secret, row):
    sel = By.CSS_SELECTOR
    ele_user = select_item_in_elements(row, (sel, '[col-id="UserName"]'))
    ele_name = find_element_safe(ele_user, sel, '[data-testid="grid-cell-UserName"]')

    user = ele_name.get_attribute("innerText")
    user, reason, censor_user, issue, actions = get_account(config.accounts, user)
    if issue is not None:
        print(f"{padding}Issue with user: {user} ({issue})")
        return None, False, None

    ele_act = select_item_in_elements(row, (sel, '[col-id="ActionColumn"]'))
    ele_more = find_element_safe(ele_act, sel, '[data-testid="more-actions-button"]')
    ele_more.click()

    secret = get_secret(driver, reason)
    actions = copy.deepcopy(actions)
    return user, censor_user, secret, actions


def parse_arguments(version):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="config.json", help="Specify config file"
    )
    parser.add_argument("-v", "--version", action="version", version=version)
    args = parser.parse_args()
    return args


def main():
    global driver, config

    config = read_config(args.config)
    driver_class = select_driver(config.driver)
    get_secret = get_secret_method(config.method)
    authenticate = get_authentication_method(config.auth_method)

    driver = driver_class()
    bring_to_front(driver)
    authenticate(driver)

    # Wait for the next page to load
    WebDriverWait(driver, 60).until(EC.title_is("Accounts"))

    # Get the login table
    driver.switch_to.frame("frame-epv")
    find_count_class = ".grid-title__title__filter__results"
    selector = (By.CSS_SELECTOR, find_count_class)
    _ = await_text_in_element(driver, selector, "results", 20)

    elem_logins = await_element(driver, (By.CSS_SELECTOR, "[ref=eBodyContainer]"))
    elem_actions = await_element(driver, (By.CSS_SELECTOR, "[ref=eRightContainer]"))

    # Get table elements
    children_logins = get_children(elem_logins)
    children_actions = get_children(elem_actions)
    rows = zip(children_logins, children_actions)

    # Get the logins
    print("Logins:")
    for row in rows:
        user, censor_user, secret, actions = get_row_secret(get_secret, row)
        if user is not None:
            censor_local = config.censor or censor_user
            if censor_local:
                secret = len(secret) * "█"

            print(f"{padding}{user}: {secret}")

            param_object = {"user": user, "password": secret}
            run_action_specs(actions, param_object)

            sleep(3)

    save_config(config, args.config)


def close():
    if driver is not None:
        driver.stop_client()
        driver.quit()

    frozen_exit()


def excepthook(type, value, traceback):
    global driver
    match type:
        case seleniumError.NoSuchWindowException:
            print("Why did you close the window?")
            driver = None
        case seleniumError.TimeoutException:
            print("Be quicker!")
        case seleniumError.WebDriverException:
            print("Web issue, please try again later.")
        case _:
            if type is KeyboardInterrupt:
                print("Goodbye.")
            else:
                print("Fatal exception:")
                sys.__excepthook__(type, value, traceback)
    close()


sys.excepthook = excepthook
args = parse_arguments(version)
main()
close()
