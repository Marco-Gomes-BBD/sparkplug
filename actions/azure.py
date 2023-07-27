import os
import time

import pygetwindow as gw
import subprocess

from helper.gui import getElementBounds, typeWaitElement

next_image = os.path.join("res", "aws_next.png")
signin_image = os.path.join("res", "aws_signin.png")

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


def gui_login(email, password):
    cmd = ["aws-azure-login.cmd", "--mode=gui"]
    process = subprocess.Popen(cmd)

    window = wait_login_window(login_window_name, 30)

    window = gw.getActiveWindow()
    if window.title == login_window_name:
        bounds = getElementBounds(window)
        typeWaitElement(next_image, email, bounds, 5)
        typeWaitElement(signin_image, password, bounds)

    process.wait()


def main(**kwargs):
    email = kwargs["account"]
    password = kwargs["password"]

    # TODO: Implement AWS profiles
    _profile = None
    # TODO: Allow console login
    gui_login(email, password)
