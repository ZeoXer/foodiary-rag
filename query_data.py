import argparse
import os
import time
from dotenv import load_dotenv
from langdetect import detect
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from operate_database import PineconeIndex, RedisClient

load_dotenv()

PROMPT_TEMPLATE = """
Answer the question only based on the following two kinds of contents:

1. Related contexts:

{context}

2. Previous conversation records:

{record}

---

Answer the question based on the above contents: {question}
Don't mention the word 'context' in your response.
If the contexts have no relation with the question, you must answer 'Your question goes beyond my understanding'.
"""

TRANSLATE_PROMPT_TEMPLATE = """
Translate the following text to {language}: {text}
Just translate the text, don't add any additional information.
"""

model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", api_key=os.getenv("GEMINI_API_KEY")
)
pc = PineconeIndex()
rc = RedisClient()
TEST_USER_ID = "user_0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text")
    args = parser.parse_args()
    query_text = args.query_text
    response_text = query_rag(query_text)
    messages = make_message(TEST_USER_ID, query_text, response_text)
    rc.save_message(TEST_USER_ID, messages)


def query_rag(query_text, language="zh-TW"):
    if detect(query_text) != "en":
        translate_query_text = translate_text("English", query_text)

    # Search Pinecone for similar contexts
    context_results = pc.search_documents(translate_query_text)

    # Search Redis for previous messages
    record_results = rc.get_recent_messages(TEST_USER_ID)

    context_text = "\n\n---\n\n".join(context_results)
    record_text = format_chat_messages(record_results)
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(
        context=context_text, record=record_text, question=query_text
    )
    # print(prompt)

    response_text = model.invoke(prompt).content
    translate_response_text = translate_text(language, response_text)

    # sources = [doc.metadata.get("id", None) for doc, _score in results]

    formatted_response = f"Response:\n\n{translate_response_text}"
    print(formatted_response)

    return response_text


def translate_text(language, query_text):
    translate_prompt_template = ChatPromptTemplate.from_template(
        TRANSLATE_PROMPT_TEMPLATE
    )
    translate_prompt = translate_prompt_template.format(
        language=language, text=query_text
    )
    response_query_text = model.invoke(translate_prompt)
    return response_query_text.content


def make_message(user_id, user_message, bot_message):
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


def format_chat_messages(record_results):
    formatted_messages = []

    for record in record_results:
        chat_content = record["chat_content"]
        formatted_content = [
            f"{message['role'].capitalize()}: {message['message']}\n"
            for message in chat_content
        ]
        formatted_messages.extend(formatted_content)

    return "\n---".join(formatted_messages)


if __name__ == "__main__":
    main()
