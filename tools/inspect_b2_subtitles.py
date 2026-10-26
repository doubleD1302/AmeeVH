import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN")
b2_path = ROOT / "StellaSora_VietHoa" / "work" / "batches" / "BATCH_FIX_02_SUBTITLES_CH10001INTRO.json"
b2 = json.loads(b2_path.read_text(encoding="utf-8"))

print(f"Batch 2 has {len(b2['entries'])} entries")

# Group by file
files = {}
for it in b2["entries"]:
    # id is e.g. "Persistent_Store/Videos/CH10001Intro1-CH10001Intro1_CNVA_FP_EN.srt::1"
    fpath_str, cue_id = it["id"].split("::")
    cue_num = int(cue_id)
    files.setdefault(fpath_str, []).append((cue_num, it["source_en"], it["text_vi"]))

for fpath_str, cues in files.items():
    print(f"\nFile: {fpath_str} ({len(cues)} cues)")
    actual_f = ROOT / fpath_str
    print(f"  Actual file exists: {actual_f.exists()}")
    if actual_f.exists():
        content = actual_f.read_text(encoding="utf-8")
        print(f"  Current file length: {len(content.splitlines())} lines")
        for cue_num, src, vi in cues[:3]:
            print(f"    Cue {cue_num}: [{src}] -> [{vi}]")
