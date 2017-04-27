import json

from kobold.compare import compare

def parse_body(content_type, content):
    if content_type == 'application/json':
        return json.loads(content)
    else:
        return content

def response_matches(expected,
                     response,
                     type_compare=None):
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
    default_expected_headers =\
        {'__compare' : 'existing'}

    for key, value in default_expected.items():
        expected.setdefault(key, value)

    for key, value in default_expected_headers.items():
        expected['headers'].setdefault(key, value)

    content_type = response.headers.get('Content-Type')
    actual = {'status_code' : response.status_code,
              'headers' : response.headers,
              'body' : parse_body(content_type, response.data)}

    return compare(expected, 
                   actual,
                   type_compare)
