#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "work" / "research" / "data_decrypted" / "entries"

    # Analyze EN tables specifically
    en_categories = defaultdict(lambda: {"count": 0, "file": "", "examples": []})
    total_en_strings = 0
    en_files_count = 0

    bin_files = list(data_dir.glob("*.bin"))

    for f in bin_files:
        try:
            content = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(content, dict):
                continue
            
            # Identify if this is the EN/VI file vs the CN file
            # If >30% of chars in first 5 string values are CJK, it's CN
            sample_strings = [v for v in content.values() if isinstance(v, str)][:5]
            if not sample_strings:
                continue
            
            cjk_chars = 0
            total_chars = 0
            for s in sample_strings:
                for c in s:
                    total_chars += 1
                    if '\u4e00' <= c <= '\u9fff':
                        cjk_chars += 1
            
            is_cn = (cjk_chars / max(1, total_chars)) > 0.3
            if is_cn:
                continue # Skip CN reference table for EN inventory count

            en_files_count += 1
            for k, v in content.items():
                if not isinstance(v, str):
                    continue
                total_en_strings += 1
                prefix = k.split(".")[0] if "." in k else "Other"
                en_categories[prefix]["count"] += 1
                en_categories[prefix]["file"] = f.name
                if len(en_categories[prefix]["examples"]) < 2:
                    en_categories[prefix]["examples"].append((k, v[:60]))
        except Exception:
            pass

    print(f"Total EN Table Files: {en_files_count}")
    print(f"Total Unique EN Localization Strings: {total_en_strings}")

    # Track translated status
    # Translated so far:
    # 1. 00007 (UIText): 35 strings
    # 2. 00577 (Item): 3,777 strings
    # 3. 00494 (Achievement): 1,314 strings
    # 4. 00636 (Skill): 1,350 strings
    translated_stats = {
        "UIText (Core UI)": 35,
        "Item": 3777,
        "Achievement": 1314,
        "Skill": 1350,
        "Subtitles (Videos)": 51
    }
    total_translated = sum(translated_stats.values())
    print(f"Total Strings Translated So Far: {total_translated}")

    sorted_cats = sorted(en_categories.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # Save structured breakdown
    breakdown = {
        "summary": {
            "total_en_tables": en_files_count,
            "total_en_strings": total_en_strings,
            "total_translated_strings": total_translated,
            "total_remaining_strings": total_en_strings - total_translated + 51,
            "percent_completed": round((total_translated / (total_en_strings + 51)) * 100, 2)
        },
        "translated_breakdown": translated_stats,
        "categories": [
            {
                "category": cat,
                "count": info["count"],
                "file": info["file"],
                "example_key": info["examples"][0][0] if info["examples"] else "",
                "example_value": info["examples"][0][1] if info["examples"] else ""
            }
            for cat, info in sorted_cats
        ]
    }

    out_file = root / "work" / "research" / "detailed_localization_breakdown.json"
    out_file.write_text(json.dumps(breakdown, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Breakdown saved to: {out_file}")

if __name__ == "__main__":
    main()
