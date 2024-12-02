import threading
from flask import Flask, jsonify, request, after_this_request
from flask_api import status
from RAG_bot import RAGChatbot

app = Flask(__name__)

chat_bot = RAGChatbot()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), status.HTTP_200_OK


@app.route("/getChatRecords", methods=["GET"])
def get_chat_records():
    pass


@app.route("/chatWithBot", methods=["POST"])
def chat_with_bot():
    user_id = request.json.get("user_id")
    query_text = request.json.get("query_text")
    response_text = chat_bot.query(user_id, query_text)
    threading.Thread(
        target=chat_bot.backup_conversation, args=(user_id, query_text, response_text)
    ).start()

    return jsonify({"response": response_text}), status.HTTP_200_OK


if __name__ == "__main__":
    app.run(port=5432, debug=True)
