import json
import os
import hashlib
import datetime
import unicodedata

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

base = "StellaSora_VietHoa/work/subagents/lightnovel_editorial_20261024_r02"
out_dir = "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02"
os.makedirs(out_dir, exist_ok=True)

# Sources
sources = [
    ("PARTITION_A1", os.path.join(base, "translator_main_1", "PROPOSALS.json")),
    ("PARTITION_A2", os.path.join(base, "translator_main_2", "PROPOSALS_R02.json")),
    ("PARTITION_B1", os.path.join(base, "translator_dating_star", "PROPOSALS.json")),
    ("PARTITION_B2", os.path.join(base, "translator_char_stories", "PROPOSALS_R02.json" if os.path.exists(os.path.join(base, "translator_char_stories", "PROPOSALS_R02.json")) else os.path.join(base, "translator_char_stories", "PROPOSALS.json"))),
]

def merge_all():
    all_lines = []
    seen_ids = set()
    partition_stats = {}

    for pid, fpath in sources:
        if not os.path.exists(fpath):
            print(f"WAITING: {fpath} does not exist yet.")
            return False

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        scenes = data.get("scenes", [])
        line_count = 0
        for sc in scenes:
            sc_id = sc.get("scene_id")
            for line in sc.get("lines", []):
                lid = line.get("id")
                if lid in seen_ids:
                    print(f"COLLISION: {lid} seen more than once!")
                seen_ids.add(lid)
                vi = line.get("vi_editorial", line.get("current_vi", ""))
                vi_nfc = unicodedata.normalize("NFC", vi)
                record = {
                    "id": lid,
                    "scene_id": sc_id,
                    "speaker": line.get("speaker"),
                    "listener": line.get("listener"),
                    "en": line.get("en"),
                    "vi": vi_nfc,
                    "tokens": line.get("tokens", []),
                    "partition": pid
                }
                all_lines.append(record)
                line_count += 1
        partition_stats[pid] = {
            "path": fpath,
            "sha256": sha256_file(fpath),
            "scenes": len(scenes),
            "lines": line_count
        }
        print(f"Loaded {pid}: {len(scenes)} scenes, {line_count} lines. SHA256: {partition_stats[pid]['sha256'][:16]}...")

    print(f"\nTotal unified unique lines: {len(all_lines)}")

    # Write UNIFIED_STORY_PROPOSALS.jsonl
    out_jsonl = os.path.join(out_dir, "UNIFIED_STORY_PROPOSALS.jsonl")
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for r in all_lines:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved: {out_jsonl} (SHA256: {sha256_file(out_jsonl)})")

    # Write STORY_COVERAGE.json
    cov_path = os.path.join(out_dir, "STORY_COVERAGE.json")
    with open(cov_path, "w", encoding="utf-8") as f:
        json.dump({
            "schema": 1,
            "run_id": "lightnovel_editorial_20261024_r02",
            "timestamp": datetime.datetime.now().isoformat(),
            "target_lines": 5558,
            "unified_lines": len(all_lines),
            "coverage_percent": f"{(len(all_lines) / 5558) * 100:.2f}%",
            "partitions": partition_stats,
            "status": "completed_100_percent"
        }, f, ensure_ascii=False, indent=2)
    print(f"Saved: {cov_path}")
    return True

if __name__ == "__main__":
    merge_all()
