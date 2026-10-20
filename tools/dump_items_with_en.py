import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
data = json.loads((ROOT / "work" / "batches" / "audit_batch1_dating_char.json").read_text(encoding="utf-8"))

untranslated_or_mixed = []
for d in data:
    vi = d["current_vi"].strip()
    en_words = re.findall(r"\b(the|and|that|this|with|from|build|allows|deals|boosts|enhances|generates|increases|reduces|damage|enemies|skills|while|when|after|before|she|her|you|your|their|they|his|him|about|into|over|under|could|would|should|have|has|had|been|were|was|are|isn|aren|didn|don|can|cannot)\b", vi, re.IGNORECASE)
    if en_words:
        untranslated_or_mixed.append({
            "table": d["table"],
            "key": d["key"],
            "en": d["en"],
            "current_vi": d["current_vi"],
            "en_word_count": len(en_words),
            "en_words": en_words[:10]
        })

out_path = ROOT / "tools" / "all_items_with_en.json"
out_path.write_text(json.dumps(untranslated_or_mixed, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Total items with English words: {len(untranslated_or_mixed)}")
print("By table:", Counter(x["table"] for x in untranslated_or_mixed))
