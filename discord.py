import json, hashlib, hmac, os, requests
from http.server import BaseHTTPRequestHandler

PUBLIC_KEY = '6c351cb59ede8ce6413d7a0543002f6d68877e1e003072a3bba38fb95305c007'
TOKEN = 'ваш_токен_бота'
ADMIN_ID = 123456789  # ваш Discord user ID

def verify_signature(body, signature, timestamp):
    message = f'{timestamp}{body}'.encode()
    key = PUBLIC_KEY.encode()
    mac = hmac.new(key, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

def handler(request):
    # Обрабатываем только POST на /api/discord
    if request.method != 'POST' or request.path != '/api/discord':
        return {'statusCode': 404, 'body': 'Not Found'}

    # Проверка подписи Discord
    signature = request.headers.get('x-signature-ed25519', '')
    timestamp = request.headers.get('x-signature-timestamp', '')
    body = request.body
    if not verify_signature(body, signature, timestamp):
        return {'statusCode': 401, 'body': 'invalid request signature'}

    data = json.loads(body)
    # Discord шлёт тип 1 (PING) для проверки webhook
    if data.get('type') == 1:
        return {'statusCode': 200, 'body': json.dumps({'type': 1})}

    # Команды приложения (тип 2)
    if data.get('type') == 2:
        command = data['data']['name']
        user_id = int(data['member']['user']['id'])
        # Простейшая проверка на админа
        if user_id != ADMIN_ID:
            reply = f'Ваш ID: {user_id}. Нет доступа.'
        else:
            reply = execute_command(command)

        response = {
            'type': 4,
            'data': {'content': reply}
        }
        return {'statusCode': 200, 'body': json.dumps(response)}

    return {'statusCode': 404, 'body': ''}

def execute_command(cmd):
    # Здесь можно добавить свою логику выполнения команд
    if cmd == 'ping':
        return 'pong! Бот работает.'
    elif cmd == 'whoami':
        import subprocess, platform
        return f'Host: {platform.node()}, OS: {platform.system()}'
    else:
        return f'Неизвестная команда: {cmd}'
