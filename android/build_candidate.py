"""Build-only Android candidate; never invokes adb, emulator, app, install or tests."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

EXPECTED_CERT_SHA256 = "21a38b89d9a315aee7028d25324fe4fd30ff40c97d4708310ae43ba670d74cd2"
EXPECTED_PACKAGE = "com.stellasora.viethoa.localadb"


def parse_gradle_version(app_gradle: Path):
    text = app_gradle.read_text(encoding="utf8")
    code_match = re.search(r"\bversionCode\s+(\d+)\b", text)
    name_match = re.search(r"\bversionName\s+['\"]([^'\"]+)['\"]", text)
    if not code_match or not name_match:
        raise SystemExit("Unable to parse versionCode/versionName from app/build.gradle")
    return int(code_match.group(1)), name_match.group(1)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parent
    project = root.parent
    gradle_version_code, gradle_version_name = parse_gradle_version(root / "app/build.gradle")

    parser = argparse.ArgumentParser(description="Build and statically verify Android Local ADB Launcher APK candidate.")
    parser.add_argument("--revision", default="r04", help="Candidate revision suffix (e.g. r04)")
    parser.add_argument("--version-name", default=gradle_version_name, help="Expected versionName for output APK filename")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing candidate in the same revision folder")
    args = parser.parse_args()

    rev = args.revision.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", rev):
        raise SystemExit(f"Invalid revision: {rev}")
    version_name = args.version_name.strip()
    if version_name != gradle_version_name:
        raise SystemExit(f"--version-name ({version_name}) does not match app/build.gradle versionName ({gradle_version_name})")

    work = project / f"work/build_android_launcher_{rev}"
    report = project / f"reports/android_launcher_candidate_{rev}"
    dist = project / f"dist/android_launcher_candidate_{rev}"
    gradle_out = work / "gradle-output"

    gradle = Path(r"C:\Users\chann\.gradle\wrapper\dists\gradle-9.3.1-all\9ot9r568e8zfvvd4mn8rbu1j0\gradle-9.3.1\bin\gradle.bat")
    jbr = Path(r"C:\Program Files\Android\Android Studio\jbr")
    sdk = Path(r"C:\Users\chann\AppData\Local\Android\Sdk")
    shared = Path(r"C:\Users\chann\.gradle\caches")

    for folder in (work, report, dist, work / "tmp", work / "gradle-home", work / "android-user", gradle_out):
        folder.mkdir(parents=True, exist_ok=True)

    # Seed isolated gradle-home with offline AGP 9.1.0 / Kotlin 2.2.10 modules-2 cache (read-only copy, skipping lockfiles)
    seed_modules = project / "work/build_android_v110/gradle-home/caches/modules-2"
    target_modules = work / "gradle-home/caches/modules-2"
    if seed_modules.is_dir() and not (target_modules / "files-2.1").is_dir():
        target_modules.mkdir(parents=True, exist_ok=True)
        for sub in seed_modules.iterdir():
            if sub.is_dir() and (sub.name == "files-2.1" or sub.name.startswith("metadata-")):
                shutil.copytree(sub, target_modules / sub.name, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.lock"))

    output = dist / f"StellaSora-Android_v{version_name}.apk"
    if output.exists() and not args.overwrite:
        raise SystemExit("Delivered candidate exists; choose a new revision or pass --overwrite.")

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
        f"-PstellaBuildOut={gradle_out}",
        "assembleDebug",
    ]

    (report / "BUILD_ENVIRONMENT.json").write_text(
        json.dumps({
            "revision": rev,
            "version_name": version_name,
            "version_code": gradle_version_code,
            "java_home": str(jbr),
            "sdk_read_only": str(sdk),
            "gradle": str(gradle),
            "shared_dependency_cache_read_only": str(shared),
            "isolated_gradle_home": str(work / "gradle-home"),
            "gradle_output_dir": str(gradle_out),
            "tests": "not_run_by_builder_root_device_tests_pending",
            "devices_or_apps_executed": False,
        }, indent=2),
        encoding="utf8",
    )

    started = time.time()
    with (report / "build.log").open("w", encoding="utf8") as log:
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", subprocess.list2cmdline(command)],
            cwd=root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    if result.returncode:
        tail = (report / "build.log").read_text(encoding="utf8", errors="replace")[-4000:]
        sys.stderr.write(tail + "\n")
        raise SystemExit(result.returncode)

    assembled = gradle_out / "app/outputs/apk/debug/app-debug.apk"
    if not assembled.is_file():
        raise SystemExit("Gradle returned without expected APK at " + str(assembled))
    shutil.copy2(assembled, output)

    # Static APK/signature accounting is packaging evidence, not device testing.
    verify = [str(sdk / "build-tools/36.0.0/apksigner.bat"), "verify", "--verbose", "--print-certs", str(output)]
    verified = subprocess.run(
        ["cmd.exe", "/d", "/c", subprocess.list2cmdline(verify)],
        env=env,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf8",
        errors="replace",
    )
    (report / "APK_SIGNATURE.txt").write_text(verified.stdout, encoding="utf8")

    badging = subprocess.run(
        [str(sdk / "build-tools/36.0.0/aapt2.exe"), "dump", "badging", str(output)],
        env=env,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf8",
        errors="replace",
    )
    (report / "APK_METADATA.txt").write_text(badging.stdout, encoding="utf8")

    cert_ok = verified.returncode == 0 and EXPECTED_CERT_SHA256 in verified.stdout.lower()
    expected_badging = f"package: name='{EXPECTED_PACKAGE}' versionCode='{gradle_version_code}' versionName='{version_name}'"
    badging_ok = badging.returncode == 0 and expected_badging in badging.stdout

    apk_sha = sha(output)
    apk_bytes = output.stat().st_size

    dist_top_copy = project / f"dist/StellaSora-Android_v{version_name}.apk"
    bin_copy = root / "bin/StellaSora_VietHoa.apk"
    copied_targets = []
    if cert_ok and badging_ok:
        bin_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, dist_top_copy)
        shutil.copy2(output, bin_copy)
        if sha(dist_top_copy) != apk_sha or sha(bin_copy) != apk_sha:
            raise SystemExit("Copied APK SHA256 mismatch.")
        copied_targets = [str(dist_top_copy), str(bin_copy)]

    receipt = {
        "revision": rev,
        "version_name": version_name,
        "version_code": gradle_version_code,
        "command": command,
        "working_directory": str(root),
        "build_exit_code": result.returncode,
        "duration_seconds": round(time.time() - started, 2),
        "apk": str(output),
        "copied_targets": copied_targets,
        "bytes": apk_bytes,
        "sha256": apk_sha,
        "signature_read_exit_code": verified.returncode,
        "signature_cert_sha256_verified": cert_ok,
        "expected_cert_sha256": EXPECTED_CERT_SHA256,
        "metadata_read_exit_code": badging.returncode,
        "badging_verified": badging_ok,
        "expected_badging": expected_badging,
        "keystore": str(root / "signing/candidate-debug.keystore"),
        "keystore_sha256": sha(root / "signing/candidate-debug.keystore"),
        "runtime_adb_keys": "created privately per app only at runtime; no host copy",
        "tests": "not_run_by_builder_root_device_tests_pending",
        "app_apk_emulator_or_device_executed": False,
        "installed": False,
        "published": False,
    }
    (report / "BUILD_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf8")
    (dist / "SHA256SUMS.txt").write_text(apk_sha + " *" + output.name + "\n", encoding="utf8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    if not cert_ok or not badging_ok:
        raise SystemExit("Packaging metadata/signature verification failed; inspect reports.")


if __name__ == "__main__":
    main()
