import os
import time

import pyperclip

import pyautogui as ag
import pygetwindow as gw
import subprocess

next_image = os.path.join("res", "aws_next.png")

login_window_name = "Sign in to your account"


def console_login(password):
    command = ["aws-azure-login.cmd"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        text=True,
    )

    # Write input to the process
    process.stdin.write(password)
    process.stdin.write("\n")
    process.stdin.flush()
    process.wait()


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


def typeWaitElement(image, text, bounds, searchTime: int = 60):
    element = ag.locateOnScreen(image, region=bounds, minSearchTime=searchTime)
    ag.typewrite(text)
    if element is not None:
        x, y = getElementCenter(element)
        ag.click(x, y)


def wait_login_window(name: str, timeout: float):
    login_window = None
    start_time = time.time()
    while login_window is None:
        windows = gw.getWindowsWithTitle(name)

        if len(windows) == 1:
            login_window = windows[0]

        current_time = time.time() - start_time
        if current_time >= timeout:
            break
        time.sleep(1 / 50)
    return login_window


def gui_login(password):
    cmd = ["aws-azure-login.cmd", "--mode=gui"]
    process = subprocess.Popen(cmd)

    window = wait_login_window(login_window_name, 30)

    window = gw.getActiveWindow()
    if window.title == login_window_name:
        bounds = getElementBounds(window)
        typeWaitElement(next_image, password, bounds)

    process.wait()


password = pyperclip.paste()
gui_login(password)
