import subprocess
import pyperclip

command = ["aws-azure-login.cmd"]
process = subprocess.Popen(
    command,
    stdin=subprocess.PIPE,
    text=True,
)

# Write input to the process
password = pyperclip.paste()
password.strip("\n\t ")
process.stdin.write(f"${password}\n")
process.stdin.flush()
process.wait()
