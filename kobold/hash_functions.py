import kobold
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
        default_for_key = default.get(key, kobold.NotPresent)
        extra_for_key = extra.get(key, kobold.NotPresent)
        if (isinstance(default_for_key, dict) and 
            isinstance(extra_for_key, dict)):
            new[key] = deep_combine(
                    default_for_key,
                    extra_for_key)
        else:
            new[key] = default_for_key
            if extra_for_key is not kobold.NotPresent:
                new[key] = extra_for_key
    return new


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
    if kobold.compare.acts_like_a_list(data_structure):
        new_data_structure = HashableList()
        for element in data_structure:
            new_data_structure.append(make_hashable(element))
        return new_data_structure
    elif kobold.compare.acts_like_a_hash(data_structure):
        new_data_structure = HashableDict()
        for key, value in data_structure.items():
            new_key = make_hashable(key)
            new_value = make_hashable(value)
            new_data_structure[new_key] = new_value
        return new_data_structure
    else:
        return data_structure


def get_from_args_and_kwargs(
        args,
        kwargs,
        arg_names,
        exclusive_args=None,
        args_in_hash=True):
    if exclusive_args is None:
        exclusive_args = []
    return_dict = {}
    return_list = []
    current_arg_index = 0
    exclusive_arg_keys = set(exclusive_args)
    for arg_name in arg_names:
        result = kwargs.get(arg_name, kobold.compare.NotPresent)

        if arg_name in exclusive_arg_keys:
            if current_arg_index >= len(args):
                continue
            value = args[current_arg_index]
            current_arg_index += 1
            if args_in_hash:
                return_dict[arg_name] = value
            else:
                return_list.append(value)
        else:
            if result is not kobold.compare.NotPresent:
                return_dict[arg_name] = result
            else:
                if current_arg_index >= len(args):
                    continue
                value = args[current_arg_index]
                current_arg_index += 1
                return_dict[arg_name] = value


    kwargs_keys = set(kwargs.keys())
    exclusive_kwarg_keys = kwargs_keys.difference(arg_names)
    for key in exclusive_kwarg_keys:
        return_dict[key] = kwargs.get(key)

    if args_in_hash:
        return return_dict
    else:
        return (return_list, return_dict)






