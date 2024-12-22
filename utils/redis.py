import os
import json
import time
import redis

MAX_RECORD_COUNT = 5
MAX_USER_COUNT = 9000
EXPIRE_TIME = 3600


class RedisClient:

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
        )
        self.expire_time = EXPIRE_TIME
        self.activity_set = "chat_activity"

    def save_message(self, user_id, message):
        key = f"chat:{user_id}"
        self.client.rpush(key, json.dumps(message))
        if self.client.llen(key) > MAX_RECORD_COUNT:
            self.client.lpop(key)

        self.client.expire(key, self.expire_time)

        current_time = time.time()
        self.client.zadd(self.activity_set, {user_id: current_time})

    def get_recent_messages(self, user_id, count=5):
        key = f"chat:{user_id}"
        messages = self.client.lrange(key, -count, -1)
        return [json.loads(message) for message in messages]

    def clean_oldest_users(self):
        excess_users = self.client.zrange(self.activity_set, 0, -MAX_USER_COUNT - 1)

        for user_id in excess_users:
            key = f"chat:{user_id}"
            self.client.delete(key)
            self.client.zrem(self.activity_set, user_id)
