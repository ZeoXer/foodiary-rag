import threading
import time
import boto3
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, g
from flask_api import status
from flask_cors import CORS
from RAG_bot import RAGChatbot

load_dotenv()

app = Flask(__name__)

chat_bot = RAGChatbot()
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://foodiary-zeoxers-projects.vercel.app",
                "https://foodiary-git-frontend-zeoxers-projects.vercel.app",
            ]
        }
    },
)


@app.before_request
def start_timer():
    if request.endpoint == "chat_with_bot":
        g.start_time = time.time()


@app.after_request
def log_latency():
    if request.endpoint == "chat_with_bot":
        if hasattr(g, "start_time"):
            latency = time.time() - g.start_time
            send_to_cloudwatch("chat_with_bot", latency)


def send_to_cloudwatch(endpoint, latency):
    client = boto3.client(
        "cloudwatch",
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    client.put_metric_data(
        Namespace="FooDiary",
        MetricData=[
            {
                "MetricName": "APILatency",
                "Dimensions": [{"Name": "Endpoint", "Value": endpoint}],
                "Value": latency * 1000,
                "Unit": "Milliseconds",
            }
        ],
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), status.HTTP_200_OK


@app.route("/getChatRecords/<string:user_id>", methods=["GET"])
def get_chat_records(user_id):
    before_timestamp = request.args.get("timestamp")

    if not user_id:
        return jsonify({"error": "user_id is required"}), status.HTTP_400_BAD_REQUEST

    if before_timestamp:
        try:
            before_timestamp = float(before_timestamp)
        except ValueError:
            return (
                jsonify({"error": "timestamp should be a float"}),
                status.HTTP_400_BAD_REQUEST,
            )

    chat_records = chat_bot.get_chat_records(user_id, before_timestamp)
    for record in chat_records:
        record["_id"] = str(record["_id"])

    return jsonify({"content": chat_records}), status.HTTP_200_OK


@app.route("/chatWithBot", methods=["POST"])
def chat_with_bot():
    user_id = request.json.get("user_id")
    query_text = request.json.get("query_text")

    if not user_id or not query_text:
        return (
            jsonify({"error": "user_id and query_text are required"}),
            status.HTTP_400_BAD_REQUEST,
        )

    response_text = chat_bot.query(user_id, query_text)
    threading.Thread(
        target=chat_bot.backup_conversation, args=(user_id, query_text, response_text)
    ).start()

    return jsonify({"response": response_text}), status.HTTP_200_OK


if __name__ == "__main__":
    app.run(port=5432, debug=True)
