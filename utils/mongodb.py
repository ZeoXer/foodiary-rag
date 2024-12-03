import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

MESSAGE_GET_LIMIT = 5


class MongoDBClient:

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi("1"))

    def save_message(self, user_id, message):
        db = self.client["chat_records"]
        collection = db[user_id]
        try:
            collection.insert_one(message)
        except Exception as e:
            if "duplicate key" not in str(e):
                print(f"save messages error: {str(e)}")

    def get_chat_messages(self, user_id, before_timestamp=None):
        db = self.client["chat_records"]
        collection = db[user_id]
        query = {"user_id": user_id}
        if before_timestamp:
            query["timestamp"] = {"$lt": before_timestamp}
        messages = collection.find(query).sort("timestamp", -1).limit(MESSAGE_GET_LIMIT)
        return list(messages)


if __name__ == "__main__":
    mongodb_client = MongoDBClient()
    message1 = mongodb_client.get_chat_messages("user_0")
    print("Part1:\n---\n")
    print(len(message1))
    print(message1)
    message2 = mongodb_client.get_chat_messages(
        "user_0", before_timestamp=message1[-1]["timestamp"]
    )
    print("Part2:\n---\n")
    print(len(message2))
    print(message2)
