import base64
import json
import pickle

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
        return base64.b64decode(thing_to_parse)

class PickleParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        return pickle.loads(thing_to_parse)

class MultiMatch(ParsingHint):
    def __init__(self, payload):
        self.payload = payload
        self.count = 0

    def add_match(self, element):
        self.count += 1

    def matched(self):
        return self.count > 0


