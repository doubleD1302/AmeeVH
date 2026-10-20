import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
EN_DIR = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"
VI_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
CN_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
BATCH_DIR = ROOT / "work" / "batches"
BATCH_DIR.mkdir(parents=True, exist_ok=True)

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

def main():
    print("Extracting Dialogue & Character Voice Batches...")
    
    # 1. Package 1: Noya - Khải Minh (Archive Voice, Backstory, Awakening Plot, Affinity Quests)
    b1_items = []
    
    # CharacterArchiveVoice (Noya 162)
    cav_fname = "00594_0xd8b61831cfe58bf2.bin"
    cav_en = load_json(EN_DIR / cav_fname)
    cav_vi = load_json(VI_DIR / cav_fname)
    cav_cn = load_json(CN_DIR / cav_fname)
    for k, v in cav_vi.items():
        if k.startswith("CharacterArchiveVoice.162"):
            b1_items.append({
                "table": "CharacterArchiveVoice",
                "file": cav_fname,
                "key": k,
                "en": cav_en.get(k, ""),
                "cn": cav_cn.get(k, ""),
                "current_vi": v
            })
            
    # CharacterArchiveContent (Noya 162)
    cac_fname = "00593_0x843b3b0812018dd2.bin"
    cac_en = load_json(EN_DIR / cac_fname)
    cac_vi = load_json(VI_DIR / cac_fname)
    cac_cn = load_json(CN_DIR / cac_fname)
    for k, v in cac_vi.items():
        if k.startswith("CharacterArchiveContent.162"):
            b1_items.append({
                "table": "CharacterArchiveContent",
                "file": cac_fname,
                "key": k,
                "en": cac_en.get(k, ""),
                "cn": cac_cn.get(k, ""),
                "current_vi": v
            })
            
    # Plot (Awakening Noya 162)
    plot_fname = "00703_0x8dc130b6f79ff422.bin"
    plot_en = load_json(EN_DIR / plot_fname)
    plot_vi = load_json(VI_DIR / plot_fname)
    plot_cn = load_json(CN_DIR / plot_fname)
    for k, v in plot_vi.items():
        if k.startswith("Plot.162"):
            b1_items.append({
                "table": "Plot",
                "file": plot_fname,
                "key": k,
                "en": plot_en.get(k, ""),
                "cn": plot_cn.get(k, ""),
                "current_vi": v
            })
            
    # AffinityQuest (Noya 162)
    aff_fname = "00576_0xde9e039952f8c2d2.bin"
    aff_en = load_json(EN_DIR / aff_fname)
    aff_vi = load_json(VI_DIR / aff_fname)
    aff_cn = load_json(CN_DIR / aff_fname)
    for k, v in aff_vi.items():
        if k.startswith("AffinityQuest.162"):
            b1_items.append({
                "table": "AffinityQuest",
                "file": aff_fname,
                "key": k,
                "en": aff_en.get(k, ""),
                "cn": aff_cn.get(k, ""),
                "current_vi": v
            })
            
    print(f"Package 1 (Noya Complete Archive): {len(b1_items)} entries")
    (BATCH_DIR / "dialogue_batch1_noya_archive.json").write_text(json.dumps(b1_items, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Package 2: Dating Character & Landmark Events
    b2_items = []
    dce_fname = "00611_0xd46d025e8dae5d69.bin"
    dce_en = load_json(EN_DIR / dce_fname)
    dce_vi = load_json(VI_DIR / dce_fname)
    dce_cn = load_json(CN_DIR / dce_fname)
    for k, v in dce_vi.items():
        v_en = dce_en.get(k, "")
        if v == v_en or any(w in v for w in ["của bạn", "của tôi", "trong khi", "cô ấy", "không thể không"]):
            b2_items.append({
                "table": "DatingCharacterEvent",
                "file": dce_fname,
                "key": k,
                "en": v_en,
                "cn": dce_cn.get(k, ""),
                "current_vi": v
            })
            
    dle_fname = "00613_0xdc09272e31aceb9b.bin"
    dle_en = load_json(EN_DIR / dle_fname)
    dle_vi = load_json(VI_DIR / dle_fname)
    dle_cn = load_json(CN_DIR / dle_fname)
    for k, v in dle_vi.items():
        v_en = dle_en.get(k, "")
        if v == v_en or any(w in v for w in ["của bạn", "của tôi", "trong khi", "cô ấy", "không thể không"]):
            b2_items.append({
                "table": "DatingLandmarkEvent",
                "file": dle_fname,
                "key": k,
                "en": v_en,
                "cn": dle_cn.get(k, ""),
                "current_vi": v
            })
    print(f"Package 2 (Dating & Landmark Events): {len(b2_items)} entries")
    (BATCH_DIR / "dialogue_batch2_dating_events.json").write_text(json.dumps(b2_items, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Package 3: Star Tower Dialogues & Story Quotes
    b3_items = []
    stt_fname = "00751_0xc4f681981a12028e.bin"
    stt_en = load_json(EN_DIR / stt_fname)
    stt_vi = load_json(VI_DIR / stt_fname)
    stt_cn = load_json(CN_DIR / stt_fname)
    for k, v in stt_vi.items():
        v_en = stt_en.get(k, "")
        if v == v_en or any(w in v for w in ["của bạn", "trí tưởng tượng của bạn", "của tôi", "Lữ Khách của bạn"]):
            b3_items.append({
                "table": "StarTowerTalk",
                "file": stt_fname,
                "key": k,
                "en": v_en,
                "cn": stt_cn.get(k, ""),
                "current_vi": v
            })
            
    story_fname = "00752_0xdda397c15ce0b289.bin"
    story_en = load_json(EN_DIR / story_fname)
    story_vi = load_json(VI_DIR / story_fname)
    story_cn = load_json(CN_DIR / story_fname)
    for k, v in story_vi.items():
        v_en = story_en.get(k, "")
        if any(w in v for w in ["nhiên liệu cuối cùng của bạn", "Chạy theo ý muốn của bạn", "mỏ neo của bạn"]):
            b3_items.append({
                "table": "Story",
                "file": story_fname,
                "key": k,
                "en": v_en,
                "cn": story_cn.get(k, ""),
                "current_vi": v
            })
    print(f"Package 3 (Star Tower & Story Quotes): {len(b3_items)} entries")
    (BATCH_DIR / "dialogue_batch3_startower_story.json").write_text(json.dumps(b3_items, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
