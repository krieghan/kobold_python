from response import response_matches
from compare import compare

def assert_response_matches(expected,
                            response,
                            type_compare=None):
    if type_compare is None:
        type_compare = {}
    result = response_matches(expected,
                              response,
                              type_compare=type_compare)
    raise_if_not_match(result)

def assert_equal(
        expected, 
        actual, 
        type_compare=None):
    if type_compare is None:
        type_compare = {}
    result = compare(expected, 
                     actual,
                     type_compare=type_compare)
    raise_if_not_match(result)

def raise_if_not_match(result):
    if result != 'match':
        expected_diff, actual_diff = result
        raise AssertionError(
                "Expected %s\nBut Got %s" %\
                        (expected_diff,
                         actual_diff))

