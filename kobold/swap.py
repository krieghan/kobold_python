import asyncio

from kobold import doubles

class SafeSwap(object):
    '''Instances of this class manage runtime replacements of members,
       and enable all replacements to be undone with the rollback method'''
       
    def __init__(self):
        self.registry = {}

    def swap(self, 
             host,
             member_name,
             new_member,
             default_original=False):
        '''Given a host object, a member name, and some other object,
           replace the member of that name on that host with the given object.
           This can be undone with rollback()'''
        key = self.get_key(host, member_name)
        if not key in self.registry:
            self.registry[key] = (host, getattr(host, member_name, None))

        setattr(host, member_name, new_member)
        if default_original:
            new_member.default_original(self.registry[key][1])

    def install_proxy(self,
                      host,
                      member_name,
                      proxy_factory=doubles.SpyFunction,
                      stub_function_factory=doubles.StubFunction):
        '''Replace a member with a function that does something else,
           and then calls that original member (this is very similar
           to the idea of dynamically decorating a function at runtime, 
           except that the decoration will be undone when rollback is called.

           Typically, the idea here is to inject a spy in front of the
           original functionality.  So, the function will have the same
           result as it would without this replacement, except the spy remembers
           each call.'''
        key = self.get_key(host, member_name)
        proxy = proxy_factory(stub_function_factory=stub_function_factory)
        self.swap(host, member_name, proxy)
        (host, original_member) = self.registry[key]
        proxy.stub_function.calls(original_member)
        return proxy

    def make_decorator(
            self,
            decorated_function,
            before=None,
            after=None,
            on_failure=None):
        if asyncio.iscoroutinefunction(decorated_function):
            async def decorator(*args, **kwargs):
                if before:
                    before(*args, **kwargs)
                try:
                    ret = await decorated_function(*args, **kwargs)
                except Exception as e:
                    if on_failure:
                        return on_failure(e, *args, **kwargs)
                    else:
                        raise
                if after:
                    after(ret, *args, **kwargs)
                return ret
        else:
            def decorator(*args, **kwargs):
                if before:
                    before(*args, **kwargs)
                try:
                    ret = decorated_function(*args, **kwargs)
                except Exception as e:
                    if on_failure:
                        return on_failure(e, *args, **kwargs)
                    else:
                        raise
                if after:
                    after(ret, *args, **kwargs)
                return ret

        return decorator

    def install_decorator(self,
                          host,
                          member_name,
                          before=None,
                          after=None,
                          on_failure=None):
        decorator = self.make_decorator(
            getattr(host, member_name),
            before=before,
            after=after,
            on_failure=on_failure)
        self.swap(host, member_name, decorator)
        return decorator


    def unswap(self, host, member_name):
        '''Rollback a specific replacement'''
        key = self.get_key(host, member_name)
        (host, original_member) = self.registry[key]
        setattr(host, member_name, original_member)
        del self.registry[key]

    def rollback(self):
        '''Rollback all replacements (at the end of a test, for instance)'''
        for ((host_name, member_name), (host, original_member)) in self.registry.items():
            setattr(host, member_name, original_member)

    def get_key(self,
                host,
                member_name):
        return (id(host), member_name)

