def merge(default, to_mutate):
    for key, value in default.items():
        to_mutate.setdefault(key, value)

    return to_mutate 

def combine(default, extra):
    new = {}
    for key, value in default.items():
        new[key] = value

    for key, value in extra.items():
        new[key] = value

    return new


