# -*- coding: utf-8 -*-
"""
Builder for STsp_09, STsp_10, STsp_11
Produces:
- trans_stsp_09.json (233 items)
- trans_stsp_10.json (261 items)
- trans_stsp_11.json (274 items)
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01"
TOOLS_DIR = ROOT / "tools/campaign12"

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

# ==========================================
# 1. BUILD STsp_09 (One-Day Partner - 233 items)
# ==========================================
with open(TOOLS_DIR / "stsp_09_items.json", "r", encoding="utf-8") as f:
    items_09 = json.load(f)

# STsp_09 specific replacements and fixes
REP_09 = [
    ("Chết tiệt! Tất cả những quyết tâm đó chẳng là gì cả!", "Tức thật chứ! Bao nhiêu quyết tâm thế mà đổ sông đổ bể hết!"),
    ("Chết tiệt. Tôi không thấy điều này sắp xảy ra.", "Hỏng rồi. Chuyện này hoàn toàn nằm ngoài dự tính của tôi."),
    ("Đó không phải là... người yêu của Lutty sao? ==W== Chết tiệt—đừng nói", "Đó không phải là... người tình của Lutty sao? ==W== Chết thật—đừng nói"),
    ("Chờ đợi! Sự trở lại! Chết tiệt!", "Đứng lại! Quay lại mau! Đáng ghét thật!"),
    ("Đ-chết tiệt... Đúng là một cặp đôi ngọt ngào đến phát bệnh...", "K-Khốn thật... Đúng là một cặp đôi ngọt ngào đến phát ớn..."),
    ("chết tiệt", "chết thật"),
    ("Lutty đã trôi dạt", "Lutty bắt sóng nhanh đấy"),
    ("Chỉ cần chơi cùng!", "Cứ diễn theo tôi đi!"),
    ("chỉ cần chơi cùng", "cứ diễn theo tôi"),
    ("công việc bí mật", "nhiệm vụ bí mật"),
    ("hợp pháp", "chính đáng"),
    ("nghi ngờ", "ngờ vực"),
]

T_09 = {}
for it in items_09:
    iid = it["id"]
    en = it["en"]
    cur_vi = it.get("current_vi", en)
    
    vi = cur_vi
    for old, new in REP_09:
        vi = vi.replace(old, new)
        
    vi = unicodedata.normalize("NFC", vi)
    T_09[iid] = vi

# Token & control verification for 09
err_09 = []
for it in items_09:
    iid = it["id"]
    st = sorted(TAG_PATTERN.findall(it["en"]))
    dt = sorted(TAG_PATTERN.findall(T_09[iid]))
    if st != dt:
        err_09.append(f"{iid}: {st} vs {dt}")

print(f"STsp_09 processed: {len(T_09)} items, {len(err_09)} token errors.")
if not err_09:
    with open(CAMPAIGN_DIR / "trans_stsp_09.json", "w", encoding="utf-8") as f:
        json.dump(T_09, f, ensure_ascii=False, indent=2)
    print("Saved trans_stsp_09.json successfully!")


# ==========================================
# 2. BUILD STsp_10 (Ridge Greenhouse - 261 items)
# ==========================================
with open(TOOLS_DIR / "stsp_10_items.json", "r", encoding="utf-8") as f:
    items_10 = json.load(f)

KEEP_10 = {"STsp_10_03.26", "STsp_10_03.100"}

REP_10 = [
    ("Nhà máy im lặng", "Cây Lặng Thinh"),
    ("nhà máy im lặng", "cây lặng thinh"),
    ("Tôi đã có nó!", "Tôi chịu hết nổi rồi đấy nhé!"),
    ("NHẬN CÁI NÀY!", "NẾM MÙI NÀY ĐI!"),
    ("Tôi đã xong rồi", "Tôi tiêu đời rồi"),
    ("hoàn toàn xong rồi", "hoàn toàn tiêu đời rồi"),
    ("Chiến Binh Cây Bụi", "Chuột Bụi"),
    ("Chuột Cây Bụi", "Chuột Bụi"),
    ("Thành cổ Cây bụi", "Chuột Bụi"),
    ("Cây Bụi", "Chuột Bụi"),
    ("Điều đó nên làm điều đó.", "Như vậy chắc là ổn rồi."),
    ("Đó là một sai lầm lớn", "đã phạm phải một sai lầm tai hại"),
]

T_10 = {}
for it in items_10:
    iid = it["id"]
    en = it["en"]
    cur_vi = it.get("current_vi", en)
    
    if iid in KEEP_10:
        vi = en
    else:
        vi = cur_vi
        for old, new in REP_10:
            vi = vi.replace(old, new)
            
    vi = unicodedata.normalize("NFC", vi)
    T_10[iid] = vi

err_10 = []
for it in items_10:
    iid = it["id"]
    if iid in KEEP_10:
        continue
    st = sorted(TAG_PATTERN.findall(it["en"]))
    dt = sorted(TAG_PATTERN.findall(T_10[iid]))
    if st != dt:
        err_10.append(f"{iid}: {st} vs {dt}")

print(f"STsp_10 processed: {len(T_10)} items, {len(err_10)} token errors.")
if not err_10:
    with open(CAMPAIGN_DIR / "trans_stsp_10.json", "w", encoding="utf-8") as f:
        json.dump(T_10, f, ensure_ascii=False, indent=2)
    print("Saved trans_stsp_10.json successfully!")


# ==========================================
# 3. BUILD STsp_11 (Donna - 274 items)
# ==========================================
with open(TOOLS_DIR / "stsp_11_items.json", "r", encoding="utf-8") as f:
    items_11 = json.load(f)

REP_11 = [
    ("Chuyển Phát Hỏa Tốc Chuyển Phát Hỏa Tốc Chuyển Phát Hỏa Tốc Post Haste", "Chuyển Phát Hỏa Tốc"),
    ("Chuyển Phát Hỏa Tốc Chuyển Phát Hỏa Tốc Post Haste", "Chuyển Phát Hỏa Tốc"),
    ("Chuyển Phát Hỏa Tốc Post Haste", "Chuyển Phát Hỏa Tốc"),
    ("Post Haste", "Chuyển Phát Hỏa Tốc"),
    ("Đêm buồn quá!", "Chúc ngủ ngon nhé!"),
    ("ở trong tình trạng đỏ", "bị thâm hụt tài chính"),
    ("hủy hoại tài chính", "nguy cơ phá sản"),
    ("Chỉ muốn bắt đầu thuận lợi và hoàn thành một số chuyến giao hàng, thế thôi!", "Chỉ muốn tranh thủ đi sớm để giao xong mấy kiện hàng thôi mà, có gì đâu!"),
]

T_11 = {}
for it in items_11:
    iid = it["id"]
    en = it["en"]
    cur_vi = it.get("current_vi", en)
    
    vi = cur_vi
    for old, new in REP_11:
        vi = vi.replace(old, new)
        
    vi = unicodedata.normalize("NFC", vi)
    T_11[iid] = vi

err_11 = []
for it in items_11:
    iid = it["id"]
    st = sorted(TAG_PATTERN.findall(it["en"]))
    dt = sorted(TAG_PATTERN.findall(T_11[iid]))
    if st != dt:
        err_11.append(f"{iid}: {st} vs {dt}")

print(f"STsp_11 processed: {len(T_11)} items, {len(err_11)} token errors.")
if not err_11:
    with open(CAMPAIGN_DIR / "trans_stsp_11.json", "w", encoding="utf-8") as f:
        json.dump(T_11, f, ensure_ascii=False, indent=2)
    print("Saved trans_stsp_11.json successfully!")
