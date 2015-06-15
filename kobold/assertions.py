from response import response_matches
from compare import Compare

def assert_response_matches(expected,
                            response,
                            compare=None):
    result = response_matches(expected,
                              response,
                              compare)
    raise_if_not_match(result)

def assert_equal(expected, actual, compare=None):
    result = Compare.compare(expected, 
                             actual,
                             type_compare=compare)
    raise_if_not_match(result)

def raise_if_not_match(result):
    if result != 'match':
        expected_diff, actual_diff = result
        raise AssertionError(
                "Expected %s\nBut Got %s" %\
                        (expected_diff,
                         actual_diff))

