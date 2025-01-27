import unittest

from kobold import hash_functions

class TestMakeHashable(unittest.TestCase):
    def test_str(self):
        str_to_test = 'a'
        result_str = hash_functions.make_hashable(str_to_test)
        self.assertEqual(
            str_to_test,
            result_str)
        dictionary = {result_str: result_str}
        self.assertEqual(
            result_str,
            dictionary[result_str])

    def test_list(self):
        list_to_test = ['a', 'b']
        result_list = hash_functions.make_hashable(list_to_test)
        self.assertEqual(
            list_to_test,
            result_list)
        dictionary = {result_list: result_list}
        self.assertEqual(
            result_list,
            dictionary[result_list])

    def test_dict(self):
        dict_to_test = {'a': 1}
        result_dict = hash_functions.make_hashable(dict_to_test)
        self.assertEqual(
            dict_to_test,
            result_dict)
        dictionary = {result_dict: result_dict}
        self.assertEqual(
            result_dict,
            dictionary[result_dict])

    def test_nested_dict(self):
        dict_to_test = {
            'a': {
                'a_1': {
                    'a_2': 1
                },
            }
        }
        result_dict = hash_functions.make_hashable(dict_to_test)
        self.assertEqual(
            dict_to_test,
            result_dict)
        dictionary = {result_dict: result_dict}
        self.assertEqual(
            result_dict,
            dictionary[result_dict])



