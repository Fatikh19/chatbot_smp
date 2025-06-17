from flask import Flask, request, jsonify
import os
import requests

# Import chatbot logic
from chatbot import detect_intent, generate_response

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "chatbotsmpislamarrohman123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "EAAUHgvUZAMoABO7qgvFYZAYGZB0pkJOqZC91Y4BLC0buOnYo0pfoMldODEEp30w53L51Q6hkNhZCQK5vxmnps4sAwJGAHMplbRwN0V0mu9zwW9AZCjqjzbkMU6EenXuAHuhvn4HmaM4oGquj9ghQZAvttnoPLnZCpgtWLjTTyWFG37i03JYb1Ama0OFXXi36xwZDZD")

@app.route("/", methods=["GET"])
def index():
    return "Chatbot is running!"

# Webhook verification (called by Meta when setting up)
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args["hub.challenge"], 200
        return "Verification token mismatch", 403
    return "Hello, this is the webhook endpoint.", 200

# Webhook message handler
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data["entry"][0]
        message = entry["changes"][0]["value"]["messages"][0]
        phone_number_id = entry["changes"][0]["value"]["metadata"]["phone_number_id"]
        from_number = message["from"]
        user_text = message["text"]["body"]

        intent = detect_intent(user_text)
        response_text = generate_response(user_text, intent)

        # Send response back to user via WhatsApp
        url = f"https://graph.facebook.com/v22.0/669840469540031/messages"
        headers = {
            "Authorization": f"Bearer EAAUHgvUZAMoABO7qgvFYZAYGZB0pkJOqZC91Y4BLC0buOnYo0pfoMldODEEp30w53L51Q6hkNhZCQK5vxmnps4sAwJGAHMplbRwN0V0mu9zwW9AZCjqjzbkMU6EenXuAHuhvn4HmaM4oGquj9ghQZAvttnoPLnZCpgtWLjTTyWFG37i03JYb1Ama0OFXXi36xwZDZD",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "text": {"body": response_text}
        }
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print("Error processing message:", str(e))

    return "OK", 200
