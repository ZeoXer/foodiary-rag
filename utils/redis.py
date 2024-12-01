import os
import json
import redis

MAX_RECORD_COUNT = 5


class RedisClient:

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
        )

    def save_message(self, user_id, message):
        key = f"chat:{user_id}"
        self.client.rpush(key, json.dumps(message))
        if self.client.llen(key) > MAX_RECORD_COUNT:
            self.client.lpop(key)

    def get_recent_messages(self, user_id, count=5):
        key = f"chat:{user_id}"
        messages = self.client.lrange(key, -count, -1)
        return [json.loads(message) for message in messages]
