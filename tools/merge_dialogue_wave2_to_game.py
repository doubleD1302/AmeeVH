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

TABLE_FILES = {
    "CharGetLines": "00603_0x8dcf06b298f46b28.bin",
    "CharacterArchiveContent": "00593_0x843b3b0812018dd2.bin",
    "Plot": "00703_0x8dc130b6f79ff422.bin",
    "StarTowerTalk": "00751_0xc4f681981a12028e.bin",
    "Story": "00752_0xdda397c15ce0b289.bin"
}

def load_batch(p: Path):
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error loading {p}: {e}")
        return []

def main():
    print("=== MASTER DIALOGUE WAVE 2 INTEGRATION PIPELINE ===")
    
    b4_path = BATCH_DIR / "dialogue_batch4_chargetlines_approved.json"
    b5a_path = BATCH_DIR / "dialogue_batch5a_archive_core_approved.json"
    b5b_path = BATCH_DIR / "dialogue_batch5b_archive_allies_approved.json"
    b6_path = BATCH_DIR / "dialogue_batch6_awakening_talk_approved.json"
    
    b4_items = load_batch(b4_path)
    b5a_items = load_batch(b5a_path)
    b5b_items = load_batch(b5b_path)
    b6_items = load_batch(b6_path)
    
    print(f"Loaded: B4={len(b4_items)}, B5A={len(b5a_items)}, B5B={len(b5b_items)}, B6={len(b6_items)}")
    all_items = b4_items + b5a_items + b5b_items + b6_items
    
    if not all_items:
        print("No approved items ready yet.")
        return False
        
    by_table = {}
    new_mods = []
    
    for it in all_items:
        t = it.get("table")
        k = it.get("key")
        after = it.get("approved_vi") or it.get("vi") or it.get("current_vi") or ""
        before = it.get("before") or it.get("en") or ""
        
        if not after or not t or not k:
            continue
            
        fname = TABLE_FILES.get(t)
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
                    "category": f"Lời Thoại & Ký Sự Nhân Vật ({t})",
                    "reason": it.get("reason", "Trau chuốt văn phong thuần Việt, xóa bỏ calque dịch máy thô thiển"),
                    "agent": it.get("agent", "Dialogue & Lore Specialist Subagent"),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
    print(f"Prepared {len(new_mods)} unique modifications across {len(by_table)} tables.")
    
    # Apply to entries
    applied = 0
    for tname, items in by_table.items():
        fname = TABLE_FILES.get(tname)
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
    total_md = export_audit_markdown(limit_preview=5000)
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
    
    print("\nMASTER DIALOGUE WAVE 2 INTEGRATION COMPLETE!")
    return True

if __name__ == "__main__":
    main()
