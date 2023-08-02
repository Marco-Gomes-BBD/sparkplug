import subprocess

from type.converter import str2bool


def command(cmd, recur=False):
    run = True
    while run:
        process = subprocess.Popen(cmd, text=True)
        code = process.wait()

        print(f"Code: {code}")
        run = code != 0 and recur


def main(**kwargs):
    cmd = kwargs["cmd"]
    recur = kwargs.get("recur", None)
    recur = str2bool(str(recur), False)

    command(cmd, recur)
