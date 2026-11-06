"""Persistent queue for SS workflow. This helper never calls a model or edits game text."""
import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import tomllib
from uuid import uuid4

RESOURCE = "StellaSora_TaiNguyen_EN_JP_CN_Text_20261101_r03"
STAGES = ("merge", "terms", "translate", "verify")
ROLES = {"terms": "term-controller", "merge": "merger", "translate": "translator", "verify": "parent"}
SOURCE_WARNING = re.compile(r"KHÔNG CÓ (?:NGUỒN|KHÓA TRONG NGUỒN)\s+(?:EN|JP|CN)(?:\b|\])")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def signature(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def natural(value):
    return [int(x) if x.isdigit() else x.casefold() for x in re.split(r"(\d+)", value)]


class Queue:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.directory = self.root / ".ss-workflow"
        require(self.directory.resolve().is_relative_to(self.root), "State directory escapes project")
        self.path = self.directory / "state.json"

    @contextmanager
    def locked(self):
        self.directory.mkdir(exist_ok=True)
        # OS locking releases on process exit; a leftover file is not a stale lock.
        with (self.directory / "state.lock").open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"0"); handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise OSError("Workflow state is being updated by another process") from error
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)

    def atomic(self, path, raw):
        fd, pending = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".pending", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(raw); output.flush(); os.fsync(output.fileno())
            os.replace(pending, path)
        except OSError as error:
            raise OSError(f"Could not save {path}; preserve recovery file {pending}: {error}") from error

    def read(self):
        require(self.path.is_file(), "Workflow not initialized; use init")
        raw = self.path.read_bytes()
        state = json.loads(raw.decode("utf-8-sig"))
        require(isinstance(state, dict) and state.get("schema_version") in (1, 2) and state.get("resource_root") == RESOURCE, "Unknown/corrupt workflow state; do not reset it")
        require(isinstance(state.get("jobs"), list) and isinstance(state.get("revision"), int), "Corrupt workflow collections")
        ids = set()
        for job in state["jobs"]:
            valid_stages = STAGES + (("inspect",) if state["schema_version"] == 1 else ())
            require(isinstance(job, dict) and job.get("stage") in valid_stages and job.get("status") in ("pending", "running", "done", "blocked", "failed"), "Corrupt job")
            require(job.get("id") == signature(job.get("merge_path"))[:20] and job["id"] not in ids, "Invalid/duplicate job identity")
            self.resource_path(job["merge_path"])
            expected = f"{job.get('folder')}/{job.get('base')}_Merge.txt"
            require(job["merge_path"] == expected and job.get("sources") == {
                k: f"{job['folder']}/{job['base']}_{k}.txt" for k in ("EN", "JP", "CN")
            }, "Corrupt job source paths")
            claim = job.get("claim")
            require(claim is None or isinstance(claim, dict) and job["status"] == "running" and
                    claim.get("stage") == job["stage"] and isinstance(claim.get("token"), str), "Corrupt active claim")
            ids.add(job["id"])
        run = state.get("run")
        require(run is None or isinstance(run, dict) and isinstance(run.get("token"), str) and run.get("status") in ("running", "completed", "finished_with_issues", "limited", "stopped", "paused", "needs_attention"), "Corrupt run")
        return raw, state

    def save(self, original, state):
        require((self.path.read_bytes() if self.path.exists() else None) == original, "Workflow changed during update")
        state["updated_at"] = timestamp()
        state["revision"] += 1
        raw = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8-sig")
        if original is not None:
            self.atomic(self.directory / "state.backup.json", original)
        self.atomic(self.path, raw)
        require(self.path.read_bytes() == raw, "Saved state readback failed")

    def resource_path(self, value):
        require(isinstance(value, str) and "\\" not in value and ".." not in Path(value).parts, "Use project-relative paths with /")
        path = (self.root / value).resolve()
        require(value.startswith(RESOURCE + "/") or value == RESOURCE, "Scope must be inside the resource folder")
        require(path.is_relative_to((self.root / RESOURCE).resolve()), "Path escapes resource folder")
        return path

    def helper(self):
        path = self.root / ".agents/skills/translate/scripts/update_reports.py"
        spec = importlib.util.spec_from_file_location("ss_workflow_reports", path)
        module = importlib.util.module_from_spec(spec)
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
        return module

    def sources(self, job):
        hashes, texts, issues = {}, [], []
        for language in ("EN", "JP", "CN"):
            path = self.resource_path(job["sources"][language])
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8-sig")
            except (OSError, UnicodeError) as error:
                issues.append(f"{language}: {job['sources'][language]}: {error}")
                continue
            hashes[language] = digest(raw)
            texts.append(text)
            for number, line in enumerate(text.splitlines(), 1):
                if SOURCE_WARNING.search(line):
                    issues.append(f"{language}: {job['sources'][language]}:{number}: {line.strip()}")
            for line in text.splitlines()[:8]:
                declaration = re.match(r"^[^|\n]+\|\s*(EN|JP|CN)\s*\|", line) or re.match(r"^(?:Language|Ngôn ngữ)\s*[:=]\s*(EN|JP|CN)\s*$", line, re.I)
                if declaration and declaration[1].upper() != language:
                    issues.append(f"{language}: declared {declaration[1]} in {job['sources'][language]}")
        return hashes, texts, issues

    def glossary(self, texts):
        raw = (self.root / "glossary/glossary.csv").read_bytes()
        import io
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        require(reader.fieldnames == ["id", "EN", "target", "category", "JP", "CN"], "Invalid glossary columns")
        rows = list(reader)
        require(all(set(row) == set(reader.fieldnames) and all(isinstance(v, str) for v in row.values()) for row in rows), "Malformed glossary row")
        en_terms = [r["EN"].strip().casefold() for r in rows if r["category"] == "term"]
        require(len(en_terms) == len(set(en_terms)), "Duplicate EN term in glossary")
        combined = "\n".join(texts)
        relevant, definitions = {}, {}
        for row in rows:
            identifier = row["id"]
            token = re.match(r"SEX/([^/]+)/\d+$", identifier)
            matches_id = bool(identifier and identifier in combined or token and token[1] in combined)
            matches_text = False
            for language in ("EN", "JP", "CN"):
                text = row[language].strip()
                if not text or text == "[EMPTY_SOURCE]":
                    continue
                if language == "EN" and len(text) >= 3:
                    # A literal occurrence is necessary for the boundary-aware match.
                    # Searching the literal first avoids testing a lookbehind at every
                    # character for hundreds of glossary values absent from a story.
                    literal = re.escape(text)
                    if re.search(literal, combined, re.I) is not None:
                        matches_text |= re.search(r"(?<!\w)" + literal + r"(?:s|es|['’]s)?(?!\w)", combined, re.I) is not None
                elif language != "EN" and len(text) >= 2:
                    matches_text |= text in combined
            if matches_id or matches_text:
                key = "term:" + row["EN"].strip().casefold() if row["category"] == "term" else "map:" + row["category"] + ":" + identifier
                require(key not in relevant, "Duplicate relevant glossary mapping")
                relevant[key] = signature(row)
                definitions[key] = row
        mapping = {"map:" + r["category"] + ":" + r["id"]: [r[k] for k in ("id", "EN", "JP", "CN")]
                   for r in rows if r["category"] != "term" and "map:" + r["category"] + ":" + r["id"] in relevant}
        return {"sha256": digest(raw), "relevant": signature(relevant), "mapping": signature(mapping),
                "definitions": definitions}, rows

    def inputs(self, job):
        hashes, texts, issues = self.sources(job)
        glossary, _ = self.glossary(texts)
        merge = self.resource_path(job["merge_path"])
        return {"sources": hashes, "glossary": glossary, "merge": digest(merge.read_bytes()) if merge.exists() else None}, issues

    def event(self, job, message):
        job["history"].append({"at": timestamp(), "message": message})
        job["history"] = job["history"][-40:]

    def rewind(self, job, stage, reason):
        job.update(status="pending", stage=stage, claim=None, attempts={})
        job.pop("review_scope", None)
        for later in STAGES[STAGES.index(stage):]:
            job["checkpoints"].pop(later, None)
        if stage == "merge":
            job["proposals"] = []
            job.pop("review_glossary", None)
            job.pop("review_merge_sha256", None)
            job.pop("glossary_baseline", None)
        self.event(job, reason)

    def role(self, name):
        if name == "parent":
            return {"name": "parent"}
        path = self.root / ".codex/agents" / (name + ".toml")
        config = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        require(config.get("name") == name and all(isinstance(config.get(k), str) and config[k].strip() for k in ("description", "model", "model_reasoning_effort", "developer_instructions")), "Invalid agent configuration: " + name)
        return config

    def checked_reports(self, job, layout=None):
        helper = self.helper()
        path = self.resource_path(job["merge_path"])
        data = path.read_bytes()
        current = helper.parse_merge(data)
        if layout is not None:
            require(set(layout) == {str(n) for n in current}, "Source block inventory changed during translation")
        require(data.startswith(b"\xef\xbb\xbf") and b"\n" not in data.replace(b"\r\n", b""), "Merge must be UTF-8 BOM/CRLF")
        _, stores = helper.load_pair(self.root)
        for kind, store in stores.items():
            info = store["files"].get(job["merge_path"])
            require(info and info["merge_sha256"] == digest(data), "Report does not match current Merge: " + kind)
            require(set(info["coverage"]) == {str(n) for n in current} and not info["unresolved"], "Report coverage is incomplete or has unresolved locations: " + kind)
            require(set(info["entries"]) == {str(n) for n in current}, "Missing reviewed block entries: " + kind)
            for number, block in current.items():
                entry = info["entries"][str(number)]
                require(entry["status"] != "needs_review" and entry["current_text_vi"] == entry["text_vi"] and entry["text_vi"].strip(), "Unfinished VI/report block: " + str(number))
                require(info["coverage"][str(number)]["body_sha256"] == block["body_sha256"] and entry["header"] == block["header"], "Report block snapshot mismatch")
                require("\n".join([entry["source"][k] for k in ("CN", "JP", "EN")] + [entry["text_vi"]]) == block["body"], "Report source/VI mismatch")
                if layout is not None:
                    require(layout[str(number)] == self.layout_entry(entry), "Source content or static code changed during translation")
        return {"merge_sha256": digest(data), "block_count": len(current), "glossary": self.inputs(job)[0]["glossary"]}

    @staticmethod
    def layout_entry(block):
        return signature([block["kind"], block["source"], block.get("source_code", "")])

    @staticmethod
    def v2(state):
        require(state["schema_version"] == 2, "Migrate stopped v1 state before running the pipeline")

    @staticmethod
    def block_signature(block):
        return signature([block["header"], block["body_sha256"]])

    @staticmethod
    def row_in_block(row, block):
        # Static source codes are identifiers, not visible text. Do not search them.
        raw_text = "\n".join(block["source"].values())
        speaker = block.get("speaker", "")
        if speaker and row["EN"].strip() == speaker:
            return True
        token = re.match(r"SEX/([^/]+)/\d+$", row["id"])
        if token and token[1] in raw_text:
            return True
        text = re.sub(r'<[^>\n]*>', '', raw_text)
        text = re.sub(r'==[^=\n]+==', ' ', text)
        for language in ("EN", "JP", "CN"):
            value = row[language].strip()
            if not value or value == "[EMPTY_SOURCE]":
                continue
            if language == "EN":
                if re.search(r"(?<!\w)" + re.escape(value) + r"(?:s|es|['’]s)?(?!\w)", text, re.I):
                    return True
            else:
                visible = re.sub(r'<[^>\n]*>', '', value)
                if visible and visible in text:
                    return True
        return False

    def glossary_scope(self, job, old, new):
        self.checked_reports(job, job["checkpoints"]["merge"]["layout"])
        _, stores = self.helper().load_pair(self.root)
        entries = stores["conflicts"]["files"][job["merge_path"]]["entries"]
        before, after = old["definitions"], new["definitions"]
        changes = [{"key": key, "before": before.get(key), "after": after.get(key)}
                   for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]
        numbers = sorted(int(number) for number, block in entries.items()
                         if any(self.row_in_block(row, block) for change in changes
                                for row in (change["before"], change["after"]) if row))
        raw = self.resource_path(job["merge_path"]).read_bytes()
        current = self.helper().parse_merge(raw)
        return {"mode": "glossary", "blocks": numbers, "changes": changes,
                "merge_sha256": digest(raw),
                "block_hashes": {str(n): self.block_signature(b) for n, b in current.items()}}

    def review_packet(self, job_id, context=0):
        require(type(context) is int and context >= 0, "Context must be a nonnegative integer")
        with self.locked():
            _, state = self.read(); self.v2(state)
            job = next((j for j in state['jobs'] if j['id'] == job_id), None)
            require(job and job.get('review_scope'), "Job has no scoped glossary review")
            require(not any(j['claim'] and (j['stage'] == 'terms' or
                        j['stage'] == 'translate' and j['id'] != job_id) for j in state['jobs']),
                    "Wait for the glossary/report writer before reading a review packet")
            proof = self.checked_reports(job, job['checkpoints']['merge']['layout'])
            _, stores = self.helper().load_pair(self.root)
            entries = stores['conflicts']['files'][job['merge_path']]['entries']
            selected = set(job['review_scope']['blocks'])
            neighbors = {n + offset for n in selected for offset in range(-context, context + 1)
                         if str(n + offset) in entries} - selected
            def entry(number):
                saved = entries[str(number)]
                block = {key: saved[key] for key in ('block_order', 'kind', 'speaker', 'source', 'text_vi',
                                                     'ui_type', 'source_code', 'source_refs', 'header')}
                for kind, store in stores.items():
                    block[kind] = [{k: v for k, v in f.items() if k not in ('status', 'previous_context')}
                                   for f in store['files'][job['merge_path']]['entries'][str(number)]['findings']
                                   if f.get('status', 'active') == 'active']
                return block
            return {'reviewed_blocks': sorted(selected), 'changes': job['review_scope']['changes'],
                    'payload': {'files': [{'merge_path': job['merge_path'], 'merge_sha256': proof['merge_sha256'],
                                          'blocks': [entry(n) for n in sorted(selected)]}]},
                    'context_blocks': [entry(n) for n in sorted(neighbors)]}

    def reconcile(self, job, reports_safe=True):
        if job["claim"]:
            return  # A worker may be writing its Merge; never invalidate a live claim.
        hashes, texts, issues = self.sources(job)
        if issues:
            job.update(status="blocked", error="\n".join(issues), error_kind="source")
            self.event(job, job["error"])
            return
        merged = job["checkpoints"].get("merge")
        if merged and hashes != merged["sources"]:
            self.rewind(job, "merge", "Sources changed; remerge while preserving current VI")
        elif job["status"] == "blocked" and job.get("error_kind") == "source":
            self.rewind(job, "merge", "Language source issue resolved")
        if job["status"] in ("blocked", "failed") or not job["checkpoints"].get("merge"):
            return
        previous = next((job["checkpoints"][s] for s in reversed(STAGES) if s in job["checkpoints"]), None)
        glossary, _ = self.glossary(texts)
        if previous["glossary"].get("mapping") != glossary["mapping"]:
            self.rewind(job, "merge", "Source-language name/token mapping changed; preserve edits")
            return
        # Terms are intentionally applied after Merge. Do not turn that into another merge.
        reviewed_glossary = job.get("review_glossary", previous["glossary"])
        # Compatible v2 checkpoints can acquire a baseline without rereading text
        # in a model. Never reconstruct old definitions from a different glossary.
        if ("definitions" not in reviewed_glossary and
                reviewed_glossary["relevant"] == glossary["relevant"]):
            reviewed_glossary = {**reviewed_glossary, "definitions": glossary["definitions"]}
            job["review_glossary"] = reviewed_glossary
        if job["stage"] != "terms" and reviewed_glossary["relevant"] != glossary["relevant"]:
            verified = job.get("glossary_baseline") or job["checkpoints"].get("verify")
            if verified:
                if not reports_safe:
                    return  # Do not read either report during another writer's commit.
                if "definitions" not in reviewed_glossary:
                    job.update(status="blocked", error_kind="decision",
                               error="Missing glossary baseline; compare prior definitions before scoped review")
                    self.event(job, job["error"])
                    return
                path = self.resource_path(job["merge_path"])
                trusted_hash = job.get("review_merge_sha256", previous["merge_sha256"])
                if path.exists() and digest(path.read_bytes()) == trusted_hash:
                    baseline = (job["glossary_baseline"]["glossary"]
                                if job.get("review_scope") and job.get("glossary_baseline") else reviewed_glossary)
                    scope = self.glossary_scope(job, baseline, glossary)
                    if not scope["blocks"]:
                        # Changed definitions occurred only in non-visible source data.
                        previous["glossary"] = glossary
                        job["review_glossary"] = glossary
                        if job.get("review_scope"):
                            restored = job["glossary_baseline"].get("checkpoint")
                            require(restored, "Missing verified checkpoint for reverted glossary changes")
                            job["checkpoints"]["verify"] = {**restored, "glossary": glossary}
                            job.update(status="done", stage="verify")
                            job.pop("review_scope", None)
                            job["review_merge_sha256"] = trusted_hash
                            job["glossary_baseline"] = {"glossary": glossary, "merge_sha256": trusted_hash}
                        self.event(job, "Glossary change has no visible block matches; existing VI retained")
                    else:
                        restored = job["checkpoints"].get("verify") or verified.get("checkpoint")
                        job["glossary_baseline"] = {"glossary": baseline, "merge_sha256": trusted_hash,
                                                   "checkpoint": restored}
                        self.rewind(job, "translate", "Glossary changed; review affected blocks only")
                        job["review_scope"] = scope
                        job["review_glossary"] = glossary
                        job["review_merge_sha256"] = scope["merge_sha256"]
                else:
                    self.rewind(job, "translate", "Merge edited; full review required before glossary sync")
                    job["review_glossary"] = glossary
            else:
                self.rewind(job, "translate", "Relevant VI definitions changed; review translation with latest glossary")
                job["review_glossary"] = glossary
        path = self.resource_path(job["merge_path"])
        current_hash = digest(path.read_bytes()) if path.exists() else None
        if current_hash is None:
            self.rewind(job, "merge", "Merge missing; existing checkpoints retained in history")
            return
        reviewed_hash = job.get("review_merge_sha256", previous["merge_sha256"])
        if job["stage"] != "terms" and reviewed_hash != current_hash:
            self.rewind(job, "translate", "Merge edited; preserve current VI and recheck reports")
            job["review_merge_sha256"] = current_hash
        if job["status"] == "done" and reports_safe:
            try:
                self.checked_reports(job, job["checkpoints"]["merge"]["layout"])
            except (ValueError, OSError, KeyError) as error:
                self.rewind(job, "translate", "Report verification required: " + str(error))

    def init(self):
        with self.locked():
            if self.path.exists():
                _, state = self.read()
                return {"initialized": False, "schema_version": state["schema_version"]}
            self.save(None, {"schema_version": 2, "resource_root": RESOURCE, "revision": 0,
                             "updated_at": timestamp(), "run": None, "jobs": []})
            return {"initialized": True, "jobs": 0}

    def migrate(self):
        with self.locked():
            original, state = self.read()
            if state["schema_version"] == 2:
                return {"migrated": False}
            require(not state["run"] or state["run"]["status"] != "running", "Stop v1 coordinator and workers before migration")
            require(not any(j["claim"] for j in state["jobs"]), "Release stopped v1 claims before migration")
            for job in state["jobs"]:
                job["legacy_checkpoints"] = job["checkpoints"].copy()
                job["checkpoints"].pop("inspect", None)
                if "merge" not in job["checkpoints"]:
                    # v1 terms-before-merge is history, never a completed v2 Merge.
                    job["checkpoints"] = {}
                    job.update(stage="merge", claim=None, attempts={})
                    if job["status"] not in ("blocked", "failed"):
                        job["status"] = "pending"
                else:
                    job["stage"] = "translate" if job["stage"] in ("inspect", "terms", "merge") else job["stage"]
                    hashes, texts, issues = self.sources(job)
                    if not issues:
                        glossary, _ = self.glossary(texts)
                        for checkpoint in job["checkpoints"].values():
                            if checkpoint["glossary"]["sha256"] == glossary["sha256"]:
                                checkpoint["glossary"]["mapping"] = glossary["mapping"]
                self.event(job, "Migrated to merge-first pipeline; artifacts and legacy evidence preserved")
            state["schema_version"] = 2
            self.save(original, state)
            return {"migrated": True, "jobs": len(state["jobs"])}

    def enqueue(self, scopes, recursive=False):
        with self.locked():
            original, state = self.read(); self.v2(state)
            require(not state["run"] or state["run"]["status"] != "running", "Stop active run before extending scope")
            require(not any(j["claim"] for j in state["jobs"]), "Workers still own claims")
            discovered = {}
            for scope in scopes:
                folder = self.resource_path(scope.rstrip("/"))
                require(folder.is_dir(), "Scope is not a directory: " + scope)
                for path in (folder.rglob("*.txt") if recursive else folder.glob("*.txt")):
                    match = re.fullmatch(r"(.+)_(EN|JP|CN)\.txt", path.name)
                    if match:
                        relative = path.with_name(match[1] + "_Merge.txt").relative_to(self.root).as_posix()
                        self.resource_path(relative)
                        discovered[relative] = (path.parent, match[1])
            require(discovered, "No source sets; --recursive requires explicitly recursive scope")
            known = {j["merge_path"] for j in state["jobs"]}
            added = []
            for relative in sorted(discovered, key=natural):
                if relative in known:
                    continue
                folder, base = discovered[relative]
                job = {"id": signature(relative)[:20], "merge_path": relative, "folder": folder.relative_to(self.root).as_posix(), "base": base,
                       "sources": {k: (folder / (base + "_" + k + ".txt")).relative_to(self.root).as_posix() for k in ("EN", "JP", "CN")},
                       "status": "pending", "stage": "merge", "checkpoints": {}, "proposals": [], "attempts": {}, "claim": None, "history": []}
                state["jobs"].append(job); added.append(job["id"])
            self.save(original, state)
            return {"added": added, "total": len(state["jobs"])}

    def start(self, max_items=10, max_minutes=60, max_attempts=2, recover=False):
        require(all(type(n) is int and n > 0 for n in (max_items, max_minutes, max_attempts)), "Limits must be positive integers")
        with self.locked():
            original, state = self.read(); self.v2(state)
            old = state["run"]
            require(recover or not any(j["claim"] for j in state["jobs"]) and (not old or old["status"] != "running"), "Confirm old coordinator/workers stopped before --recover")
            require(state["jobs"], "Queue empty; enqueue explicit scope")
            if recover:
                for job in state["jobs"]:
                    if job["claim"]:
                        job.update(status="pending", claim=None)
                        self.event(job, "Interrupted claim recovered; re-read saved artifacts before retry")
            for job in state["jobs"]:
                self.reconcile(job)
            run = {"token": uuid4().hex, "status": "running", "started_at": timestamp(),
                   "deadline": (datetime.now(timezone.utc) + timedelta(minutes=max_minutes)).isoformat(),
                   "max_items": max_items, "max_attempts": max_attempts, "finished_items": 0, "admitted_jobs": [], "reason": ""}
            state["run"] = run
            self.save(original, state)
            return run

    @staticmethod
    def active_run(state, token, finish=False):
        run = state["run"]
        allowed = ("running", "needs_attention") if finish else ("running",)
        require(run and run["status"] in allowed and token == run["token"], "Invalid or inactive run token")
        return run

    @staticmethod
    def eligible(job, jobs):
        """One lookahead Merge, no term handoff while any translation is unfinished."""
        active = [j for j in jobs if j["claim"]]
        live = [j for j in jobs if j["status"] not in ("done", "blocked", "failed")]
        stage = job["stage"]
        if stage == "verify":
            return not any(j["stage"] in ("translate", "verify", "terms") for j in active)
        if stage == "translate":
            return not any(j["stage"] in ("translate", "verify", "terms") for j in active) and not any(j["stage"] == "verify" for j in live)
        if stage == "terms":
            return not active and not any(j["stage"] in ("translate", "verify") for j in live)
        # A completed lookahead Merge waiting for terms/translation blocks Merge C.
        producer = next((j for j in live if j["stage"] in ("merge", "terms")), None)
        consumers = [j for j in live if j["stage"] in ("translate", "verify")]
        return (producer is job and not any(j["stage"] in ("merge", "terms") for j in active)
                and len(consumers) <= 1 and (not consumers or consumers[0]["claim"] is not None))

    def claim(self, token):
        with self.locked():
            original, state = self.read(); self.v2(state); run = self.active_run(state, token)
            if any(j["claim"] and j["stage"] == "terms" for j in state["jobs"]):
                return {"stop": False, "wait": True, "reason": "Term-controller owns glossary; wait for its checkpoint"}
            reports_safe = not any(j["claim"] and j["stage"] == "translate" for j in state["jobs"])
            for job in state["jobs"]:
                self.reconcile(job, reports_safe=reports_safe)
            active = [j for j in state["jobs"] if j["claim"]]
            expired = datetime.now(timezone.utc) >= datetime.fromisoformat(run["deadline"])
            if expired or run["finished_items"] >= run["max_items"]:
                if active:
                    self.save(original, state)
                    return {"stop": False, "wait": True, "reason": "Budget reached; drain active workers before stopping"}
                run.update(status="limited", reason="Run item/time budget reached")
                self.save(original, state)
                return {"stop": True, "run": run}
            priority = {"verify": 0, "translate": 1, "terms": 2, "merge": 3}
            candidates = sorted((j for j in state["jobs"] if j["status"] == "pending"), key=lambda j: priority[j["stage"]])
            for job in candidates:
                if not self.eligible(job, state["jobs"]):
                    continue
                admitted = run["admitted_jobs"]
                reserved = sum(j["id"] in admitted and j["status"] not in ("done", "blocked", "failed") for j in state["jobs"])
                if job["id"] not in admitted and run["finished_items"] + reserved >= run["max_items"]:
                    continue
                stage = job["stage"]
                attempts = job["attempts"].get(stage, 0)
                if attempts >= run["max_attempts"]:
                    job.update(status="failed", error="Stage attempt limit reached", error_kind="worker")
                    continue
                if stage in ("translate", "verify"):
                    try:
                        self.helper().load_pair(self.root)
                    except (ValueError, OSError, KeyError) as error:
                        run.update(status="needs_attention", reason="Repair report pair: " + str(error))
                        self.save(original, state)
                        return {"stop": True, "run": run}
                snapshot, issues = self.inputs(job)
                require(not issues, "Source became invalid; claim again to record issue")
                config = self.role(ROLES[stage])
                claim = {"token": uuid4().hex, "stage": stage, "started_at": timestamp(), "snapshot": snapshot}
                job.update(status="running", claim=claim)
                job["attempts"][stage] = attempts + 1
                if job["id"] not in admitted:
                    admitted.append(job["id"])
                self.save(original, state)
                return {"stop": False, "wait": False, "run_token": token, "job": job, "agent": config}
            # Re-run after marking an exhausted candidate failed, so it cannot strand a barrier.
            if any(j["claim"] for j in state["jobs"]):
                self.save(original, state)
                return {"stop": False, "wait": True, "reason": "Waiting for worker/barrier; keep term proposals queued"}
            if any(j["status"] == "pending" for j in state["jobs"]):
                self.save(original, state)
                return {"stop": False, "wait": True, "reason": "Re-evaluate pending jobs after attempt/admission changes"}
            run.update(status="finished_with_issues" if any(j["status"] in ("blocked", "failed") for j in state["jobs"]) else "completed", reason="No runnable jobs remain")
            self.save(original, state)
            return {"stop": True, "run": run}

    def complete(self, token, job_id, claim_token, receipt):
        with self.locked():
            original, state = self.read(); self.v2(state); run = self.active_run(state, token, finish=True)
            job = next((j for j in state["jobs"] if j["id"] == job_id), None)
            require(job and job["status"] == "running" and job["claim"] and job["claim"]["token"] == claim_token, "Stale job claim")
            require(isinstance(receipt, dict) and isinstance(receipt.get("summary"), str) and receipt["summary"].strip(), "Receipt needs summary")
            before = job["claim"]["snapshot"]
            now, issues = self.inputs(job)
            require(not issues and now["sources"] == before["sources"], "Source changed/became invalid during stage")
            stage = job["stage"]
            checkpoint = {"summary": receipt["summary"], "at": timestamp(), "sources": now["sources"], "glossary": now["glossary"], "merge_sha256": now["merge"]}
            if stage == "merge":
                require(now["glossary"]["sha256"] == before["glossary"]["sha256"], "Glossary changed during Merge; re-read latest before accepting")
                require(receipt.get("ui_type") in ("story", "static") and isinstance(receipt.get("term_proposals"), list), "Merge needs ui_type and term_proposals (including [])")
                proposals = receipt["term_proposals"]
                for proposal in proposals:
                    require(isinstance(proposal, dict) and all(isinstance(proposal.get(k), str) for k in ("EN", "JP", "CN", "context", "source_ref")) and proposal["EN"].strip() and proposal["context"].strip() and proposal["source_ref"].strip(), "Proposal needs EN/JP/CN/context/source_ref")
                require(len({p["EN"].strip().casefold() for p in proposals}) == len(proposals), "Duplicate proposal")
                raw = self.resource_path(job["merge_path"]).read_bytes()
                require(raw.startswith(b"\xef\xbb\xbf") and b"\n" not in raw.replace(b"\r\n", b""), "Merge must be UTF-8 BOM/CRLF")
                require(isinstance(receipt.get("snapshot_path"), str), "Merge needs snapshot_path")
                payload = json.loads(Path(receipt["snapshot_path"]).read_text(encoding="utf-8-sig"))
                prepared = self.helper().validate_payload(self.root, payload)
                require(len(prepared) == 1 and prepared[0]["path"] == job["merge_path"], "Snapshot must cover assigned Merge only")
                snapshot = prepared[0]
                require({b["block_order"] for b in snapshot["blocks"]} == set(snapshot["current"]), "Snapshot must cover all blocks")
                require(all(b["ui_type"] == receipt["ui_type"] for b in snapshot["blocks"]), "Snapshot UI type mismatch")
                checkpoint.update(layout={str(b["block_order"]): self.layout_entry(b) for b in snapshot["blocks"]}, block_count=len(snapshot["current"]))
                job.update(ui_type=receipt["ui_type"], proposals=proposals)
                next_stage = "terms" if proposals else "translate"
            elif stage == "terms":
                require(not any(j["claim"] and j["id"] != job_id for j in state["jobs"]), "Terms cannot overlap other workers")
                require(now["merge"] == before["merge"], "term-controller must not modify Merge")
                require(now["glossary"]["mapping"] == before["glossary"]["mapping"], "Term update changed source-language mapping; parent must resolve")
                outcomes = receipt.get("outcomes")
                expected = {p["EN"].strip().casefold() for p in job["proposals"]}
                require(isinstance(outcomes, list) and all(isinstance(o, dict) for o in outcomes), "Terms needs outcomes")
                require(len(outcomes) == len(expected) and {o.get("EN", "").strip().casefold() for o in outcomes} == expected, "Cover every proposal exactly once")
                _, rows = self.glossary(self.sources(job)[1])
                definitions = {r["EN"].strip().casefold(): r["target"] for r in rows if r["category"] == "term"}
                for outcome in outcomes:
                    require(outcome.get("status") in ("added", "existing", "unresolved"), "Invalid term status")
                    if outcome["status"] == "unresolved":
                        require(isinstance(outcome.get("reason"), str) and outcome["reason"].strip(), "Unresolved needs reason")
                    else:
                        require(outcome.get("target") and definitions.get(outcome["EN"].strip().casefold()) == outcome["target"], "Target does not match saved glossary")
                checkpoint["outcomes"] = outcomes
                next_stage = "translate"
            else:
                require(now["glossary"]["sha256"] == before["glossary"]["sha256"], "Glossary changed during translation/verification; review latest definitions")
                require("merge" in job["checkpoints"], "Missing Merge evidence")
                scope = job.get("review_scope")
                if scope:
                    if stage == "translate":
                        reviewed = receipt.get("reviewed_blocks")
                        require(isinstance(reviewed, list) and all(type(n) is int for n in reviewed)
                                and len(reviewed) == len(set(reviewed))
                                and set(reviewed) == set(scope["blocks"]), "Receipt must cover exactly the affected blocks")
                    current = self.helper().parse_merge(self.resource_path(job["merge_path"]).read_bytes())
                    require(set(map(str, current)) == set(scope["block_hashes"]), "Scoped review changed block inventory")
                    require(all(self.block_signature(block) == scope["block_hashes"][str(n)]
                                for n, block in current.items() if n not in scope["blocks"]),
                            "Scoped review modified an unaffected block")
                    checkpoint["review_scope"] = scope
                try:
                    checkpoint.update(self.checked_reports(job, job["checkpoints"]["merge"]["layout"]))
                except (ValueError, OSError, KeyError) as error:
                    run.update(status="needs_attention", reason="Report/translation verification failed: " + str(error))
                    job.update(status="pending", stage="translate", claim=None, error=str(error), error_kind="reports")
                    job["checkpoints"].pop("translate", None); job["checkpoints"].pop("verify", None)
                    self.save(original, state)
                    raise ValueError(run["reason"]) from error
                if stage == "verify":
                    require(now["merge"] == before["merge"], "Verification must not modify Merge")
                    job["status"] = "done"
                    run["finished_items"] += 1
                    job["glossary_baseline"] = {"glossary": now["glossary"], "merge_sha256": now["merge"]}
                    job.pop("review_scope", None)
                next_stage = "verify"
            final, final_issues = self.inputs(job)
            require(not final_issues and final == now, "Inputs changed during validation; re-read before retry")
            job["checkpoints"][stage] = checkpoint
            job.pop("review_glossary", None)
            job.pop("review_merge_sha256", None)
            job.update(stage=next_stage, claim=None)
            if job["status"] != "done": job["status"] = "pending"
            self.event(job, stage + ": " + receipt["summary"])
            self.save(original, state)
            return {"job_id": job_id, "status": job["status"], "next_stage": next_stage, "run_status": run["status"]}

    def fail(self, token, job_id, claim_token, reason, blocked=False, reports=False):
        require(isinstance(reason, str) and reason.strip(), "Failure needs reason")
        with self.locked():
            original, state = self.read(); run = self.active_run(state, token, finish=True)
            job = next((j for j in state["jobs"] if j["id"] == job_id), None)
            require(job and job["claim"] and job["claim"]["token"] == claim_token, "Stale job claim")
            status = "blocked" if blocked else "failed" if job["attempts"][job["stage"]] >= run["max_attempts"] else "pending"
            job.update(status=status, claim=None, error=reason, error_kind="reports" if reports else "decision" if blocked else "worker")
            if reports: run.update(status="needs_attention", reason=reason)
            self.event(job, reason); self.save(original, state)
            return {"job_id": job_id, "status": status, "run_status": run["status"]}

    def stop(self, token, reason, pause=False):
        require(reason.strip(), "Stop needs reason")
        with self.locked():
            original, state = self.read(); run = self.active_run(state, token, finish=True)
            for job in state["jobs"]:
                if job["claim"]:
                    job.update(status="pending", claim=None)
                    self.event(job, "Parent stopped/interrupted worker: " + reason)
            run.update(status="paused" if pause else "stopped", reason=reason)
            self.save(original, state)
            return run

    def retry(self, job_id):
        with self.locked():
            original, state = self.read(); self.v2(state)
            require(not any(j["claim"] for j in state["jobs"]) and (not state["run"] or state["run"]["status"] != "running"), "Stop run/workers before retry")
            job = next((j for j in state["jobs"] if j["id"] == job_id), None)
            require(job and job["status"] in ("blocked", "failed"), "Only blocked/failed jobs can be explicitly retried")
            self.rewind(job, "merge", "Explicit retry; current artifacts preserved")
            self.save(original, state)
            return {"job_id": job_id, "status": job["status"]}

    def status(self):
        _, state = self.read()
        return {"schema_version": state["schema_version"], "revision": state["revision"], "run": state["run"],
                "counts": {s: sum(j["status"] == s for j in state["jobs"]) for s in ("pending", "running", "done", "blocked", "failed")}, "jobs": state["jobs"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[4])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "migrate"): commands.add_parser(name)
    enqueue = commands.add_parser("enqueue"); enqueue.add_argument("scopes", nargs="+"); enqueue.add_argument("--recursive", action="store_true")
    start = commands.add_parser("start"); start.add_argument("--max-items", type=int, default=10); start.add_argument("--max-minutes", type=int, default=60); start.add_argument("--max-attempts", type=int, default=2); start.add_argument("--recover", action="store_true")
    claim = commands.add_parser("claim"); claim.add_argument("--run", required=True)
    for name in ("complete", "fail"):
        p = commands.add_parser(name); p.add_argument("--run", required=True); p.add_argument("--job", required=True); p.add_argument("--claim", required=True)
        if name == "complete": p.add_argument("--receipt", required=True, type=Path)
        else:
            p.add_argument("--reason", required=True); p.add_argument("--blocked", action="store_true"); p.add_argument("--reports", action="store_true")
    stop = commands.add_parser("stop"); stop.add_argument("--run", required=True); stop.add_argument("--reason", required=True); stop.add_argument("--pause", action="store_true")
    retry = commands.add_parser("retry"); retry.add_argument("--job", required=True)
    review = commands.add_parser("review"); review.add_argument("--job", required=True); review.add_argument("--context", type=int, default=0)
    args = parser.parse_args(); q = Queue(args.project_root)
    try:
        if args.command in ("init", "status", "migrate"): result = getattr(q, args.command)()
        elif args.command == "enqueue": result = q.enqueue(args.scopes, args.recursive)
        elif args.command == "start": result = q.start(args.max_items, args.max_minutes, args.max_attempts, args.recover)
        elif args.command == "claim": result = q.claim(args.run)
        elif args.command == "complete": result = q.complete(args.run, args.job, args.claim, json.loads(args.receipt.read_text(encoding="utf-8-sig")))
        elif args.command == "fail": result = q.fail(args.run, args.job, args.claim, args.reason, args.blocked, args.reports)
        elif args.command == "stop": result = q.stop(args.run, args.reason, args.pause)
        elif args.command == "review": result = q.review_packet(args.job, args.context)
        else: result = q.retry(args.job)
        print(json.dumps(result, ensure_ascii=True, indent=2)); return 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
