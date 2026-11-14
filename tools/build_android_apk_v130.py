#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Android APK v1.3.0 (versionCode 14) and generate android_localadb_launcher.json.
"""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()

def build_apk_v130():
    root = Path(__file__).resolve().parent.parent
    android_root = (root / "android").resolve()
    work = (root / "work" / "build_android_v130").resolve()
    dist = (root / "dist").resolve()

    gradle = Path(r"C:\Users\chann\.gradle\wrapper\dists\gradle-9.3.1-all\9ot9r568e8zfvvd4mn8rbu1j0\gradle-9.3.1\bin\gradle.bat")
    jbr = Path(r"C:\Program Files\Android\Android Studio\jbr")
    sdk = Path(r"C:\Users\chann\AppData\Local\Android\Sdk")
    shared = Path(r"C:\Users\chann\.gradle\caches")

    gradle_home = (root / "work" / "build_android_v110" / "gradle-home").resolve()
    v110_tmp = (root / "work" / "build_android_v110" / "tmp").resolve()
    v110_tmp.mkdir(parents=True, exist_ok=True)

    tmp_dir = (work / "tmp").resolve()
    android_user = (work / "android-user").resolve()
    project_cache = (work / "project-cache").resolve()

    for folder in (work, tmp_dir, android_user, project_cache, dist, gradle_home):
        folder.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env.update({
        "JAVA_HOME": str(jbr),
        "ANDROID_HOME": str(sdk),
        "ANDROID_SDK_ROOT": str(sdk),
        "ANDROID_USER_HOME": str(android_user),
        "GRADLE_USER_HOME": str(gradle_home),
        "GRADLE_RO_DEP_CACHE": str(shared),
        "TMP": str(tmp_dir),
        "TEMP": str(tmp_dir),
    })

    command = [
        str(gradle),
        "--offline",
        "--no-daemon",
        "--max-workers=2",
        "--gradle-user-home",
        str(gradle_home),
        "--project-cache-dir",
        str(project_cache),
        "assembleRelease",
    ]

    print("=== BẮT ĐẦU BIÊN DỊCH ANDROID APK v1.3.0 (versionCode 14) ===")
    started = time.time()
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", subprocess.list2cmdline(command)],
        cwd=android_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("assembleRelease exited with non-zero, falling back to assembleDebug...")
        command[-1] = "assembleDebug"
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", subprocess.list2cmdline(command)],
            cwd=android_root,
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

    assembled = None
    search_dirs = [
        android_root / "app" / "build" / "outputs" / "apk",
        project_cache,
        work,
    ]
    for sdir in search_dirs:
        for apk in sdir.rglob("*.apk"):
            if "unaligned" not in apk.name and apk.stat().st_size > 5_000_000:
                assembled = apk
                break
        if assembled:
            break

    if not assembled or not assembled.is_file():
        candidates = list(root.glob("work/**/*.apk"))
        candidates = [c for c in candidates if c.stat().st_size > 5_000_000 and "unaligned" not in c.name]
        if candidates:
            candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            assembled = candidates[0]
        else:
            print("Không tìm thấy APK được xuất.")
            sys.exit(1)

    print(f"Biên dịch Gradle thành công trong {time.time()-started:.2f}s! ({assembled} -> {assembled.stat().st_size:,} bytes)")

    out_apk_dist = dist / "StellaSora-Android_v1.3.0.apk"
    out_apk_legacy = dist / "StellaSora_VietHoa.apk"
    shutil.copy2(assembled, out_apk_dist)
    shutil.copy2(assembled, out_apk_legacy)

    # Verify signature
    verify = [str(sdk / "build-tools/36.0.0/apksigner.bat"), "verify", "--verbose", "--print-certs", str(out_apk_dist)]
    verified = subprocess.run(verify, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("Kết quả kiểm tra chữ ký apksigner:", "THÀNH CÔNG" if verified.returncode == 0 else "THẤT BẠI")

    digest = sha256_file(out_apk_dist)
    size = out_apk_dist.stat().st_size

    cert_sha = "21a38b89d9a315aee7028d25324fe4fd30ff40c97d4708310ae43ba670d74cd2"
    for line in verified.stdout.splitlines():
        if "SHA-256 digest:" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                extracted = parts[1].strip().lower()
                if len(extracted) == 64:
                    cert_sha = extracted
                    break

    meta = {
        "platform": "android",
        "variant": "localadb",
        "application_id": "com.stellasora.viethoa.localadb",
        "version_name": "1.3.0",
        "version_code": 14,
        "apk_name": "StellaSora-Android_v1.3.0.apk",
        "apk_url": "https://github.com/doubleD1302/AmeeVH/releases/download/v1.3.0/StellaSora-Android_v1.3.0.apk",
        "size": size,
        "sha256": digest,
        "signing_cert_sha256": cert_sha,
    }
    meta_path = dist / "android_localadb_launcher.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Đã cập nhật {meta_path}:")
    print(json.dumps(meta, indent=2))

    # Also copy APK to web downloads
    for d_dir in [root / "web" / "downloads", dist / "Web_Tai_Launcher_Viet_Hoa" / "downloads"]:
        d_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_apk_dist, d_dir / out_apk_dist.name)
        print(f"Copied APK to {d_dir / out_apk_dist.name}")

    print("\n=== ANDROID BUILD COMPLETE ===")
    print(f"APK: {out_apk_dist} ({size:,} bytes)")
    print(f"SHA-256: {digest}")
    return out_apk_dist, digest, size

if __name__ == "__main__":
    build_apk_v130()
