#!/usr/bin/env python3
"""Verify preparation artifacts and exercise the CLI using temporary synthetic data."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import localize as loc


def run_cli(arguments, expected=0):
    process = subprocess.run([sys.executable, str(loc.PROJECT / "tools/localize.py"), *arguments],
                             cwd=loc.PROJECT, capture_output=True, encoding="utf-8", errors="replace")
    result = {"arguments": arguments, "exit_code": process.returncode,
              "expected_exit_code": expected, "stdout": process.stdout, "stderr": process.stderr}
    if process.returncode != expected:
        raise ValueError("CLI result mismatch: " + json.dumps(result))
    return result


def smoke_cli():
    base = loc.PROJECT / "work"
    base.mkdir(exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="synthetic_verify_", dir=base) as folder:
        temp = Path(folder).resolve()
        if temp.parent != base.resolve():
            raise ValueError("Temporary workspace escaped verification root")
        relative = temp.relative_to(loc.PROJECT).as_posix()
        game = temp / "synthetic_game"
        source = game / "Persistent_Store/Videos/example.srt"
        source.parent.mkdir(parents=True)
        original = b'1\r\n00:00:00,000 --> 00:00:01,000\r\nHello {name}!\r\n\r\n'
        source.write_bytes(original)
        catalog = relative + "/catalog.jsonl"
        proposal = relative + "/proposal.json"
        review = relative + "/review.json"
        results.append(run_cli(["extract-srt", "--game-root", str(game), "--out", catalog]))
        results.append(run_cli(["batch", "--catalog", catalog, "--batch-id", "SYNTHETIC_ONLY", "--out", proposal]))
        results.append(run_cli(["audit", "--catalog", catalog, "--proposal", proposal,
                                "--out", relative + "/empty_audit.json"], expected=2))
        p = loc.read(loc.PROJECT / proposal)
        p["translator"] = "synthetic-cli-fixture-translator"
        p["entries"][0]["text_vi"] = "Chào {name}!"
        (loc.PROJECT / proposal).write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
        results.append(run_cli(["audit", "--catalog", catalog, "--proposal", proposal,
                                "--out", relative + "/audit.json"]))
        results.append(run_cli(["review-template", "--catalog", catalog, "--proposal", proposal, "--out", review]))
        r = loc.read(loc.PROJECT / review)
        if r["independent"] is not False or any(d["status"] != "pending" for d in r["decisions"]):
            raise ValueError("Review template must not auto-approve")
        results.append(run_cli(["merge", "--catalog", catalog, "--proposal", proposal,
                                "--review", review, "--out", relative + "/must_not_exist.json"], expected=2))
        if (temp / "must_not_exist.json").exists():
            raise ValueError("Pending review incorrectly produced merged artifact")
        # This is ONLY a gate fixture; no real game row is approved by this script.
        r["reviewer"] = "synthetic-cli-fixture-reviewer"
        r["independent"] = True
        for d in r["decisions"]:
            d.update(status="approved", rationale="SYNTHETIC TEST ONLY", evidence="Synthetic fixture in verify_setup.py")
        (loc.PROJECT / review).write_text(json.dumps(r), encoding="utf-8")
        results.append(run_cli(["merge", "--catalog", catalog, "--proposal", proposal,
                                "--review", review, "--out", relative + "/merged.json"]))
        results.append(run_cli(["build-srt", "--game-root", str(game), "--catalog", catalog,
                                "--proposal", proposal, "--review", review, "--out", relative + "/candidate"]))
        if source.read_bytes() != original:
            raise ValueError("Synthetic source was modified")
        candidate = temp / "candidate/files/Persistent_Store/Videos/example.srt"
        _, cues = loc.parse_srt(candidate.read_bytes())
        if cues[0]["text"] != "Chào {name}!":
            raise ValueError("CLI readback mismatch")
        results.append(run_cli(["diff-sources", "--old", catalog, "--new", catalog,
                                "--out", relative + "/diff.json"]))
        if loc.read(temp / "diff.json")["counts"]["unchanged"] != 1:
            raise ValueError("Source diff mismatch")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = loc.output_path(args.out)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                           cwd=loc.PROJECT, capture_output=True, encoding="utf-8", errors="replace")
    cli_results = smoke_cli()
    catalog = loc.PROJECT / "work/source/subtitles_persistent_20261019.jsonl"
    rows = loc.load_catalog(catalog)
    batches = []
    ids = []
    for p in sorted((loc.PROJECT / "work/batches").glob("SRT00*.json")):
        data = loc.read(p)
        if data["catalog_sha256"] != loc.digest_file(catalog):
            raise ValueError("Batch catalog hash mismatch")
        ids.extend(e["id"] for e in data["entries"])
        batches.append({"path": p.relative_to(loc.PROJECT).as_posix(), "sha256": loc.digest_file(p),
                        "entries": len(data["entries"]), "translated": sum(bool(e["text_vi"]) for e in data["entries"])})
    if len(ids) != len(set(ids)) or set(ids) != {r["id"] for r in rows}:
        raise ValueError("Prepared batches must cover source catalog exactly once")
    roundtrips = []
    for folder in ["Persistent_Store/Videos", "StellaSora_Data/StreamingAssets/InstallResource"]:
        for p in sorted((loc.PROJECT.parent / folder).glob("*.srt")):
            raw = p.read_bytes()
            _, cues = loc.parse_srt(raw)
            if loc.render_srt(raw, {c["index"]: c["text"] for c in cues}) != raw:
                raise ValueError("Real SRT no-op roundtrip failed")
            roundtrips.append({"path": p.relative_to(loc.PROJECT.parent).as_posix(),
                               "sha256": loc.digest_bytes(raw), "cues": len(cues), "byte_identical_noop": True})
    old = {r["path"]: r for r in loc.read(args.baseline)["files"]}
    current = loc.inventory(loc.PROJECT.parent)
    new = {r["path"]: r for r in current["files"]}
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    removed, added = sorted(old.keys() - new.keys()), sorted(new.keys() - old.keys())
    report = {"schema": 1, "created_utc": loc.now(), "pass_scope": "preparation_tooling_and_srt_readonly",
              "independent_qa": False, "semantic_review": "not_performed", "runtime": "not_tested",
              "tests": {"exit_code": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr},
              "cli_smoke": cli_results, "source_catalog_sha256": loc.digest_file(catalog),
              "source_cues": len(rows), "source_file_counts": dict(Counter(r["source_path"] for r in rows)),
              "batches": batches, "real_srt_roundtrips": roundtrips,
              "preservation": {"metadata_files_checked": len(new), "sha256_files_checked": sum("sha256" in r for r in new.values()),
                               "changed": changed, "removed": removed, "added": added},
              "passed": tests.returncode == 0 and not changed and not removed and not added}
    inventory_out = loc.output_path(str(Path(args.out).with_name(out.stem + "_inventory.json")))
    loc.save(inventory_out, current)
    loc.save(out, report)
    print(json.dumps({"passed": report["passed"], "report": str(out), "source_cues": len(rows),
                      "real_srt_files": len(roundtrips), "cli_checks": len(cli_results),
                      "preservation": report["preservation"]}, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
