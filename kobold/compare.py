import json
import re
import six

from dateutil import parser

from kobold.hash_functions import (
        combine,
        acts_like_a_hash,
        acts_like_a_list)

def compare(expected, actual, type_compare=None):
    '''A wrapper around Compare.compare'''
    return Compare.compare(
            expected,
            actual,
            type_compare=type_compare)

class NotPresent(object):
    '''Used to explicitly specify that something isn't present,
       or wasn't supplied'''
    pass

class ValidationError(Exception):
    pass

class DontCare(object):
    '''Used as the "expected" argument in a comparison to mean "I don't 
       care what the 'actual' object is, as long as some rules hold."  
       By default, the rule is not_none_or_missing.
       
       Rules:

       not_none_or_missing: The second argument can be anything,
       as long as it is neither None nor NotPresent.
       
       list: The second argument can be anything, as long as it is
       an instance of list.
       
       json: The second argument may be any json-parseable string

       iso8601_datetime: The second argument must be able to be 
       evaluated as an ISO 8601 datetime string (eg. 
       2017-01-01T00:00:00)

       no_rules: The second argument may be anything - I literally
       do not care.
       '''

    
    def __init__(self,
                 rule='not_none_or_missing',
                 **kwargs):
        self.rule = rule
        self.options = kwargs
        self.validate()

    def validate(self):
        if self.rule == 'isinstance':
            if self.options.get('of_class') is None:
                raise ValidationError('isinstance dontcares must have an "of_class" option specivied')
        

    def compare_with(self, other_thing):
        if self.rule == 'not_none_or_missing':
            return other_thing is not None
        elif self.rule == 'list':
            if not isinstance(other_thing, list):
                return False

            if self.options['length']:
                return len(other_thing) == self.options['length']
        elif self.rule == 'json':
            try:
                json.loads(other_thing)
                return True
            except:
                return False
        elif self.rule == 'iso8601_datetime':
            try:
                parser.parse(other_thing)
                return True
            except:
                return False
        elif self.rule == 'isinstance':
            return isinstance(other_thing, self.options['of_class'])
        elif self.rule is None or self.rule == 'no_rules':
            return True
        else:
            raise NotImplementedError('DontCare rule {} not recognized'.format(self.rule))
        
class ListDiff(list):
    def __init__(self, arr=None, display_type=list):
        if arr is None:
            arr = []
        self.with_positions = arr
        self.display_type = display_type
        val = [x for x in arr if x != '_']
        super(ListDiff, self).__init__(val)

    def display(self):
        to_display = []
        return self.display_type(self.with_positions)

    def append_match(self):
        self.with_positions.append('_')

    def append(self, value):
        super(ListDiff, self).append(value)
        self.with_positions.append(value)


def get_parsing_hint(rule):
    class ParsingHint(object):
        '''Tells the comparison function to parse the 
           second argument ("actual") in a specific way to
           get a simple data-structure'''

        def __init__(self, payload):
            '''Rules'''
            self.payload = payload
            self.rule = rule

        def parse(self, thing_to_parse):
            if thing_to_parse is NotPresent:
                return NotPresent

            if self.rule == 'json':
                return json.loads(thing_to_parse)
            elif self.rule == 'object_dict':
                return thing_to_parse.__dict__
            elif self.rule == 'object_attr':
                attr_dict = {}
                for (key, value) in self.payload.items():
                    attr_dict[key] = getattr(thing_to_parse, key)
                return attr_dict

    return ParsingHint

JSONParsingHint = get_parsing_hint('json')
ObjectDictParsingHint = get_parsing_hint('object_dict')
ObjectAttrParsingHint = get_parsing_hint('object_attr')

class Compare(object):
    @classmethod
    def compare(cls,
                expected,
                actual,
                type_compare=None):
        '''
        Compare two arguments against each other.  If they are 
        dicts or lists, recursively compare their components.
        Return the difference.  If there is no difference, return the string
        'match'.  

        The third, optional argument is type_compare, which gives compare
        some information about how it should do matching.  The value may
        be either a string or a dictionary.  If it is a dictionary,
        the two keys are "hash" and "ordered".  If type_compare is a 
        string, the value is treated as the value for "hash".  

        The hash key may either be "full" or "existing".  Full means that
        two dictionaries must match entirely.  Existing means that only
        the keys in the first dictionary must match in the second
        dictionary (ie. the keys that are only in the second dictionary
        are ignored).

        The ordered key may be either True or False.  If it is True,
        lists that are compared against each other are expected
        to be ordered the same way.  If it is False, lists that are
        compared against each other are expected to have the same
        elements, but in any order.

        hash defaults to "full", and ordered defaults to True.

        The hash comparison mode may be overridden in a sub-hash, 
        by specifying a special key "__compare".  The mode names
        are the same - "full" and "existing"
        '''

        if type_compare is None:
            type_compare = {}
        elif isinstance(type_compare, str):
            type_compare = {'hash' : type_compare,
                            'ordered' : True}
        default_type_compare = {'hash' : 'full',
                                'ordered' : True}
        type_compare =\
            combine(default_type_compare, type_compare)

        if type(expected) == DontCare:
            if expected.compare_with(actual):
                return 'match'
            else:
                return ("dontcare: %s" % expected.rule,
                        actual)
        elif (type(expected) == re._pattern_type and 
              isinstance(actual, six.string_types)):
            match = expected.match(actual)
            if match:
                return 'match'
            else:
                return ('regex: %s' % expected.pattern, actual)
        elif (type(expected).__name__ == 'ParsingHint'):
            return cls.compare(
                    expected.payload,
                    expected.parse(actual),
                    type_compare)
        elif (acts_like_a_hash(expected) and 
              acts_like_a_hash(actual)):
            return cls.hash_compare(expected, 
                                    actual, 
                                    type_compare)
        elif (isinstance(expected, tuple) and isinstance(actual, tuple)):
            return cls.list_compare(expected,
                                    actual,
                                    type_compare,
                                    iter_type=tuple)
        elif (acts_like_a_list(expected) and 
              acts_like_a_list(actual)):
            return cls.list_compare(expected, 
                                    actual,
                                    type_compare,
                                    iter_type=list)

        else:
            if expected == actual:
                return 'match'
            else:
                return (expected, actual)

    @classmethod
    def hash_compare(cls,
                     expected,
                     actual,
                     type_compare={}):
        default_type_compare =\
            {'hash' : 'full',
             'dontcare_keys' : [],
             'ordered' : True}
        type_compare =\
            combine(default_type_compare, type_compare)
        if '__compare' in expected:
            compare_override = expected['__compare']
            if acts_like_a_hash(compare_override):
                type_compare = combine(default_type_compare, compare_override)
            else:
                type_compare['hash'] = compare_override
            expected = dict((k, v) for (k, v) in expected.items() if k != '__compare')

        expected_return = {}
        actual_return = {}

        if type_compare['hash'] == 'full':
            keys = set([])
            keys.update(expected.keys())
            keys.update(actual.keys())
        else:
            keys = set(expected.keys())

        for key in keys:
            if key in type_compare['dontcare_keys']:
                result = cls.compare(DontCare(), 
                                     actual.get(key, NotPresent),
                                     type_compare)
            else:
                result = cls.compare(expected.get(key, NotPresent),
                                     actual.get(key, NotPresent),
                                     type_compare)

            if result != 'match':
                expected_sub, actual_sub = result
                expected_return[key] = expected_sub
                actual_return[key] = actual_sub

        if len(expected_return) == 0:
            return 'match'
        else:
            return (expected_return, actual_return)

    @classmethod
    def ordered_list_compare(cls,
                             expected,
                             actual,
                             type_compare,
                             iter_type=list):
        expected_elements = ListDiff(display_type=iter_type)
        actual_elements = ListDiff(display_type=iter_type)

        for i in range(max(len(expected), len(actual))):
            if len(expected) > i:
                expected_value = expected[i]
            else:
                expected_value = NotPresent
            if len(actual) > i:
                actual_value = actual[i]
            else:
                actual_value = NotPresent
            match = True
            result = cls.compare(expected_value,
                                 actual_value,
                                 type_compare)
            if result == 'match':
                expected_elements.append_match()
                actual_elements.append_match()
            else:
                expected_sub, actual_sub = result
                expected_elements.append(expected_sub)
                actual_elements.append(actual_sub)

        if (len(expected_elements) == 0 and
            len(actual_elements) == 0):
            return 'match'
        else:
            return (expected_elements.display(),
                    actual_elements.display())

    @classmethod
    def unordered_list_compare(cls,
                               expected,
                               actual,
                               type_compare,
                               iter_type=list):
        # Make a list of all the indexes of the "expected" list 
        # and the "actual" list.  
        # Iterate through the "expected" list.  For each item,
        # try to find a corresponding match in the "actual" list
        # (by iterating through that - n^2 style).
        # If a match is found, remove the corresponding indexes
        # from the "expected" and "actual" lists.  What we're left
        # with is two lists of missing indexes (one from the expected,
        # one from the actual).
        
        missing_expected_indexes = list(range(len(expected)))
        missing_actual_indexes = list(range(len(actual)))
        expected_index_index = 0
        while expected_index_index < len(missing_expected_indexes):
            expected_index = missing_expected_indexes[expected_index_index]
            expected_element = expected[expected_index]
            actual_index_index = 0
            while actual_index_index < len(missing_actual_indexes):
                actual_index = missing_actual_indexes[actual_index_index]
                actual_element = actual[actual_index]
                result = cls.compare(expected_element, 
                                     actual_element, 
                                     type_compare)
                if result == 'match':
                    missing_expected_indexes.pop(expected_index_index)
                    missing_actual_indexes.pop(actual_index_index)
                    expected_index_index -= 1
                    actual_index_index -= 1
                    break
                actual_index_index += 1
            expected_index_index += 1

       
        # The remaining elements in the expected and actual
        # lists (the elements that didn't have a partner in the
        # other list) are all still "full".  My theory (unsubstantiated)
        # is that it is more helpful for them to be displayed "diffed".
        # The question is, diffed with what.  Since this is an unordered
        # comparison, there's no obviously right answer to that question.
        # I figure, let's diff the missing elements from the "expected" 
        # list with the missing elements from the "actual" list in order.
        # That should at least give us friendlier output.
        # So, this section gets us the ordered diffs of the remaining
        # elements
        max_len = max(len(expected), len(actual))
        displayed_expecteds = [None] * max_len
        displayed_actuals = [None] * max_len

        for i in range(max(len(missing_expected_indexes),
                           len(missing_actual_indexes))):
            if i < len(missing_expected_indexes):
                missing_expected_index = missing_expected_indexes[i]
                missing_expected = expected[missing_expected_index]
            else:
                missing_expected_index = None
                missing_expected = NotPresent

            if i < len(missing_actual_indexes):
                missing_actual_index = missing_actual_indexes[i]
                missing_actual = actual[missing_actual_index]
            else:
                missing_actual_index = None
                missing_actual = NotPresent

            displayed_expected = cls.display(
                    missing_expected,
                    missing_actual)
            displayed_actual = cls.display(
                    missing_actual,
                    missing_expected)


            if missing_expected_index is not None:
                displayed_expecteds[missing_expected_index] = displayed_expected

            if missing_actual_index is not None:
                displayed_actuals[missing_actual_index] = displayed_actual

        # For each element of the expected and actual lists,
        # if there was a match, just append the "match" character
        # (_).  If there wasn't a match, append the in-order diff
        # from above.
        expected_return = ListDiff(display_type=iter_type)
        actual_return = ListDiff(display_type=iter_type)
        for i in range(len(expected)):
            if i in missing_expected_indexes:
                expected_return.append(displayed_expecteds[i])
            else:
                expected_return.append_match()

        for j in range(len(actual)):
            if j in missing_actual_indexes:
                actual_return.append(displayed_actuals[j])
            else:
                actual_return.append_match()

        if (len(expected_return) == 0 and
            len(actual_return) == 0):
            return 'match'
        else:
            return (expected_return.display(),
                    actual_return.display())
                                 
    @classmethod
    def list_compare(cls,
                     expected,
                     actual,
                     type_compare,
                     iter_type=list):
        default_type_compare =\
            {'hash' : 'full',
             'ordered' : True}

        type_compare =\
            combine(default_type_compare, type_compare)

        if type(expected) == set and type(actual) == set:
            isset = True
            expected = list(expected)
            actual = list(actual)
        else:
            isset = False

        if type_compare['ordered'] and not isset:
            ret = cls.ordered_list_compare(expected,
                                           actual,
                                           type_compare,
                                           iter_type=iter_type)
        else:
            ret = cls.unordered_list_compare(expected,
                                             actual,
                                             type_compare,
                                             iter_type=iter_type)
        if ret == 'match' or not isset:
            return ret
        else:
            ret_exp, ret_act = ret
            ret_exp = [x for x in ret_exp if x != '_']
            ret_act = [x for x in ret_act if x != '_']
            return (set(ret_exp), set(ret_act))


    # These "display" functions are used by the unordered list comparison
    # for intelligently displaying unordered diffs of lists
    @classmethod
    def display(cls, element, other_element):
        if type(element) == DontCare:
            return "dontcare: %s" % element.rule
        elif acts_like_a_hash(element) and acts_like_a_hash(other_element):
            return cls.display_hash(element, other_element)
        elif isinstance(element, tuple) and isinstance(other_element, tuple):
            return cls.display_list(element, other_element, iter_type=tuple)
        elif acts_like_a_list(element) and acts_like_a_list(other_element):
            return cls.display_list(element, other_element, iter_type=list)
        elif type(element) == re._pattern_type:
            return 'regex: %s' % element.pattern
        elif type(other_element).__name__ == 'ParsingHint':
            return cls.display(other_element.parse(element), other_element.payload)
        elif type(element).__name__ == 'ParsingHint':
            return cls.display(element.payload, element.parse(other_element))
        else:
            return element

    @classmethod
    def display_hash(cls, one_hash, other_hash):
        display_hash = {}
        for key in one_hash.keys():
            display_hash[key] = cls.display(one_hash.get(key), other_hash.get(key))

        return display_hash

    @classmethod
    def display_list(cls, one_list, other_list, iter_type=list):
        max_len = max(len(one_list), len(other_list))
        display_list = []

        for i in range(max_len):
            if i > len(one_list):
                element = NotPresent
            else:
                element = one_list[i]

            if i > len(other_list):
                other_element = NotPresent
            else:
                other_element = other_list[i]

            display_list.append(cls.display(element, other_element))
        return iter_type(display_list)


