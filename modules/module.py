import os
import sys

import importlib.util


def get_executable_location():
    return os.path.dirname(os.path.abspath(sys.executable))


def import_module_path(name, folder):
    executable_location = get_executable_location()
    script_path = os.path.join(executable_location, folder, name + ".py")
    module_name = f"{name}.{name}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module
