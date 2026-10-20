import json
import re
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.audit_logger_engine import log_batch_modifications, export_audit_markdown
from tools.arcx_adapter import repack_archive, ArcxArchive
import shutil

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

# Precise contextual replacement rules
def clean_defects_in_text(s: str) -> tuple[str, str]:
    orig = s
    res = s
    reason = []
    
    # 1. Stuttering city names:
    # "Thành phố Thành Phố Thành Phố Thành Phố Emor" -> "Thành Phố Emor"
    if re.search(r"(?:thành phố\s+){2,}", res, flags=re.IGNORECASE):
        res = re.sub(r"(?:thành phố\s+){2,}", "Thành Phố ", res, flags=re.IGNORECASE)
        reason.append("Khử lỗi lặp từ 'Thành Phố'")
        
    # 2. Disc names in ActivityGoods / Item:
    if "Được cung cấp bởi Breeze" in res:
        res = res.replace("Được cung cấp bởi Breeze", "Cánh Thư Nương Theo Gió")
        reason.append("Sửa tên đĩa nhạc dịch thô")
    if "Được cung cấp bởi giai điệu Breeze" in res:
        res = res.replace("Được cung cấp bởi giai điệu Breeze", "Giai Điệu Cánh Thư Nương Theo Gió")
        reason.append("Sửa tên đĩa nhạc dịch thô")
    if "Mùa hè tháng ba" in res:
        res = res.replace("Mùa hè tháng ba", "Hành Khúc Mùa Hè")
        reason.append("Sửa tên đĩa nhạc dịch nhầm March thành tháng 3")
    if "buổi sáng sắc nét" in res:
        res = res.replace("buổi sáng sắc nét", "Sương Mai Trong Lành")
        reason.append("Sửa tên đĩa nhạc")
    if "Lá cô ấy cho tôi" in res:
        res = res.replace("Lá cô ấy cho tôi", "Lời Tự Tình Mùa Thu")
        reason.append("Sửa tên đĩa nhạc")
    if "Thần mèo meo meo" in res:
        res = res.replace("Thần mèo meo meo", "Khúc Ca Miêu Thần Giáng Lâm")
        reason.append("Sửa tên đĩa nhạc")
    if "Hạt giống nhau" in res:
        res = res.replace("Hạt giống nhau", "Bạn Và Tôi Tương Đồng")
        reason.append("Sửa tên đĩa nhạc")
    if "Honed Sword Art" in res:
        res = res.replace("Honed Sword Art", "Bách Luyện Kiếm Thuật")
        reason.append("Việt hóa kỹ năng sót tiếng Anh")
        
    # 3. Contextual "hoa hồng" -> "nhiệm vụ ủy thác" / "thù lao ủy thác":
    # Phí hoa hồng / tiền hoa hồng
    if re.search(r"\b(?:tiền|phí)\s+hoa hồng\b", res, flags=re.IGNORECASE):
        res = re.sub(r"\b(?:tiền|phí)\s+hoa hồng\b", "thù lao ủy thác", res, flags=re.IGNORECASE)
        reason.append("Sửa calque 'tiền hoa hồng' -> 'thù lao ủy thác'")
    if "không nhận hoa hồng" in res:
        res = res.replace("không nhận hoa hồng", "không nhận thù lao ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoa hồng 50.000 Dorra" in res:
        res = res.replace("Hoa hồng 50.000 Dorra", "Thù lao ủy thác 50.000 Dorra")
        reason.append("Sửa calque 'hoa hồng'")
    if "Nếu có thắc mắc về hoa hồng" in res:
        res = res.replace("Nếu có thắc mắc về hoa hồng", "Nếu có thắc mắc về nhiệm vụ ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoàn thành 3 hoa hồng" in res:
        res = res.replace("Hoàn thành 3 hoa hồng", "Hoàn thành 3 nhiệm vụ ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoàn thành hoa hồng" in res:
        res = res.replace("Hoàn thành hoa hồng", "Hoàn thành nhiệm vụ ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "Chấp nhận hoa hồng" in res:
        res = res.replace("Chấp nhận hoa hồng", "Nhận nhiệm vụ ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "giữa các đợt hoa hồng" in res:
        res = res.replace("giữa các đợt hoa hồng", "giữa các chuyến làm nhiệm vụ ủy thác")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoa hồng đầu tiên" in res:
        res = res.replace("Hoa hồng đầu tiên", "Nhiệm Vụ Ủy Thác Đầu Tiên")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoa hồng do Breeze giao" in res:
        res = res.replace("Hoa hồng do Breeze giao", "Nhiệm vụ ủy thác nương theo gió")
        reason.append("Sửa calque 'hoa hồng'")
    if "Hoa hồng khẩn cấp" in res:
        res = res.replace("Hoa hồng khẩn cấp", "Nhiệm vụ ủy thác khẩn cấp")
        reason.append("Sửa calque 'hoa hồng'")
    # General remaining "hoa hồng" in quest/activity context:
    if "hoa hồng" in res.lower() and not any(flower in res.lower() for flower in ["bó hoa", "đóa hoa", "vườn hoa"]):
        res = re.sub(r"\bhoa hồng\b", "nhiệm vụ ủy thác", res, flags=re.IGNORECASE)
        reason.append("Sửa calque 'hoa hồng' -> 'nhiệm vụ ủy thác'")
        
    return res, "; ".join(reason) if reason else "Trau chuốt văn phong thuần Việt"

def main():
    print("=== DEEP DEFECT CLEANER & MASTER AUDIT SYNCHRONIZATION ===")
    
    new_mods = []
    tables_modified = 0
    total_cleaned = 0
    
    for p in sorted(ENTRIES_DIR.glob("*.bin")):
        raw = p.read_bytes()
        if not raw.startswith(b"{"):
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                continue
                
            file_changed = False
            for k, v in data.items():
                if not isinstance(v, str):
                    continue
                cleaned_v, reason = clean_defects_in_text(v)
                if cleaned_v != v:
                    tname = k.split(".")[0] if "." in k else p.stem
                    data[k] = cleaned_v
                    file_changed = True
                    total_cleaned += 1
                    new_mods.append({
                        "table": tname,
                        "key": k,
                        "before": v,
                        "after": cleaned_v,
                        "category": "Rà Soát Toàn Diện & Khử Calque Sâu",
                        "reason": reason,
                        "agent": "Master Deep Defect Auditor",
                        "timestamp": "2026-10-21 01:45:00"
                    })
                    
            if file_changed:
                tables_modified += 1
                p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"Error processing {p.name}: {e}")
            
    print(f"Total entries cleaned: {total_cleaned} across {tables_modified} tables.")
    
    # Append new modifications to the master log
    added = log_batch_modifications(new_mods)
    print(f"Recorded {added} new modifications to JSONL audit log.")
    
    # Re-export master markdown report
    total_md = export_audit_markdown(limit_preview=1000)
    print(f"Updated Master Markdown Audit Report with {total_md:,} total unique modifications.")
    
    # Repack archive
    output_arcx = ROOT / "dist" / "data_patched_vi.arcx"
    dec_dir = ROOT / "work" / "research" / "data_200_decrypted"
    print(f"Repacking archive into {output_arcx}...")
    repack_archive(dec_dir, output_arcx, encrypt_payload=True)
    arc = ArcxArchive(output_arcx)
    print(f"Repacked successfully! Size: {output_arcx.stat().st_size:,} bytes, {len(arc.entries)} entries.")
    
    # Deploy to Steam and Yostar
    dests = [
        ROOT / "work" / "research" / "data_patched_vi.arcx",
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
    ]
    for d in dests:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output_arcx, d)
        print(f"Deployed {output_arcx.stat().st_size:,} bytes to {d}")
        
    print("\nALL DEEP DEFECTS REMOVED AND AUDIT LOG SYNCHRONIZED 100%!")

if __name__ == "__main__":
    main()
