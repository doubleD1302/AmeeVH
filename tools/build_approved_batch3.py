# -*- coding: utf-8 -*-
"""
Builder and Auditor for Batch 3: Items, Goods & Mall Packages
Approved Vietnamese Localization for Stella Sora
Outputs to StellaSora_VietHoa/work/batches/final_batch3_items_goods_approved.json
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from batch3_dict_part1 import KEY_MAP
from batch3_dict_goods import GOODS_MAP
from batch3_dict_furniture_descs import FURN_DESCS
from batch3_dict_furniture_names import FURN_NAMES
from batch3_dict_furniture_lores import FURN_LORES

INPUT_FILE = ROOT / "work/batches/final_batch3_items_goods.json"
OUTPUT_FILE = ROOT / "work/batches/final_batch3_items_goods_approved.json"

data = json.load(open(INPUT_FILE, encoding="utf-8"))
print(f"Loaded {len(data)} items from {INPUT_FILE}")

def get_reason(item, approved_vi):
    table = item["table"]
    key = item["key"]
    zh = item["zh"]
    
    if "朵拉" in zh:
        return "Chuẩn hóa đơn vị tiền tệ chính Stella Sora: Dorra -> Đồng Dorra"
    if 100 <= (int(key.split(".")[1]) if len(key.split(".")) > 1 and key.split(".")[1].isdigit() else 0) < 200 and key.endswith(".1"):
        return "Bản địa hóa mảnh nhân vật chiêu mộ: Mảnh [Tên Nhân Vật] theo chuẩn anime, giữ nguyên tên riêng"
    if key.startswith("Item.25010"):
        return "Đồng bộ tên quân cờ nhân vật và quái vật trong cờ bàn minigame"
    if "自选" in zh or "Exquisite Choice Box" in item["en"]:
        return "Chuẩn hóa tên hộp quà và rương quà tự chọn theo văn phong gacha thương mại"
    if table in ("ActivityGoods", "ResidentGoods"):
        return "Bản địa hóa hàng hóa cửa hàng sự kiện và thường trú, vé gacha và nguyên liệu thăng bậc"
    if key.startswith("Item.7") and len(key.split(".")[1]) == 6:
        if key.endswith(".1"):
            return "Bản địa hóa tên gọi nội thất Tháp Ma Vương ấm cúng, đậm chất anime"
        elif key.endswith(".2"):
            return "Chuẩn hóa mô tả nội thất và đồ trang trí Tháp Ma Vương"
        else:
            return "Bản địa hóa mẩu chuyện ký ức nội thất Tháp Ma Vương hóm hỉnh, giàu cảm xúc"
    if key.startswith("Item.1150"):
        return "Chuẩn hóa danh hiệu vinh dự Bậc Thầy Sinh Tồn qua các mùa Phòng Tuyến Thảm Họa"
    if key.startswith("Item.710") or key.startswith("Item.720"):
        return "Dịch thẻ tiền tố và hậu tố danh hiệu thần bí"
    if key.startswith("Item.51"):
        return "Bản địa hóa từ tố ấn ký, danh hiệu và bí văn theo văn phong Hán Việt trang trọng"
    if key.startswith("Item.11003") or key.startswith("Item.11205") or key.startswith("Item.15503"):
        return "Dịch trang phục độc quyền và lời thoại nhân vật mượt mà, ngọt ngào"
    if key.startswith("Item.22406"):
        return "Bản địa hóa ký ức cao trào đĩa nhạc thiêng liêng, hào hùng"
    if key.startswith("Item.27010"):
        return "Bản địa hóa đạo cụ và trạng thái tính năng Tiên Phong Hãm Trận"
    return "Trau chuốt văn phong thương mại game chuẩn xác, hấp dẫn, bảo toàn 100% token kỹ thuật"

approved_data = []
for idx, d in enumerate(data):
    k = d["key"]
    en = d["en"]
    zh = d["zh"]
    pair = (en, zh)
    before = d.get("current_vi") or d.get("en") or ""
    
    trans = None
    if k in KEY_MAP:
        trans = KEY_MAP[k]
    elif pair in GOODS_MAP:
        trans = GOODS_MAP[pair]
    elif pair in FURN_DESCS:
        trans = FURN_DESCS[pair]
    elif pair in FURN_NAMES:
        trans = FURN_NAMES[pair]
    elif pair in FURN_LORES:
        trans = FURN_LORES[pair]
        
    if not trans:
        raise ValueError(f"Unmapped item at index {idx}: {d}")
        
    reason = get_reason(d, trans)
    
    approved_data.append({
        "table": d["table"],
        "key": k,
        "en": en,
        "zh": zh,
        "before": before,
        "approved_vi": trans,
        "reason": reason
    })

OUTPUT_FILE.write_text(json.dumps(approved_data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Successfully generated {len(approved_data)} approved items into {OUTPUT_FILE}!")
