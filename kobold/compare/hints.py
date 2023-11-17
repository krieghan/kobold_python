import base64
import binascii
import json
import pickle
import urllib.parse

import kobold


class ParsingHint(object):
    '''Tells the comparison function to parse the 
       second argument ("actual") in a specific way to
       get a simple data-structure'''


    def __init__(self, payload):
        self.payload = payload

    def __repr__(self):
        return '{}(payload={})'.format(
            self.__class__.__name__,
            self.payload)

    def parse(self, thing_to_parse):
        if thing_to_parse is kobold.NotPresent:
            return kobold.NotPresent

        result = self.sub_parse(thing_to_parse)
        return result

    def sub_parse(self, thing_to_parse):
        return thing_to_parse


class TypeCompareHint(ParsingHint):
    def __init__(self, payload, type_compare):
        self.payload = payload
        self.type_compare = type_compare

    def parse(self, *args, **kwargs):
        raise NotImplementedError(
            'TypeCompareHint should never be used in comparisons!')


class JSONParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        try:
            return json.loads(thing_to_parse)
        except (TypeError, json.decoder.JSONDecodeError):
            raise kobold.InvalidMatch


class ObjectDictParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        return thing_to_parse.__dict__


class ObjectAttrParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        attr_dict = {}
        for (key, _) in self.payload.items():
            if len(key) > 1 and key[-2:] == '()':
                is_function = True
                attr_key = key[:-2]
            else:
                is_function = False
                attr_key = key

            value = getattr(
                thing_to_parse, 
                attr_key, 
                kobold.NotPresent)
            if is_function:
                try:
                    value = value()
                except Exception as e:
                    value = e
            
            attr_dict[key] = value
        return attr_dict


class Base64Hint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        try:
            return base64.b64decode(thing_to_parse)
        except binascii.Error:
            raise kobold.InvalidMatch

class PickleParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        return pickle.loads(thing_to_parse)

class UrlParsingHint(ParsingHint):
    def __init__(self, payload, qs_lists=True):
        super().__init__(payload)
        self.qs_lists = qs_lists

    def sub_parse(self, thing_to_parse):
        url, querystring = thing_to_parse.split('?')
        query_dict = urllib.parse.parse_qs(querystring)
        if not self.qs_lists:
            new_query_dict = {}
            for key, values in query_dict.items():
                if len(values) > 1:
                    raise AssertionError(
                        'len of values for qs key {} was {}, but '
                        'should be 1'.format(
                            key,
                            len(values)))
                new_query_dict[key] = values[0]
            query_dict = new_query_dict

        return {
            'url': url,
            'qs': query_dict}


class MultiMatch(ParsingHint):
    def __init__(self, payload):
        self.payload = payload
        self.count = 0

    def add_match(self, element):
        self.count += 1

    def matched(self):
        return self.count > 0


