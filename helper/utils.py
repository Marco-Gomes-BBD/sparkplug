import sys


def frozen_exit():
    if getattr(sys, "frozen", False):
        input()
    sys.exit()


def dict_lookup(dict, key, default, lookup_handler=None):
    method = dict.get(key, None)
    if method is None:
        if lookup_handler is not None:
            lookup_handler(key)
        method = default
    return method
