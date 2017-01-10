from kobold import doubles

class SafeSwap(object):
    def __init__(self):
        self.registry = {}

    def rollback(self):
        for ((host_name, member_name), (host, original_member)) in self.registry.items():
            setattr(host, member_name, original_member)

    def unswap(self, host, member_name):
        key = self.get_key(host, member_name)
        original_member = self.registry[key]
        setattr(host, member_name, original_member)
        del self.registry[key]

    def swap(self, 
             host,
             member_name,
             new_member):
        key = self.get_key(host, member_name)
        if not key in self.registry:
            self.registry[key] = (host, getattr(host, member_name, None))

        setattr(host, member_name, new_member)

    def get_key(self,
                host,
                member_name):
        return (id(host), member_name)

    def install_proxy(self,
                      host,
                      member_name,
                      proxy_factory=doubles.SpyFunction,
                      stub_function_factory=doubles.StubFunction):
        key = self.get_key(host, member_name)
        proxy = proxy_factory(stub_function_factory=stub_function_factory)
        self.swap(host, member_name, proxy)
        (host, original_member) = self.registry[key]
        proxy.stub_function.calls(original_member)
        return proxy
        
        


