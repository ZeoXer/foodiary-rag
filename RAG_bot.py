import argparse
import os
import time
from dotenv import load_dotenv
from langdetect import detect
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.pinecone import PineconeIndex
from utils.redis import RedisClient
from utils.mongodb import MongoDBClient

load_dotenv()

PROMPT_TEMPLATE = """
Answer the question only based on the following two kinds of contents:

1. Related contexts:

{context}

2. Previous conversation records:

{record}

---

Answer the question based on the above contents: {question}
Do not mention the word 'provided text' in your response, use 'my knowledge' instead.
If the contexts have no relation with the question, you must answer 'Your question goes beyond my understanding'.
"""

TRANSLATE_PROMPT_TEMPLATE = """
Translate the following text to {language}: {text}
Just translate the text, don't add any additional information.
"""

TEST_USER_ID = "user_0"


class RAGChatbot:

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", api_key=os.getenv("GEMINI_API_KEY")
        )
        self.pinecone_index = PineconeIndex()
        self.redis_client = RedisClient()
        self.mongodb_client = MongoDBClient()

    def query(self, user_id, query_text, language="zh-TW"):
        if detect(query_text) != "en":
            translate_query_text = self.translate_text("en", query_text)

        context_results = self.pinecone_index.search_documents(translate_query_text)
        record_results = self.redis_client.get_recent_messages(user_id)

        context_text = "\n\n---\n\n".join(context_results)
        record_text = self.format_chat_messages(record_results)
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(
            context=context_text, record=record_text, question=query_text
        )

        response_text = self.model.invoke(prompt).content
        translate_response_text = self.translate_text(language, response_text)

        print(translate_response_text)
        return translate_response_text

    def backup_conversation(self, user_id, query_text, response_text):
        message = self.make_message(user_id, query_text, response_text)
        self.redis_client.save_message(user_id, message)
        self.mongodb_client.save_message(user_id, message)

    def translate_text(self, query_text, language):
        translate_prompt_template = ChatPromptTemplate.from_template(
            TRANSLATE_PROMPT_TEMPLATE
        )
        translate_prompt = translate_prompt_template.format(
            language=language, text=query_text
        )
        response_query_text = self.model.invoke(translate_prompt)
        return response_query_text.content

    def make_message(self, user_id, user_message, bot_message):
        return {
            "user_id": user_id,
            "timestamp": time.time(),
            "chat_content": [
                {
                    "role": "user",
                    "message": user_message,
                },
                {"role": "bot", "message": bot_message},
            ],
        }

    def format_chat_messages(self, record_results):
        formatted_messages = []

        for record in record_results:
            chat_content = record["chat_content"]
            formatted_content = [
                f"{message['role'].capitalize()}: {message['message']}\n"
                for message in chat_content
            ]
            formatted_messages.extend(formatted_content)

        return "\n---".join(formatted_messages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text")
    args = parser.parse_args()
    query_text = args.query_text
    chatbot = RAGChatbot()
    chatbot.query(TEST_USER_ID, query_text)


if __name__ == "__main__":
    main()
