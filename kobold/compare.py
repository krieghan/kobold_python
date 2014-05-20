import re
import json
from dateutil import parser

from hash_functions import combine

def acts_like_a_hash(candidate):
    return hasattr(candidate, 'items')

def acts_like_a_list(candidate):
    return isinstance(candidate, list)

class DontCare(object):
    def __init__(self,
                 rule='not_none_or_missing',
                 **kwargs):
        self.rule = rule
        self.options = kwargs

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
        elif self.rule is None or self.rule == 'no_rules':
            return True
        
class ListDiff(list):
    def __init__(self, arr=None):
        if arr is None:
            arr = []
        self.with_positions = arr
        val = [x for x in arr if x != '_']
        super(ListDiff, self).__init__(val)

    def display(self):
        return self.with_positions

    def append_match(self):
        self.with_positions.append('_')

    def append(self, value):
        super(ListDiff, self).append(value)
        self.with_positions.append(value)
        
class Compare(object):
    @classmethod
    def compare(cls,
                expected,
                actual,
                type_compare={}):
        default_type_compare = {'hash' : 'full',
                                'list' : 'full',
                                'ordered' : True}
        type_compare =\
            combine(default_type_compare, type_compare)

        if expected.__class__ == DontCare:
            if expected.compare_with(actual):
                return 'match'
            else:
                return ("dontcare: %s" % expected.rule,
                        actual)
        elif (acts_like_a_hash(expected) and 
              acts_like_a_hash(actual)):
            return cls.hash_compare(expected, 
                                    actual, 
                                    type_compare)
        elif (acts_like_a_list(expected) and 
              acts_like_a_list(actual)):
            return cls.list_compare(expected, 
                                    actual,
                                    type_compare)
        elif (expected.__class__ == re._pattern_type and isinstance(actual, basestring)):
            match = expected.match(actual)
            if match:
                return 'match'
            else:
                return ('regex: %s' % expected.pattern, actual)
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
             'list' : 'full',
             'dontcare_keys' : [],
             'ordered' : True}
        type_compare =\
            combine(default_type_compare, type_compare)
        if expected.has_key('__compare'):
            compare_override = expected['__compare']
            if acts_like_a_hash(compare_override):
                type_compare = combine(default_type_compare, compare_override)
            else:
                type_compare['hash'] = compare_override
                type_compare['list'] = compare_override
            del(expected['__compare'])

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
                                     actual.get(key),
                                     type_compare)
            else:
                result = cls.compare(expected.get(key),
                                     actual.get(key),
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
                             type_compare):
        if len(expected) != len(actual):
            return (expected, actual)
        else:
            expected_elements = ListDiff()
            actual_elements = ListDiff()

        for i in range(len(expected)):
            expected_value = expected[i]
            actual_value = actual[i]
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
                               type_compare):
        missing_expected_indexes = range(len(expected_list))
        missing_actual_indexes = range(len(actual_list))
        for i in range(len(expected_list)):
            expected_element = expected[i]
            for j in missing_actual_indexes:
                actual_element = actual[j]
                result = cls.compare(expected_element, 
                                     actual_element, 
                                     type_compare)
                if result == 'match':
                    missing_expected_indexes.delete(i)
                    missing_actual_indexes.delete(j)
                    break

        expected_return = ListDiff()
        actual_return = ListDiff()
        for i in len(expected_list):
            if i in missing_expected_indexes:
                expected_return.append(expected[i])
            else:
                expected_return.append_match()

        for j in len(actual_list):
            if j in missing_actual_indexes:
                actual_return.append(actual[j])
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
                     type_compare):
        default_type_compare =\
            {'hash' : 'full',
             'list' : 'full',
             'ordered' : True}
        type_compare =\
            combine(default_type_compare, type_compare)

        if type_compare['ordered']:
            return cls.ordered_list_compare(expected,
                                            actual,
                                            type_compare)
        else:
            return cls.unordered_list_compare(expected,
                                              actual,
                                              type_compare)

