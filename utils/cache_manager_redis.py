"rename this file as cache_manager.py and delete the other cache manager after moving to production"
"This is a production file after deployment with docker. using REDIS for smoother performance"
"change all the codes for cache use to redis parameters."

import json
import hashlib
import redis
import time
from typing import Any, Optional

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def get_file_hash(file_path: str) -> str:
    """Generate a stable hash for file content."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def cache_key(file_hash: str) -> str:
    """Generate Redis key for a file hash."""
    return f"filecache:{file_hash}"


def get_from_cache(file_hash: str) -> Optional[Any]:
    """Retrieve cached result if exists."""
    key = cache_key(file_hash)
    data = redis_client.get(key)
    return json.loads(data) if data else None


def set_cache(file_hash: str, data: dict, ttl: int = 3600):
    """Store data in Redis with optional TTL (1 hour default)."""
    key = cache_key(file_hash)
    redis_client.set(key, json.dumps(data), ex=ttl)


def move_cache_to_dump(file_hash: str):
    """Move cache data into permanent dump store."""
    data = get_from_cache(file_hash)
    if not data:
        return
    key = f"dump:{file_hash}"
    redis_client.set(key, json.dumps(data))
    redis_client.delete(cache_key(file_hash))


def get_dump(file_hash: str) -> Optional[Any]:
    """Get dumped file data."""
    data = redis_client.get(f"dump:{file_hash}")
    return json.loads(data) if data else None


def clear_cache(file_hash: str):
    """Delete cache and dump."""
    redis_client.delete(cache_key(file_hash))
    redis_client.delete(f"dump:{file_hash}")
