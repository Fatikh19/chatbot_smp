from flask import Flask, request, jsonify
from chatbot_model import generate_response
from database import save_message
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    sender_id = data['from']
    user_message = data['message']

    # Simulasi proses jawaban dari chatbot
    bot_reply = generate_response(user_message)

    # Simpan ke database
    save_message(sender_id, user_message, bot_reply)

    # Kirim balasan (simulasi, disesuaikan dengan WhatsApp API)
    response = {
        "to": sender_id,
        "message": bot_reply
    }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)
