# from types.dict import MissingKeyDefaultDict
from modules.module import import_module_path
from type.dict import MissingKeyDefaultDict

import actions.azure as azure
import actions.example as example

builtin = {"azure": azure, "example": example}


def run_action(module_name, params):
    module_import = import_module_path(module_name, "actions")
    module_builtin = builtin[module_name]
    module = module_import or module_builtin
    module.main(**params)


def run_action_specs(actions, kwargs):
    kwargs = MissingKeyDefaultDict(**kwargs)

    for action_spec in actions:
        action = action_spec.get("action", None)
        params = action_spec.get("params", {})

        for k, v in params.items():
            if type(v) is str:
                v = v.format_map(kwargs)
            params[k] = v

        run_action(action, params)
