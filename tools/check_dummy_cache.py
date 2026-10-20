import sys
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from pipeline_translator_engine import load_cache

cache = load_cache()
print(f"Total cache entries: {len(cache)}")

dummy_entries = []
for k, v in cache.items():
    if k == v:
        # Check if k contains multiple English words (not just a proper noun)
        words = re.findall(r'[a-zA-Z]{2,}', k)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', k))
        if len(words) >= 2 and not has_vi:
            dummy_entries.append(k)

print(f"Dummy cache entries (English sentences mapped to themselves): {len(dummy_entries)}")
print("Sample dummy entries:")
for s in dummy_entries[:10]:
    print("  ", s[:60])
