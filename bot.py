import telebot
from flask import Flask, request

TOKEN = "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc"
ADMIN_ID = 6099860667

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def start(msg):
    if str(msg.from_user.id) != str(ADMIN_ID):
        bot.reply_to(msg, f"Ваш ID: {msg.from_user.id}")
    else:
        bot.reply_to(msg, "Бот на Vercel работает!")

# Vercel serverless function handler
def handler(request, response):
    if request.method == 'POST' and request.path == '/api/webhook':
        json_string = request.body.decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        response.status = 200
    else:
        response.status = 404
    return response
