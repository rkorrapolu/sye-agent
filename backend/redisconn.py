"""Basic connection example.
"""
# need to install redis first
#%pip install redis

import redis

class rclient:
    def __init__(self):
        self.r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=os.getenv("REDIS_PORT", "6379"),
            decode_responses=True,
            username=os.getenv("REDIS_USER", "default"),
            password=os.getenv("REDIS_PASSWORD", "")
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


