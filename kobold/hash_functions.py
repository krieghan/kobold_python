def project(hash_in, attributes):
    '''
    Given a dict and a list of keys, return a
    dict that only includes the keys in the list
    '''

    return dict(
        (key, value) for (key, value) 
        in hash_in.items() if key in attributes)

def merge(default, to_mutate):
    '''
    Mutate a dict (to_mutate) with defaults from the first.
    Obviously, if to_mutate already has a key, don't override it.
    Return the mutated dict.
    '''

    for key, value in default.items():
        to_mutate.setdefault(key, value)

    return to_mutate 

def combine(default, extra):
    '''
    Take two dicts and create a third dict with all the keys
    from both.  If both dicts share a key, the second dict
    overrides the first.  Return the new dict.
    '''

    new = {}
    for key, value in default.items():
        new[key] = value

    for key, value in extra.items():
        new[key] = value

    return new


