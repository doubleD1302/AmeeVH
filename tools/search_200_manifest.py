import urllib.request
import json

url = "https://launcher-pkg-ss-en.yo-star.com/zip_online_config_json/2.0.0tgQuFPED.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode('utf-8'))

files = data.get("file", [])
print(f"Total files: {len(files)}")
matches = []
for f in files:
    p = f.get('path', '')
    if any(k in p.lower() for k in ['table', 'data.arcx', 'lua.arcx']):
        matches.append(f)

print("Matches found in 2.0.0 manifest:")
for m in matches:
    print(" ", m)
