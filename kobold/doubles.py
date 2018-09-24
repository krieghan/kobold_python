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

    def __call__(self, *args, **kwargs):
        if self.to_raise:
            raise self.to_raise
        elif self.to_call:
            return self.to_call(*args, **kwargs)
        else:
            return self.to_return

class StubCoroutine(StubFunction):
    async def __call__(self, *args, **kwargs):
        return super(StubCoroutine, self).__call__(*args, **kwargs)


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

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.stub_function(*args, **kwargs)

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
    async def __call__(self, *args, **kwargs):
        return super(SpyCoroutine, self).__call__(*args, **kwargs)

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
                

class RoutableStubFunction(object):
    '''RoutableStubFunction is a special type of Stub that returns
       different results based on the arguments supplied.  The arguments form
       the basis of a "route".  A route determines which action is taken
       when the StubFunction is called.  A default_route may be supplied.  
       Default routes are followed if no other route matched.'''

    def __init__(self, default_route=None, *args, **kwargs):
        self.routes = {}
        self.route_indexes = {}
        if default_route is not None and len(default_route) == 2:
            default_route = ('default',) + default_route
        self.default_route = default_route
        self.host = compare.NotPresent
        self.calls_by_key = {}

    def add_route(self, condition, stub_type, stub_value, key=None):
        '''Add a route to the StubFunction.  A route consists of a 
           condition, a stub_type and a stub_value.

           A condition is the arguments received by the StubFunction that
           triggers the given result.  The condition argument may be a 
           dictionary of keyword arguments, a tuple of arguments, or a 
           dictionary with two keys - kwargs and args - that map to 
           keyword arguments and arguments, respectively.

           The stub_type is a string that is either "value", "exception"
           or "callable".  This determines whether the stub function
           returns a value, throws an exception, or returns the result
           of calling another function (respectively).  

           The third argument, stub_value is the value that is returned,
           the exception that is raised, or the function that is called,
           depending on what stub_type was specified to be.

           When the stub function is called, we iterate over each
           route.  Depending on the form that condition took when it 
           was provided, we compare the condition against either the args,
           the kwargs, or a dictionary with keys "args" and "kwargs"
           mapped to each.  The comparison is performed using kobold
           compare, with hashes being compared using the "existing"
           logic, and lists being given an ordered comparison.  This means,
           among other things, that regexes may be provided in the condition.

           If the route matches, it is added to the list of matching routes.
           If the route does not match, it is ignored and we move on to 
           the next.  When all the routes have been compared, if we ended
           up matching against exactly one route, we follow the action
           specified in the route (ie. return, raise or call the stub_value).
           If no routes matched, we use the default route, if it was provided.
           If no default route was provided, or if more than one route matched,
           we raise an exception.
           '''

        if key is None:
            key = uuid.uuid4().hex
        condition = hash_functions.make_hashable(condition)

        self.routes[key] = (condition, stub_type, stub_value)

        if condition == 'default':
            self.default_route = ('default', stub_type, stub_value)


    def clear_routes(self):
        '''Get rid of any route that has been setup, including the
           default_route'''
        self.routes = {}
        self.default_route = None

    def default_original(self, original_reference):
        self.default_route = ('default', 'callable', original_reference)

    def get_candidates(self, args, kwargs):
        candidates = []
        for key, route in self.routes.items():
            (condition, stub_type, stub_value) = route
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
                        condition['self'] = compare.ObjectAttrParsingHint(
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

        return candidates

    def __get__(self, obj, objtype):
        self.host = obj
        return self

    def __call__(self, *args, **kwargs):
        candidates = self.get_candidates(args, kwargs)

        if len(candidates) > 1:
            raise StubRoutingException("More than one route candidate for stub: %s" % candidates)

        if len(candidates) == 0:
            raise StubRoutingException("No route candidates for stub")

        key, route = candidates[0]
        calls_for_key = self.calls_by_key.get(key)
        if calls_for_key is None:
            calls_for_key = self.calls_by_key[key] = []

        calls_for_key.append((args, kwargs))

        (condition, stub_type, stub_value) = route
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

class RoutableStubCoroutine(RoutableStubFunction):
    async def __call__(self, *args, **kwargs):
        candidates = self.get_candidates(args, kwargs)

        if len(candidates) > 1:
            raise StubRoutingException("More than one route candidate for stub: %s" % candidates)

        if len(candidates) == 0:
            raise StubRoutingException(
                "No route candidates for stub: {}; {}".format(
                    args, kwargs))

        key, route = candidates[0]

        calls_for_key = self.calls_by_key.get(key)
        if calls_for_key is None:
            calls_for_key = self.calls_by_key[key] = []

        calls_for_key.append((args, kwargs))

        (condition, stub_type, stub_value) = route
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


class StubRoutingException(Exception):
    '''This exception indicates that a RoutableStubFunction could
       not determine which route to follow.  A RoutableStubFunction
       should always be able to identify exactly one route to 
       follow for each function call'''
    pass


