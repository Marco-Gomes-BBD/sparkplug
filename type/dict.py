from collections import defaultdict


class MissingKeyDefaultDict(defaultdict):
    def __missing__(self, key):
        return "{" + key + "}"
