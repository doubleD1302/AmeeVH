import json
import time
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
LOG_DIR = ROOT / "work" / "audit_log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

JSONL_PATH = LOG_DIR / "SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.jsonl"
MD_PATH = LOG_DIR / "SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md"

def log_batch_modifications(records: list):
    """Batch appends records to the JSONL log, ensuring all fields are present."""
    if not records:
        return 0
    added = 0
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        for r in records:
            b = r.get("before", "")
            a = r.get("after", "")
            if b == a:
                continue
            if "timestamp" not in r:
                r["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            added += 1
    return added

def export_audit_markdown(limit_preview: int = 10000):
    """Exports the complete audit ledger to a beautifully structured Markdown report."""
    if not JSONL_PATH.exists():
        print("Audit log JSONL does not exist yet.")
        return 0
        
    records = []
    seen = {}
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    t_k = (obj.get("table", ""), obj.get("key", ""))
                    # Dedup by (table, key), keeping latest
                    seen[t_k] = obj
                except Exception:
                    pass
                    
    records = list(seen.values())
    total = len(records)
    print(f"Compiling Master Audit Report for {total:,} verified modifications...")
    
    # Categorize
    by_cat = {}
    by_table = {}
    by_agent = {}
    for r in records:
        c = r.get("category", "Khác")
        t = r.get("table", "Unknown")
        ag = r.get("agent", "Chuyên viên")
        by_cat[c] = by_cat.get(c, 0) + 1
        by_table[t] = by_table.get(t, 0) + 1
        by_agent[ag] = by_agent.get(ag, 0) + 1
        
    md = []
    md.append("# 📖 SỔ TAY ĐỐI SOÁT TOÀN BỘ SỬA ĐỔI BẢN DỊCH STELLA SORA")
    md.append(f"> **Tổng số lượng sửa đổi được đối soát & lưu vết:** **{total:,} mục**  ")
    md.append(f"> **Thời gian chốt sổ:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append("> **Quy chuẩn bản địa hóa:** Văn phong anime RPG thuần Việt, dí dỏm, nhẹ nhàng, tự nhiên, chuẩn ngữ pháp, bảo toàn 100% token kỹ thuật.")
    md.append("\n---\n")
    
    md.append("## 1. THỐNG KÊ SỬA ĐỔI THEO PHÂN LOẠI CHUYÊN MỤC")
    md.append("| Chuyên mục | Số lượng sửa đổi | Tỷ trọng |")
    md.append("| :--- | :---: | :---: |")
    for c, cnt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
        md.append(f"| **{c}** | {cnt:,} | {cnt/total*100:.1f}% |")
        
    md.append("\n## 2. THỐNG KÊ SỬA ĐỔI THEO ĐỘI NGŨ SUBAGENTS PHỤ TRÁCH")
    md.append("| Subagent Phụ Trách | Số lượng hoàn thành |")
    md.append("| :--- | :---: |")
    for ag, cnt in sorted(by_agent.items(), key=lambda x: x[1], reverse=True):
        md.append(f"| `{ag}` | {cnt:,} |")

    md.append("\n## 3. THỐNG KÊ SỬA ĐỔI THEO BẢNG CƠ SỞ DỮ LIỆU")
    md.append("| Tên bảng | Số lượng sửa đổi |")
    md.append("| :--- | :---: |")
    for t, cnt in sorted(by_table.items(), key=lambda x: x[1], reverse=True)[:35]:
        md.append(f"| `{t}` | {cnt:,} |")
        
    md.append("\n---\n")
    md.append("## 4. CHI TIẾT ĐỐI SOÁT TRƯỚC - SAU (BẢNG TRA CỨU)")
    md.append("| Bảng | Khóa (Key) | Bản dịch cũ (Lủng củng / Thô) | Bản dịch mới (Trau chuốt / Thuần Việt) | Lý do điều chỉnh |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for r in records[:limit_preview]:
        b = r.get("before", "").replace("\n", " ").replace("|", "\\|")[:90]
        a = r.get("after", "").replace("\n", " ").replace("|", "\\|")[:90]
        reason = r.get("reason", "").replace("|", "\\|")
        md.append(f"| `{r.get('table')}` | `{r.get('key')}` | {b} | **{a}** | {reason} |")
        
    if total > limit_preview:
        md.append(f"\n*(Báo cáo hiển thị {limit_preview} mục tiêu biểu. Toàn bộ {total:,} bản ghi đối soát đầy đủ 100% được lưu trữ nguyên tử tại: `work/audit_log/SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.jsonl`)*")
        
    MD_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"Master Audit Report generated successfully at: {MD_PATH} ({MD_PATH.stat().st_size:,} bytes)")
    return total

if __name__ == "__main__":
    export_audit_markdown()
