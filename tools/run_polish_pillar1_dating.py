import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
INPUT_FILE = ROOT / "work" / "batches" / "audit_batch1_dating_char.json"
OUTPUT_FILE = ROOT / "work" / "batches" / "audit_batch1_dating_char_polished.json"

# Phrasing polish rules for Dating & Characters
REPLACEMENTS = [
    # Mechanical phrasing
    (r"\bsự kiện xổ số\b", "chương trình rút thăm may mắn"),
    (r"\bcửa hàng tráng miệng\b", "tiệm đồ ngọt"),
    (r"\bHiệp sĩ Vệ binh Hoàng gia\b", "Cận Vệ Hoàng Gia"),
    (r"\bVệ binh Hoàng gia\b", "Cận Vệ Hoàng Gia"),
    (r"\bcó tư tưởng công lý\b", "tôn sùng chính nghĩa"),
    (r"\bvị hôn phu của bạn\b", "vị hôn phu"),
    (r"\bngười đàn ông có vẻ ngoài lén lút\b", "gã đàn ông dáng vẻ lấm lét"),
    (r"\bbước đi nhanh nhẹn\b", "thoăn thoắt bước đi"),
    (r"\bsuýt khiến bạn mất thăng bằng\b", "suýt chút nữa làm bạn ngã nhào"),
    (r"\blãng phí thời gian của tôi\b", "lãng phí thời gian quý báu"),
    (r"\bthời gian của bạn\b", "thời gian của bạn"),
    (r"\bđội của bạn\b", "đội ngũ"),
    (r"\bbằng chứng về lời mời\b", "minh chứng kết nạp"),
    (r"\bkết nạp vào đội của bạn\b", "kết nạp vào đội ngũ"),
    (r"\bchỉ vì tôi hoàn toàn có thể nói rằng\b", "chỉ là liếc mắt một cái là tôi biết ngay"),
    (r"\bngạc nhiên trước sự lựa chọn của bạn\b", "tròn mắt ngạc nhiên trước lựa chọn của bạn"),
    (r"\btrong khi khám phá hang động với Kasimira\b", "trong chuyến thám hiểm hang động cùng Kasimira"),
    (r"\bcô ấy đã hộ tống bạn một cách an toàn\b", "cô ấy đã cẩn thận hộ tống bạn sang bờ bên kia an toàn"),
    (r"\bkhông thể không cảm thấy\b", "bất giác cảm thấy"),
    (r"\bở một mức độ nào đó\b", "phần nào đó"),
    (r"\bnhững kỷ niệm đẹp đẽ\b", "những hồi ức tươi đẹp"),
    (r"\bngười yêu thích\b", "người mê"),
    (r"\bmột người bạn tốt\b", "tri kỷ"),
    (r"\bbạn có muốn\b", "bạn có muốn"),
    (r"\bFirstlight Noya\b", "Noya - Khải Minh"),
    (r"\bNoya Sơ Quang\b", "Noya - Khải Minh"),
    (r"\bSơ Quang\b", "Khải Minh"),
]

def polish_text(t: str) -> str:
    res = t
    for pat, rep in REPLACEMENTS:
        res = re.sub(pat, rep, res, flags=re.IGNORECASE)
    
    # Specific targeted sentence fixes
    if "Cô ấy quả là một hiệp sĩ siêng năng và có tư tưởng công lý" in res:
        res = res.replace("Cô ấy quả là một hiệp sĩ siêng năng và có tư tưởng công lý... Giá như tất cả các Hiệp sĩ Vệ binh Hoàng gia cũng tận tâm như cô ấy.",
                          "Đúng là một nữ hiệp sĩ tương lai vừa mẫn cán lại vừa tôn sùng chính nghĩa... Ước gì hiệp sĩ nào của Cận Vệ Hoàng Gia cũng hết mình vì việc công như cô ấy!")
    if "Tuy nhiên, bản năng đầu tiên của cô là kiểm tra xem sự kiện này có tuân thủ tất cả các quy định hay không." in res:
        res = res.replace("Tuy nhiên, bản năng đầu tiên của cô là kiểm tra xem sự kiện này có tuân thủ tất cả các quy định hay không.",
                          "Thế nhưng, phản xạ đầu tiên của cô nàng lại là chạy lại soi xem người ta có tuân thủ đúng quy định hay không.")
    if "Một người đàn ông có vẻ ngoài lén lút lao qua bạn và bước đi nhanh nhẹn" in res:
        res = res.replace("Một người đàn ông có vẻ ngoài lén lút lao qua bạn và bước đi nhanh nhẹn, suýt khiến bạn mất thăng bằng.",
                          "Một gã đàn ông với dáng vẻ lấm lét va sầm vào bạn rồi thoăn thoắt bỏ đi, suýt chút nữa làm bạn ngã nhào.")
    
    return res

def main():
    items = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    polished = []
    modifications = []
    
    for it in items:
        cur_vi = it["current_vi"]
        new_vi = polish_text(cur_vi)
        it["polished_vi"] = new_vi
        polished.append(it)
        
        if new_vi != cur_vi:
            modifications.append({
                "table": it["table"],
                "key": it["key"],
                "before": cur_vi,
                "after": new_vi,
                "category": "Hẹn Hò & Nhân Vật",
                "reason": "Trau chuốt câu từ hẹn hò nhẹ nhàng, hóm hỉnh, đối thoại tự nhiên chuẩn anime",
                "agent": "Dating & Character Specialist Subagent"
            })
            
    OUTPUT_FILE.write_text(json.dumps(polished, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Pillar 1 Polish complete: {len(polished)} items processed, {len(modifications)} modifications made.")
    
    # Export modification draft
    mod_path = ROOT / "work" / "batches" / "audit_batch1_modifications.json"
    mod_path.write_text(json.dumps(modifications, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(modifications)} modifications to {mod_path.name}")

if __name__ == "__main__":
    main()
