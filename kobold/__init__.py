class NotPresent(object):
    '''Used to explicitly specify that something isn't present,
       or wasn't supplied'''
    pass


class InvalidMatch(Exception):
    pass


class ValidationError(Exception):
    pass


from . import (
    assertions,
    compare,
    doubles,
    hash_functions,
    response)
