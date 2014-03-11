import json
from compare import Compare

def parse_body(content_type, content):
    if content_type == 'application/json':
        return json.loads(content)
    else:
        return content

def response_matches(expected,
                     response,
                     compare=None):
    if compare is None:
        compare = {'hash' : 'full',
                   'list' : 'full',
                   'ordered' : True}
    else:
        if isinstance(compare, str):
            compare = {'hash' : compare,
                       'list' : compare,
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

    return Compare.compare(expected, 
                           actual,
                           compare)
