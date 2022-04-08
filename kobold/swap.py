import asyncio
import inspect

from kobold import compare, doubles


class SafeSwap(object):
    '''Instances of this class manage runtime replacements of members,
       and enable all replacements to be undone with the rollback method'''
       
    def __init__(self):
        self.registry = {}

    def swap(self, 
             host,
             member_name,
             new_member,
             default_original=False,
             pass_original=False,
             swap_type='member'):
        '''Given a host object, a member name, and some other object,
           replace the member of that name on that host with the given object.
           This can be undone with rollback()'''
        key = self.get_key(host, member_name)
        if not key in self.registry:
            if swap_type == 'member':
                original = getattr(host, member_name, compare.NotPresent)
            elif swap_type == 'key':
                original = host.get(member_name, compare.NotPresent)

            self.registry[key] = (
                host,
                original,
                swap_type)

        if pass_original:
            def stub_wrapper(*args, **kwargs):
                return new_member(
                    *args,
                    original_reference=self.registry[key][1],
                    **kwargs)
            swap_target = stub_wrapper
        else:
            swap_target = new_member
        
        if swap_type == 'member':
            if new_member is compare.NotPresent:
                delattr(host, member_name)
            else:
                setattr(host, member_name, swap_target)
        elif swap_type == 'key':
            if new_member is compare.NotPresent:
                if host.get(member_name, compare.NotPresent) is not compare.NotPresent:
                    del host[member_name]
            else:
                host[member_name] = swap_target

        if getattr(new_member, 'set_original_reference', None) is not None:
            new_member.set_original_reference(self.registry[key][1])

        if default_original:
            new_member.default_original(self.registry[key][1])

    def install_proxy(self,
                      host,
                      member_name,
                      proxy_factory=compare.NotPresent,
                      stub_function_factory=compare.NotPresent):
        '''Replace a member with a function that does something else,
           and then calls that original member (this is very similar
           to the idea of dynamically decorating a function at runtime, 
           except that the decoration will be undone when rollback is called.

           Typically, the idea here is to inject a spy in front of the
           original functionality.  So, the function will have the same
           result as it would without this replacement, except the spy remembers
           each call.'''
        key = self.get_key(host, member_name)
        registry_entry = self.registry.get(
            key,
            None)

        if registry_entry is None:
            original_member = getattr(host, member_name)
        else:
            original_member = registry_entry[1]

        if inspect.iscoroutinefunction(original_member):
            if proxy_factory is compare.NotPresent:
                proxy_factory = doubles.SpyCoroutine
            if stub_function_factory is compare.NotPresent:
                stub_function_factory = doubles.StubCoroutine
        elif callable(original_member):
            if proxy_factory is compare.NotPresent:
                proxy_factory = doubles.SpyFunction
            if stub_function_factory is compare.NotPresent:
                stub_function_factory = doubles.StubFunction
        else:
            raise NotImplementedError(
                'Original member {}.{} is neither '
                'a coroutine nor a function'.format(
                    host,
                    member_name))

        proxy = proxy_factory(stub_function_factory=stub_function_factory)
        self.swap(host, member_name, proxy)
        (host, original_member, swap_type) = self.registry[key]
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
                    if asyncio.iscoroutinefunction(before):
                        await before(*args, **kwargs)
                    else:
                        before(*args, **kwargs)
                try:
                    ret = await decorated_function(*args, **kwargs)
                except Exception as e:
                    if on_failure:
                        return on_failure(e, *args, **kwargs)
                    else:
                        raise
                if after:
                    if asyncio.iscoroutinefunction(after):
                        ret = await after(ret, *args, **kwargs)
                    else:
                        ret = after(ret, *args, **kwargs)
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
                    ret = after(ret, *args, **kwargs)
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
        (host, original_member, swap_type) = self.registry[key]
        self._unswap(host, member_name, original_member, swap_type)
        del self.registry[key]

    def _unswap(self, host, member_name, original_member, swap_type):
        if swap_type == 'member':
            if original_member is compare.NotPresent:
                delattr(host, member_name)
            else:
                setattr(host, member_name, original_member)
        elif swap_type == 'key':
            if original_member is compare.NotPresent:
                if (host.get(member_name, compare.NotPresent)
                        is not compare.NotPresent):
                    del host[member_name]
            else:
                host[member_name] = original_member

    def rollback(self):
        '''Rollback all replacements (at the end of a test, for instance)'''
        for ((host_name, member_name),
             (host, original_member, swap_type)) in self.registry.items():
            self._unswap(host, member_name, original_member, swap_type)
        self.registry = {}

    def get_key(self,
                host,
                member_name):
        return (id(host), member_name)
