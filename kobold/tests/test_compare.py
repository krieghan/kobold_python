import unittest
from kobold import compare

JsonParsingHint = compare.get_parsing_hint('json')
ObjectDictParsingHint = compare.get_parsing_hint('object_dict')

class ObjectThing(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class TestCompare(unittest.TestCase):
    def test_empty_hashes(self):
        self.assertEqual('match', compare.compare({}, {}))

    def test_equal_hashes(self):
        self.assertEqual('match', compare.compare({'a' : 1}, {'a' : 1}))

    def test_distinct_keys(self):
        self.assertEqual(
                ({'a' : 1, 'b' : compare.NotPresent}, {'a' : compare.NotPresent, 'b' : 2}), 
                compare.compare(
                    {'a' : 1}, 
                    {'b' : 2}))

    def test_distinct_keys_only_existing(self):
        self.assertEqual(
                ({'a' : 1}, {'a' : compare.NotPresent}), 
                compare.compare(
                    {'a' : 1}, 
                    {'b' : 2},
                    type_compare='existing'))

    def test_intersecting_keys(self):
        self.assertEqual(
                ({'a' : 1, 'c' : compare.NotPresent}, {'a' : compare.NotPresent, 'c' : 3}),
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

    def test_compare_notpresent_with_object_dict(self):
        expected = {'a' : 1, 'b' : 2, 'c' : 3}
        self.assertEqual(
                ({'a' : 1, 'b' : 2, 'c' : 3},
                 compare.NotPresent),
                compare.compare(
                    ObjectDictParsingHint(expected),
                    compare.NotPresent))

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
    
    def test_list_of_objects_unordered(self):
        expected = [
                ObjectDictParsingHint({'a' : 1}),
                ObjectDictParsingHint({'a' : 2}),
                ObjectDictParsingHint({'a' : 3})]
        actual = [
                ObjectThing(a=4),
                ObjectThing(a=5),
                ObjectThing(a=6)]

        self.assertEqual(
                ([{'a' : 1}, {'a' : 2}, {'a' : 3}],
                 [{'a' : 4}, {'a' : 5}, {'a' : 6}]),
                compare.compare(
                    expected, 
                    actual,
                    type_compare={'hash' : 'existing',
                                  'ordered' : False}))

    def test_unordered_comparison_object_dict_one_item(self):
        expected = [
                ObjectDictParsingHint(
                    dict(a=1, b=2, c=3, d=4, e=5))]
        actual = [
                ObjectThing(a=1, b=3, c=3, d=4, e=5)]
        self.assertEqual(
                ([dict(a=1, b=2, c=3, d=4, e=5)],
                 [dict(a=1, b=3, c=3, d=4, e=5)]),
                compare.compare(
                    expected,
                    actual,
                    type_compare={'hash' : 'existing',
                                  'ordered' : False}))

    def test_unordered_comparison_object_dict_multiple_items(self):
        expected = [
                ObjectDictParsingHint(dict(a=1, b=2)),
                ObjectDictParsingHint(dict(a=2, b=3)),
                ObjectDictParsingHint(dict(a=3, b=4))]
        actual = [ObjectThing(a=2, b=3),
                  ObjectThing(a=2, b=1),
                  ObjectThing(a=3, b=2)]
        self.assertEqual(
                ([dict(a=1, b=2), '_', dict(a=3, b=4)],
                 ['_', dict(a=2, b=1), dict(a=3, b=2)]),
                compare.compare(
                    expected,
                    actual,
                    type_compare={'hash' : 'existing',
                                  'ordered' : False}))

    def test_two_sets(self):
        expected = set([1, 2, 3])
        actual = set([1, 3, 4])
        self.assertEqual(
            (set([2]), set([4])),
            compare.compare(expected, actual))


    def test_tuples(self):
        expected = (1, 2, 3, 4)
        actual = (1, 2, 4, 4)
        self.assertEqual(
            (('_', '_', 3, '_'), ('_', '_', 4, '_')),
            compare.compare(expected, actual))

    def test_list_of_tuples(self):
        expected = [(1, 2), (3, 4), (5, 6)]
        actual = [(1, 2), (3, 5), (5, 6)]
        self.assertEqual(
            (['_', ('_', 4), '_'], ['_', ('_', 5), '_']),
            compare.compare(expected, actual))

    def test_tuple_of_tuples(self):
        expected = ((1, 2), (3, 4), (5, 6))
        actual = ((1, 2), (3, 5), (5, 6))
        self.assertEqual(
            (('_', ('_', 4), '_'), ('_', ('_', 5), '_')),
            compare.compare(expected, actual))

    def test_tuple_of_lists(self):
        expected = ([1, 2], [3, 4], [5, 6])
        actual = ([1, 2], [3, 5], [5, 6])
        self.assertEqual(
            (('_', ['_', 4], '_'), ('_', ['_', 5], '_')),
            compare.compare(expected, actual))

    def test_sets_of_distinct_tuples(self):
        expected = set([(1, 2)])
        actual = set([(3, 4)])
        self.assertEqual(
            (set([(1, 2)]), set([(3, 4)])),
            compare.compare(expected, actual))

    def test_sets_of_intersecting_tuples(self):
        expected = set([(1, 2)])
        actual = set([(2, 3)])
        self.assertEqual(
            (set([(1, 2)]), set([(2, 3)])),
            compare.compare(
                expected, 
                actual,
                type_compare={'ordered' : False}))

    def test_compare_none_with_not_present(self):
        expected = {}
        actual = {'a' : None}
        self.assertEqual(
                ({'a' : compare.NotPresent}, {'a' : None}),
                compare.compare(
                    expected,
                    actual,
                    type_compare='full'))

    def test_compare_empty_list_with_empty_hash(self):
        expected = {}
        actual = []
        self.assertEqual(
            ({}, []),
            compare.compare(
                expected,
                actual))

    def test_compare_empty_hash_with_empty_list(self):
        expected = []
        actual = {}
        self.assertEqual(
            ([], {}),
            compare.compare(
                expected,
                actual))

    def test_compare_nonempty_list_with_nonempty_hash(self):
        expected = {'a': 1}
        actual = [1]
        self.assertEqual(
            ({'a': 1}, [1]),
            compare.compare(
                expected,
                actual))


