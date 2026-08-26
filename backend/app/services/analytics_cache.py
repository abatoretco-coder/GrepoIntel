"""Small Redis cache for expensive profile-specific intelligence responses."""
import json
from redis import Redis
from app.core.config import settings

def _client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)

def cache_key(world_code: str, player_id: int, name: str, suffix: str = "") -> str:
    return f"analytics:{world_code}:profile:{player_id}:{name}:v2{suffix}"

def get_cached(key: str):
    client = _client()
    try:
        value = client.get(key)
        return json.loads(value) if value else None
    finally:
        client.close()

def set_cached(key: str, value, ttl_seconds: int = 600) -> None:
    client = _client()
    try:
        client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    finally:
        client.close()

def invalidate_profile(world_code: str, player_id: int) -> None:
    client = _client()
    try:
        for key in client.scan_iter(match=f"analytics:{world_code}:profile:{player_id}:*:v2*"):
            client.delete(key)
    finally:
        client.close()
