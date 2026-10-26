import json
from pathlib import Path
import re

ROOT = Path("c:/YostarGames/StellaSora_EN/StellaSora_VietHoa")
DEC_DIR = ROOT / "work/research/data_200_decrypted/entries"
EN_DIR = ROOT / "work/research/data_200_pristine_en/entries"

p_voice = DEC_DIR / "00552_0x80911df3a563e0f3.bin"
p_en = EN_DIR / "00552_0x80911df3a563e0f3.bin"
d_voice = json.loads(p_voice.read_text(encoding="utf-8"))
d_en = json.loads(p_en.read_text(encoding="utf-8"))

# Define forbidden pronouns per character ID
# For example:
# If character is 110 (Firenze): self is 'tôi', target is 'cậu'. CANNOT have 'em', CANNOT have 'anh' (as pronoun)!
# If character is 103 (Amber): self is 'tớ', target is 'cậu/Sếp'. CANNOT have 'tôi'!
# If character is 107 (Tilia): self is 'em/Tilia', target is 'Chúa Tể/chiến hữu/anh'. CANNOT have 'tôi', CANNOT have 'bạn'!
# If character is 162 (Alina): self is 'ta/Alina', target is 'ngươi/Du Hành Giả'. CANNOT have 'anh', 'em'!

FORBIDDEN_PATTERNS = {
    # 103 Amber: no 'tôi', no 'bạn', no 'ông chủ'
    "103": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bông chủ\b", r"\bÔng chủ\b"],
    # 107 Tilia: no 'tôi', no 'bạn'
    "107": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b"],
    # 108 Kasimira: no 'em', no 'anh'
    "108": [r"\bem\b", r"\bEm\b", r"\banh\b", r"\bAnh\b", r"\bbạn\b", r"\bBạn\b"],
    # 110 Firenze: no 'em', no 'anh', no 'bạn'
    "110": [r"\bem\b", r"\bEm\b", r"\banh\b", r"\bAnh\b", r"\bbạn\b", r"\bBạn\b"],
    # 111 Iris: no 'tôi', no 'bạn', no 'cậu'
    "111": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bcậu\b", r"\bCậu\b"],
    # 112 Noya: no 'tôi', no 'bạn', no 'em', no 'anh'
    "112": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bem\b", r"\bEm\b", r"\banh\b", r"\bAnh\b"],
    # 113 Shimiao: no 'anh', no 'em' (when referring to player), no 'bạn'
    "113": [r"\banh\b", r"\bAnh\b", r"\bbạn\b", r"\bBạn\b"],
    # 114 Chaton: no 'tôi', no 'bạn'
    "114": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b"],
    # 115 Firefly: no 'tôi', no 'bạn', no 'cậu'
    "115": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bcậu\b", r"\bCậu\b"],
    # 116 Ridge: no 'bạn'
    "116": [r"\bbạn\b", r"\bBạn\b"],
    # 134 Fuyuka: no 'tôi', no 'bạn', no 'cậu' (always em - Chủ nhân)
    "134": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bcậu\b", r"\bCậu\b"],
    # 137 Eleanor: no 'tôi', no 'bạn', no 'cậu' (always em - Tiền bối)
    "137": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bcậu\b", r"\bCậu\b"],
    # 139 Allie: no 'tôi', no 'bạn' (always chị/em - cậu)
    "139": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b"],
    # 140 Sparkla: no 'tôi', no 'bạn' (always em/Sparkla - Ma Vương)
    "140": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b"],
    # 142 Cosette: no 'tôi', no 'bạn', no 'cậu' (always em - Chủ nhân)
    "142": [r"\btôi\b", r"\bTôi\b", r"\bbạn\b", r"\bBạn\b", r"\bcậu\b", r"\bCậu\b"],
    # 156 Nazuna: no 'anh', no 'em', no 'bạn'
    "156": [r"\banh\b", r"\bAnh\b", r"\bem\b", r"\bEm\b", r"\bbạn\b", r"\bBạn\b"],
    # 159 Coronis: no 'anh', no 'em', no 'bạn'
    "159": [r"\banh\b", r"\bAnh\b", r"\bem\b", r"\bEm\b", r"\bbạn\b", r"\bBạn\b"],
    # 162 Alina: no 'anh', no 'em', no 'bạn'
    "162": [r"\banh\b", r"\bAnh\b", r"\bem\b", r"\bEm\b", r"\bbạn\b", r"\bBạn\b"],
}

violations = []
for k, v in d_voice.items():
    parts = k.split("_")
    if len(parts) >= 2 and parts[1].isdigit():
        cid = parts[1]
        if cid in FORBIDDEN_PATTERNS:
            txt = v.get("text", {}).get("female_jp", [""])[0]
            for pat in FORBIDDEN_PATTERNS[cid]:
                if re.search(pat, txt):
                    violations.append((k, cid, pat, d_en.get(k, {}).get("text", {}).get("female_jp", [""])[0], txt))
                    break

print(f"Total pronoun violations found: {len(violations)}")
for k, cid, pat, en, vi in violations[:30]:
    print(f"[{k}] (Char {cid}, Pat {pat})\n  EN: {en}\n  VI: {vi}")
