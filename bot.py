import telebot
from flask import Flask, request

TOKEN = "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc"
ADMIN_ID = 6099860667

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@bot.message_handler(commands=['start'])
def start(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        bot.reply_to(msg, f"Ваш ID: {msg.from_user.id}")
    else:
        bot.reply_to(msg, "Бот работает на Render!")
