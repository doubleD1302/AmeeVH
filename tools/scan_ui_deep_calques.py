#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep scan of UIText (00789_0x87cc29ac0defc2d9.bin):
Finds:
1. Funny machine translation calques (like "khoảng không quảng cáo", "chụp nhanh bộ nhớ", "lợn bay", "mỡ khuỷu tay", "đám mây", etc.)
2. Inconsistent terminology with Master Glossary (Monolith -> Cự Tháp, Artifact -> Di Vật, Dusk Arbiter -> Thẩm Phán Hoàng Hôn, Boss Accord -> Hiệp Ước Của Sếp, etc.)
3. Remnant English words or untranslated labels (VUL, RES, EVA, etc.)
4. Grammar glitches or awkward literal translations
"""

import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
f789 = ROOT / "work/research/data_200_decrypted/entries/00789_0x87cc29ac0defc2d9.bin"
f1036 = ROOT / "work/research/data_200_decrypted/entries/01036_0x363690c09b175230.bin"

CALQUE_PATTERNS = [
    (r"khoảng không quảng cáo", "Inventory bị dịch thành quảng cáo"),
    (r"chụp nhanh bộ nhớ", "Memory snapshot bị dịch thành chụp bộ nhớ"),
    (r"bộ nhớ", "Memory (kỷ niệm / ký ức / hồi ức) bị dịch thành bộ nhớ máy tính"),
    (r"tập tin", "File bị dịch thành tập tin"),
    (r"tải trọng", "Payload / Load bị dịch thành tải trọng"),
    (r"cổ vật", "Artifact phải là Di Vật"),
    (r"bảo bối", "Artifact/Treasure"),
    (r"Cự Thạch", "Monolith phải là Cự Tháp"),
    (r"Trọng Tài", "Dusk Arbiter phải là Thẩm Phán Hoàng Hôn"),
    (r"Bạo Quân", "Tyrant phải là Bạo Chúa"),
    (r"Ma Vương", "Demon King / Lord"),
    (r"chết tiệt", "Chửi thề thô tục"),
    (r"cái quái gì", "What the hell"),
    (r"bạn biết đấy", "You know"),
    (r"làm sao mà", "How come"),
    (r"Sơ Quang", "Noya Khải Minh"),
    (r"Hổ phách", "Amber"),
    (r"Diên Vĩ", "Iris"),
    (r"quái vật", "Monster"),
    (r"phi hành đoàn", "Crew -> Đội / Nhóm"),
    (r"ông chủ", "Boss -> Sếp / Thủ Lĩnh"),
    (r"đặt cược", "You bet -> Chắc chắn rồi"),
    (r"nâng ly", "Toast"),
    (r"bánh mì nướng", "Toast"),
    (r"đám mây", "Cloud save / mây"),
    (r"người giúp việc", "Maid -> Hầu gái"),
    (r"người đàn ông từ chức", "Resigned man"),
]

def main():
    d789 = json.loads(f789.read_text(encoding="utf-8"))
    d1036 = json.loads(f1036.read_text(encoding="utf-8"))

    findings = []
    for k, v in d789.items():
        if not isinstance(v, str):
            continue
        cn = d1036.get(k, "")
        for pat, desc in CALQUE_PATTERNS:
            m = re.search(pat, v, re.IGNORECASE)
            if m:
                findings.append({
                    "id": k,
                    "pattern": pat,
                    "desc": desc,
                    "vi": v,
                    "cn": cn
                })

    print(f"Total calque/glossary findings in UIText: {len(findings)}")
    # Group by pattern
    by_pat = {}
    for f in findings:
        by_pat.setdefault(f["pattern"], []).append(f)

    for pat, items in sorted(by_pat.items(), key=lambda x: -len(x[1])):
        print(f"\n--- Pattern: '{pat}' ({len(items)} hits) ---")
        for it in items[:6]:
            print(f"  [{it['id']}]")
            print(f"    VI: {repr(it['vi'])}")
            print(f"    CN: {repr(it['cn'])}")

if __name__ == "__main__":
    main()
