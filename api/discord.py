import json, hashlib, hmac, os, requests, platform, socket

PUBLIC_KEY = os.environ.get('6c351cb59ede8ce6413d7a0543002f6d68877e1e003072a3bba38fb95305c007', '')
TOKEN = os.environ.get('MTUyNzk4NjYxMDg1ODEwMjkzNQ.GLZqnj.ffrheD6FqZSZR7OgdpwDp8RDXOBfP_J1VVKiOg', '')
ADMIN_ID = int(os.environ.get('1527986610858102935', '0'))

def verify_signature(body, signature, timestamp):
    message = f'{timestamp}{body}'.encode()
    key = PUBLIC_KEY.encode()
    mac = hmac.new(key, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

def execute_command(command):
    if command == 'ping':
        return 'Pong! Бот работает.'
    elif command == 'whoami':
        return f'Host: {platform.node()}, OS: {platform.system()}'
    else:
        return f'Неизвестная команда: {command}'

def handler(request):
    if request.method != 'POST' or request.path != '/api/discord':
        return {'statusCode': 404, 'body': 'Not Found'}

    signature = request.headers.get('x-signature-ed25519', '')
    timestamp = request.headers.get('x-signature-timestamp', '')
    body = request.body
    if not verify_signature(body, signature, timestamp):
        return {'statusCode': 401, 'body': 'invalid request signature'}

    data = json.loads(body)

    # Проверочный PING от Discord (тип 1)
    if data.get('type') == 1:
        return {'statusCode': 200, 'body': json.dumps({'type': 1})}

    # Слеш-команда (тип 2)
    if data.get('type') == 2:
        command = data['data']['name']
        user_id = int(data['member']['user']['id'])
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
