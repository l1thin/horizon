import os

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

class MemoryRedis:
    def __init__(self):
        self.store = {}
    
    async def set(self, key, value, ex=None):
        if isinstance(value, str):
            value = value.encode('utf-8')
        self.store[key] = value
        
    async def get(self, key):
        return self.store.get(key)

_client = None

def get_redis_client():
    global _client
    if _client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url and aioredis:
            _client = aioredis.from_url(redis_url)
        else:
            if not redis_url:
                print("WARNING: REDIS_URL not set. Using in-memory dict for Redis fallback.")
            _client = MemoryRedis()
    return _client
