#!/usr/bin/env python3
"""Stella Sora EN -> VI preparation tools. Standard library; never writes game data."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata

PROJECT = Path(__file__).resolve().parents[1]
SCHEMA = 1
GROUPS = ["StellaSora_Data", "Persistent_Store", "Patch_Store"]
TOKEN = re.compile(
    r"\$\{[^{}\n]+\}|\{\{[^{}\n]+\}\}|\{[^{}\n]+\}|"
    r"\$[A-Za-z_][\w.]*\$|%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs]|"
    r"%%|<[^<>\n]+>|\\[nrt]|\[/?(?:color|size|b|i|url|sprite)(?:[^\]\n]*)\]"
)
NUMBER = re.compile(r"(?<!\w)[+\-−]?\d+(?:[.,]\d+)*(?:[%％])?")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
TIMESTAMP = r"\d{2,}:\d{2}:\d{2},\d{3}"
CUE = re.compile(
    rf"(?m)^(?P<index>\d+)\r?\n(?P<time>{TIMESTAMP} --> {TIMESTAMP}[^\r\n]*)"
    r"\r?\n(?P<body>[^\r\n]+(?:\r?\n(?!\r?$)[^\r\n]+)*)"
)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def digest_text(text):
    return digest_bytes(text.encode("utf-8"))


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def linked(path):
    # Windows junctions as well as ordinary symbolic links must not be followed.
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def confined(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or p.drive or ".." in p.parts or ":" in str(p):
        raise ValueError(f"Expected a safe relative path: {relative}")
    candidate = root / p
    cur = root
    for part in p.parts:
        cur = cur / part
        if cur.exists() and linked(cur):
            raise ValueError(f"Symlink/junction refused: {cur}")
    if not candidate.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes root: {relative}")
    return candidate


def output_path(relative):
    # CLI outputs are restricted even if an agent accidentally supplies a live game path.
    p = confined(PROJECT, relative)
    if not Path(relative).parts or Path(relative).parts[0] not in {"work", "reports", "staging"}:
        raise ValueError("--out must be inside project work/, reports/ or staging/")
    if p.exists():
        raise ValueError(f"Output already exists; choose a new run name: {p}")
    return p


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents replacing checkpoints, reviews, or previous runs.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_catalog(path):
    rows = []
    seen = set()
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for key in ["id", "source_text", "source_sha256", "source_path", "source_file_sha256", "locale", "category", "locator"]:
            if key not in row:
                raise ValueError(f"Catalog line {line_no}: missing {key}")
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in seen:
            raise ValueError(f"Catalog duplicate/invalid id: {row['id']}")
        if not isinstance(row["source_text"], str) or digest_text(row["source_text"]) != row["source_sha256"]:
            raise ValueError(f"Invalid source hash: {row['id']}")
        if not re.fullmatch(r"[0-9a-f]{64}", row["source_file_sha256"]):
            raise ValueError(f"Invalid file hash: {row['id']}")
        confined(PROJECT.parent, row["source_path"])
        seen.add(row["id"])
        rows.append(row)
    if not rows:
        raise ValueError("Empty catalog")
    return rows


def parse_srt(raw):
    text = raw.decode("utf-8-sig", errors="strict")
    cues = []
    previous_end = 0
    seen = set()
    for match in CUE.finditer(text):
        if text[previous_end:match.start()].strip():
            raise ValueError("Unparsed SRT data before cue")
        key = match["index"]
        if key in seen:
            raise ValueError(f"Duplicate SRT cue {key}")
        seen.add(key)
        cues.append({"index": key, "timestamp": match["time"],
                     "text": match["body"].replace("\r\n", "\n"),
                     "start": match.start("body"), "end": match.end("body")})
        previous_end = match.end()
    if text[previous_end:].strip() or not cues:
        raise ValueError("Unparsed/empty SRT data")
    return text, cues


def render_srt(raw, translations):
    text, cues = parse_srt(raw)
    if set(translations) - {c["index"] for c in cues}:
        raise ValueError("Unknown subtitle cue")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    for cue in reversed(cues):
        if cue["index"] in translations:
            target = translations[cue["index"]]
            if "\r" in target or "\n\n" in target or not target.strip():
                raise ValueError("Invalid subtitle body")
            text = text[:cue["start"]] + target.replace("\n", newline) + text[cue["end"]:]
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return bom + text.encode("utf-8")


def walk_files(root):
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not linked(Path(current) / d))
        for name in sorted(files):
            p = Path(current) / name
            if not linked(p):
                yield p


def inventory(game):
    game = Path(game).resolve()
    files = []
    for name in GROUPS:
        folder = confined(game, name)
        if folder.is_dir():
            files.extend(walk_files(folder))
    files.extend(p for p in game.iterdir() if p.is_file() and not linked(p) and p.name != "AGENTS.md")
    records, versions = [], {}
    for p in sorted(files):
        rel = p.relative_to(game).as_posix()
        st = p.stat()
        record = {"path": rel, "size": st.st_size, "mtime_ns": st.st_mtime_ns}
        candidate = p.suffix.lower() in {".arcx", ".arch", ".mani", ".srt"} or p.name in {
            "font.unity3d", "data.unity3d", "game-launcher-config.json", "manifest.json",
            "Hotfix.dll", "GameAssembly.dll", "global-metadata.dat", "StellaSoraBase.dll", "StellaSora.exe"}
        if candidate:
            with p.open("rb") as f:
                head = f.read(96)
            record.update(sha256=digest_file(p), header_hex=head[:32].hex())
            if head.startswith(b"UnityFS\0"):
                record["format"] = "UnityFS"
                record["header_strings"] = [x.decode("ascii") for x in re.findall(rb"[ -~]{4,}", head)][:4]
            elif head.startswith(b"\x1aBAR"):
                record["format"] = "BAR_header_observed_decoder_unimplemented"
            elif head.startswith(b"PK\x03\x04"):
                record["format"] = "ZIP_signature"
            if p.suffix == ".mani":
                headers = {}
                with p.open(encoding="utf-8-sig") as f:
                    for line in f:
                        if line.startswith(("$RES_VER:", "$CLIENT_VER:", "$GAME_VER:")):
                            k, v = line.strip().split(":", 1)
                            headers[k] = v
                versions[rel] = headers
        records.append(record)
    cfg = game / "game-launcher-config.json"
    if cfg.is_file():
        data = read(cfg)
        versions["launcher"] = {k: data.get(k) for k in ("name", "tag", "version")}
    return {"schema": SCHEMA, "created_utc": now(), "game_root": str(game),
            "scope": "metadata of selected game directories and root files; SHA256 of localization candidates only",
            "versions": versions, "file_count": len(records), "total_bytes": sum(r["size"] for r in records),
            "files": records}


def extract_srt(game, source_dir):
    game = Path(game).resolve()
    folder = confined(game, source_dir)
    rows = []
    for p in sorted(folder.glob("*.srt")):
        if linked(p):
            raise ValueError(f"Linked source refused: {p}")
        raw = p.read_bytes()
        _, cues = parse_srt(raw)
        if render_srt(raw, {c["index"]: c["text"] for c in cues}) != raw:
            raise ValueError(f"No-op roundtrip mismatch: {p}")
        rel = p.relative_to(game).as_posix()
        for i, cue in enumerate(cues):
            issues = []
            if "dffd" in cue["text"]:
                issues.append("SOURCE_SUSPECT_DFFD: inspect this source artifact; do not silently delete")
            rows.append({"id": rel + "::" + cue["index"], "source_text": cue["text"],
                         "source_sha256": digest_text(cue["text"]), "source_path": rel,
                         "source_file_sha256": digest_bytes(raw), "locale": "en", "category": "subtitle",
                         "locator": {"adapter": "srt-v1", "cue": cue["index"], "timestamp": cue["timestamp"]},
                         "context": {"previous": cues[i-1]["text"] if i else "",
                                     "next": cues[i+1]["text"] if i+1 < len(cues) else "",
                                     "voice_variant": "JPVA" if "JPVA" in p.name else "CNVA" if "CNVA" in p.name else "unspecified",
                                     "loader_precedence": "unverified; explicit source folder"},
                         "source_issues": issues})
    if not rows:
        raise ValueError(f"No SRT files in {folder}")
    return rows


def tokens(text):
    return TOKEN.findall(text)


def quality(source, target, glossary):
    errors, warnings = [], []
    src = source["source_text"]
    if not isinstance(target, str) or not target.strip():
        return ["EMPTY_TRANSLATION"], []
    if target != unicodedata.normalize("NFC", target):
        errors.append("NON_NFC")
    if any(unicodedata.category(c) == "Cc" and c not in "\n\t" for c in target):
        errors.append("CONTROL_CHARACTER")
    if Counter(tokens(src)) != Counter(tokens(target)):
        errors.append("TOKEN_MISMATCH")
    # Positional placeholders may move; unnumbered printf arguments must keep order.
    src_printf = [t for t in tokens(src) if t.startswith("%") and t != "%%" and not re.match(r"%\d+\$", t)]
    dst_printf = [t for t in tokens(target) if t.startswith("%") and t != "%%" and not re.match(r"%\d+\$", t)]
    if src_printf != dst_printf:
        errors.append("PRINTF_ORDER_MISMATCH")
    src_tags = [x for x in tokens(src) if x.startswith(("<", "["))]
    dst_tags = [x for x in tokens(target) if x.startswith(("<", "["))]
    if src_tags != dst_tags:
        errors.append("TAG_ORDER_MISMATCH")
    if Counter(NUMBER.findall(TOKEN.sub("", src))) != Counter(NUMBER.findall(TOKEN.sub("", target))):
        errors.append("NUMBER_OR_SIGN_MISMATCH")
    if src.count("\n") != target.count("\n"):
        errors.append("LINE_BREAK_MISMATCH")
    if "\n\n" in target:
        errors.append("EMPTY_LINE_IN_TEXT")
    if target.strip() == src.strip():
        warnings.append("UNCHANGED_SOURCE")
    if CJK.search(TOKEN.sub("", target)):
        warnings.append("CJK_REMAINS")
    if len(target) > max(50, len(src) * 1.5):
        warnings.append("LENGTH_EXPANSION")
    if source["category"] == "subtitle":
        if any(len(line) > 48 for line in target.splitlines()):
            warnings.append("SUBTITLE_LINE_OVER_48")
    if source.get("source_issues"):
        warnings.append("SOURCE_ISSUE_REQUIRES_REVIEW")
    for item in glossary.get("entries", []):
        if item.get("status") == "approved" and re.search(r"(?<!\w)" + re.escape(item["source"]) + r"(?!\w)", src, re.I):
            if item["target"] not in target:
                errors.append("GLOSSARY:" + item["source"])
    return errors, warnings


def audit(catalog_path, proposal_path, glossary):
    rows = load_catalog(catalog_path)
    catalog = {r["id"]: r for r in rows}
    proposal = read(proposal_path)
    errors, results = [], []
    if proposal.get("schema") != SCHEMA or proposal.get("kind") != "translation_proposal":
        errors.append("PROPOSAL_SCHEMA")
    if proposal.get("catalog_sha256") != digest_file(catalog_path):
        errors.append("STALE_CATALOG_HASH")
    if not isinstance(proposal.get("translator"), str) or not proposal["translator"].strip():
        errors.append("MISSING_TRANSLATOR")
    entries = proposal.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise ValueError("Proposal entries must be a non-empty list")
    seen = set()
    for item in entries:
        key = item.get("id")
        item_errors, warnings = [], []
        if key in seen:
            item_errors.append("DUPLICATE_ID")
        seen.add(key)
        if key not in catalog:
            item_errors.append("UNKNOWN_ID")
        else:
            source = catalog[key]
            if item.get("source_sha256") != source["source_sha256"]:
                item_errors.append("STALE_SOURCE_HASH")
            if item.get("source") != source:
                item_errors.append("SOURCE_CONTEXT_CHANGED")
            e, warnings = quality(source, item.get("text_vi"), glossary)
            item_errors.extend(e)
        results.append({"id": key, "errors": item_errors, "warnings": warnings})
    errors_count = len(errors) + sum(len(r["errors"]) for r in results)
    return {"schema": SCHEMA, "created_utc": now(), "pass_scope": "static_structure_only",
            "catalog_sha256": digest_file(catalog_path), "proposal_sha256": digest_file(proposal_path),
            "glossary_sha256": digest_text(canonical(glossary)),
            "passed": errors_count == 0, "errors": errors, "error_count": errors_count,
            "warning_count": sum(len(r["warnings"]) for r in results), "rows": results,
            "semantic_review": "not_proven_by_this_tool", "runtime": "not_tested"}


def approved(catalog_path, proposal_path, review_path, glossary):
    result = audit(catalog_path, proposal_path, glossary)
    if not result["passed"]:
        raise ValueError(f"Static audit failed: {result['error_count']} errors")
    proposal, review = read(proposal_path), read(review_path)
    if review.get("schema") != SCHEMA:
        raise ValueError("Unknown review schema")
    if review.get("glossary_sha256") != digest_text(canonical(glossary)):
        raise ValueError("Review glossary hash is stale")
    if review.get("proposal_sha256") != digest_file(proposal_path) or review.get("catalog_sha256") != digest_file(catalog_path):
        raise ValueError("Review is stale or belongs to a different proposal/catalog")
    reviewer = review.get("reviewer", "")
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer.strip().casefold() == proposal["translator"].strip().casefold():
        raise ValueError("A distinct named reviewer is required")
    if review.get("independent") is not True:
        raise ValueError("Independent review declaration is missing")
    decisions = review.get("decisions", [])
    ids = [d["id"] for d in decisions]
    expected = {e["id"] for e in proposal["entries"]}
    if len(ids) != len(set(ids)) or set(ids) != expected:
        raise ValueError("Review must cover exactly the proposal IDs, with no duplicates")
    warnings = {row["id"]: set(row["warnings"]) for row in result["rows"]}
    for d in decisions:
        if d.get("status") != "approved" or any(not isinstance(d.get(k), str) or not d[k].strip() for k in ("rationale", "evidence")):
            raise ValueError(f"Incomplete semantic decision: {d['id']}")
        if not warnings[d["id"]].issubset(set(d.get("warnings_ack", []))):
            raise ValueError(f"Unresolved warning: {d['id']}")
    return proposal, review, result


def build_srt(game, catalog_path, proposal_path, review_path, glossary, out):
    proposal, review, audit_result = approved(catalog_path, proposal_path, review_path, glossary)
    rows = load_catalog(catalog_path)
    by_id = {r["id"]: r for r in rows}
    targets = {e["id"]: e["text_vi"] for e in proposal["entries"]}
    paths = {by_id[key]["source_path"] for key in targets}
    prepared, files = [], []
    for rel in sorted(paths):
        records = [r for r in rows if r["source_path"] == rel]
        if any(r["id"] not in targets for r in records):
            raise ValueError(f"Partial subtitle file refused; translate/review every cue: {rel}")
        if any(r["locator"].get("adapter") != "srt-v1" for r in records):
            raise ValueError("This builder only supports srt-v1")
        raw = confined(game, rel).read_bytes()
        if any(r["source_file_sha256"] != digest_bytes(raw) for r in records):
            raise ValueError(f"Source file changed since extraction: {rel}")
        _, original_cues = parse_srt(raw)
        native = {c["index"]: c for c in original_cues}
        if len(records) != len(native) or {r["locator"]["cue"] for r in records} != set(native):
            raise ValueError("Catalog does not cover all native cues exactly")
        for row in records:
            cue = native[row["locator"]["cue"]]
            if row["source_text"] != cue["text"] or row["locator"]["timestamp"] != cue["timestamp"]:
                raise ValueError("Catalog/source cue mismatch")
        if render_srt(raw, {c["index"]: c["text"] for c in original_cues}) != raw:
            raise ValueError("No-op roundtrip failed")
        translated = {r["locator"]["cue"]: targets[r["id"]] for r in records}
        candidate = render_srt(raw, translated)
        _, actual = parse_srt(candidate)
        if [(c["index"], c["timestamp"]) for c in actual] != [(c["index"], c["timestamp"]) for c in original_cues]:
            raise ValueError("Readback cue/timing mismatch")
        if {c["index"]: c["text"] for c in actual} != translated:
            raise ValueError("Readback text mismatch")
        prepared.append((rel, candidate))
        files.append({"source_path": rel, "source_sha256": digest_bytes(raw),
                      "candidate_sha256": digest_bytes(candidate), "cues": len(actual)})
    if out.exists():
        raise ValueError("Staging destination exists")
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".stage-", dir=out.parent))
    try:
        for rel, data in prepared:
            destination = confined(temporary, "files/" + rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            if digest_file(destination) != digest_bytes(data):
                raise ValueError("Staged disk readback mismatch")
        save(temporary / "manifest.json", {"schema": SCHEMA, "created_utc": now(), "kind": "srt_staging_only",
             "catalog_sha256": digest_file(catalog_path), "proposal_sha256": digest_file(proposal_path),
             "review_sha256": digest_file(review_path), "files": files, "static_audit": audit_result,
             "installed": False, "runtime": "not_tested", "loader_precedence": "unverified"})
        temporary.rename(out)
    finally:
        # Only this function's newly created staging directory may be removed.
        if temporary.exists() and temporary.parent.resolve() == out.parent.resolve() and temporary.name.startswith(".stage-"):
            shutil.rmtree(temporary)
    return len(files)


def diff_catalogs(old_path, new_path):
    old = {r["id"]: r for r in load_catalog(old_path)}
    new = {r["id"]: r for r in load_catalog(new_path)}
    result = {"added": sorted(new.keys() - old.keys()), "removed": sorted(old.keys() - new.keys()),
              "text_changed": [], "context_or_file_changed": [], "unchanged": []}
    for key in sorted(old.keys() & new.keys()):
        if old[key]["source_sha256"] != new[key]["source_sha256"]:
            result["text_changed"].append(key)
        elif old[key] != new[key]:
            result["context_or_file_changed"].append(key)
        else:
            result["unchanged"].append(key)
    return {"schema": SCHEMA, "old_sha256": digest_file(old_path), "new_sha256": digest_file(new_path),
            "counts": {k: len(v) for k, v in result.items()}, "ids": result,
            "policy": "No automatic reuse; changed text/context/provenance requires rebasing and review"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    for name in ["inventory", "extract-srt"]:
        p = sub.add_parser(name)
        p.add_argument("--game-root", type=Path, default=PROJECT.parent)
        p.add_argument("--out", required=True)
        if name == "extract-srt":
            p.add_argument("--source-dir", default="Persistent_Store/Videos")
    p = sub.add_parser("batch")
    p.add_argument("--catalog", required=True, type=Path)
    p.add_argument("--batch-id", required=True)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--source-file", help="Exact source_path; use to select a complete SRT file")
    p.add_argument("--out", required=True)
    for name in ["audit", "review-template", "merge", "build-srt"]:
        p = sub.add_parser(name)
        p.add_argument("--catalog", required=True, type=Path)
        p.add_argument("--proposal", required=True, type=Path)
        p.add_argument("--glossary", type=Path, default=PROJECT / "config/glossary.json")
        p.add_argument("--out", required=True)
        if name in {"merge", "build-srt"}:
            p.add_argument("--review", required=True, type=Path)
        if name == "build-srt":
            p.add_argument("--game-root", type=Path, default=PROJECT.parent)
    p = sub.add_parser("diff-sources")
    p.add_argument("--old", required=True, type=Path)
    p.add_argument("--new", required=True, type=Path)
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        print(json.dumps({"python": sys.version.split()[0], "project": str(PROJECT),
                          "game_root_exists": PROJECT.parent.is_dir(), "dependencies": "stdlib only",
                          "srt_adapter": "implemented", "arcx_adapter": "unimplemented",
                          "unity_asset_adapter": "unimplemented", "live_installer": "not_provided"}, indent=2))
        return 0
    out = output_path(args.out)
    if args.command == "inventory":
        result = inventory(args.game_root)
        save(out, result)
        print(f"Inventory: {result['file_count']} files; {out}")
    elif args.command == "extract-srt":
        rows = extract_srt(args.game_root, args.source_dir)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.writelines(canonical(r) + "\n" for r in rows)
        print(f"Extracted {len(rows)} subtitle cues: {out}")
    elif args.command == "batch":
        rows = load_catalog(args.catalog)
        if args.offset < 0 or args.limit < 1 or args.limit > 200:
            raise ValueError("offset >= 0; limit must be 1..200")
        if args.source_file:
            rows = [r for r in rows if r["source_path"] == args.source_file]
        rows = rows[args.offset:args.offset + args.limit]
        if not rows:
            raise ValueError("Empty batch selection")
        save(out, {"schema": SCHEMA, "kind": "translation_proposal", "batch_id": args.batch_id,
                   "catalog_sha256": digest_file(args.catalog), "translator": "",
                   "entries": [{"id": r["id"], "source_sha256": r["source_sha256"],
                                "source": r, "text_vi": "", "notes": ""} for r in rows]})
        print(f"Prepared {len(rows)} untranslated entries: {out}")
    elif args.command in {"audit", "review-template", "merge", "build-srt"}:
        glossary = read(args.glossary)
        if args.command == "audit":
            result = audit(args.catalog, args.proposal, glossary)
            save(out, result)
            print(f"Static audit: {result['error_count']} errors, {result['warning_count']} warnings; {out}")
            return 0 if result["passed"] else 2
        if args.command == "review-template":
            result = audit(args.catalog, args.proposal, glossary)
            if not result["passed"]:
                raise ValueError("Fix static errors before preparing semantic review")
            save(out, {"schema": SCHEMA, "catalog_sha256": digest_file(args.catalog),
                       "proposal_sha256": digest_file(args.proposal), "glossary_sha256": digest_text(canonical(glossary)),
                       "reviewer": "", "independent": False,
                       "decisions": [{"id": r["id"], "status": "pending", "rationale": "", "evidence": "",
                                      "warnings_to_review": r["warnings"], "warnings_ack": []} for r in result["rows"]]})
            print(f"Pending review template: {out}")
        elif args.command == "merge":
            proposal, review, result = approved(args.catalog, args.proposal, args.review, glossary)
            save(out, {"schema": SCHEMA, "kind": "reviewed_batch", "created_utc": now(),
                       "catalog_sha256": digest_file(args.catalog), "proposal_sha256": digest_file(args.proposal),
                       "review_sha256": digest_file(args.review), "batch_id": proposal["batch_id"],
                       "entries": [{"id": e["id"], "source_sha256": e["source_sha256"], "text_vi": e["text_vi"]}
                                   for e in proposal["entries"]], "scope": "this batch only", "installed": False})
            print(f"Recorded reviewed batch (catalog not overwritten): {out}")
        else:
            count = build_srt(args.game_root, args.catalog, args.proposal, args.review, glossary, out)
            print(f"Staged {count} SRT files with readback; not installed: {out}")
    else:
        save(out, diff_catalogs(args.old, args.new))
        print(f"Source diff: {out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
