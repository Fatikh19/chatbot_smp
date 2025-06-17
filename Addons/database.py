import mysql.connector
from config import DB_CONFIG

def save_message(sender, user_msg, bot_reply):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = "INSERT INTO messages (sender_id, user_message, bot_reply) VALUES (%s, %s, %s)"
    values = (sender, user_msg, bot_reply)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()
