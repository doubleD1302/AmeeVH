"""Offline change detection and verified Sheet request generation. No network I/O."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import uuid4

RESOURCE = "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03"
SPREADSHEET = "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM"
HEADERS = ["file_id", "block_order", "kind", "speaker_en", "speaker_jp", "speaker_cn",
           "speaker_vi", "text_vi", "text_cn", "text_jp", "text_en", "source_refs_json"]
HEADER = re.compile(r"^([1-9]\d*)\. \[(.*)\](?: \(([^\n]+)\))?\n", re.M)
REPORT = re.compile(r'<script id="report-data" type="application/json">(.*?)</script>', re.S)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if Path(name).exists():
            Path(name).unlink()


def home(root):
    return Path(root) / ".ss-sync/update-sheet"


def relative(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve()
    require(path.is_relative_to(root / RESOURCE), "Path must stay in the resource tree")
    return path.relative_to(root).as_posix()


def group(key):
    parts = Path(key).parts
    require(parts[0] == RESOURCE and parts[-1].endswith("_Merge.txt"), "Not a Merge path")
    p = parts[1:]
    if len(p) >= 4 and p[0] == "01_CotTruyen" and p[1] in ("01_Chinh", "02_SuKien"):
        return p[2]
    if len(p) >= 3 and p[0] == "01_CotTruyen" and p[1] not in ("01_Chinh", "02_SuKien"):
        return p[1]
    if len(p) >= 3 and p[0] == "02_NhanVat":
        return p[1]
    if len(p) >= 2 and p[0] in ("03_BangText_UI_KyNang", "04_PhuDeVideo", "90_CN_Moi_2.0.1"):
        return p[0]
    raise ValueError("Unsupported source group")


def file_id(key):
    return Path(key).name.removesuffix("_Merge.txt")


def metadata(path):
    s = Path(path).stat()
    return {"size": s.st_size, "mtime_ns": s.st_mtime_ns, "ctime_ns": s.st_ctime_ns,
            "device": s.st_dev, "inode": s.st_ino}


def snapshot(path):
    before = metadata(path)
    data = Path(path).read_bytes()
    require(before == metadata(path), "Merge changed while reading; retry later")
    return data, before


def load_state(root):
    path = home(root) / "state.json"
    if path.exists():
        state = read_json(path)
        require(state.get("schema_version") == 1 and state.get("spreadsheet_id") == SPREADSHEET,
                "Unexpected sync state schema or spreadsheet")
        return state
    state = {"schema_version": 1, "spreadsheet_id": SPREADSHEET, "files": {}}
    for manifest in sorted((Path(root) / ".ss-sync").glob("*/partition_manifest.json")):
        m = read_json(manifest)
        if m.get("spreadsheet_id") != SPREADSHEET or m.get("headers") != HEADERS:
            continue
        for f in m["files"]:
            verification = m.get("verification", {})
            if not verification.get("matched") and verification.get("verified_files", {}).get(f["file_id"]) != f["source_sha256"]:
                continue
            key = relative(root, f["merge_path"])
            require(group(key) == m["sheet_name"] and file_id(key) == f["file_id"], "Invalid imported mapping")
            require(key not in state["files"], "Duplicate imported path")
            state["files"][key] = {"sheet_name": m["sheet_name"], "file_id": f["file_id"],
                                    "published_sha256": f["source_sha256"], "blocks": f["blocks"],
                                    "imported_manifest": manifest.relative_to(root).as_posix()}
    return state


def begin(root):
    base = home(root)
    base.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    with (base / "run.json").open("x", encoding="utf-8") as stream:
        json.dump({"token": token, "started_at": stamp(), "purpose": "update-sheet"}, stream)
    return {"run": token}


@contextmanager
def locked(root, token):
    require(read_json(home(root) / "run.json").get("token") == token, "Wrong sync run token")
    guard = home(root) / "command.lock"
    fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.close(fd)
        yield
    finally:
        guard.unlink()


def scan(root, scopes=(), rehash=False, save=False):
    root = Path(root).resolve()
    state = load_state(root)
    scopes = [relative(root, s) for s in scopes]
    selected = lambda key: not scopes or any(key == s or key.startswith(s.rstrip("/") + "/") for s in scopes)
    inventory = {}
    for category in ("01_CotTruyen", "02_NhanVat", "03_BangText_UI_KyNang", "04_PhuDeVideo", "90_CN_Moi_2.0.1"):
        for path in (root / RESOURCE / category).rglob("*_Merge.txt"):
            key = relative(root, path)
            try:
                inventory[key] = {"sheet_name": group(key), "file_id": file_id(key), "stat": metadata(path)}
            except ValueError:
                continue
    ids = {}
    for key, info in inventory.items():
        ids.setdefault(info["file_id"], []).append(key)
    result = {"new": [], "changed": [], "unchanged": [], "metadata_only": [], "blocked": [], "missing": []}
    for key, info in sorted(inventory.items()):
        if not selected(key):
            continue
        entry = state["files"].get(key, {})
        other = [p for p, e in state["files"].items() if p != key and e.get("file_id") == info["file_id"]]
        if len(ids[info["file_id"]]) > 1 or other:
            result["blocked"].append({"path": key, "reason": "Duplicate/moved file_id; reconcile mappings", "other_paths": other or ids[info["file_id"]]})
            continue
        if entry and entry["sheet_name"] != info["sheet_name"]:
            result["blocked"].append({"path": key, "reason": "Sheet mapping changed"})
            continue
        if not rehash and entry.get("observed_stat") == info["stat"] and entry.get("observed_sha256") == entry.get("published_sha256") and not entry.get("pending"):
            result["unchanged"].append(key)
            continue
        try:
            data, stat = snapshot(root / key)
        except (OSError, ValueError) as exc:
            result["blocked"].append({"path": key, "reason": str(exc)})
            continue
        digest = sha(data)
        entry.update(sheet_name=info["sheet_name"], file_id=info["file_id"], observed_stat=stat, observed_sha256=digest)
        state["files"][key] = entry
        if digest == entry.get("published_sha256") and not entry.get("pending"):
            result["metadata_only"].append(key)
        else:
            result["changed" if entry.get("published_sha256") else "new"].append(key)
    for key in sorted(state["files"]):
        if selected(key) and key not in inventory:
            result["missing"].append(key)
    if save:
        atomic(home(root) / "state.json", state)
    return result


def blocks(data):
    require(data.startswith(b"\xef\xbb\xbf"), "Merge must use UTF-8 BOM")
    require(b"\n" not in data.replace(b"\r\n", b""), "Merge must use CRLF")
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    matches = list(HEADER.finditer(text))
    require(matches and matches[0].start() == 0, "Expected numbered Merge blocks")
    out = []
    for i, m in enumerate(matches):
        require(int(m[1]) == i + 1, "Noncontinuous block_order")
        body = text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        if i + 1 < len(matches):
            require(body.endswith("\n\n"), "Missing blank block separator")
            body = body[:-2]
        elif body.endswith("\n"):
            body = body[:-1]
        out.append({"header": m[0].rstrip("\n"), "label": m[2], "kind": m[3] or "", "body": body})
    return out


def refs(code):
    if code.startswith("EN:"):
        m = re.fullmatch(r"EN: (.+)/JP: (.+)/CN: (.+)", code)
        require(m is not None, "Invalid language-specific static codes")
        return dict(zip(("EN", "JP", "CN"), m.groups()))
    require(bool(code.strip()), "Missing static source code")
    return {lang: code for lang in ("EN", "JP", "CN")}


def report_export(root, key, digest, parsed):
    stores = []
    indexes = []
    for name in ("conflicts", "references"):
        path = Path(root) / f"reports/translation-{name}.html"
        require(path.exists(), "Need --structured export: no matching translation reports")
        m = REPORT.search(path.read_text(encoding="utf-8-sig"))
        require(m is not None, "Invalid translation report")
        store = json.loads(m[1])
        info = store.get("files", {}).get(key, {})
        require(info.get("merge_sha256") == digest and info.get("total_blocks") == len(parsed),
                "Need --structured export: reports do not match current Merge")
        stores.append(info)
        index = {}
        for entry in info.get("entries", {}).values():
            index.setdefault(entry.get("block_order"), []).append(entry)
        indexes.append(index)
    result = []
    for i, block in enumerate(parsed, 1):
        require(all(str(i) in s.get("coverage", {}) for s in stores), "Translation report coverage incomplete")
        exports = []
        for index in indexes:
            candidates = []
            for entry in index.get(i, []):
                if entry.get("block_order") != i or entry.get("header") != block["header"].split(". ", 1)[1]:
                    continue
                source = entry.get("source", {})
                vi = entry.get("current_text_vi", entry.get("text_vi"))
                if set(source) == {"CN", "JP", "EN"} and isinstance(vi, str) and "\n".join([source[l] for l in ("CN", "JP", "EN")] + [vi]) == block["body"]:
                    candidates.append({"block_order": i, "header": block["header"], "source": source, "text_vi": vi})
            unique = {compact(c): c for c in candidates}
            require(len(unique) == 1, "Need --structured export: missing/ambiguous report block")
            exports.append(next(iter(unique.values())))
        require(exports[0] == exports[1], "Translation reports disagree")
        result.append(exports[0])
    return {"merge_sha256": digest, "blocks": result}


def prepare(root, key, structured=None):
    root = Path(root).resolve()
    key = relative(root, key)
    title = group(key)
    data, stat = snapshot(root / key)
    digest = sha(data)
    parsed = blocks(data)
    export = structured if structured is not None else report_export(root, key, digest, parsed)
    require(export.get("merge_sha256") == digest, "Structured export has stale Merge hash")
    require(len(export.get("blocks", [])) == len(parsed), "Export must cover every block")
    rows = []
    for i, (block, item) in enumerate(zip(parsed, export["blocks"]), 1):
        require(item.get("block_order") == i and item.get("header") == block["header"], "Export header/order mismatch")
        source = item.get("source", {})
        vi = item.get("text_vi")
        require(set(source) == {"CN", "JP", "EN"} and all(isinstance(v, str) for v in source.values()), "Export needs CN/JP/EN strings")
        require(isinstance(vi, str) and bool(vi.strip()), "File is not fully translated")
        require("\n".join([source[l] for l in ("CN", "JP", "EN")] + [vi]) == block["body"], "Export does not reconstruct Merge body")
        if block["kind"]:
            names = item.get("speakers")
            if names is None:
                names = block["label"].split("/ ")
                require(len(names) in (1, 4), "Need explicit VI/EN/JP/CN speakers for ambiguous header")
                names = [s.strip() for s in names]
                if len(names) == 1:
                    names += ["", "", ""]
            else:
                require(isinstance(names, list) and len(names) == 4 and all(isinstance(s, str) for s in names), "Invalid explicit speakers")
                require("/ ".join(names) == block["label"] or (names[0] == block["label"] and names[1:] == ["", "", ""]), "Speakers do not reconstruct header")
            speakers = [names[1], names[2], names[3], names[0]]
            references = ""
        else:
            speakers = ["", "", "", ""]
            references = json.dumps(refs(block["label"]), ensure_ascii=False, separators=(",", ":"))
        rows.append([file_id(key), i, block["kind"], *speakers, vi, source["CN"], source["JP"], source["EN"], references])
    return {"spreadsheet_id": SPREADSHEET, "path": key, "sheet_name": title, "file_id": file_id(key),
            "merge_sha256": digest, "stat": stat, "headers": HEADERS, "rows": rows}


def validate_remote(remote, payload):
    require(remote.get("spreadsheet_id") == SPREADSHEET, "Wrong remote spreadsheet")
    require(remote.get("title") == payload["sheet_name"], "Wrong remote sheet")
    require(type(remote.get("sheet_id")) is int and 0 <= remote["sheet_id"] < 2**31, "Invalid sheet_id")
    if not remote.get("exists", True):
        require(not remote.get("keys") and not remote.get("rows"), "New sheet must be empty")
        return
    require(remote.get("headers") == HEADERS and remote.get("column_count") == 12, "Remote header/grid schema mismatch")
    keys = remote["keys"]
    require(all(isinstance(k, list) and len(k) == 2 and isinstance(k[0], str) and k[0] and type(k[1]) is int and k[1] > 0 for k in keys), "Invalid/gapped remote keys")
    require(len({tuple(k) for k in keys}) == len(keys), "Duplicate remote block key")
    require(remote["row_count"] >= len(keys) + 1, "Keys exceed grid")
    selected = [i for i, k in enumerate(keys) if k[0] == payload["file_id"]]
    require(not selected or selected == list(range(selected[0], selected[-1] + 1)), "File rows are not contiguous")
    current = remote.get("rows", [])
    require(len(current) == len(selected) and all(len(r) == 12 for r in current), "Need complete selected file rows")
    require([r[:2] for r in current] == [keys[i] for i in selected], "Rows and keys disagree")
    table = remote.get("table")
    if table:
        require(table.get("headers") == HEADERS and table.get("sheet_id") == remote["sheet_id"] and table.get("start_row", 0) == 0 and table.get("start_column", 0) == 0 and table.get("end_column") == 12 and table.get("end_row", 0) >= len(keys) + 1, "Remote table does not cover the data/schema")
        require(table.get("block_order_type") == "DOUBLE", "Remote block_order table type must be DOUBLE")


def cell(value):
    return {"userEnteredValue": {"numberValue": value} if type(value) is int else {"stringValue": value}}


def build(root, token, payload, remote):
    current = prepare_from_payload(root, payload)
    validate_remote(remote, current)
    title, sid, fid = current["sheet_name"], remote["sheet_id"], current["file_id"]
    require(title not in ("DB_Proposals", "DB_Scenes", "DB_Blocks", "DB_Control"), "Reserved sheet")
    keys = remote.get("keys", [])
    selected = [i for i, k in enumerate(keys) if k[0] == fid]
    first = selected[0] if selected else len(keys)
    count = len(selected)
    rows = current["rows"]
    expected_keys = keys[:first] + [r[:2] for r in rows] + keys[first + count:]
    requests = []
    existing = remote.get("exists", True)
    grid = remote.get("row_count", 0)
    if not existing:
        grid = max(2, len(rows) + 1)
        requests.append({"addSheet": {"properties": {"sheetId": sid, "title": title, "gridProperties": {"rowCount": grid, "columnCount": 12, "frozenRowCount": 1, "frozenColumnCount": 2}}}})
        requests.append({"updateCells": {"start": {"sheetId": sid, "rowIndex": 0, "columnIndex": 0}, "rows": [{"values": [cell(v) for v in HEADERS]}], "fields": "userEnteredValue"}})
    elif remote["rows"] != rows:
        delta = len(rows) - count
        index = first + 1 + min(count, len(rows))
        if delta < 0:
            requests.append({"deleteDimension": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": index, "endIndex": index - delta}}})
            grid += delta
        while delta > 0:
            if index == grid:
                requests.append({"appendDimension": {"sheetId": sid, "dimension": "ROWS", "length": delta}})
                grid += delta
                delta = 0
            else:
                step = min(delta, grid - index)
                requests.append({"insertDimension": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": index, "endIndex": index + step}, "inheritFromBefore": True}})
                grid += step
                delta -= step
    changed = not existing or remote.get("rows") != rows
    if changed:
        requests.append({"updateCells": {"start": {"sheetId": sid, "rowIndex": first + 1, "columnIndex": 0}, "rows": [{"values": [cell(v) for v in r]} for r in rows], "fields": "userEnteredValue"}})
        requests.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": first + 1, "endRowIndex": first + 1 + len(rows), "startColumnIndex": 0, "endColumnIndex": 12}, "cell": {"userEnteredFormat": {"verticalAlignment": "TOP", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat.verticalAlignment,userEnteredFormat.wrapStrategy"}})
    table_range = {"sheetId": sid, "startRowIndex": 0, "endRowIndex": len(expected_keys) + 1, "startColumnIndex": 0, "endColumnIndex": 12}
    table = remote.get("table")
    if table:
        if table["end_row"] != table_range["endRowIndex"]:
            requests.append({"updateTable": {"table": {"tableId": str(table["table_id"]), "range": table_range}, "fields": "range"}})
    else:
        requests.append({"addTable": {"table": {"name": f"SS_Data_{sid}", "range": table_range, "columnProperties": [{"columnIndex": i, "columnName": name, "columnType": "DOUBLE" if i == 1 else "TEXT"} for i, name in enumerate(HEADERS)], "rowsProperties": {"headerColorStyle": {"rgbColor": {"red": .92941177, "green": .9372549, "blue": .9490196}}, "firstBandColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}, "secondBandColorStyle": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}}})
    if not existing:
        for a, b, width in ((0, 1, 160), (1, 2, 110), (2, 3, 120), (3, 7, 160), (7, 11, 430), (11, 12, 220)):
            requests.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": a, "endIndex": b}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})
        requests.append({"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 12}, "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "textFormat": {"bold": True}}}, "fields": "userEnteredFormat"}})
    if changed:
        requests.append({"autoResizeDimensions": {"dimensions": {"sheetId": sid, "dimension": "ROWS", "startIndex": first + 1, "endIndex": first + 1 + len(rows)}}})
    plan = {"run": token, "payload": current, "sheet_id": sid, "expected_keys": expected_keys,
            "write_start_row": first + 1, "grid_rows": grid, "requests": requests}
    plan["plan_sha256"] = sha(compact(plan).encode("utf-8"))
    state = load_state(root)
    entry = state["files"].setdefault(current["path"], {"sheet_name": title, "file_id": fid})
    entry["pending"] = {"run": token, "plan_sha256": plan["plan_sha256"], "merge_sha256": current["merge_sha256"]}
    atomic(home(root) / "state.json", state)
    return plan


def prepare_from_payload(root, payload):
    rows = payload["rows"]
    key = relative(root, payload["path"])
    data, stat = snapshot(Path(root) / key)
    require(sha(data) == payload["merge_sha256"] and stat == payload["stat"], "Payload is stale")
    parsed = blocks(data)
    require(len(rows) == len(parsed), "Payload block count mismatch")
    structured = {"merge_sha256": payload["merge_sha256"], "blocks": []}
    for i, (r, b) in enumerate(zip(rows, parsed), 1):
        require(len(r) == 12 and r[0] == file_id(key) and type(r[1]) is int and r[1] == i, "Invalid payload rows")
        item = {"block_order": i, "header": b["header"], "source": dict(zip(("CN", "JP", "EN"), r[8:11])), "text_vi": r[7]}
        if b["kind"]:
            item["speakers"] = [r[6], r[3], r[4], r[5]]
        structured["blocks"].append(item)
    checked = prepare(root, key, structured)
    require(payload == checked, "Payload schema or values were changed")
    return checked


def confirm(root, token, plan, remote):
    signed = dict(plan)
    digest = signed.pop("plan_sha256")
    require(digest == sha(compact(signed).encode("utf-8")) and plan["run"] == token, "Invalid plan")
    p = prepare_from_payload(root, plan["payload"])
    validate_remote(remote, p)
    require(remote.get("exists", True) and remote["sheet_id"] == plan["sheet_id"], "Readback sheet mismatch")
    require(remote["keys"] == plan["expected_keys"] and remote["rows"] == p["rows"], "Readback differs from expected data")
    table = remote.get("table")
    require(table and table["end_row"] == len(plan["expected_keys"]) + 1 and table.get("block_order_type") == "DOUBLE", "Readback table/range/type mismatch")
    state = load_state(root)
    entry = state["files"].get(p["path"], {})
    require(entry.get("pending", {}).get("plan_sha256") == digest, "Plan is not the pending write")
    # A recovery receipt is persisted before the two local files are replaced.
    receipt = {"confirmed_at": stamp(), "path": p["path"], "file_id": p["file_id"],
               "merge_sha256": p["merge_sha256"], "stat": p["stat"], "blocks": len(p["rows"]),
               "sheet_name": p["sheet_name"], "sheet_id": remote["sheet_id"], "table_id": str(table["table_id"])}
    atomic(home(root) / "receipts" / (digest + ".json"), receipt)
    entry.update(sheet_name=p["sheet_name"], file_id=p["file_id"], published_sha256=p["merge_sha256"],
                 observed_sha256=p["merge_sha256"], observed_stat=p["stat"], blocks=len(p["rows"]),
                 verified_at=receipt["confirmed_at"], payload_sha256=sha(compact(p["rows"]).encode("utf-8")))
    entry.pop("pending", None)
    state["files"][p["path"]] = entry
    mp = Path(root) / ".ss-sync" / p["sheet_name"] / "partition_manifest.json"
    manifest = read_json(mp) if mp.exists() else {}
    require(not manifest or (manifest.get("spreadsheet_id") == SPREADSHEET and manifest.get("sheet_name") == p["sheet_name"] and manifest.get("headers") == HEADERS), "Manifest conflicts with destination")
    files = {f["file_id"]: f for f in manifest.get("files", [])}
    verified_files = dict(manifest.get("verification", {}).get("verified_files", {}))
    if manifest.get("verification", {}).get("matched"):
        verified_files.update({f["file_id"]: f["source_sha256"] for f in files.values()})
    verified_files[p["file_id"]] = p["merge_sha256"]
    types = {"story" if r[2] else "static" for r in p["rows"]}
    content_type = next(iter(types)) if len(types) == 1 else "mixed"
    files[p["file_id"]] = {"file_id": p["file_id"], "merge_path": p["path"], "source_sha256": p["merge_sha256"], "blocks": len(p["rows"]), "content_type": content_type}
    all_types = {f.get("content_type", manifest.get("content_type", content_type)) for f in files.values()}
    manifest.update(schema_version=3, spreadsheet_id=SPREADSHEET, spreadsheet_url=f"https://docs.google.com/spreadsheets/d/{SPREADSHEET}/edit",
                    sheet_name=p["sheet_name"], sheet_id=remote["sheet_id"], table_id=str(table["table_id"]),
                    content_type=next(iter(all_types)) if len(all_types) == 1 else "mixed", headers=HEADERS, identity=["file_id", "block_order"], files=sorted(files.values(), key=lambda f: f["file_id"]))
    # Per-file readback is not evidence that every other file has been rechecked.
    manifest["verification"] = {"matched": False, "scope": "per_file", "last_verified_file": p["file_id"],
                                "verified_files": verified_files,
                                "last_verified_sha256": p["merge_sha256"], "last_verified_at": receipt["confirmed_at"],
                                "data_rows": len(remote["keys"]), "columns": 12, "verified_cells": len(p["rows"]) * 12}
    atomic(mp, manifest)
    atomic(home(root) / "state.json", state)
    return {"confirmed": p["path"], "blocks": len(p["rows"]), "receipt": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("begin")
    for name in ("scan", "prepare", "build", "confirm", "finish"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--run", required=name != "scan")
        if name != "finish":
            cmd.add_argument("--output", type=Path)
        if name == "scan":
            cmd.add_argument("--scope", action="append", default=[])
            cmd.add_argument("--rehash", action="store_true")
            cmd.add_argument("--dry-run", action="store_true")
        if name == "prepare":
            cmd.add_argument("--path", required=True)
            cmd.add_argument("--structured", type=Path)
        if name in ("build", "confirm"):
            cmd.add_argument("--remote", required=True, type=Path)
            cmd.add_argument("--payload" if name == "build" else "--plan", required=True, type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    require((root / RESOURCE).is_dir(), "Resource root not found")
    if args.command == "begin":
        result = begin(root)
    elif args.command == "scan" and args.dry_run:
        result = scan(root, args.scope, args.rehash)
    else:
        require(args.run, "Mutating commands require --run; use scan --dry-run for read-only discovery")
        with locked(root, args.run):
            if args.command == "scan":
                result = scan(root, args.scope, args.rehash, save=True)
            elif args.command == "prepare":
                result = prepare(root, args.path, read_json(args.structured) if args.structured else None)
            elif args.command == "build":
                result = build(root, args.run, read_json(args.payload), read_json(args.remote))
            elif args.command == "confirm":
                result = confirm(root, args.run, read_json(args.plan), read_json(args.remote))
            else:
                (home(root) / "run.json").unlink()
                result = {"finished": args.run}
    if getattr(args, "output", None):
        atomic(args.output, result)
        print(compact({"output": str(args.output)}))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(compact({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
