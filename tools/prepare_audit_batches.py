import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
EN_DIR = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"
VI_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
CN_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
BATCH_DIR = ROOT / "work" / "batches"
BATCH_DIR.mkdir(parents=True, exist_ok=True)

TABLE_FILES = {
    # Pillar 1: Dating, Character Events & Profiles
    "DatingCharacterEvent": "00611_0xd46d025e8dae5d69.bin",
    "DatingLandmarkEvent": "00613_0xdc09272e31aceb9b.bin",
    "CharacterArchiveContent": "00593_0x843b3b0812018dd2.bin",
    "CharacterArchiveBaseInfo": "00592_0x200c969f988e4634.bin",
    "CharacterDes": "00596_0x189f915177d3b2ff.bin",
    
    # Pillar 2: UI, System, Achievements & World Encyclopedia
    "UIText": "00789_0x87cc29ac0defc2d9.bin",
    "Achievement": "00553_0x5b0fc2f5fe45a572.bin",
    "Word": "00798_0x78b1aa32bbcf433e.bin",
    "DictionaryDiagram": "00616_0x88d705ae9564e65e.bin",
    
    # Pillar 3: Items, Mall Packages & Tasks
    "Item": "00653_0xe60634348b826f41.bin",
    "MallPackage": "00671_0xee9e1d54770d965d.bin",
    "ActivityGoods": "00557_0x988f7b6f2592bacd.bin",
    "ActivityTask": "00573_0x5c7be7cfcb1d2241.bin",
    "LevelQuestTarget": "00662_0x246664fcfc9d916b.bin"
}

def load_json(p: Path):
    if not p.exists():
        return {}
    try:
        raw = p.read_bytes()
        if raw.startswith(b"{"):
            return json.loads(raw.decode("utf-8"))
    except Exception:
        pass
    return {}

def extract_pillar(tables, max_items=None):
    items = []
    for tname in tables:
        fname = TABLE_FILES.get(tname)
        if not fname:
            continue
        vi_data = load_json(VI_DIR / fname)
        en_data = load_json(EN_DIR / fname)
        cn_data = load_json(CN_DIR / fname)
        
        for k, vi_val in vi_data.items():
            if not isinstance(vi_val, str) or not vi_val.strip():
                continue
            en_val = en_data.get(k, "")
            cn_val = cn_data.get(k, "")
            
            # Skip if purely numeric or technical identifier
            if vi_val.isdigit() or vi_val.startswith("res/") or vi_val.endswith(".png"):
                continue
            # If 104 music discs in Item, skip since already polished
            if tname == "Item" and any(k.startswith(f"Item.{did}.") for did in range(211000, 215000)):
                continue
                
            items.append({
                "table": tname,
                "file": fname,
                "key": k,
                "en": en_val,
                "cn": cn_val,
                "current_vi": vi_val
            })
            if max_items and len(items) >= max_items:
                break
    return items

def main():
    print("Preparing audit batches...")
    
    p1_tables = ["DatingCharacterEvent", "DatingLandmarkEvent", "CharacterArchiveContent", "CharacterArchiveBaseInfo", "CharacterDes"]
    p2_tables = ["UIText", "Achievement", "Word", "DictionaryDiagram"]
    p3_tables = ["Item", "MallPackage", "ActivityGoods", "ActivityTask", "LevelQuestTarget"]
    
    p1_items = extract_pillar(p1_tables)
    p2_items = extract_pillar(p2_tables)
    p3_items = extract_pillar(p3_tables)
    
    print(f"Pillar 1 (Dating & Characters): {len(p1_items)} entries")
    print(f"Pillar 2 (UI, System, Ach & Dict): {len(p2_items)} entries")
    print(f"Pillar 3 (Items, Mall & Tasks): {len(p3_items)} entries")
    
    b1_path = BATCH_DIR / "audit_batch1_dating_char.json"
    b2_path = BATCH_DIR / "audit_batch2_ui_sys_ach.json"
    b3_path = BATCH_DIR / "audit_batch3_item_mall_task.json"
    
    b1_path.write_text(json.dumps(p1_items, indent=2, ensure_ascii=False), encoding="utf-8")
    b2_path.write_text(json.dumps(p2_items, indent=2, ensure_ascii=False), encoding="utf-8")
    b3_path.write_text(json.dumps(p3_items, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"Saved {b1_path.name} ({b1_path.stat().st_size:,} bytes)")
    print(f"Saved {b2_path.name} ({b2_path.stat().st_size:,} bytes)")
    print(f"Saved {b3_path.name} ({b3_path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
