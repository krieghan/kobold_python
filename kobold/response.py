import json
import re

import kobold
from kobold import compare


def parse_body(content_type, content):
    if content_type is None:
        return content
    if content_type == 'application/json':
        return json.loads(content)
    elif re.compile('application/json;.*').search(content_type):
        return json.loads(content)
    else:
        return content


def response_matches(expected,
                     response,
                     type_compare=None,
                     header_type_compare='existing'):
    '''
    Compare two HTTP responses (using kobold.compare).
    A type_compare may be provided, but if none is set,
    the default is for hashes to be compared using "full" mode,
    and for lists to be compared using "ordered" mode.
    Headers, however, are supplied an override to ensure that 
    they are compared in "existing" mode.

    The first two arguments are the expected and actual response.
    Responses are expected to be a hash, with three keys: status_code,
    body and headers.  By default, the status_code of the response is 
    expected to be 200 (ie. success of the request is enforced), and no 
    headers are enforced.  

    Body will be a string, unless the actual response has a 
    Content-Type header of "application/json".  In that case,
    we parse the JSON and set body to be the parsed data structure.
    Remember, by default all keys in the body will be compared.
    type_compare can be set to "existing" to change this behavior.

    Ultimately, the expected and response hashes are compared using
    kobold.compare, and the result is returned.  In the case of a match,
    the result will be the string "match".  In the case of a mismatch,
    the result will be a tuple of two elements - the first describing
    the mismatched values in the first argument, and the second
    describing the mismatched values in the second argument.
    '''

    if expected is None:
        expected = {}
    if type_compare is None:
        type_compare = {
                'hash' : 'full',
                'ordered' : True}
    else:
        if isinstance(type_compare, str):
            type_compare = {
                    'hash' : type_compare,
                    'ordered' : True}

    default_expected =\
        {'status_code' : 200,
         'headers' : {}}

    for key, value in default_expected.items():
        expected.setdefault(key, value)

    # If the response code is 302, force the location
    # header to be included in the diff
    if (response.status_code == 302 and
            response.status_code != expected['status_code'] and
            getattr(expected['headers'], 'get', None) is not None and
            expected['headers'].get('location') is None):
        expected['headers']['location'] = kobold.NotPresent

    expected['headers'] = compare.TypeCompareHint(
        payload=expected['headers'],
        type_compare=header_type_compare
    )

    content_type = response.headers.get('content-type')
    actual = {'status_code' : response.status_code,
              'headers' : response.headers,
              'body' : parse_body(content_type, response.data)}


    return compare.compare(
        expected, 
        actual,
        type_compare
    )
