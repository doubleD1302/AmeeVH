"""Read current story Merge files and export the agreed twelve-column partition.

This is independent of the legacy DB_Blocks publisher. No source is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from prepare import CHAPTER, WORKSPACE, parse_merge

HEADERS = [
    "file_id", "block_order", "kind", "speaker_en", "speaker_jp", "speaker_cn",
    "speaker_vi", "text_vi", "text_cn", "text_jp", "text_en", "source_refs_json",
]


def export_file(path):
    blocks, file_hash = parse_merge(path)
    file_id = path.stem.removesuffix("_Merge")
    rows = []
    for b in blocks:
        speaker_vi, speaker_en, speaker_jp, speaker_cn = b["speakers"]
        text_cn, text_jp, text_en, text_vi = b["texts"]
        rows.append([file_id, b["order"], b["kind"], speaker_en, speaker_jp,
                     speaker_cn, speaker_vi, text_vi, text_cn, text_jp, text_en, ""])
    assert len({(r[0], r[1]) for r in rows}) == len(rows)
    assert all(len(r) == 12 and r[11] == "" and r[7].strip() for r in rows)
    return {"file_id": file_id, "merge_path": path.relative_to(WORKSPACE).as_posix(),
            "source_sha256": file_hash, "blocks": len(rows), "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", default="Chuong_STm01")
    parser.add_argument("--file")
    parser.add_argument("--chunk", nargs=2, type=int, metavar=("START", "COUNT"))
    args = parser.parse_args()
    assert re.fullmatch(r"Chuong_STm\d+", args.chapter), "Invalid chapter name"
    chapter = CHAPTER.with_name(args.chapter)
    paths = sorted(chapter.rglob("*_Merge.txt"))
    assert paths, f"No Merge files: {chapter}"
    if args.chapter == "Chuong_STm01":
        assert len(paths) == 12
    if args.file:
        selected = [p for p in paths if p.stem.removesuffix("_Merge") == args.file]
        assert len(selected) == 1
        result = export_file(selected[0])
    else:
        files = [export_file(p) for p in paths]
        total = sum(f["blocks"] for f in files)
        if args.chapter == "Chuong_STm01":
            assert total == 1507
        assert len({f["file_id"] for f in files}) == len(files)
        result = {"sheet_name": args.chapter, "content_type": "story", "headers": HEADERS,
                  "files": [{k: v for k, v in f.items() if k != "rows"} for f in files],
                  "total_blocks": total}
        if args.chunk:
            start, count = args.chunk
            assert start >= 0 and count > 0
            result = {"start": start, "rows": [r for f in files for r in f["rows"]][start:start + count]}
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
