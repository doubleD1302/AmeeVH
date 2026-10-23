import json
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\STATUS.json")
data = json.loads(p.read_text(encoding="utf-8"))

data["updated_local_date"] = "2026-10-23"
data["preparation_validation"]["unit_tests_passed"] = 48
data["preparation_validation"]["unit_tests_total"] = 48

data["texture_localization"] = {
    "run_id": "texture_vi_20261023_candidate_v096",
    "source_client_game_version": "2.0.0",
    "resource_version": "2610201624",
    "bundle_names_indexed": 219,
    "texture_objects_indexed": 1276,
    "sprite_objects_indexed": 1322,
    "total_png_vi_audited": 842,
    "safe_patchable_textures": 53,
    "safe_patchable_bundles": 16,
    "pending_atlas_sprites": 314,
    "pending_tight_mesh_sprites": 466,
    "candidate_zip": "staging/texture_candidate_v096/StellaSora_AssetBundles_VI.zip",
    "candidate_zip_sha256": "baec3ee93d9800a2959c9a8470edb037218c7c48c2cb220dee9b514a9aadc60d",
    "candidate_manifest": "staging/texture_candidate_v096/patch_manifest.json",
    "candidate_manifest_sha256": "1d8f24fddaa198d022ea16104c9955faef374e2a149a4e3fa38e9ee208159670",
    "report": "reports/TEXTURE_INTEGRATION_CANDIDATE_V096.md",
    "audit_file": "work/textures/texture_mapping_audit.json",
    "remaining_scope": "Honor Titles, Logos, and Event Banners kept in PENDING due to tight-mesh polygon geometry and BC7 atlas regional isolation rules.",
    "installed": False,
    "runtime": "not_tested",
    "published": False
}

data["launcher_pc"] = "launcher/launcher_pc.py (v0.9.6: Manifest-verified sync, SHA256 integrity check, path traversal guard, allowlist check, atomic replace on same volume, rollback journal, and accurate scope reporting)"

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Updated STATUS.json successfully")
