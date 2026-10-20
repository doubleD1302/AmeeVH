import json

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_catalog.json', 'r', encoding='utf-8') as f:
    cat = json.load(f)

print(f"Total files in lua_catalog: {len(cat)}")
for k in list(cat.keys())[:10]:
    print(k, ":", cat[k])

# Check for pb files in lua_catalog
for k in cat.keys():
    if k.endswith('.pb') or 'table' in k.lower() or 'proto' in k.lower():
        print("PB match:", k, cat[k])
