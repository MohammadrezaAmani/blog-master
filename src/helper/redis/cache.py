from aiocache import Cache, cached
from src.config.settings import REDIS_HOST, REDIS_PORT

cache = Cache.REDIS

Cache.REDIS(endpoint=REDIS_HOST, port=int(REDIS_PORT), timeout=10)

__all__ = ["cache", "cached"]
