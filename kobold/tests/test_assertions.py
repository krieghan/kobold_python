import collections
import unittest
from kobold import assertions

class TestAssertEqual(unittest.TestCase):
    def test_empty_hashes(self):
        assertions.assert_equal({}, {})

    def test_distinct_keys(self):
        self.assertRaises(
                AssertionError,
                assertions.assert_equal,
                {'a' : 1},
                {'b' : 2})
        
Response = collections.namedtuple('Response', 'headers status_code data')

class TestAssertResponseMatches(unittest.TestCase):
    def test_empty_body(self):
        actual = Response(headers={}, status_code=200, data={})
        assertions.assert_response_matches({'body' : {},
                                            'status_code' : 200,
                                            'headers' : {}}, actual)

    def test_omit_status_and_headers(self):
        actual = Response(headers={}, status_code=200, data={})
        assertions.assert_response_matches({'body' : {}}, actual)

    def test_equal_bodies(self):
        actual = Response(
                headers={}, 
                status_code=200, 
                data={'key' : 'value'})
        assertions.assert_response_matches({'body' : {'key' : 'value'},
                                            'status_code' : 200,
                                            'headers' : {}}, actual)

    def test_unequal_bodies(self):
        actual = Response(
                headers={}, 
                status_code=200, 
                data={'key' : 'value'})
        self.assertRaises(
                AssertionError,
                assertions.assert_response_matches,
                {'body' : {'key' : 'anothervalue'},
                           'status_code' : 200,
                           'headers' : {}}, 
                actual)

    def test_unequal_headers(self):
        actual = Response(
                headers={'header' : 'value'}, 
                status_code=200, 
                data={'key' : 'value'})
        self.assertRaises(
                AssertionError,
                assertions.assert_response_matches,
                {'body' : {'key' : 'value'},
                           'status_code' : 200,
                           'headers' : {'header' : 'anothervalue'}}, 
                actual)

