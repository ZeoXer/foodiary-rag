import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()


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

    def get_chat_messages(self, user_id, count=5):
        db = self.client["chat_records"]
        collection = db[user_id]
        messages = collection.find().sort("_id", -1).limit(count)
        return list(messages)
