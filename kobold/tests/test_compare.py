import unittest
from kobold import compare

JsonParsingHint = compare.get_parsing_hint('json')
ObjectDictParsingHint = compare.get_parsing_hint('object_dict')

class ObjectThing(object):
    def __init__(self, a=1, b=2, c=3):
        self.a = a
        self.b = b
        self.c = c

class TestCompare(unittest.TestCase):
    def test_empty_hashes(self):
        self.assertEqual('match', compare.compare({}, {}))

    def test_equal_hashes(self):
        self.assertEqual('match', compare.compare({'a' : 1}, {'a' : 1}))

    def test_distinct_keys(self):
        self.assertEqual(
                ({'a' : 1, 'b' : None}, {'a' : None, 'b' : 2}), 
                compare.compare(
                    {'a' : 1}, 
                    {'b' : 2}))

    def test_distinct_keys_only_existing(self):
        self.assertEqual(
                ({'a' : 1}, {'a' : None}), 
                compare.compare(
                    {'a' : 1}, 
                    {'b' : 2},
                    type_compare='existing'))

    def test_intersecting_keys(self):
        self.assertEqual(
                ({'a' : 1, 'c' : None}, {'a' : None, 'c' : 3}),
                compare.compare(
                    {'a' : 1, 'b' : 2},
                    {'b' : 2, 'c' : 3}))

    def test_same_keys_different_values(self):
        self.assertEqual(
                ({'a' : 1, 'b' : 2}, {'a' : 2, 'b' : 1}),
                compare.compare(
                    {'a' : 1, 'b' : 2},
                    {'a' : 2, 'b' : 1}))

    def test_ordered_lists(self):
        self.assertEqual(
                ([1, 2], [2, 1]),
                compare.compare(
                    [1, 2],
                    [2, 1]))

    def test_unordered_lists(self):
        self.assertEqual(
                'match',
                compare.compare(
                    [1, 2],
                    [2, 1],
                    type_compare={'ordered' : False}))

    def test_one_element_off(self):
        self.assertEqual(
                (['_', 2, '_'], ['_', 4, '_']),
                compare.compare(
                    [1, 2, 3],
                    [1, 4, 3]))

    def test_parseable_json_dict(self):
        expected = JsonParsingHint({'a' : 1})
        actual = '{"a" : 1}'
        self.assertEqual(
                'match',
                compare.compare(expected, actual))

    def test_parseable_json_list(self):
        expected = JsonParsingHint([1, 2, 3])
        actual = '[1, 2, 3]'
        self.assertEqual(
                'match',
                compare.compare(expected, actual))

    def test_parseable_json_mismatch(self):
        expected = JsonParsingHint({'a' : 1})
        actual = '{"a" : "1"}'
        self.assertEqual(
                ({'a' : 1}, {'a' : '1'}),
                compare.compare(expected, actual))

    def test_expected_list_longer_than_actual(self):
        expected = [{'a' : 1}, {'b' : 2}]
        actual = [{'a' : 1}]
        self.assertEqual(
                (['_', {'b' : 2}], ['_', compare.NotPresent]),
                compare.compare(expected, actual))

    def test_expected_list_shorter_than_actual(self):
        expected = [{'a' : 1}]
        actual = [{'a' : 1}, {'b' : 2}]
        self.assertEqual(
                (['_', compare.NotPresent], ['_', {'b' : 2}]),
                compare.compare(expected, actual))

    def test_compare_dict_with_object_dict(self):
        expected = {'a' : 1, 'b' : 2, 'c' : 3}
        actual = ObjectThing(a=1, b=2, c=3)
        self.assertEqual(
                'match',
                compare.compare(
                    ObjectDictParsingHint(expected),
                    actual))

    def test_compare_dict_with_object_dict_mismatch(self):
        expected = {'a' : 1, 'b' : 2, 'c' : 4}
        actual = ObjectThing(a=1, b=2, c=3)
        self.assertEqual(
                ({'c' : 4}, {'c' : 3}),
                compare.compare(
                    ObjectDictParsingHint(expected),
                    actual))

    def test_list_of_objects(self):
        expected = {'a' : 1, 'b' : 2, 'c' : 3}
        actual = [ObjectThing(a=1, b=2, c=4)]
        self.assertEqual(
                ([{'c' : 3}], [{'c' : 4}]),
                compare.compare(
                    [ObjectDictParsingHint(expected)],
                    actual))

   
