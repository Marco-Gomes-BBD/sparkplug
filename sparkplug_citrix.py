import os
import time
from dotenv_flow import dotenv_flow

import pygetwindow as gw
import subprocess

from helper.gui import typeWaitElement, getElementBounds
from helper.utils import frozen_exit

next_image = os.path.join("res", "citrix_next.png")
signin_image = os.path.join("res", "citrix_signin.png")

# Get environment
dotenv_flow("")
email = os.getenv("STDB_EMAIL")
password = os.getenv("STDB_PASSWORD")


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


citrix = r"C:\Program Files\Citrix\Secure Access Client\nsload"
citrix_name = "Citrix Secure Access"
subprocess.Popen(citrix)

login_window = wait_biggest_window(citrix_name, 10)
if login_window is None:
    print("Window not found.")
    frozen_exit("Press enter to exit...")
login_window.activate()

window = gw.getActiveWindow()
if window.title == citrix_name:
    bounds = getElementBounds(window)
    typeWaitElement(next_image, email, bounds)
    typeWaitElement(signin_image, password, bounds)
