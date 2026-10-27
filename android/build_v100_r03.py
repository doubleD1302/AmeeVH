#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Android APK v1.0.0 (versionCode 4) with Developer Mode auto-detection and teleport feature.
"""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
project = root.parent
work = project / "work" / "build_android_v100_r03"
dist = project / "dist"

gradle = Path(r"C:\Users\chann\.gradle\wrapper\dists\gradle-9.3.1-all\9ot9r568e8zfvvd4mn8rbu1j0\gradle-9.3.1\bin\gradle.bat")
jbr = Path(r"C:\Program Files\Android\Android Studio\jbr")
sdk = Path(r"C:\Users\chann\AppData\Local\Android\Sdk")
shared = Path(r"C:\Users\chann\.gradle\caches")

for folder in (work, work / "tmp", work / "gradle-home", work / "android-user"):
    folder.mkdir(parents=True, exist_ok=True)

env = dict(os.environ)
env.update({
    "JAVA_HOME": str(jbr),
    "ANDROID_HOME": str(sdk),
    "ANDROID_SDK_ROOT": str(sdk),
    "ANDROID_USER_HOME": str(work / "android-user"),
    "GRADLE_USER_HOME": str(work / "gradle-home"),
    "GRADLE_RO_DEP_CACHE": str(shared),
    "TMP": str(work / "tmp"),
    "TEMP": str(work / "tmp"),
})

command = [
    str(gradle),
    "--offline",
    "--no-daemon",
    "--max-workers=2",
    "--gradle-user-home",
    str(work / "gradle-home"),
    "--project-cache-dir",
    str(work / "project-cache"),
    "assembleDebug",
]

print("=== BẮT ĐẦU BIÊN DỊCH APK V1.0.0 (VERSIONCODE 4) ===")
started = time.time()
result = subprocess.run(
    ["cmd.exe", "/d", "/c", subprocess.list2cmdline(command)],
    cwd=root,
    env=env,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)

if result.returncode != 0:
    print(f"Lỗi biên dịch Gradle (code {result.returncode}):")
    print(result.stdout[-2000:])
    print(result.stderr[-2000:])
    sys.exit(result.returncode)

assembled = project / "work" / "build_android_launcher_r02" / "gradle-output" / "app" / "outputs" / "apk" / "debug" / "app-debug.apk"
if not assembled.is_file():
    candidates = list(project.glob("work/**/app-debug.apk"))
    if candidates:
        assembled = candidates[0]
    else:
        print("Không tìm thấy app-debug.apk được xuất.")
        sys.exit(1)

print(f"Biên dịch Gradle thành công trong {time.time()-started:.2f}s! ({assembled.stat().st_size:,} bytes)")

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

out_apk_dist = dist / "StellaSora-Android_v1.0.2.apk"
out_apk_legacy = dist / "StellaSora_VietHoa.apk"
shutil.copy2(assembled, out_apk_dist)
shutil.copy2(assembled, out_apk_legacy)

# Verify signature
verify = [str(sdk / "build-tools/36.0.0/apksigner.bat"), "verify", "--verbose", "--print-certs", str(out_apk_dist)]
verified = subprocess.run(verify, capture_output=True, text=True, encoding="utf-8", errors="replace")
print("Kết quả kiểm tra chữ ký apksigner:", "THÀNH CÔNG" if verified.returncode == 0 else "THẤT BẠI")

# Dump badging
badging = subprocess.run(
    [str(sdk / "build-tools/36.0.0/aapt2.exe"), "dump", "badging", str(out_apk_dist)],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
lines = [l for l in badging.stdout.splitlines() if l.startswith("package:")]
if lines:
    print("Metadata APK:", lines[0])

apk_sha = sha(out_apk_dist)
apk_size = out_apk_dist.stat().st_size
print(f"APK Size: {apk_size:,} bytes")
print(f"APK SHA256: {apk_sha}")

# Update android_localadb_launcher.json
launcher_json_path = dist / "android_localadb_launcher.json"
launcher_data = json.loads(launcher_json_path.read_text(encoding="utf-8"))
launcher_data["version_code"] = 6
launcher_data["version_name"] = "1.0.2"
launcher_data["size"] = apk_size
launcher_data["sha256"] = apk_sha
launcher_data["download_url"] = "https://github.com/doubleD1302/AmeeVH/releases/download/v1.0.2/StellaSora-Android_v1.0.2.apk"
launcher_json_path.write_text(json.dumps(launcher_data, indent=2, ensure_ascii=False), encoding="utf-8")
print("Đã cập nhật android_localadb_launcher.json với versionCode: 6 (v1.0.2)!")

print("\n=== HOÀN TẤT BIÊN DỊCH VÀ XÁC THỰC APK V1.0.0 (CODE 4)! ===")
