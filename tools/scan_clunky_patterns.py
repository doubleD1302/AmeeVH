import json
import re
from pathlib import Path

entries_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_200_decrypted\entries")

# Known table hashes
TABLES = {
    "UIText": "00789_0x87cc29ac0defc2d9.bin",
    "Item": "00653_0xe60634348b826f41.bin",
    "CharacterArchiveVoice": "00594_0xd8b61831cfe58bf2.bin",
    "DatingCharacterEvent": "00611_0xd46d025e8dae5d69.bin",
    "Achievement": "00553_0x5b0fc2f5fe45a572.bin",
    "ActivityTask": "00573_0x5c7be7cfcb1d2241.bin",
    "MallPackage": "00671_0ee9e1d54770d965d.bin",
    "DictionaryDiagram": "00616_0x88d705ae9564e65e.bin",
    "Word": "00798_0x78b1aa32bbcf433e.bin"
}

# Suspicious machine translation keywords / unnatural phrasing
PATTERNS = [
    r"\bđược cung cấp bởi\b",
    r"\bhoa hồng\b", # commission
    r"\bbánh mì nướng\b", # toast
    r"\bô kìa\b",
    r"\bôi chao\b",
    r"\btuyệt vời!\b",
    r"\bngười dùng\b",
    r"\btài khoản\b",
    r"\bcho đến khi hết số tiền hiện có\b",
    r"\bbản sao\b",
    r"\bcủa bạn\b",
    r"\bcủa tôi\b",
    r"\bvui lòng kiểm tra\b",
    r"\btrong khi\b",
    r"\bở một mức độ nào đó\b",
    r"\bthực hiện một cuộc\b",
    r"\bcó thể được\b",
    r"\bđã được\b",
    r"\bsẽ được\b",
    r"\bnhận được\b",
    r"\bchúng tôi\b",
    r"\bbạn có thể\b",
    r"\bkhông thể không\b"
]

results = {}
for tname, fname in TABLES.items():
    fpath = entries_dir / fname
    if not fpath.exists():
        continue
    try:
        data = json.loads(fpath.read_text(encoding="utf-8"))
        suspicious = []
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            for pat in PATTERNS:
                if re.search(pat, v, re.IGNORECASE):
                    suspicious.append((k, v, pat))
                    break
        results[tname] = (len(data), len(suspicious), suspicious[:5])
    except Exception as e:
        results[tname] = (0, 0, str(e))

print("=== CLUNKY / SUSPICIOUS STRING SCAN SUMMARY ===")
for tname, (tot, sus_cnt, samples) in results.items():
    print(f"\n[{tname}] Total: {tot}, Flagged clunky: {sus_cnt} ({sus_cnt/tot*100:.1f}%)")
    if isinstance(samples, list):
        for k, v, pat in samples:
            clean_v = v.replace("\n", " ")[:90]
            print(f"  * {k} (Pattern '{pat}'): {clean_v}")
