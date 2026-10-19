#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "work" / "research" / "data_decrypted" / "entries"
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return

    bin_files = list(data_dir.glob("*.bin"))
    print(f"Total bin files in data.arcx: {len(bin_files)}")

    categories = defaultdict(lambda: {"count": 0, "files": set(), "examples": []})
    total_strings = 0
    en_tables = 0
    cn_tables = 0

    for f in bin_files:
        try:
            content = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(content, dict):
                continue
            
            # Check if EN or CN based on content
            sample_val = next((v for v in content.values() if isinstance(v, str)), "")
            is_cn = any('\u4e00' <= char <= '\u9fff' for char in sample_val[:100])
            if is_cn:
                cn_tables += 1
            else:
                en_tables += 1

            for k, v in content.items():
                if not isinstance(v, str):
                    continue
                total_strings += 1
                prefix = k.split(".")[0] if "." in k else "Other"
                categories[prefix]["count"] += 1
                categories[prefix]["files"].add(f.name)
                if len(categories[prefix]["examples"]) < 2:
                    categories[prefix]["examples"].append((k, v[:40]))
        except Exception:
            pass

    print(f"\nTotal localization table files: {en_tables + cn_tables} ({en_tables} EN/VI tables, {cn_tables} CN reference tables)")
    print(f"Total localized string entries in data.arcx: {total_strings}")

    # Output detailed report
    report = []
    sorted_cats = sorted(categories.items(), key=lambda x: x[1]["count"], reverse=True)
    
    for cat, info in sorted_cats:
        c = info["count"]
        files_cnt = len(info["files"])
        ex = info["examples"][0] if info["examples"] else ("", "")
        report.append({
            "category": cat,
            "count": c,
            "files_count": files_cnt,
            "example_key": ex[0],
            "example_text": ex[1]
        })

    out_file = root / "work" / "research" / "text_inventory_summary.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved full inventory to: {out_file}")

    # Also inspect Lua scripts if available
    lua_arcx = root.parent / "Persistent_Store" / "Lua" / "lua.arcx"
    print(f"Lua archive exists: {lua_arcx.exists()} ({lua_arcx.stat().st_size if lua_arcx.exists() else 0} bytes)")

    # Inspect Video Subtitles
    videos_dir = root.parent / "Persistent_Store" / "Videos"
    srt_files = list(videos_dir.glob("*.srt"))
    total_cues = 0
    for srt in srt_files:
        lines = srt.read_text(encoding="utf-8", errors="ignore").splitlines()
        cue_cnt = sum(1 for line in lines if "-->" in line)
        total_cues += cue_cnt
        print(f"Subtitle: {srt.name} ({cue_cnt} cues)")
    print(f"Total Subtitle Cues: {total_cues} cues across {len(srt_files)} files")

if __name__ == "__main__":
    main()
