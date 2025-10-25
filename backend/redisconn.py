"""Basic connection example.
"""
# need to install redis first
#%pip install redis

import redis

r = redis.Redis(
    host='redis-11623.c253.us-central1-1.gce.redns.redis-cloud.com',
    port=11623,
    decode_responses=True,
    username="default",
    password="3e61Hp9yvrxAu2Tht1XPXeIDSs9oL1xK",
)

success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar


