import os
import itertools
from utils.embeddings import get_embedding_function
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


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
