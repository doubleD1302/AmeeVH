import json
import time
import shutil
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.audit_logger_engine import log_batch_modifications, export_audit_markdown
from tools.arcx_adapter import repack_archive, ArcxArchive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
PRISTINE_DIR = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"
BATCH_DIR = ROOT / "work" / "batches"

def get_table_files():
    en_files = {}
    for p in ENTRIES_DIR.glob("00[5-7]*.bin"):
        try:
            raw = p.read_bytes()
            if not raw.startswith(b"{"):
                continue
            d = json.loads(raw.decode("utf-8"))
            if not d:
                continue
            tname = next(iter(d.keys())).split(".")[0]
            en_files[tname] = p.name
        except:
            pass
    return en_files

def load_batch(p: Path):
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error loading {p}: {e}")
        return []

def main():
    print("=== FINAL CLEANUP 6-BATCH MASTER INTEGRATION PIPELINE ===")
    table_files = get_table_files()
    
    batch_defs = [
        (1, "combat_skills", "Kỹ Năng & Chiến Đấu Hệ Khác"),
        (2, "soldier_roguelike", "Minigame Binh Sĩ Giác Đấu"),
        (3, "items_goods", "Vật Phẩm, Tiền Tệ & Shop"),
        (4, "ui_system", "Giao Diện & Hệ Thống Cài Đặt"),
        (5, "quests_activities", "Nhiệm Vụ & Mốc Thân Mật"),
        (6, "char_info_mail", "Thông Tin Nhân Vật & Thư Từ")
    ]
    
    batches = []
    for num, tag, cat in batch_defs:
        f_ver = BATCH_DIR / f"final_batch{num}_{tag}_verified.json"
        f_app = BATCH_DIR / f"final_batch{num}_{tag}_approved.json"
        chosen = f_ver.name if f_ver.exists() else f_app.name
        batches.append((chosen, cat))
    
    all_items = []
    for fname, cat in batches:
        fpath = BATCH_DIR / fname
        items = load_batch(fpath)
        print(f"{fname:45} : {len(items)} items loaded")
        for it in items:
            it["_cat"] = cat
            all_items.append(it)
            
    if not all_items:
        print("No approved items ready yet.")
        return False
        
    by_table = {}
    new_mods = []
    
    for it in all_items:
        t = it.get("table")
        k = it.get("key")
        after = it.get("approved_vi") or it.get("vi") or ""
        before = it.get("before") or it.get("en") or ""
        
        if not after or not t or not k:
            continue
            
        fname = table_files.get(t)
        if not fname:
            continue
            
        cur_file = ENTRIES_DIR / fname
        if cur_file.exists():
            data_cur = json.loads(cur_file.read_text(encoding="utf-8"))
            val_in_file = data_cur.get(k, "")
            if val_in_file != after:
                by_table.setdefault(t, []).append((k, after))
                new_mods.append({
                    "table": t,
                    "key": k,
                    "before": val_in_file if val_in_file else before,
                    "after": after,
                    "category": it.get("_cat", f"Việt Hóa ({t})"),
                    "reason": it.get("reason", "Việt hóa hoàn thiện, trau chuốt chuẩn xác theo nguyên tác"),
                    "agent": it.get("agent", "Final Cleanup Specialist Subagent"),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
    print(f"\nPrepared {len(new_mods)} unique modifications across {len(by_table)} tables.")
    
    # Apply to entries
    applied = 0
    for tname, items in by_table.items():
        fname = table_files.get(tname)
        if not fname:
            continue
        fpath = ENTRIES_DIR / fname
        if not fpath.exists():
            continue
        data = json.loads(fpath.read_text(encoding="utf-8"))
        for k, v in items:
            data[k] = v
            applied += 1
        fpath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated {len(items)} keys in {tname} ({fname})")
        
    print(f"Total applied to database files: {applied}")
    
    # Log to audit ledger JSONL
    added = log_batch_modifications(new_mods)
    print(f"Recorded {added} modifications to Master JSONL audit log.")
    
    # Export full markdown report
    total_md = export_audit_markdown(limit_preview=6000)
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

    # Copy to Artifact directory
    artifact_md = Path(r"C:\Users\chann\.gemini\antigravity\brain\8e8a9173-a2d5-480c-8796-43f007ac5c32\SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md")
    shutil.copy2(ROOT / "work" / "audit_log" / "SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md", artifact_md)
    print(f"Copied updated report to artifact: {artifact_md} ({artifact_md.stat().st_size:,} bytes)")
    
    print("\nFINAL CLEANUP INTEGRATION COMPLETE!")
    return True

if __name__ == "__main__":
    main()
