import unittest
from kobold.compare import compare

class TestCompare(unittest.TestCase):
    def test_empty_hashes(self):
        self.assertEqual('match', compare({}, {}))

    def test_equal_hashes(self):
        self.assertEqual('match', compare({'a' : 1}, {'a' : 1}))

    def test_distinct_keys(self):
        self.assertEqual(
                ({'a' : 1, 'b' : None}, {'a' : None, 'b' : 2}), 
                compare(
                    {'a' : 1}, 
                    {'b' : 2}))

    def test_distinct_keys_only_existing(self):
        self.assertEqual(
                ({'a' : 1}, {'a' : None}), 
                compare(
                    {'a' : 1}, 
                    {'b' : 2},
                    type_compare='existing'))

    def test_intersecting_keys(self):
        self.assertEqual(
                ({'a' : 1, 'c' : None}, {'a' : None, 'c' : 3}),
                compare(
                    {'a' : 1, 'b' : 2},
                    {'b' : 2, 'c' : 3}))

    def test_same_keys_different_values(self):
        self.assertEqual(
                ({'a' : 1, 'b' : 2}, {'a' : 2, 'b' : 1}),
                compare(
                    {'a' : 1, 'b' : 2},
                    {'a' : 2, 'b' : 1}))

    def test_ordered_lists(self):
        self.assertEqual(
                ([1, 2], [2, 1]),
                compare(
                    [1, 2],
                    [2, 1]))

    def test_unordered_lists(self):
        self.assertEqual(
                'match',
                compare(
                    [1, 2],
                    [2, 1],
                    type_compare={'ordered' : False}))

    def test_one_element_off(self):
        self.assertEqual(
                (['_', 2, '_'], ['_', 4, '_']),
                compare(
                    [1, 2, 3],
                    [1, 4, 3]))



   
