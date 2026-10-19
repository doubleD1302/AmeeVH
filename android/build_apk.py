#!/usr/bin/env python3
"""Builds StellaSora_VietHoa.apk using local Android SDK build-tools 36.0.0 and Java."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

SDK_ROOT = Path(r"C:\Users\chann\AppData\Local\Android\Sdk")
BUILD_TOOLS = SDK_ROOT / "build-tools" / "36.0.0"
PLATFORM_JAR = SDK_ROOT / "platforms" / "android-35" / "android.jar"

AAPT2 = BUILD_TOOLS / "aapt2.exe"
D8 = BUILD_TOOLS / "d8.bat"
ZIPALIGN = BUILD_TOOLS / "zipalign.exe"
APKSIGNER = BUILD_TOOLS / "apksigner.bat"


def get_keytool():
    candidates = [
        Path(r"C:\Program Files\Java\jdk-25.0.2\bin\keytool.exe"),
        Path(os.environ.get("JAVA_HOME", "")) / "bin" / "keytool.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("keytool")
    if found:
        return found
    # Search in C:\Program Files\Java
    java_dir = Path(r"C:\Program Files\Java")
    if java_dir.exists():
        for k in java_dir.rglob("keytool.exe"):
            return str(k)
    return "keytool"


BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "app" / "src" / "main"
RES_DIR = SRC_DIR / "res"
JAVA_DIR = SRC_DIR / "java"
MANIFEST = SRC_DIR / "AndroidManifest.xml"

OUT_DIR = BASE_DIR / "build"
BIN_DIR = BASE_DIR / "bin"


def run(cmd, cwd=None):
    cmd_str = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    print(f"-> {cmd_str}")
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(f"ERROR ({proc.returncode}):\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}")
        raise RuntimeError(f"Command failed: {cmd[0]}")
    return proc.stdout


def main():
    print("=== Bắt đầu đóng gói StellaSora_VietHoa.apk ===")
    if not AAPT2.exists() or not PLATFORM_JAR.exists():
        print("Lỗi: Không tìm thấy Android SDK build-tools hoặc android.jar.")
        return 1

    shutil.rmtree(OUT_DIR, ignore_errors=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    compiled_res_zip = OUT_DIR / "compiled_res.zip"
    gen_dir = OUT_DIR / "gen"
    classes_dir = OUT_DIR / "classes"
    gen_dir.mkdir(parents=True, exist_ok=True)
    classes_dir.mkdir(parents=True, exist_ok=True)

    # 1. aapt2 compile
    print("1. Biên dịch tài nguyên (aapt2 compile)...")
    run([str(AAPT2), "compile", "--dir", str(RES_DIR), "-o", str(compiled_res_zip)])

    # 2. aapt2 link
    print("2. Liên kết tài nguyên (aapt2 link)...")
    unaligned_apk = OUT_DIR / "unaligned.apk"
    run([
        str(AAPT2), "link",
        "-I", str(PLATFORM_JAR),
        "--manifest", str(MANIFEST),
        "--java", str(gen_dir),
        "-o", str(unaligned_apk),
        str(compiled_res_zip),
        "--auto-add-overlay"
    ])

    # 3. javac
    print("3. Biên dịch mã nguồn Java (javac)...")
    java_files = list(JAVA_DIR.rglob("*.java")) + list(gen_dir.rglob("*.java"))
    run([
        "javac",
        "-source", "8",
        "-target", "8",
        "-bootclasspath", str(PLATFORM_JAR),
        "-d", str(classes_dir),
        *[str(f) for f in java_files]
    ])

    # 4. d8 (dex)
    print("4. Chuyển đổi mã máy ảo Android DEX (d8)...")
    class_files = list(classes_dir.rglob("*.class"))
    run([
        str(D8),
        "--release",
        "--lib", str(PLATFORM_JAR),
        "--output", str(OUT_DIR),
        *[str(f) for f in class_files]
    ])

    dex_file = OUT_DIR / "classes.dex"
    if not dex_file.exists():
        raise FileNotFoundError("D8 did not produce classes.dex")

    # 5. Thêm classes.dex vào unaligned apk
    print("5. Nhúng classes.dex vào gói APK...")
    with zipfile.ZipFile(unaligned_apk, "a") as z:
        z.write(dex_file, "classes.dex")

    # 6. zipalign
    print("6. Tối ưu hóa phân vùng bộ nhớ (zipalign)...")
    aligned_apk = OUT_DIR / "aligned.apk"
    run([str(ZIPALIGN), "-f", "4", str(unaligned_apk), str(aligned_apk)])

    # 7. Tạo debug keystore nếu chưa có
    keystore = BASE_DIR / "debug.keystore"
    if not keystore.exists():
        print("Tạo debug keystore tạm thời...")
        run([
            get_keytool(), "-genkeypair",
            "-keystore", str(keystore),
            "-storepass", "android",
            "-alias", "androiddebugkey",
            "-keypass", "android",
            "-dname", "CN=StellaSora, OU=VietHoa, O=Dev, C=VN",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000"
        ])

    # 8. Ký APK (apksigner)
    final_apk = BIN_DIR / "StellaSora_VietHoa.apk"
    print("7. Ký số APK (apksigner)...")
    run([
        str(APKSIGNER), "sign",
        "--ks", str(keystore),
        "--ks-pass", "pass:android",
        "--ks-key-alias", "androiddebugkey",
        "--key-pass", "pass:android",
        "--out", str(final_apk),
        str(aligned_apk)
    ])

    print(f"\n🎉 THÀNH CÔNG! Đã tạo gói APK: {final_apk}")
    print(f"Kích thước: {final_apk.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
