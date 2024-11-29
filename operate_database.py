import glob
import os
import itertools
import json
from dotenv import load_dotenv
from get_embedding_function import get_embedding_function
from pinecone import Pinecone
import redis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

DATA_PATH = glob.glob("data/*.txt")
MAX_RECORD_COUNT = 5


class MongoDBClient:

    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"), server_api=ServerApi("1"))
        self.db = self.client["foodiary"]

    def save_messages(self, user_id, messages):
        db = self.client["chat_records"]
        collection = db[user_id]
        collection.insert_many(messages)


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


class PineconeIndex:

    def __init__(self):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        self.embeddings = get_embedding_function()

    def add_documents(self, documents):

        # 製作 chunks 以批次 upsert 到 Pinecone
        def chunks(iterable, batch_size=500):
            it = iter(iterable)
            chunk = tuple(itertools.islice(it, batch_size))
            while chunk:
                yield chunk
                chunk = tuple(itertools.islice(it, batch_size))

        # 取得 documents 的 id, embeddings, content, filename
        ids = [doc.metadata.get("id") for doc in documents]
        embeddings = self.embeddings.embed_documents(
            [doc.page_content for doc in documents]
        )
        contents = [doc.page_content for doc in documents]
        filenames = [doc.metadata.get("filename") for doc in documents]

        # 統整成 vectors
        vectors = [
            {
                "id": ids[i],
                "values": embeddings[i],
                "metadata": {"content": contents[i], "filename": filenames[i]},
            }
            for i in range(len(documents))
        ]

        print(f"👉 Adding new vectors: {len(vectors)}")
        # 非同步 upsert vectors 到 Pinecone
        async_results = [
            self.index.upsert(vectors=chunk, async_req=True)
            for chunk in chunks(vectors)
        ]
        [async_results.get() for async_results in async_results]

    def search_documents(self, query_text, k=10):
        embedding_query = self.embeddings.embed_query(query_text)
        query_results = self.index.query(
            vector=[embedding_query], include_metadata=True, top_k=k
        )
        return [match["metadata"]["content"] for match in query_results["matches"]]


def load_documents():
    document_loader = UnstructuredLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, chunk_overlap=80, length_function=len, is_separator_regex=False
    )
    return text_splitter.split_documents(documents)


def calculate_chunk_ids(chunks):
    count_dict = {}

    for chunk in chunks:
        filename = chunk.metadata.get("filename")

        if filename not in count_dict:
            count_dict[filename] = 0
        else:
            count_dict[filename] += 1

        element_id = chunk.metadata.get("element_id")
        chunk_id = f"{filename}_{element_id}_{count_dict[filename]}"

        chunk.metadata["id"] = chunk_id

    return chunks


if __name__ == "__main__":
    # docs = load_documents()
    # chunks = split_documents(docs)
    # chunks = calculate_chunk_ids(chunks)
    pc = PineconeIndex()
    # pc.search_documents("How to make high protein meals?")
    rc = RedisClient()
    messages = rc.get_recent_messages("user_0")
    print(len(messages))
    print(messages)
