import telebot
from flask import Flask, request

TOKEN = "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc"
ADMIN_ID = 6099860667

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def start(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        bot.reply_to(msg, f"ID: {msg.from_user.id}")
    else:
        bot.reply_to(msg, "Бот на Vercel работает без Flask.")

def handler(request):
    if request.method == 'POST' and request.path == '/api/webhook':
        update = telebot.types.Update.de_json(request.body)
        bot.process_new_updates([update])
        return {
            'statusCode': 200,
            'body': ''
        }
    # Для GET /api/setup
    if request.method == 'GET' and request.path == '/api/setup':
        bot.set_webhook(url='https://tgb-0-pu0ux3x3v-ivan2014maligin-4222s-projects.vercel.app/api/webhook')
        return {
            'statusCode': 200,
            'body': 'Webhook установлен'
        }
    return {
        'statusCode': 404,
        'body': 'Not Found'
    }
