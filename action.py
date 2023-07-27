from modules.module import import_module_path
import actions.azure as azure

builtin = {"azure": azure}


def run_action(module_name):
    module_import = import_module_path(module_name, "actions")
    module_builtin = builtin[module_name]
    module = module_import or module_builtin
    module.main()
