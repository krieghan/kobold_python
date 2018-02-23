from kobold import compare
import six


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

def deep_combine(default, extra):
    keys = set()
    keys.update(default.keys())
    keys.update(extra.keys())
    new = {}
    for key in keys:
        default_for_key = default.get(key, compare.NotPresent)
        extra_for_key = extra.get(key, compare.NotPresent)
        if (isinstance(default_for_key, dict) and 
            isinstance(extra_for_key, dict)):
            new[key] = deep_combine(
                    default_for_key,
                    extra_for_key)
        else:
            new[key] = default_for_key
            if extra_for_key is not compare.NotPresent:
                new[key] = extra_for_key
    return new


def acts_like_a_hash(candidate):
    return hasattr(candidate, 'items')

def acts_like_a_list(candidate):
    return (hasattr(candidate, '__iter__') and 
            hasattr(candidate, '__len__') and
            not isinstance(candidate, six.string_types) and
            not isinstance(candidate, dict))


# Based on https://stackoverflow.com/a/1151686/2619588'''
class HashableDict(dict):
    def __key(self):
        return tuple((k,self[k]) for k in sorted(self))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not isinstance(other, dict):
            return False

        if not isinstance(other, HashableDict):
            other = self.from_dict(other)
        return self.__key() == other.__key()

    @classmethod
    def from_dict(self, dictionary):
        return HashableDict(**dictionary)

class HashableList(list):
    def __key(self):
        return tuple(self)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not isinstance(other, list):
            return False

        if not isinstance(other, HashableList):
            other = self.from_list(other)
        return self.__key() == other.__key()

    @classmethod
    def from_list(self, original_list):
        new_list = HashableList()
        new_list.extend(original_list)
        return new_list

def make_hashable(data_structure):
    if acts_like_a_list(data_structure):
        new_data_structure = HashableList()
        for element in data_structure:
            new_data_structure.append(make_hashable(element))
        return new_data_structure
    elif acts_like_a_hash(data_structure):
        new_data_structure = HashableDict()
        for key, value in data_structure.items():
            new_key = make_hashable(key)
            new_value = make_hashable(value)
            new_data_structure[new_key] = new_value
        return new_data_structure
    else:
        return data_structure



