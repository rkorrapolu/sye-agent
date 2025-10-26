"""Basic connection example.
"""
# need to install redis first
#%pip install redis

import redis

class rclient:
    def __init__(self):
        self.r = redis.Redis(
            host='redis-11623.c253.us-central1-1.gce.redns.redis-cloud.com',
            port=11623,
            decode_responses=True,
            username="default",
            password="3e61Hp9yvrxAu2Tht1XPXeIDSs9oL1xK",
    )
    
    def create(self, key: str) -> str:
        if self.r.exists(key):
            return key + " already exist"
        else:
            self.r.set(key, '')
            return key + " created"
    
    def save(self, key:str, val:str) -> None:
        self.r.set(key, val)

    def get(self, key:str) -> str:
        return self.r.get(key)

r = rclient()

print(r.create('foo'))
print(r.create('foo'))
success = r.save('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar


