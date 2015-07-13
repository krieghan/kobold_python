from kobold import compare

class StubRoutingException(Exception):
    pass

class SafeSwap(object):

    def __init__(self):
        self.registry = {}

    def rollback(self):
        for ((host, member_name), original_member) in self.registry.items():
            setattr(host, member_name, original_member)

    def swap(self, 
             host,
             member_name,
             new_member):
        key = (host, member_name)
        if not self.registry.has_key(key):
            self.registry[key] = getattr(host, member_name)

        setattr(host, member_name, new_member)

class StubFunction(object):
    def __init__(self, returns=None):
        self.returns = returns

    def __call__(self, *args, **kwargs):
        return self.returns

class RoutableStub(object):
    '''A stub that can return different things based on the arguments 
       that it's called with.'''

    def __init__(self, default_route=None):
        self.routes = []
        if default_route is not None and len(default_route) == 2:
            default_route = ('default',) + default_route
        self.default_route = default_route

    def add_route(self, condition, stub_type, stub_value):
        self.routes.append((condition, stub_type, stub_value))
        if condition == 'default':
            self.default_route = ('default', stub_type, stub_value)

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



