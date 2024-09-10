import pprint

import kobold

def assert_response_matches(expected,
                            response,
                            type_compare=None,
                            exception_context=None,
                            header_type_compare='existing'):
    '''
    If the responses don't match (in the kobold.compare sense),
    raise an AssertionError
    '''

    if type_compare is None:
        type_compare = {}
    result = kobold.response.response_matches(
        expected,
        response,
        type_compare=type_compare,
        header_type_compare=header_type_compare)
    raise_if_not_match(result, exception_context=exception_context)

def assert_equal(
        expected, 
        actual, 
        type_compare=None,
        exception_context=None):
    '''
    If two data structures don't match (in the kobold.compare sense),
    raise an AssertionError
    '''

    if type_compare is None:
        type_compare = {}
    result = kobold.compare.compare(expected, 
                     actual,
                     type_compare=type_compare)
    raise_if_not_match(result, exception_context=exception_context)

assert_match = assert_equal

def raise_if_not_match(result, exception_context=None):
    if result != 'match':
        expected_diff, actual_diff = result
        assertion_text =\
            "Expected\n\n%s\n\nBut Got\n\n%s" %\
                    (pprint.pformat(expected_diff),
                     pprint.pformat(actual_diff))
        if exception_context is None:
            exception_text = assertion_text
        else:
            exception_text = "{}: {}".format(exception_context, assertion_text)
        raise AssertionError(exception_text)

