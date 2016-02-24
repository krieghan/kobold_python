from kobold import doubles

class SafeSwap(object):
    def __init__(self):
        self.registry = {}

    def rollback(self):
        for ((host, member_name), original_member) in self.registry.items():
            setattr(host, member_name, original_member)

    def unswap(self, host, member_name):
        key = (host, member_name)
        original_member = self.registry[key]
        setattr(host, member_name, original_member)
        del self.registry[key]

    def swap(self, 
             host,
             member_name,
             new_member):
        key = (host, member_name)
        if not self.registry.has_key(key):
            self.registry[key] = getattr(host, member_name, None)

        setattr(host, member_name, new_member)

    def install_proxy(self,
                      host,
                      member_name,
                      proxy_factory=doubles.SpyFunction,
                      stub_function_factory=doubles.StubFunction):
        key = (host, member_name)
        proxy = proxy_factory(stub_function_factory=stub_function_factory)
        self.swap(host, member_name, proxy)
        original_member = self.registry[key]
        proxy.stub_function.calls(original_member)
        return proxy
        
        


