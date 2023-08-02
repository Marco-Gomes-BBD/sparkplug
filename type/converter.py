def str2bool(string: str, default: bool = None):
    string = string.lower()

    value = default
    if string in ("y", "yes", "t", "true", "on", "1"):
        value = True
    if string in ("n", "no", "f", "false", "off", "0"):
        value = False

    if value is None:
        raise ValueError("No default bool conversion specified.")
    return value
