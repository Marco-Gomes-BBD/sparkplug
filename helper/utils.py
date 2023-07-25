import sys


def frozen_exit():
    if getattr(sys, "frozen", False):
        input()
    exit()


def dict_lookup(dict, key, lookup_handler, default):
    method = dict.get(key, None)
    if method is None:
        lookup_handler(key)
        method = default
    return method
