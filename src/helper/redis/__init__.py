import time
from typing import Any, Dict, List, Optional

from redis.client import Redis
from src.config.settings import (
    REDIS_HOST,
    REDIS_KWARGS,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_USERNAME,
)

main_redis = Redis(
    REDIS_HOST,
    REDIS_PORT,
    password=REDIS_PASSWORD,
    username=REDIS_USERNAME,
    **REDIS_KWARGS,
)


def set_key_if_not_exists(
    redis_client: Redis, key: str, value: Any, expire: Optional[int] = None
) -> bool:
    if redis_client.setnx(key, value):
        if expire:
            redis_client.expire(key, expire)
        return True
    return False


def get_and_delete_key(redis_client: Redis, key: str) -> Optional[str]:
    pipeline = redis_client.pipeline()
    pipeline.get(key)
    pipeline.delete(key)
    result = pipeline.execute()
    return result[0].decode("utf-8") if result[0] else None


def update_hash_field(redis_client: Redis, key: str, field: str, value: Any) -> bool:
    if redis_client.hexists(key, field):
        redis_client.hset(key, field, value)
        return True
    return False


def pop_from_list(
    redis_client: Redis, key: str, from_start: bool = True
) -> Optional[str]:
    func = redis_client.lpop if from_start else redis_client.rpop
    result = func(key)
    return result.decode("utf-8") if result else None


def transfer_list_items(redis_client: Redis, source_key: str, dest_key: str) -> int:
    items = redis_client.lrange(source_key, 0, -1)
    if items:
        redis_client.rpush(dest_key, *items)
        redis_client.delete(source_key)
        return len(items)
    return 0


def increment_sorted_set_score(
    redis_client: Redis, key: str, member: str, increment: float
) -> float:
    if redis_client.zscore(key, member) is not None:
        return redis_client.zincrby(key, increment, member)
    return 0.0


def move_set_member(
    redis_client: Redis, source_key: str, dest_key: str, member: Any
) -> bool:
    return redis_client.smove(source_key, dest_key, member)


def atomic_counter(
    redis_client: Redis, counter_key: str, limit: int, expire: Optional[int] = None
) -> bool:
    pipeline = redis_client.pipeline()
    pipeline.incr(counter_key)
    if expire:
        pipeline.expire(counter_key, expire)
    current_value, _ = pipeline.execute()
    if current_value > limit:
        redis_client.delete(counter_key)
        return False
    return True


def get_top_n_sorted_set(redis_client: Redis, key: str, n: int) -> List[str]:
    return [item.decode("utf-8") for item in redis_client.zrevrange(key, 0, n - 1)]


def batch_delete_keys(redis_client: Redis, keys: List[str]) -> int:
    pipeline = redis_client.pipeline()
    for key in keys:
        pipeline.delete(key)
    return sum(pipeline.execute())


def lock_with_expire(redis_client: Redis, lock_key: str, expire: int) -> bool:
    return redis_client.set(lock_key, "1", nx=True, ex=expire)


def set_with_version(
    redis_client: Redis, key: str, value: Any, version: Optional[int] = None
) -> bool:
    current_version = redis_client.get(f"{key}_version")
    if version and (not current_version or int(current_version) != version):
        return False
    pipeline = redis_client.pipeline()
    pipeline.set(key, value)
    pipeline.incr(f"{key}_version")
    pipeline.execute()
    return True


def cache_with_fallback(
    redis_client: Redis, key: str, fallback_func: Any, expire: Optional[int] = None
) -> Any:
    cached_value = redis_client.get(key)
    if cached_value:
        return cached_value.decode("utf-8")
    new_value = fallback_func()
    redis_client.set(key, new_value, ex=expire)
    return new_value


def get_or_set(
    redis_client: Redis, key: str, fetch_func: Any, expire: Optional[int] = None
) -> Any:
    cached_value = redis_client.get(key)
    if cached_value:
        return cached_value.decode("utf-8")
    value = fetch_func()
    redis_client.set(key, value, ex=expire)
    return value


def set_multiple_keys(
    redis_client: Redis, key_value_pairs: Dict[str, Any], expire: Optional[int] = None
) -> bool:
    pipeline = redis_client.pipeline()
    for key, value in key_value_pairs.items():
        pipeline.set(key, value, ex=expire)
    pipeline.execute()
    return True


def get_multiple_keys(redis_client: Redis, keys: List[str]) -> Dict[str, Optional[str]]:
    pipeline = redis_client.pipeline()
    for key in keys:
        pipeline.get(key)
    results = pipeline.execute()
    return {
        keys[i]: (results[i].decode("utf-8") if results[i] else None)
        for i in range(len(keys))
    }


def increment_counter_with_limit(
    redis_client: Redis, counter_key: str, limit: int, increment: int = 1
) -> bool:
    pipeline = redis_client.pipeline()
    pipeline.incrby(counter_key, increment)
    pipeline.expire(counter_key, 3600)  # Expire after 1 hour
    current_value, _ = pipeline.execute()
    if current_value > limit:
        redis_client.delete(counter_key)
        return False
    return True


def merge_sorted_sets(redis_client: Redis, dest_key: str, *source_keys: str) -> int:
    return redis_client.zunionstore(dest_key, source_keys)


def atomic_get_and_set(redis_client: Redis, key: str, value: Any) -> Optional[str]:
    old_value = redis_client.get(key)
    redis_client.set(key, value)
    return old_value.decode("utf-8") if old_value else None


def batch_hset(redis_client: Redis, key: str, data: Dict[str, Any]) -> bool:
    pipeline = redis_client.pipeline()
    for field, value in data.items():
        pipeline.hset(key, field, value)
    pipeline.execute()
    return True


def get_or_create_set(
    redis_client: Redis, key: str, default_values: List[Any]
) -> List[str]:
    if not redis_client.exists(key):
        redis_client.sadd(key, *default_values)
    return [item.decode("utf-8") for item in redis_client.smembers(key)]


def set_if_equal(
    redis_client: Redis, key: str, value: Any, expected_value: Any
) -> bool:
    return (
        redis_client.set(key, value, xx=True)
        if redis_client.get(key) == expected_value
        else False
    )


def increment_and_get_sorted_set(
    redis_client: Redis, key: str, member: str, increment: float
) -> float:
    redis_client.zincrby(key, increment, member)
    return redis_client.zscore(key, member)


def lock_and_run(
    redis_client: Redis, lock_key: str, lock_expire: int, function: Any, *args: Any
) -> Any:
    if redis_client.set(lock_key, "locked", nx=True, ex=lock_expire):
        try:
            return function(*args)
        finally:
            redis_client.delete(lock_key)
    raise Exception("Could not acquire lock.")


def paginate_list(
    redis_client: Redis, key: str, page: int, page_size: int
) -> List[str]:
    start = (page - 1) * page_size
    end = start + page_size - 1
    return [item.decode("utf-8") for item in redis_client.lrange(key, start, end)]


def get_sorted_set_range_by_score(
    redis_client: Redis, key: str, min_score: float, max_score: float
) -> List[str]:
    return [
        item.decode("utf-8")
        for item in redis_client.zrangebyscore(key, min_score, max_score)
    ]


def set_with_version_check(
    redis_client: Redis, key: str, value: Any, version_key: str
) -> bool:
    version = redis_client.get(version_key)
    if not version:
        redis_client.set(key, value)
        redis_client.set(version_key, 1)
        return True
    version = int(version)
    redis_client.set(key, value)
    redis_client.set(version_key, version + 1)
    return True


def get_or_lock(
    redis_client: Redis, key: str, timeout: int, lock_key: str
) -> Optional[str]:
    if redis_client.set(lock_key, "locked", nx=True, ex=timeout):
        value = redis_client.get(key)
        return value.decode("utf-8") if value else None
    return None


def list_prepend(redis_client: Redis, key: str, values: List[Any]) -> int:
    return redis_client.lpush(key, *values)


def get_or_set_hash_field(
    redis_client: Redis, key: str, field: str, fetch_func: Any
) -> Any:
    value = redis_client.hget(key, field)
    if value:
        return value.decode("utf-8")
    new_value = fetch_func()
    redis_client.hset(key, field, new_value)
    return new_value


def set_and_get_old_value(redis_client: Redis, key: str, value: Any) -> Optional[str]:
    old_value = redis_client.getset(key, value)
    return old_value.decode("utf-8") if old_value else None


def clear_and_set(
    redis_client: Redis, key: str, value: Any, expire: Optional[int] = None
) -> bool:
    redis_client.delete(key)
    redis_client.set(key, value, ex=expire)
    return True


def throttle_function(
    redis_client: Redis, key: str, limit: int, time_window: int
) -> bool:
    current_time = int(time.time())
    redis_client.zremrangebyscore(key, 0, current_time - time_window)
    redis_client.zadd(key, {current_time: current_time})
    count = redis_client.zcard(key)
    return count <= limit


def multi_key_lock(redis_client: Redis, lock_keys: List[str], expire: int) -> bool:
    return all(redis_client.setnx(key, "locked") for key in lock_keys) and all(
        redis_client.expire(key, expire) for key in lock_keys
    )


def fetch_and_cache(
    redis_client: Redis, key: str, fetch_func: Any, expire: Optional[int] = None
) -> Any:
    value = redis_client.get(key)
    if value:
        return value.decode("utf-8")
    result = fetch_func()
    redis_client.set(key, result, ex=expire)
    return result


def get_or_increment(redis_client: Redis, key: str, increment: int = 1) -> int:
    if not redis_client.exists(key):
        redis_client.set(key, 0)
    return redis_client.incrby(key, increment)


def process_list(redis_client: Redis, key: str, process_func: Any) -> List[str]:
    items = redis_client.lrange(key, 0, -1)
    result = [process_func(item.decode("utf-8")) for item in items]
    redis_client.delete(key)
    redis_client.rpush(key, *result)
    return result
