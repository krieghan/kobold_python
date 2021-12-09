import base64
import json
import pickle

import kobold


class ParsingHint(object):
    '''Tells the comparison function to parse the 
       second argument ("actual") in a specific way to
       get a simple data-structure'''


    def __init__(self, payload):
        '''Rules'''
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
        for (key, value) in self.payload.items():
            attr_dict[key] = getattr(
                    thing_to_parse, 
                    key, 
                    kobold.NotPresent)
        return attr_dict


class Base64Hint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        return base64.b64decode(thing_to_parse)

class PickleParsingHint(ParsingHint):
    def sub_parse(self, thing_to_parse):
        return pickle.loads(thing_to_parse)


