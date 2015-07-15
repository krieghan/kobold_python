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

