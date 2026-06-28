import redis
import json
from backend.core.config import settings

# Initialize Redis client
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_client = None

class CacheService:
    @staticmethod
    def get(key: str):
        if redis_client:
            try:
                data = redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        return None

    @staticmethod
    def set(key: str, value: any, expire: int = 3600):
        if redis_client:
            try:
                redis_client.setex(key, expire, json.dumps(value))
            except Exception:
                pass

    @staticmethod
    def delete(key: str):
        if redis_client:
            try:
                redis_client.delete(key)
            except Exception:
                pass
