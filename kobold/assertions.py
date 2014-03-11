from response import response_matches

def assert_response_matches(expected,
                            response,
                            compare=None):
    result = response_matches(expected,
                              response,
                              compare)
    if result != 'match':
        expected_diff, actual_diff = result
        raise AssertionError(
                "Expected %s\nBut Got %s" %\
                        (expected_diff,
                         actual_diff))

