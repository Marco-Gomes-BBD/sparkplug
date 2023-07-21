import os
import sys
import time
from dotenv_flow import dotenv_flow

import pyautogui as ag
import pygetwindow as gw
import subprocess

next_image = os.path.join("res", "next.png")
signin_image = os.path.join("res", "signin.png")

# Get environment
dotenv_flow("")
email = os.getenv("STDB_EMAIL")
password = os.getenv("STDB_PASSWORD")


def close():
    if getattr(sys, "frozen", False):
        input()
    exit()


def getElementBounds(box):
    bounds = None
    if box is not None:
        left, top, width, height = box.left, box.top, box.width, box.height
        bounds = (left, top, width, height)
    return bounds


def getCenter(bounds):
    left, top, width, height = bounds
    x, y = left + width // 2, top + height // 2
    return x, y


def getElementCenter(element):
    bounds = getElementBounds(element)
    x, y = getCenter(bounds)
    return x, y


def wait_biggest_window(name: str, timeout: float):
    login_window = None
    start_time = time.time()
    while login_window is None:
        windows = gw.getWindowsWithTitle(name)

        if len(windows) == 2:
            login_window = max(windows, key=lambda w: w.width * w.height)

        current_time = time.time() - start_time
        if current_time >= timeout:
            break
        time.sleep(1 / 50)
    return login_window


def typeWaitElement(image, text, bounds, searchTime: int = 60):
    element = ag.locateOnScreen(image, region=bounds, minSearchTime=searchTime)
    ag.typewrite(text)
    if element is not None:
        x, y = getElementCenter(element)
        ag.click(x, y)


citrix = r"C:\Program Files\Citrix\Secure Access Client\nsload"
citrix_name = "Citrix Secure Access"
subprocess.Popen(citrix)

login_window = wait_biggest_window(citrix_name, 10)
if login_window is None:
    print("Window not found.")
    close()
login_window.activate()

window = gw.getActiveWindow()
if window.title == citrix_name:
    bounds = getElementBounds(window)
    typeWaitElement(next_image, email, bounds)
    typeWaitElement(signin_image, password, bounds)
