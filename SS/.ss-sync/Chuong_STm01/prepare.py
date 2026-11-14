"""Prepare lossless Ch. 1 Merge data for the existing Google spreadsheet.

This script never writes Merge/source/glossary files and makes no network calls.
Run with --summary, --chunk START COUNT, --small-tables, or --mark-published.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
import uuid

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent.parent
RESOURCE = WORKSPACE / "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03"
CHAPTER = RESOURCE / "01_CotTruyen/01_Chinh/Chuong_STm01"
MANIFEST = HERE / "manifest.json"
PAYLOAD = HERE / "payload.json"
SPREADSHEET_ID = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"
HEADER = re.compile(r"^(\d+)\. \[(.*)\] \((.*)\)$")
SOURCE_HEADER = re.compile(r"^\[([^\]]+)\]$")
BLOCK_COLUMNS = [
    "block_id", "scene_id", "block_order", "kind", "speaker_vi", "speaker_en",
    "speaker_jp", "speaker_cn", "text_cn", "text_jp", "text_en", "text_vi",
    "merge_header_raw", "source_refs_json", "source_hash", "revision", "updated_at",
]
SCENE_COLUMNS = ["scene_id", "chapter_id", "sort_order", "merge_path"]
PROPOSAL_COLUMNS = [
    "session_id", "block_id", "author_id", "author_name", "new_text", "note",
    "base_block_revision", "proposal_revision", "updated_at",
]
CONTROL_COLUMNS = [
    "schema_version", "session_id", "session_state", "release_id", "opened_at",
    "locked_at", "pending_publish_id", "pending_payload_hash",
]


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(value):
    raw = value if isinstance(value, bytes) else compact(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_merge(path):
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), f"Missing UTF-8 BOM: {path}"
    assert b"\n" not in raw.replace(b"\r\n", b""), f"Non-CRLF source: {path}"
    lines = raw.decode("utf-8-sig").splitlines(keepends=True)
    starts = [(i, HEADER.fullmatch(s.removesuffix("\r\n"))) for i, s in enumerate(lines)]
    starts = [(i, m) for i, m in starts if m]
    assert starts and starts[0][0] == 0
    blocks, rebuilt = [], []
    for index, (start, match) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        body = lines[start + 1:end]
        assert len(body) >= 4, f"Short block: {path}:{start + 1}"
        assert all(not s.strip() for s in body[4:]), f"Unexpected extra lines: {path}:{start + 1}"
        assert int(match[1]) == index + 1, f"Nonsequential block: {path}:{start + 1}"
        values = [s.removesuffix("\r\n") for s in body[:4]]
        names = match[2].split("/ ")
        assert len(names) in (1, 4), f"Unknown speaker header: {match[0]}"
        names = [s.strip() for s in names]
        if len(names) == 1:
            names = [names[0], "", "", ""]
        blocks.append({
            "order": int(match[1]), "speaker_raw": match[2], "speakers": names,
            "kind": match[3], "header": match[0], "texts": values,
        })
        rebuilt.extend([match[0] + "\r\n"] + [x + body[i][len(x):] for i, x in enumerate(values)] + body[4:])
    assert b"\xef\xbb\xbf" + "".join(rebuilt).encode("utf-8") == raw, f"Roundtrip failed: {path}"
    return blocks, digest(raw)


def token_table():
    table = collections.defaultdict(lambda: collections.defaultdict(dict))
    with (WORKSPACE / "glossary/glossary.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            match = re.fullmatch(r"SEX/(==SEX\d+==)/(\d+)", row.get("id", ""))
            if match:
                for locale in ("EN", "JP", "CN"):
                    table[locale][match[1]][int(match[2])] = row[locale]
    return {
        locale: {token: "/".join(variants[i] for i in sorted(variants)) for token, variants in tokens.items()}
        for locale, tokens in table.items()
    }


def source_index(path, token_map):
    """Only exact matches (or explicit gender expansion) are considered candidates."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    index = collections.defaultdict(list)
    for i, line in enumerate(lines):
        match = SOURCE_HEADER.fullmatch(line)
        if not match or i + 1 >= len(lines):
            continue
        value = lines[i + 1]
        if value in ("", "[EMPTY_SOURCE]"):
            continue
        source_id = match[1]
        source_id = re.sub(r"(command/\d+) [^/]+/", r"\1/", source_id)
        record = {"id": source_id, "header": match[1], "method": "exact"}
        index[value].append(record)
        expanded = re.sub(r"==SEX\d+==", lambda m: token_map.get(m[0], m[0]), value)
        if expanded != value:
            index[expanded].append({**record, "method": "gender_expanded_exact"})
            # Some Merge locales retain two complete gender-specific sentences.
            pairs = {token: replacement.split("/") for token, replacement in token_map.items()}
            if all(len(pairs[m[0]]) == 2 for m in re.finditer(r"==SEX\d+==", value) if m[0] in pairs):
                variants = [re.sub(r"==SEX\d+==", lambda m: pairs.get(m[0], [m[0], m[0]])[gender], value) for gender in (0, 1)]
                combined = "/".join(variants)
                if combined != expanded:
                    index[combined].append({**record, "method": "gender_sentence_variants_exact"})
    return index


def refs_for(text, index, source_path):
    if text == "[MISSING_SOURCE]":
        return {"status": "missing_source", "source_file": source_path}
    candidates = list({r["id"]: r for r in index.get(text, [])}.values())
    if len(candidates) == 1:
        return {"status": "matched", "source_file": source_path, **candidates[0]}
    if candidates:
        return {"status": "ambiguous", "source_file": source_path, "candidate_ids": [r["id"] for r in candidates]}
    return {"status": "unresolved", "source_file": source_path}


def build():
    previous = load_json(MANIFEST) if MANIFEST.exists() else {}
    by_position = {(r["scene_id"], r["block_order"]): r for r in previous.get("blocks", [])}
    by_hash = collections.defaultdict(list)
    for row in previous.get("blocks", []):
        by_hash[(row["scene_id"], row["source_hash"])].append(row)
    timestamp = now()
    tokens = token_table()
    scenes, rows, mappings, files, summaries = [], [], [], {}, []
    reference_counts = {locale: collections.Counter() for locale in ("en", "jp", "cn")}
    used_ids = set()
    merge_paths = sorted(CHAPTER.rglob("*_Merge.txt"))
    assert len(merge_paths) == 12, f"Expected 12 Chapter 1 files, found {len(merge_paths)}"
    for scene_order, path in enumerate(merge_paths, 1):
        scene_id = path.parent.name
        blocks, file_hash = parse_merge(path)
        relative = path.relative_to(WORKSPACE).as_posix()
        files[relative] = file_hash
        scenes.append([scene_id, "STm01", scene_order, relative])
        indexes, source_paths = {}, {}
        for locale in ("EN", "JP", "CN"):
            source = path.with_name(f"{scene_id}_{locale}.txt")
            indexes[locale] = source_index(source, tokens[locale])
            source_paths[locale] = source.relative_to(WORKSPACE).as_posix()
            files[source_paths[locale]] = digest(source.read_bytes())
        for block in blocks:
            cn, jp, en, vi = block["texts"]
            source_hash = digest({"speaker_raw": block["speaker_raw"], "kind": block["kind"], "cn": cn, "jp": jp, "en": en})
            vi_hash = digest(vi.encode("utf-8"))
            old = by_position.get((scene_id, block["order"]))
            if old and old["source_hash"] != source_hash:
                old = None
            if not old:
                matches = [x for x in by_hash[(scene_id, source_hash)] if x["block_id"] not in used_ids]
                old = matches[0] if len(matches) == 1 else None
            block_id = old["block_id"] if old else str(uuid.uuid4())
            assert block_id not in used_ids
            used_ids.add(block_id)
            revision = old["revision"] + (old["vi_hash"] != vi_hash) if old else 1
            updated_at = old["updated_at"] if old and old["vi_hash"] == vi_hash else timestamp
            refs = {}
            for locale, text in (("CN", cn), ("JP", jp), ("EN", en)):
                ref = refs_for(text, indexes[locale], source_paths[locale])
                refs[locale.lower()] = ref
                reference_counts[locale.lower()][ref["status"]] += 1
            row = [block_id, scene_id, block["order"], block["kind"], *block["speakers"],
                   cn, jp, en, vi, block["header"], compact(refs), source_hash, revision, updated_at]
            assert len(row) == len(BLOCK_COLUMNS)
            assert all(not isinstance(x, str) or len(x.encode("utf-16-le")) // 2 <= 50000 for x in row)
            rows.append(row)
            mappings.append({"block_id": block_id, "scene_id": scene_id, "block_order": block["order"],
                             "source_hash": source_hash, "vi_hash": vi_hash, "revision": revision, "updated_at": updated_at})
        summaries.append({"scene_id": scene_id, "blocks": len(blocks), "kinds": dict(collections.Counter(b["kind"] for b in blocks))})
    assert len(rows) == 1507
    payload_hash = digest({"scenes": scenes, "blocks": rows})
    unchanged = previous.get("payload_hash") == payload_hash
    session_id = previous.get("session_id") if unchanged else str(uuid.uuid4())
    release_id = previous.get("release_id") if unchanged else str(uuid.uuid4())
    prepared_at = previous.get("prepared_at") if unchanged else timestamp
    control = [1, session_id, "PUBLISHING", "", "", prepared_at, release_id, payload_hash]
    tables = {
        "DB_Scenes": {"headers": SCENE_COLUMNS, "rows": scenes},
        "DB_Blocks": {"headers": BLOCK_COLUMNS, "rows": rows},
        "DB_Proposals": {"headers": PROPOSAL_COLUMNS, "rows": []},
        "DB_Control": {"headers": CONTROL_COLUMNS, "rows": [control]},
    }
    payload = {"spreadsheet_id": SPREADSHEET_ID, "session_id": session_id, "release_id": release_id,
               "payload_hash": payload_hash, "prepared_at": prepared_at, "tables": tables,
               "summary": {"scenes": summaries, "total_blocks": len(rows), "source_refs": reference_counts,
                           "blank_vi": sum(not r[11] for r in rows), "max_cell_characters": max(len(str(x)) for r in rows for x in r)}}
    manifest = {"schema_version": 1, "spreadsheet_id": SPREADSHEET_ID, "scope": ["STm01"],
                "session_id": session_id, "release_id": release_id, "payload_hash": payload_hash,
                "prepared_at": prepared_at, "status": previous.get("status", "prepared") if unchanged else "prepared",
                "source_files": files, "blocks": mappings}
    if unchanged:
        for key in ("published_at", "sheet_ids", "remote_control"):
            if key in previous:
                manifest[key] = previous[key]
    save_json(PAYLOAD, payload)
    save_json(MANIFEST, manifest)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--chunk", nargs=2, type=int)
    parser.add_argument("--small-tables", action="store_true")
    parser.add_argument("--mark-published", action="store_true")
    parser.add_argument("--verify-sources", action="store_true")
    args = parser.parse_args()
    if args.verify_sources:
        manifest = load_json(MANIFEST)
        changed = [p for p, h in manifest["source_files"].items() if digest((WORKSPACE / p).read_bytes()) != h]
        assert not changed, changed
        print(compact({"verified_files": len(manifest["source_files"]), "changed": changed}))
        return
    if args.mark_published:
        manifest = load_json(MANIFEST)
        verification = load_json(HERE / "verification.json")
        assert verification["all_cells_match"] and verification["release_id"] == manifest["release_id"]
        assert verification["payload_hash"] == manifest["payload_hash"]
        manifest.update(status="published", published_at=now(),
                        sheet_ids={x["name"]: x["sheet_id"] for x in verification["tables"]},
                        remote_control=verification["control"])
        save_json(MANIFEST, manifest)
        print(compact({"status": manifest["status"], "published_at": manifest["published_at"]}))
        return
    payload = load_json(PAYLOAD) if (args.chunk or args.small_tables) else build()
    if args.chunk:
        start, count = args.chunk
        print(compact({"start": start, "headers": BLOCK_COLUMNS, "rows": payload["tables"]["DB_Blocks"]["rows"][start:start + count]}))
    elif args.small_tables:
        print(compact({k: v for k, v in payload["tables"].items() if k != "DB_Blocks"} | {"meta": {k: payload[k] for k in ("session_id", "release_id", "payload_hash", "prepared_at")}}))
    else:
        print(compact(payload["summary"] | {"payload_hash": payload["payload_hash"], "session_id": payload["session_id"], "release_id": payload["release_id"]}))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
