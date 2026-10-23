#!/usr/bin/env python3
"""Inventory local documentation work; never generate lore or review decisions."""
import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError("Duplicate JSON key: " + key)
            out[key] = value
        return out
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(path, parent):
    path = path.resolve()
    if not path.is_relative_to(parent.resolve()):
        raise ValueError("Path outside permitted directory: " + str(path))
    return path


def inventory(project, baseline):
    roster_file = baseline / "CHARACTER_ROSTER.json"
    profile_file = baseline / "CHARACTER_VOICE_PROFILES.json"
    roster = load(roster_file)
    profiles = load(profile_file)["profiles"]
    rows = roster["characters"]
    row_ids = [r["id"] for r in rows]
    profile_ids = [p["character_id"] for p in profiles]
    if len(row_ids) != len(set(row_ids)) or len(profile_ids) != len(set(profile_ids)):
        raise ValueError("Duplicate roster/profile ID; resolve before assigning work")
    by_id = {p["character_id"]: p for p in profiles}
    pending, preserved, excluded, unknown = [], [], [], []
    for row in rows:
        kind = row.get("record_kind")
        if kind == "character_or_variant_named_record":
            profile = by_id.get(row["id"])
            item = {"character_id": row["id"], "name_en": row["name_en"]}
            if profile is None:
                pending.append(dict(item, reason="missing_profile"))
            elif (profile.get("status") in ("source_grounded_editorial_draft", "documentation_reviewed")
                  and profile.get("observed_traits")
                  and all(t.get("evidence_refs") for t in profile["observed_traits"])):
                preserved.append(dict(item, status=profile["status"], reason="grounded_predecessor_candidate_not_review_verification"))
            else:
                pending.append(dict(item, status=profile.get("status"), reason="incomplete_or_unrecognized_status_requires_inspection"))
        elif kind in ("golem_named_record", "construct_or_non_playable_named_record"):
            excluded.append({"id": row["id"], "name_en": row["name_en"], "record_kind": kind})
        else:
            unknown.append({"id": row["id"], "name_en": row["name_en"], "record_kind": kind})
    issues = []
    outside_profiles = [p for p in profile_ids if p not in set(row_ids)]
    if outside_profiles:
        issues.append({"code": "PROFILE_NOT_IN_ROSTER", "ids": outside_profiles})
    if unknown:
        issues.append({"code": "UNKNOWN_ROSTER_KIND", "records": unknown})
    source_checks = []
    sources = roster.get("source_snapshot", {})
    if not sources:
        issues.append({"code": "MISSING_SOURCE_SNAPSHOT"})
    for name, item in sources.items():
        path = inside(project / item["path"], project)
        actual = digest(path) if path.is_file() else None
        matched = actual == item.get("sha256") and actual is not None
        source_checks.append({"source": name, "path": item["path"], "expected_sha256": item.get("sha256"), "actual_sha256": actual, "matched": matched})
        if not matched:
            issues.append({"code": "SOURCE_DRIFT_OR_MISSING", "source": name, "path": item["path"]})
    return {
        "schema": 1,
        "kind": "character_documentation_work_inventory",
        "scope": "inventory_only_not_semantic_or_review_approval",
        "project_root": str(project),
        "baseline_path": str(baseline.relative_to(project)).replace(chr(92), "/"),
        "baseline_hashes": {p.name: digest(p) for p in sorted(baseline.iterdir()) if p.is_file() and p.suffix in (".json", ".md")},
        "preflight_status": "ready_for_research" if not issues else "needs_source_or_scope_resolution",
        "counts": {"roster_records": len(rows), "character_or_variant_records": len(pending)+len(preserved), "target_pending": len(pending), "preserved_grounded_candidates": len(preserved), "excluded_constructs": len(excluded), "unresolved_roster_records": len(unknown), "glossary_only_names": len(roster.get("glossary_only_names", []))},
        "target_ids": [p["character_id"] for p in pending],
        "todo": pending,
        "preserved_predecessor_candidates": preserved,
        "excluded_constructs": excluded,
        "unresolved_roster_records": unknown,
        "glossary_only_names": roster.get("glossary_only_names", []),
        "source_checks": source_checks,
        "issues": issues,
        "approval_note": "This helper does not verify semantic claims, profile completeness or independent review. Inspect source/context and final review snapshots separately.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    if args.baseline_dir:
        baseline = args.baseline_dir if args.baseline_dir.is_absolute() else project / args.baseline_dir
    else:
        state = load(project / "STATUS.json")
        matrix = state.get("character_context_documents", {}).get("matrix")
        baseline = (project / matrix).parent if matrix else project / "work/character_context_20261023_r01"
    baseline = inside(baseline, project / "work")
    target = args.out if args.out.is_absolute() else project / args.out
    target = inside(target, project)
    if not any(target.is_relative_to(project / folder) for folder in ("work", "reports")):
        raise ValueError("Output must be a new file under project work/ or reports/")
    if target.suffix != ".json":
        raise ValueError("Output must be a JSON file")
    if target.exists():
        raise FileExistsError("Refusing to overwrite existing output: " + str(target))
    data = inventory(project, baseline)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(target), "preflight_status": data["preflight_status"], "counts": data["counts"]}, ensure_ascii=False))
    return 0 if not data["issues"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
