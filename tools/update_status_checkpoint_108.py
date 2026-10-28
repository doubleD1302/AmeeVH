# -*- coding: utf-8 -*-
import json
from pathlib import Path

# Update STATUS.json
status_p = Path("STATUS.json")
status = json.loads(status_p.read_text(encoding="utf-8"))
status["updated_local_date"] = "2026-10-29"
status["launcher_pc"] = "dist/StellaSora-Windows_v1.0.8.exe (v1.0.8: In-app seamless auto-update, Windows atomic rename file-lock bypass, parent PID termination, SHA256 integrity check)"
status["android_apk"] = "dist/StellaSora-Android_v1.0.8.apk (v1.0.8, versionCode 10: In-app seamless auto-update, local ADB pairing/connect, resource_version wildcard support)"
status["current_release"] = "v1.0.8"
status["pronoun_gender_fix"] = "completed_and_verified_gender_neutral"
status_p.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Updated STATUS.json")

# Update CHECKPOINT.json
checkpoint_p = Path("CHECKPOINT.json")
checkpoint = json.loads(checkpoint_p.read_text(encoding="utf-8"))
checkpoint["updated_local_date"] = "2026-10-29"
checkpoint["phase"] = "PHASE_RELEASE_V108_PRONOUN_AND_TERMINOLOGY_CONSISTENCY_DEPLOYED"
checkpoint_p.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Updated CHECKPOINT.json")
