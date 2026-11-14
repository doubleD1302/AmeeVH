"""Update two offline HTML reports from a saved story or static UI Merge.

The helper verifies snapshots and organizes findings; it does not translate or
infer conflicts/references. See references/reports.md for the JSON contract.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

RESOURCE = "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03"
REPORT_NAMES = {k: f"translation-{k}.html" for k in ("conflicts", "references")}
DATA_RE = re.compile(r'<script id="report-data" type="application/json">(.*?)</script>', re.S)
HEADER_RE = re.compile(r"^([1-9]\d*)\. (\[(.+)\](?: \((.+)\))?)\n", re.M)
STATUSES = {"active", "absent", "needs_review", "clear"}
LANGS = {"EN", "JP", "CN"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def now():
    return datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")


def norm(value):
    return value.replace("\r\n", "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def path_key(value):
    require(isinstance(value, str) and "\\" not in value, "merge_path must be a project-relative POSIX path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts and len(path.parts) >= 2, "Invalid merge_path")
    require(path.parts[0] == RESOURCE and value == path.as_posix() and path.name.endswith("_Merge.txt"), "Merge must be inside the resource tree")
    return value


def source_dict(value):
    require(isinstance(value, dict) and set(value) == LANGS and all(isinstance(v, str) for v in value.values()), "source requires EN, JP, CN strings")
    return {lang: norm(value[lang]) for lang in ("CN", "JP", "EN")}


def parse_merge(data):
    text = norm(data.decode("utf-8-sig"))
    matches = list(HEADER_RE.finditer(text))
    require(matches and not text[:matches[0].start()].strip(), "Expected numbered story or static UI Merge")
    result = {}
    for i, match in enumerate(matches):
        order = int(match[1])
        require(order == i + 1, "Merge numbering is not continuous")
        body = text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        if i + 1 < len(matches):
            require(body.endswith("\n\n"), "Missing blank separator between Merge blocks")
            body = body[:-2]
        elif body.endswith("\n"):
            body = body[:-1]
        is_story = match[4] is not None
        code = "" if is_story else match[3]
        result[order] = {"header": match[2], "kind": match[4] or "", "body": body,
                         "ui_type": "story" if is_story else "static", "source_code": code,
                         "source_refs": {} if is_story else static_refs(code),
                         "body_sha256": fingerprint([match[2], body])}
    return result


def static_refs(code):
    """Keep slash characters inside IDs; only language labels separate IDs."""
    require(bool(code.strip()), "Static header requires a source code")
    if code.startswith("EN:"):
        match = re.fullmatch(r"EN: (.+)/JP: (.+)/CN: (.+)", code)
        require(match is not None, "Static language-specific header needs EN/JP/CN codes")
        return dict(zip(("EN", "JP", "CN"), match.groups()))
    return {language: code for language in ("EN", "JP", "CN")}


def validate_findings(findings, kind):
    require(isinstance(findings, list), f"{kind} must be an array, including [] for no findings")
    identities = set()
    for item in findings:
        require(isinstance(item, dict), "Finding must be an object")
        for field in ("title", "detail", "handling"):
            require(isinstance(item.get(field), str) and item[field].strip(), f"Finding needs {field}")
        languages = item.get("languages")
        require(isinstance(languages, list) and languages and all(x in LANGS for x in languages), "Finding languages must contain EN/JP/CN")
        if "id" in item:
            require(isinstance(item["id"], str) and item["id"].strip(), "Finding id must be nonempty")
        identity = finding_key(item)
        require(identity not in identities, "Duplicate finding identity in a block")
        identities.add(identity)
        require(item.get("status", "active") in ("active", "absent"), "Invalid finding status")
        if "previous_context" in item:
            require(isinstance(item["previous_context"], dict) and isinstance(item["previous_context"].get("text_vi"), str), "Invalid finding history")
            source_dict(item["previous_context"].get("source"))
        if kind == "conflicts":
            require(isinstance(item.get("basis"), str) and item["basis"].strip(), "Conflict needs the basis for VI handling")
        else:
            require(item.get("confidence") in ("verified", "suspected"), "Reference confidence must be verified or suspected")
            evidence = item.get("evidence")
            require(isinstance(evidence, list) and evidence, "Reference needs evidence, even if only a textual source excerpt/reason")
            for proof in evidence:
                require(isinstance(proof, dict) and isinstance(proof.get("label"), str) and proof["label"].strip(), "Evidence needs a label")
                require(isinstance(proof.get("url", ""), str), "Evidence URL must be a string")


def finding_key(item):
    return "id:" + item["id"] if item.get("id") else fingerprint([item["title"], sorted(set(item["languages"]))])


def merge_findings(new, old):
    """Update current findings, retaining each removed finding with its context."""
    previous = {finding_key(f): copy.deepcopy(f) for f in old["findings"]} if old else {}
    merged = []
    for item in new:
        previous.pop(finding_key(item), None)
        merged.append({**copy.deepcopy(item), "status": "active"})
    for item in previous.values():
        item["status"] = "absent"
        item.setdefault("previous_context", copy.deepcopy(old.get("previous_context") or {"source": old["source"], "text_vi": old["text_vi"]}))
        merged.append(item)
    return merged


def validate_entry(entry, kind):
    require(isinstance(entry, dict), "Invalid stored entry")
    require(type(entry.get("block_order")) is int and entry["block_order"] > 0, "Invalid stored block order")
    source_dict(entry.get("source"))
    for field in ("uid", "header", "kind", "speaker", "text_vi", "current_text_vi", "updated_at", "source_fingerprint"):
        require(isinstance(entry.get(field), str), f"Invalid stored entry field: {field}")
    require(entry.get("status") in STATUSES and isinstance(entry.get("source_refs"), dict), "Invalid stored status/source_refs")
    require(entry.get("ui_type", "story") in ("story", "static"), "Invalid stored UI type")
    if entry.get("ui_type") == "static":
        require(entry["kind"] == "" and entry["speaker"] == "" and isinstance(entry.get("source_code"), str), "Static entry must retain its code without speaker/kind")
        require(entry["source_refs"] == static_refs(entry["source_code"]) and entry["header"] == "[" + entry["source_code"] + "]", "Static entry code/header mismatch")
    validate_findings(entry.get("findings"), kind)
    if "previous_context" in entry:
        previous = entry["previous_context"]
        require(isinstance(previous, dict) and isinstance(previous.get("text_vi"), str), "Invalid historical context")
        source_dict(previous.get("source"))


def read_store(data, kind):
    text = data.decode("utf-8-sig")
    matches = DATA_RE.findall(text)
    require(len(matches) == 1, f"Corrupt {kind} report: expected one embedded dataset")
    store = json.loads(matches[0])
    require(isinstance(store, dict) and store.get("schema_version") == 1 and store.get("report_type") == kind and store.get("resource_root") == RESOURCE, "Unknown report schema or type")
    require(isinstance(store.get("checkpoint"), str) and isinstance(store.get("updated_at"), str) and isinstance(store.get("files"), dict), "Invalid report metadata")
    for path, info in store["files"].items():
        path_key(path)
        require(isinstance(info, dict), "Invalid file record")
        require(type(info.get("total_blocks")) is int and info["total_blocks"] > 0, "Invalid total_blocks")
        require(isinstance(info.get("merge_sha256"), str) and isinstance(info.get("updated_at"), str), "Invalid file metadata")
        require(isinstance(info.get("coverage"), dict) and isinstance(info.get("entries"), dict) and isinstance(info.get("unresolved"), dict), "Invalid file collections")
        for number, coverage in info["coverage"].items():
            require(number.isdigit() and int(number) > 0 and isinstance(coverage, dict) and isinstance(coverage.get("body_sha256"), str) and isinstance(coverage.get("reviewed_at"), str), "Invalid coverage")
        for number, entry in info["entries"].items():
            validate_entry(entry, kind)
            require(number == str(entry["block_order"]), "Stored entry order mismatch")
        for uid, entry in info["unresolved"].items():
            validate_entry(entry, kind)
            require(uid == entry["uid"], "Stored unresolved entry mismatch")
    return store


def blank_store(kind, checkpoint, timestamp):
    return {"schema_version": 1, "report_type": kind, "resource_root": RESOURCE,
            "checkpoint": checkpoint, "updated_at": timestamp, "files": {}}


def load_pair(root):
    originals = {kind: (root / "reports" / filename).read_bytes() if (root / "reports" / filename).exists() else None
                 for kind, filename in REPORT_NAMES.items()}
    require(all(v is None for v in originals.values()) or all(v is not None for v in originals.values()), "One report is missing: restore the pair before updating")
    if all(v is None for v in originals.values()):
        checkpoint, timestamp = uuid4().hex, now()
        return originals, {kind: blank_store(kind, checkpoint, timestamp) for kind in REPORT_NAMES}
    stores = {kind: read_store(data, kind) for kind, data in originals.items()}
    left, right = stores.values()
    require(left["checkpoint"] == right["checkpoint"], "Report checkpoints differ: recover the interrupted write before updating")
    require(set(left["files"]) == set(right["files"]), "Report file inventories differ")
    for path in left["files"]:
        for field in ("coverage", "merge_sha256", "total_blocks", "updated_at"):
            require(left["files"][path][field] == right["files"][path][field], "Report coverage snapshots differ")
    return originals, stores


def validate_payload(root, payload):
    require(isinstance(payload, dict) and isinstance(payload.get("files"), list) and payload["files"], "Payload needs nonempty files")
    prepared = []
    paths = set()
    for item in payload["files"]:
        require(isinstance(item, dict), "File payload must be an object")
        path = path_key(item.get("merge_path"))
        require(path not in paths, "Repeated file in one payload")
        paths.add(path)
        target = (root / path).resolve()
        require(target.is_relative_to((root / RESOURCE).resolve()), "Merge path escapes resource tree")
        data = target.read_bytes()
        require(sha(data) == item.get("merge_sha256"), f"Stale Merge snapshot: {path}")
        current = parse_merge(data)
        reviewed = item.get("blocks")
        require(isinstance(reviewed, list) and reviewed, "File needs all reviewed blocks, including those with no findings")
        seen = set()
        normalized = []
        for block in reviewed:
            require(isinstance(block, dict), "Block must be an object")
            number = block.get("block_order")
            require(type(number) is int and number in current and number not in seen, "Invalid/repeated reviewed block order")
            seen.add(number)
            source = source_dict(block.get("source"))
            vi, speaker, kind = block.get("text_vi"), block.get("speaker"), block.get("kind")
            require(isinstance(vi, str) and isinstance(speaker, str), "Reviewed block needs text_vi and speaker strings")
            require(kind == current[number]["kind"], "Block kind does not match Merge")
            require(not speaker or speaker in current[number]["header"], "Speaker does not match Merge header")
            require(block.get("ui_type", current[number]["ui_type"]) == current[number]["ui_type"], "UI type does not match Merge")
            require(block.get("source_code", current[number]["source_code"]) == current[number]["source_code"], "Source code does not match Merge header")
            if current[number]["ui_type"] == "static":
                require(speaker == "", "Static UI must not have a speaker")
            vi = norm(vi)
            parts = [source["CN"], source["JP"], source["EN"]] + ([vi] if vi else [])
            require("\n".join(parts) == current[number]["body"], f"Source/VI snapshot does not match Merge block {number}")
            refs = block.get("source_refs", {})
            require(isinstance(refs, dict) and set(refs).issubset(LANGS) and all(isinstance(v, str) for v in refs.values()), "source_refs must map EN/JP/CN to verified source codes")
            if current[number]["ui_type"] == "static":
                require(not refs or refs == current[number]["source_refs"], "Static source_refs do not match the unchanged header")
                refs = current[number]["source_refs"]
            for report_type in REPORT_NAMES:
                validate_findings(block.get(report_type), report_type)
                require(all("status" not in f and "previous_context" not in f for f in block[report_type]), "Finding history/status is managed by the helper")
            normalized.append({**block, "source": source, "text_vi": vi, "source_refs": refs,
                               "header": current[number]["header"], "ui_type": current[number]["ui_type"],
                               "source_code": current[number]["source_code"]})
        prepared.append({"path": path, "sha256": sha(data), "current": current, "blocks": normalized})
    return prepared


def source_fingerprint(block):
    return fingerprint([block["header"], block["kind"], block["source"], block["source_refs"]])


def reconcile(info, current):
    """Relocate only unique exact source/header matches; preserve ambiguous items."""
    coverage = {}
    for number, old in info["coverage"].items():
        hits = [n for n, block in current.items() if block["body_sha256"] == old["body_sha256"]]
        if int(number) in hits:
            coverage[number] = old
        elif len(hits) == 1:
            coverage[str(hits[0])] = old
    info["coverage"] = coverage
    active, unresolved = {}, {}
    for entry in list(info["entries"].values()) + list(info["unresolved"].values()):
        prefix = "\n".join(entry["source"][lang] for lang in ("CN", "JP", "EN")) + "\n"
        hits = [n for n, b in current.items() if b["header"] == entry["header"] and b["body"].startswith(prefix)]
        if len(hits) == 1 and str(hits[0]) not in active:
            entry["block_order"] = hits[0]
            vi = current[hits[0]]["body"][len(prefix):]
            if vi != entry["text_vi"]:
                entry["status"] = "needs_review"
            entry["current_text_vi"] = vi
            active[str(hits[0])] = entry
        else:
            entry["status"] = "needs_review"
            unresolved[entry["uid"]] = entry
    info["entries"], info["unresolved"] = active, unresolved


def update_stores(stores, prepared):
    stores = copy.deepcopy(stores)
    timestamp, checkpoint = now(), uuid4().hex
    for snapshot in prepared:
        path, current = snapshot["path"], snapshot["current"]
        for report_type, store in stores.items():
            info = store["files"].setdefault(path, {"total_blocks": len(current), "merge_sha256": snapshot["sha256"], "updated_at": timestamp,
                                                   "coverage": {}, "entries": {}, "unresolved": {}})
            if info["merge_sha256"] != snapshot["sha256"]:
                reconcile(info, current)
            for block in snapshot["blocks"]:
                number = str(block["block_order"])
                signature = source_fingerprint(block)
                old = info["entries"].get(number)
                if old is not None and old["source_fingerprint"] != signature:
                    old["status"] = "needs_review"
                    info["unresolved"][old["uid"]] = old
                    old = None
                # Verified source refs supplied by the agent can resolve a moved/changed item.
                prefix = "\n".join(block["source"][lang] for lang in ("CN", "JP", "EN")) + "\n"
                unique_source = sum(b["header"] == block["header"] and b["body"].startswith(prefix) for b in current.values()) == 1
                candidates = [(uid, e) for uid, e in info["unresolved"].items()
                              if ((unique_source and e["source_fingerprint"] == signature) or
                                  (any(block["source_refs"].values()) and e["source_refs"] == block["source_refs"]))]
                if old is None and len(candidates) == 1:
                    uid, old = candidates[0]
                    del info["unresolved"][uid]
                findings = block[report_type]
                merged_findings = merge_findings(findings, old)
                historical = None
                if old and old["findings"] and not findings:
                    historical = old.get("previous_context") or {"source": old["source"], "text_vi": old["text_vi"]}
                info["entries"][number] = {
                        "uid": old["uid"] if old else uuid4().hex,
                        "block_order": block["block_order"], "header": block["header"], "kind": block["kind"],
                        "ui_type": block["ui_type"], "source_code": block["source_code"],
                        "speaker": block["speaker"], "source_refs": block["source_refs"], "source": block["source"],
                        "text_vi": block["text_vi"], "current_text_vi": block["text_vi"],
                        "source_fingerprint": signature,
                        "status": "active" if findings else ("absent" if historical else "clear"),
                        "findings": merged_findings, "updated_at": timestamp,
                    }
                if historical:
                    info["entries"][number]["previous_context"] = copy.deepcopy(historical)
                info["coverage"][number] = {"body_sha256": current[int(number)]["body_sha256"], "reviewed_at": timestamp}
            info.update(total_blocks=len(current), merge_sha256=snapshot["sha256"], updated_at=timestamp)
            info["coverage"] = {k: v for k, v in info["coverage"].items() if int(k) in current}
    for store in stores.values():
        store.update(checkpoint=checkpoint, updated_at=timestamp)
    return stores


def render(store):
    template = (Path(__file__).resolve().parent.parent / "assets" / "report_template.html").read_text(encoding="utf-8")
    require(template.count("__REPORT_DATA__") == 1 and template.count("__REPORT_TITLE__") == 1, "Invalid report template")
    payload = json.dumps(store, ensure_ascii=False, separators=(",", ":")).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    title = "Báo cáo xung đột bản dịch" if store["report_type"] == "conflicts" else "Báo cáo reference và chơi chữ"
    html = template.replace("__REPORT_TITLE__", title).replace("__REPORT_DATA__", payload)
    data = norm(html).replace("\n", "\r\n").encode("utf-8-sig")
    require(read_store(data, store["report_type"]) == store, "Report round-trip failed")
    return data


def stage(directory, name, data):
    fd, name = tempfile.mkstemp(prefix=f".{name}.", suffix=".pending", dir=directory)
    with os.fdopen(fd, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    return Path(name)


def commit_pair(root, originals, stores, prepared):
    directory = root / "reports"
    directory.mkdir(exist_ok=True)
    generated = {k: render(s) for k, s in stores.items()}
    staged = {}
    written = []
    successful = False
    recovery_complete = False
    try:
        for kind, data in generated.items():
            staged[kind] = stage(directory, REPORT_NAMES[kind], data)
        for snapshot in prepared:
            require(sha((root / snapshot["path"]).read_bytes()) == snapshot["sha256"], "Merge changed while preparing reports")
        for kind, old in originals.items():
            path = directory / REPORT_NAMES[kind]
            require((path.read_bytes() if path.exists() else None) == old, "Report changed while preparing update")
        for kind in REPORT_NAMES:
            os.replace(staged[kind], directory / REPORT_NAMES[kind])
            written.append(kind)
        for kind, data in generated.items():
            require((directory / REPORT_NAMES[kind]).read_bytes() == data, "Saved report verification failed")
        for snapshot in prepared:
            require(sha((root / snapshot["path"]).read_bytes()) == snapshot["sha256"], "Merge changed while saving reports")
        successful = True
    except Exception as error:
        # Preserve both proposed reports for recovery; never touch the saved Merge.
        recovery = []
        for kind, data in generated.items():
            try:
                recovery.append(str(stage(directory, REPORT_NAMES[kind] + ".recovery", data)))
            except OSError as recovery_error:
                recovery.append(f"Could not stage {kind}: {recovery_error}")
        recovery_complete = all(Path(p).is_file() for p in recovery)
        if not recovery_complete:
            recovery.extend(str(p) for p in staged.values() if p.exists())
        rollback_errors = []
        for kind in written:
            path = directory / REPORT_NAMES[kind]
            try:
                if originals[kind] is None:
                    path.unlink()
                else:
                    os.replace(stage(directory, REPORT_NAMES[kind] + ".rollback", originals[kind]), path)
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        raise OSError(f"Report update failed: {error}; recovery: {recovery}; rollback errors: {rollback_errors}") from error
    finally:
        for path in staged.values():
            if path.exists() and (successful or recovery_complete):
                path.unlink()


def _run(root, payload=None, initialize=False, dry_run=False):
    originals, stores = load_pair(root)
    if initialize:
        if all(v is not None for v in originals.values()):
            return {"initialized": False, "message": "Existing report pair validated; kept unchanged"}
        prepared = []
    else:
        prepared = validate_payload(root, payload)
        stores = update_stores(stores, prepared)
    # Validate serialization before any output mutation, including dry runs.
    for store in stores.values():
        render(store)
    if not dry_run:
        commit_pair(root, originals, stores, prepared)
    return {"dry_run": dry_run, "initialized": initialize,
            "files_updated": [s["path"] for s in prepared],
            "reports": {kind: {"files": len(store["files"]),
                "active": sum(e["status"] == "active" for f in store["files"].values() for e in f["entries"].values()),
                "needs_review": sum(e["status"] == "needs_review" for f in store["files"].values() for e in list(f["entries"].values()) + list(f["unresolved"].values()))}
                for kind, store in stores.items()}}


@contextmanager
def writer_lock(root):
    directory = root / "reports"
    require(directory.resolve().is_relative_to(root.resolve()), "Report directory escapes project")
    directory.mkdir(exist_ok=True)
    lock = directory / ".translation-reports.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as error:
        raise OSError(f"Reports are locked: {lock}; do not overwrite an active or interrupted writer") from error
    try:
        with handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def run(root, payload=None, initialize=False, dry_run=False):
    if dry_run:
        return _run(root, payload, initialize, True)
    with writer_lock(root):
        return _run(root, payload, initialize, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true")
    mode.add_argument("--input", type=Path)
    mode.add_argument("--inspect", metavar="MERGE_PATH")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.inspect:
            path = path_key(args.inspect)
            _, stores = load_pair(args.project_root.resolve())
            print(json.dumps({kind: store["files"].get(path) for kind, store in stores.items()}, ensure_ascii=True, indent=2))
            return 0
        payload = json.loads(args.input.read_text(encoding="utf-8-sig")) if args.input else None
        result = run(args.project_root.resolve(), payload, args.init, args.dry_run)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
