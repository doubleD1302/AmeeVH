import os
import hashlib
import json
from pathlib import Path

LIVE_DIR = Path('Persistent_Store/AssetBundles')
DIST_DIR = Path('StellaSora_VietHoa/dist/AssetBundles')
BACKUP_DIR = Path('StellaSora_VietHoa/backups/run_pre_pending_apply_20261023')
MANIFEST_PATH = Path('StellaSora_VietHoa/dist/patch_manifest.json')

def sha256_file(p):
    if not p.exists():
        return None, 0
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest(), p.stat().st_size

def reconcile_bundles():
    rq_path = Path('StellaSora_VietHoa/reports/full_localization_audit_20261026_r02/REVIEW_QUEUE.jsonl')
    bundle_items = []
    with open(rq_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            if item.get('domain') == 'texture_bundle':
                bundle_items.append(item.get('key'))

    print(f"Total target bundles to reconcile: {len(bundle_items)}")

    # Load patch_manifest if available
    manifest = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

    results = []
    for b_name in sorted(bundle_items):
        live_file = LIVE_DIR / b_name
        dist_file = DIST_DIR / b_name
        backup_file = BACKUP_DIR / b_name

        live_sha, live_size = sha256_file(live_file)
        dist_sha, dist_size = sha256_file(dist_file)
        backup_sha, backup_size = sha256_file(backup_file)

        manifest_entry = manifest.get('files', {}).get(b_name, {})

        results.append({
            "bundle_name": b_name,
            "live_installed": {
                "exists": live_file.exists(),
                "size": live_size,
                "sha256": live_sha
            },
            "dist_package": {
                "exists": dist_file.exists(),
                "size": dist_size,
                "sha256": dist_sha
            },
            "pre_patch_backup": {
                "exists": backup_file.exists(),
                "size": backup_size,
                "sha256": backup_sha
            },
            "manifest_record": manifest_entry,
            "diff_size_live_minus_dist": live_size - dist_size if (live_file.exists() and dist_file.exists()) else None,
            "match_dist": live_sha == dist_sha if (live_sha and dist_sha) else False,
            "match_backup": live_sha == backup_sha if (live_sha and backup_sha) else False
        })

    out_path = Path('StellaSora_VietHoa/work/batches/BUNDLE_DRIFT_DETAILED_RECONCILIATION.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Reconciliation written to {out_path}")
    print("\nSummary of 27 bundles:")
    print(f"{'Bundle Name':<40} | {'Live Size':<10} | {'Dist Size':<10} | {'Diff':<8} | {'Matches Backup?'}")
    print("-" * 85)
    for r in results:
        b = r['bundle_name']
        ls = r['live_installed']['size']
        ds = r['dist_package']['size']
        diff = r['diff_size_live_minus_dist']
        mb = "YES (ORIGINAL)" if r['match_backup'] else "NO (PATCHED/MODIFIED)"
        print(f"{b:<40} | {ls:<10} | {ds:<10} | {diff:<8} | {mb}")

if __name__ == '__main__':
    reconcile_bundles()
