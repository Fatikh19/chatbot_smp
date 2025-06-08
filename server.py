from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(json.dumps(data, indent=2))

    # Ambil pesan masuk
    if 'messages' in data['entry'][0]['changes'][0]['value']:
        msg = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender = msg['from']
        message_text = msg['text']['body']

        # Kirim ke fungsi chatbotmu (misalnya get_response_from_rnn)
        reply = get_response_from_rnn(message_text)

        # Kirim balasan ke WhatsApp API
        send_whatsapp_message(sender, reply)

    return 'ok', 200

def get_response_from_rnn(text):
    # Fungsi ini adalah chatbot-mu
    return "Ini jawaban dari chatbot untuk: " + text

def send_whatsapp_message(to, message):
    import requests
    headers = {
        'Authorization': 'Bearer EAAUHgvUZAMoABO7qgvFYZAYGZB0pkJOqZC91Y4BLC0buOnYo0pfoMldODEEp30w53L51Q6hkNhZCQK5vxmnps4sAwJGAHMplbRwN0V0mu9zwW9AZCjqjzbkMU6EenXuAHuhvn4HmaM4oGquj9ghQZAvttnoPLnZCpgtWLjTTyWFG37i03JYb1Ama0OFXXi36xwZDZD',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(
        'https://graph.facebook.com/v19.0/669840469540031/messages',
        headers=headers,
        json=payload
    )
    print(response.text)

if __name__ == '__main__':
    app.run(port=5000)
