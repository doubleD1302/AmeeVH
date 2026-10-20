import json

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\reviews\NOYA_STORY_TRANSLATED.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for cg, lines in d.items():
    print(f"\n=== {cg} ===")
    for l in lines[:8]:
        en_t = l["en"].replace("\n", " ")
        vi_t = l["vi"].replace("\n", " ")
        print(f"  EN: {en_t[:65]}")
        print(f"  VI: {vi_t[:65]}")
