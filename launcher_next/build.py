"""Build script to package StellaSora_Launcher into standalone EXE candidate."""

import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_candidate():
    launcher_next_dir = Path(__file__).resolve().parent
    project_root = launcher_next_dir.parent
    dist_candidate_dir = project_root / "dist" / "launcher_ui_candidate_r01"
    work_build_dir = project_root / "work" / "build_temp"

    dist_candidate_dir.mkdir(parents=True, exist_ok=True)
    work_build_dir.mkdir(parents=True, exist_ok=True)

    spec_file = launcher_next_dir / "StellaSora_Launcher.spec"
    assert spec_file.is_file(), f"Spec file not found: {spec_file}"

    pyinstaller_exe = project_root / ".venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_exe.is_file():
        pyinstaller_exe = Path(sys.executable).parent / "pyinstaller.exe"

    logging.info(f"Using PyInstaller: {pyinstaller_exe}")
    logging.info(f"Spec file: {spec_file}")
    logging.info(f"Target dist directory: {dist_candidate_dir}")

    cmd = [
        str(pyinstaller_exe),
        "--noconfirm",
        "--clean",
        "--distpath", str(dist_candidate_dir),
        "--workpath", str(work_build_dir),
        str(spec_file)
    ]

    logging.info("Starting PyInstaller compilation...")
    res = subprocess.run(cmd, cwd=str(project_root))
    if res.returncode != 0:
        logging.error(f"Build failed with exit code: {res.returncode}")
        sys.exit(res.returncode)

    target_exe = dist_candidate_dir / "StellaSora_Launcher.exe"
    assert target_exe.is_file(), f"Output executable missing: {target_exe}"

    exe_size_mb = target_exe.stat().st_size / (1024 * 1024)
    exe_hash = sha256_file(target_exe)
    logging.info(f"✓ Standalone EXE successfully built: {target_exe}")
    logging.info(f"  Size: {exe_size_mb:.2f} MB")
    logging.info(f"  SHA256: {exe_hash}")

    # Generate SHA256SUMS.txt in candidate directory
    sums_file = dist_candidate_dir / "SHA256SUMS.txt"
    sums_file.write_text(f"{exe_hash} *StellaSora_Launcher.exe\n", encoding="utf-8")
    logging.info(f"Wrote checksum file: {sums_file}")

    # Clean up work build directory
    shutil.rmtree(work_build_dir, ignore_errors=True)
    logging.info("Cleaned temporary build cache.")


if __name__ == "__main__":
    build_candidate()
