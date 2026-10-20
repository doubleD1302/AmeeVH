import json
import time
import hashlib
import urllib.request

game_id = "StellaSora_EN"
version = "1.6.0"
salt = "DE7108E9B2842FD460F4777702727869"

def get_auth_header(data_str=""):
    head = {
        "game_tag": game_id,
        "time": int(time.time()),
        "version": version
    }
    sign_str = f"{json.dumps(head, separators=(',', ':'))}{data_str}{salt}"
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    return json.dumps({"head": head, "sign": sign})

endpoints = [
    "/api/launcher/game/config",
    "/api/launcher/advanced/config",
    "/api/launcher/advanced/game/download/cdn"
]

base = "https://api-launcher-en.yo-star.com"

for ep in endpoints:
    url = base + ep
    auth = get_auth_header()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": auth
        }
    )
    print(f"Calling {ep}...")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode('utf-8')
            parsed = json.loads(data)
            print("Response:", json.dumps(parsed, indent=2, ensure_ascii=False)[:600])
    except Exception as e:
        print("Error:", e)
    print("=" * 60)
