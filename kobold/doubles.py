import asyncio
import fnmatch
import types
import uuid

from kobold import (
        compare,
        hash_functions)

class StubFunction(object):
    '''A Stub is a Test Double that is intended to replace a real function
       with one that just behaves as configured.  Usually, this means
       returning a predefined value.  We extend this to mean returning a
       value, raising an exception, or calling another function and returning
       the result.

       The constructor takes three optional params: returns, raises and calls.

       -If returns is supplied, the function will return the value of returns
        when called.

       -If raises is supplied, the function will raise the value of raises
        when called

       -If calls is supplied, the function will call "calls" when it is 
        called.  We will return the value that the function returns.
    '''

    def __init__(self, returns=None, raises=None, calls=None, *args, **kwargs):
        self.to_return = returns
        self.to_raise = raises
        self.to_call = calls

    def returns(self, to_return):
        '''This will make StubFunction return this value when called'''
        self.to_return = to_return
        self.to_raise = None
        self.to_call = None

    def raises(self, to_raise):
        '''This will make StubFunction raise this exception when called'''
        self.to_raise = to_raise
        self.to_return = None
        self.to_call = None

    def calls(self, to_call):
        '''This will make StubFunction call this function when called
           (and return the value that the function returns)'''
        self.to_call = to_call
        self.to_return = None
        self.to_raise = None

    def __call__(self, *args, original_reference=None, **kwargs):
        if self.to_raise:
            raise self.to_raise
        elif self.to_call:
            return self.to_call(*args, **kwargs)
        else:
            return self.to_return

    def set_original_reference(self, original_reference):
        self.original_reference = original_reference

class StubCoroutine(StubFunction):
    async def __call__(self, *args, original_reference=None, **kwargs):
        if self.to_raise:
            raise self.to_raise
        elif self.to_call:
            return await self.to_call(*args, **kwargs)
        else:
            return self.to_return


class SpyFunction(object):
    '''A Spy is a Test Double that makes a record of each time it is called,
       typically to be queried later.  SpyFunction saves the args and
       kwargs everytime it's called.  It then defers to whatever stub function
       factory is supplied (by default StubFunction).  The args and kwargs
       are passed into StubFunction, so that a Spy can specify what it's
       return behavior is'''

    def __init__(self, stub_function_factory=StubFunction, *args, **kwargs):
        self.stub_function = stub_function_factory(*args, **kwargs)
        self.calls = []

    def reset(self):
        '''Forget any calls this spy has recorded'''
        self.calls = []
        if getattr(self.stub_function, 'reset', None) is not None:
            self.stub_function.reset()

    def __call__(self, *args, original_reference=None, **kwargs):
        self.calls.append((args, kwargs))
        return self.stub_function(
            *args,
            original_reference=original_reference,
            **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)

    def __getattr__(self, attr):
        try:
            return super(SpyFunction, self).__getattr__(attr)
        except AttributeError:
            return getattr(self.stub_function, attr)

class SpyCoroutine(SpyFunction):
    async def __call__(self, *args, original_reference=None, **kwargs):
        self.calls.append((args, kwargs))
        if asyncio.iscoroutinefunction(self.stub_function.__call__):
            return await self.stub_function(
                *args, 
                original_reference=original_reference,
                **kwargs)
        else:
            return self.stub_function(
                *args,
                original_reference=original_reference,
                **kwargs)

def get_stub_class(
        methods_to_add, 
        coroutines_to_add=None,
        is_callable=False):
    '''Creates a class whose methods are all spies.

       methods_to_add is dictionary or a list of methods to 
       add to the class that is returned.  The methods will
       all be SpyFunctions.  If methods_to_add is a dictionary, the
       method names are the keys, and the return types are the values.
       If methods_to_add is a list, the return types are all None.

       is_callable is a flag that defaults to False.  If it is 
       set to True, we will add a __call__ method to the class
       that will make instances of the class behave like a SpyFunctions.
    '''
    if coroutines_to_add is None:
        coroutines_to_add = {}

    class StubClass(object):
        def __init__(self, *args, **kwargs):
            for name, value in kwargs.items():
                setattr(self, name, value)

            if is_callable:
                self.calls = []

        if is_callable:
            def __call__(self, *args, **kwargs):
                self.calls.append((args, kwargs))

    if isinstance(methods_to_add, dict):
        for (method_name, return_value) in methods_to_add.items():
            spy_function = SpyFunction(returns=return_value)
            setattr(StubClass, method_name, spy_function)
    elif isinstance(methods_to_add, list):
        for method_name in methods_to_add:
            setattr(StubClass, method_name, SpyFunction(returns=None))
    for (method_name, return_value) in coroutines_to_add.items():
        spy_coroutine = SpyCoroutine(returns=return_value)
        setattr(StubClass, method_name, spy_coroutine)

    return StubClass
                

class Route(object):
    def __init__(self, condition, stub_type, stub_value, priority=0):
        self.condition = condition
        self.stub_type = stub_type
        self.stub_value = stub_value
        self.priority = priority

    def select(self):
        return (self.condition, self.stub_type, self.stub_value)

    def __repr__(self):
        return 'Route(condition={})'.format(self.condition)




class RotatingRoute(object):
    def __init__(self, condition, routes, priority=0):
        self.condition = condition
        self.routes = routes
        self.index = 0
        self.priority = priority

    def select(self):
        stub_type, stub_value = self.routes[self.index]
        self.index = (self.index + 1) % len(self.routes)
        return (self.condition, stub_type, stub_value)

    def add_route(self, route):
        self.routes.append(route)


class RoutableStubFunction(object):

    def __init__(self, default_route=None, *args, **kwargs):
        self.routes = {}
        self.route_indexes = {}
        if (default_route is not None and 
             not isinstance(default_route, Route)):
            raise NotImplementedError(
                'default_route must be of an instance of doubles.Route')
        self.default_route = default_route
        self.host = compare.NotPresent
        self.calls_by_key = {}

    def add_route(
            self,
            condition=None,
            stub_type=None,
            stub_value=None,
            route=None,
            key=None,
            route_priority=0):
        if key is None:
            key = uuid.uuid4().hex
        if route is None:
            route = Route(
                condition,
                stub_type,
                stub_value,
                priority=route_priority)

        self.routes[key] = route

        if route.condition == 'default':
            self.default_route = route

    def reset(self):
        self.calls_by_key = {}

    def clear_routes(self):
        self.routes = {}
        self.default_route = None

    def calls_for_pattern(self, pattern):
        match_calls = []
        for key, calls in self.calls_by_key.items():
            if fnmatch.fnmatch(key, pattern):
                match_calls.extend(calls)
        return match_calls

    def set_original_reference(self, original_reference):
        self.original_reference = original_reference

    def default_original(self, original_reference):
        self.default_route = Route('default', 'callable', original_reference)

    def get_candidates(self, args, kwargs):
        candidates = []
        for key, route in self.routes.items():
            condition = route.condition
            if condition == 'default':
                continue
            
            if hash_functions.acts_like_a_hash(condition):
                if set(condition.keys()).intersection(
                        set(['args', 'kwargs', 'self'])):
                    thing_to_compare = {
                        'args' : args,
                        'kwargs' : kwargs,
                        'self': self.host}
                    condition_self = condition.get('self')
                    if (condition_self is not None and 
                            isinstance(condition_self, dict)):
                        condition['self'] =\
                            compare.hints.ObjectAttrParsingHint(
                                condition_self)
                else:
                    thing_to_compare = kwargs
            elif hash_functions.acts_like_a_list(condition):
                thing_to_compare = args
            else:
                raise Exception("Unknown condition type: %s" % type(condition))

            if compare.compare(
                    condition, 
                    thing_to_compare, 
                    type_compare='existing') == 'match':
                candidates.append((key, route))

        if len(candidates) == 0:
            if self.default_route:
                candidates.append(('default', self.default_route))

        candidates = self.filter_candidates_for_priority(candidates)

        return candidates

    def filter_candidates_for_priority(self, candidates):
        if len(candidates) > 1:
            priorities = sorted([x[1].priority for x in candidates])
            best_priority = priorities[0]
            return [x for x in candidates if x[1].priority == best_priority]
        else:
            return candidates

    def __get__(self, obj, objtype):
        self.host = obj
        return self

    def __call__(self, *args, original_reference=None, **kwargs):
        candidates = self.get_candidates(args, kwargs)

        if len(candidates) > 1:
            raise StubRoutingException("More than one route candidate for stub: %s" % candidates)

        if len(candidates) == 0:
            raise StubRoutingException(
                "No route candidates for stub {} {}.  Routes: {}".format(
                    args,
                    kwargs,
                    self.routes))

        key, route = candidates[0]
        calls_for_key = self.calls_by_key.get(key)
        if calls_for_key is None:
            calls_for_key = self.calls_by_key[key] = []

        calls_for_key.append((args, kwargs))

        (condition, stub_type, stub_value) = route.select()
        if stub_type == 'value':
            return stub_value

        if stub_type == 'callable':
            if self.host is compare.NotPresent:
                to_call = stub_value
            else:
                to_call = stub_value.__get__(
                        self.host,
                        self.host.__class__)
            return to_call(*args, **kwargs)

        if stub_type == 'exception':
            raise stub_value

        if stub_type == 'original':
            if original_reference is None:
                original_reference = self.original_reference

            if self.host is compare.NotPresent:
                to_call = original_reference
            else:
                to_call = original_reference.__get__(
                        self.host,
                        self.host.__class__)
            return to_call(*args, **kwargs)


class RoutableStubCoroutine(RoutableStubFunction):
    async def __call__(self, *args, original_reference=None, **kwargs):
        candidates = self.get_candidates(args, kwargs)

        if len(candidates) > 1:
            raise StubRoutingException("More than one route candidate for stub: %s" % candidates)

        if len(candidates) == 0:
            raise StubRoutingException(
                "No route candidates for stub: {}; {}.  \n\nRoutes: {}".format(
                    args,
                    kwargs,
                    {k: r.condition for (k, r) in self.routes.items()}))

        key, route = candidates[0]

        calls_for_key = self.calls_by_key.get(key)
        if calls_for_key is None:
            calls_for_key = self.calls_by_key[key] = []

        calls_for_key.append((args, kwargs))

        (condition, stub_type, stub_value) = route.select()
        if stub_type == 'value':
            return stub_value

        if stub_type == 'callable':
            if self.host is compare.NotPresent:
                to_call = stub_value
            else:
                to_call = stub_value.__get__(
                        self.host,
                        self.host.__class__)
            return await to_call(*args, **kwargs)

        if stub_type == 'exception':
            raise stub_value

        if stub_type == 'original':
            if original_reference is None:
                original_reference = self.original_reference
            if self.host is compare.NotPresent:
                to_call = original_reference
            else:
                to_call = original_reference.__get__(
                        self.host,
                        self.host.__class__)
            return await to_call(*args, **kwargs)


class StubRoutingException(Exception):
    '''This exception indicates that a RoutableStubFunction could
       not determine which route to follow.  A RoutableStubFunction
       should always be able to identify exactly one route to 
       follow for each function call'''
    pass


