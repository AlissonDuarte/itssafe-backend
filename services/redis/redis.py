
import redis.asyncio as redis
import json
from datetime import timedelta

r = redis.from_url("redis://localhost", decode_responses=True)


TOKEN_PREFIX = "pwd-recovery:"

async def save_token(user_uuid: str, token: str, ttl_seconds: int = 900):
    key = TOKEN_PREFIX + token
    await r.setex(key, timedelta(seconds=ttl_seconds), json.dumps({"user_uuid": str(user_uuid)}))

async def get_token_data(token: str):
    key = TOKEN_PREFIX + token
    data = await r.get(key)
    return json.loads(data) if data else None

async def delete_token(token: str):
    await r.delete(TOKEN_PREFIX + token)