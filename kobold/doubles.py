import types
from kobold import compare

class StubRoutingException(Exception):
    pass

class StubFunction(object):
    def __init__(self, returns=None, raises=None, calls=None, *args, **kwargs):
        self.to_return = returns
        self.to_raise = raises
        self.to_call = calls

    def returns(self, to_return):
        self.to_return = to_return
        self.to_raise = None
        self.to_call = None

    def raises(self, to_raise):
        self.to_raise = to_raise
        self.to_return = None
        self.to_call = None

    def calls(self, to_call):
        self.to_call = to_call
        self.to_return = None
        self.to_raise = None

    def __call__(self, *args, **kwargs):
        if self.to_raise:
            raise self.to_raise
        elif self.to_call:
            return self.to_call(*args, **kwargs)
        else:
            return self.to_return

class SpyFunction(object):
    def __init__(self, stub_function_factory=StubFunction, *args, **kwargs):
        self.stub_function = stub_function_factory(*args, **kwargs)
        self.calls = []

    def reset(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.stub_function(*args, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

def get_spy_class(*methods_to_add):

    class SpyClass(object):
        pass

    methods_to_add = set(methods_to_add)
    methods_to_add.add('__init__')
    for method_name in methods_to_add:
        setattr(SpyClass, method_name, SpyFunction())

    return SpyClass

class RoutableStubFunction(object):
    '''A stub that can return different things based on the arguments 
       that it's called with.'''

    def __init__(self, default_route=None, *args, **kwargs):
        self.routes = []
        if default_route is not None and len(default_route) == 2:
            default_route = ('default',) + default_route
        self.default_route = default_route

    def add_route(self, condition, stub_type, stub_value):
        self.routes.append((condition, stub_type, stub_value))
        if condition == 'default':
            self.default_route = ('default', stub_type, stub_value)

    def clear_routes(self):
        self.routes = []
        self.default_route = None

    def __call__(self, *args, **kwargs):
        candidates = []
        for route in self.routes:
            condition, stub_type, stub_value = route
            if condition == 'default':
                continue
            
            if type(condition) == dict:
                if (len(condition.keys()) == 2 
                    and 'args' in condition.keys() 
                    and 'kwargs' in condition.keys()):
                    thing_to_compare = {'args' : args, 'kwargs' : kwargs}
                else:
                    thing_to_compare = kwargs
            elif type(condition) == tuple:
                thing_to_compare = args
            else:
                raise Exception("Unknown condition type: %s" % type(condition))

            if compare.compare(
                    condition, 
                    thing_to_compare, 
                    type_compare='existing') == 'match':
                candidates.append(route)
                

        if len(candidates) == 0:
            if self.default_route:
                candidates.append(self.default_route)

        if len(candidates) > 1:
            raise StubRoutingException("More than one route candidate for stub: %s" % candidates)

        if len(candidates) == 0:
            raise StubRoutingException("No route candidates for stub")

        (condition, stub_type, stub_value) = candidates[0]

        if stub_type == 'value':
            return stub_value

        if stub_type == 'callable':
            return stub_value(*args, **kwargs)

        if stub_type == 'exception':
            raise stub_value



