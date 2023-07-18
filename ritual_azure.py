import subprocess
import pyperclip


def console_login(password):
    command = ["aws-azure-login.cmd"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        text=True,
    )

    # Write input to the process
    process.stdin.write(f"${password}\n")
    process.stdin.flush()
    process.wait()


def gui_login(password):
    cmd = ["aws-azure-login.cmd", "--mode=gui"]
    process = subprocess.Popen(cmd)

    process.wait()
    print(len(password) * "*")


password = pyperclip.paste()
password.strip("\n\t ")

console_login(password)
