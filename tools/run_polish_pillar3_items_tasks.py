import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
INPUT_FILE = ROOT / "work" / "batches" / "audit_batch3_item_mall_task.json"
OUTPUT_FILE = ROOT / "work" / "batches" / "audit_batch3_item_mall_task_polished.json"

REPLACEMENTS = [
    (r"\bbằng chứng về lời mời thêm (.+?) vào đội của bạn\b", r"Minh chứng kết nạp \1 vào đội ngũ."),
    (r"\bBằng chứng về lời mời thêm (.+?) vào đội của bạn\b", r"Minh chứng kết nạp \1 vào đội ngũ."),
    (r"\bvào đội của bạn\b", "vào đội ngũ"),
    (r"\bĐây là công lý của tôi!\b", "Chính Nghĩa Thuộc Về Ta!"),
    (r"\bĐây là công lý của tôi\b", "Chính Nghĩa Thuộc Về Ta"),
    (r"\bhoa hồng ủy thác\b", "nhiệm vụ ủy thác"),
    (r"\bhoàn thành hoa hồng\b", "hoàn thành nhiệm vụ ủy thác"),
    (r"\bhoa hồng\b", "nhiệm vụ ủy thác"),
    (r"\bVật phẩm bù chênh lệch Nâng cấp Trợ cấp\b", "Quà Bù Chênh Lệch Nâng Cấp Trợ Cấp"),
    (r"\bVật phẩm tặng kèm Trợ cấp Hoàng gia\b", "Quà Đính Kèm Trợ Cấp Hoàng Gia"),
    (r"\bBao gồm các vật phẩm tặng kèm khi mua Trợ cấp khởi đầu Hoàng gia hiện tại\.\b", 
     "Bao gồm các vật phẩm đính kèm tương ứng khi mua gói Trợ Cấp Khởi Nghiệp Hoàng Gia hiện tại."),
    (r"\bNhận được tổng cộng (\d+) điểm trong Xẻng kho báu may mắn\.\b",
     r"Tích lũy \1 điểm trong sự kiện Xẻng Báu May Mắn."),
    (r"\bNhận được tổng cộng (\d+) điểm\b", r"Tích lũy \1 điểm"),
    (r"\bFirstlight Noya\b", "Noya - Khải Minh"),
    (r"\bNoya Sơ Quang\b", "Noya - Khải Minh"),
    (r"\bSơ Quang\b", "Khải Minh"),
]

def polish_text(t: str, table: str) -> str:
    res = t
    for pat, rep in REPLACEMENTS:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
        
    # Additional specific Item adjustments
    if "Chứng chỉ mở khóa ngoại hình độc quyền của Tilia \"Đây là công lý của tôi!\"!" in res:
        res = "Đạo cụ mở khóa trang phục độc quyền của Tilia: \"Chính Nghĩa Thuộc Về Ta\"!"
        
    return res

def main():
    items = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    polished = []
    modifications = []
    
    for it in items:
        cur_vi = it["current_vi"]
        new_vi = polish_text(cur_vi, it["table"])
        it["polished_vi"] = new_vi
        polished.append(it)
        
        if new_vi != cur_vi:
            modifications.append({
                "table": it["table"],
                "key": it["key"],
                "before": cur_vi,
                "after": new_vi,
                "category": "Vật Phẩm & Nhiệm Vụ",
                "reason": "Trau chuốt mô tả vật phẩm sinh động, tên gói quà lôi cuốn, mục tiêu nhiệm vụ rõ ràng dễ hiểu",
                "agent": "Items, Mall & Quests Specialist Subagent"
            })
            
    OUTPUT_FILE.write_text(json.dumps(polished, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Pillar 3 Polish complete: {len(polished)} items processed, {len(modifications)} modifications made.")
    
    mod_path = ROOT / "work" / "batches" / "audit_batch3_modifications.json"
    mod_path.write_text(json.dumps(modifications, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(modifications)} modifications to {mod_path.name}")

if __name__ == "__main__":
    main()
