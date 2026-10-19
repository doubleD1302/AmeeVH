#!/usr/bin/env python3
"""Extract target pillars from decrypted entries for subagent processing."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    entries_dir = root / "work" / "research" / "data_decrypted" / "entries"
    grouping_file = root / "work" / "batches" / "pillars_grouping.json"
    
    with open(grouping_file, "r", encoding="utf-8") as f:
        grouping = json.load(f)

    for pillar_key, cat_list in grouping.items():
        pillar_data = {}
        for cat_info in cat_list:
            fname = cat_info.get("file")
            cat_name = cat_info.get("category")
            if not fname:
                continue
            fpath = entries_dir / fname
            if not fpath.exists():
                print(f"Warning: {fpath} does not exist!")
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                content = json.load(f)
            pillar_data[cat_name] = {
                "file": fname,
                "count": len(content),
                "entries": content
            }
        
        out_file = root / "work" / "batches" / f"{pillar_key}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(pillar_data, f, ensure_ascii=False, indent=2)
        
        total_strings = sum(v["count"] for v in pillar_data.values())
        print(f"Pillar {pillar_key}: {len(pillar_data)} tables, {total_strings} strings -> {out_file.name}")

if __name__ == "__main__":
    main()
