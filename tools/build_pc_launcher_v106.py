#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Stella Sora PC Launcher v1.0.6 with PyInstaller."""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import importlib.metadata
from pathlib import Path

def build_v106():
    root = Path(__file__).resolve().parent.parent
    src = root / "launcher"
    out = root / "dist" / "launcher_ui_candidate_v106"
    work = root / "work" / "build_launcher_ui_v106"
    report = root / "reports" / "launcher_ui_candidate_v106" / "implementer"
    cache = root / "work" / "launcher_qt_build_v106" / "pyinstaller-cache"

    for p in (out, work, report, cache):
        p.mkdir(parents=True, exist_ok=True)

    py_exec = str(root / ".venv" / "Scripts" / "python.exe")
    if not Path(py_exec).exists():
        py_exec = sys.executable

    print(f"Building PC launcher v1.0.6 with Python: {py_exec}")
    versions = {
        n: importlib.metadata.version(n)
        for n in (
            "PySide6",
            "PySide6_Essentials",
            "PySide6_Addons",
            "shiboken6",
            "PyInstaller",
            "pefile",
        )
    }
    print(f"Dependencies: {versions}")

    qt = Path(
        importlib.metadata.distribution("PySide6_Essentials").locate_file("PySide6")
    ).resolve()
    windows = Path(os.environ.get("SystemRoot", "C:/Windows")).resolve()

    path_allowlist = [
        windows / "System32",
        windows,
        Path(py_exec).resolve().parent,
        Path(sys.base_prefix).resolve(),
        Path(sys.base_prefix).resolve() / "DLLs",
        qt,
    ]

    env = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "QML2_IMPORT_PATH",
        "QML_IMPORT_PATH",
        "QT_DEBUG_PLUGINS",
        "CONDA_PREFIX",
        "CONDA_DEFAULT_ENV",
        "CONDA_DLL_SEARCH_MODIFICATION_ENABLE",
    ):
        env.pop(key, None)

    env.update(
        {
            "PATH": os.pathsep.join(str(p) for p in path_allowlist if p.is_dir()),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYINSTALLER_CONFIG_DIR": str(cache),
            "STELLA_PACKAGING_REPORT_DIR": str(report),
        }
    )

    command = [
        py_exec,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(out),
        "--workpath",
        str(work),
        str(src / "StellaSora_Launcher.spec"),
    ]

    print(f"Executing: {' '.join(command)}")
    r = subprocess.run(command, cwd=root, env=env)
    if r.returncode != 0:
        print(f"Build failed with exit code: {r.returncode}")
        sys.exit(r.returncode)

    exe = out / "StellaSora_Launcher.exe"
    if not exe.is_file():
        raise FileNotFoundError(f"Expected output EXE not found: {exe}")

    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    size = exe.stat().st_size
    (out / "SHA256SUMS.txt").write_text(f"{digest} *StellaSora_Launcher.exe\n", encoding="utf-8")

    receipt = {
        "command": command,
        "working_directory": str(root),
        "exit_code": r.returncode,
        "exe": str(exe),
        "bytes": size,
        "sha256": digest,
        "dependencies": versions,
        "version": "1.0.6",
    }
    (report / "BUILD_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    target_dist_exe = root / "dist" / "StellaSora-Windows_v1.0.6.exe"
    target_root_exe = root.parent / "StellaSora_Launcher.exe"
    target_dist_default = root / "dist" / "StellaSora_Launcher.exe"

    shutil.copy2(exe, target_dist_exe)
    shutil.copy2(exe, target_dist_default)
    print(f"Copied to {target_dist_exe} ({size:,} bytes, sha256: {digest})")

    try:
        shutil.copy2(exe, target_root_exe)
        print(f"Updated root launcher: {target_root_exe}")
    except Exception as e:
        print(f"Note: Could not overwrite root launcher directly: {e}")

    # Update dist/SHA256SUMS.txt
    sums_file = root / "dist" / "SHA256SUMS.txt"
    if sums_file.exists():
        lines = sums_file.read_text(encoding="utf-8").splitlines()
        new_lines = []
        replaced = False
        for line in lines:
            if "StellaSora-Windows_v1.0.6.exe" in line:
                new_lines.append(f"{digest}  StellaSora-Windows_v1.0.6.exe")
                replaced = True
            elif "StellaSora_Launcher.exe" in line:
                new_lines.append(f"{digest}  StellaSora_Launcher.exe")
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.insert(0, f"{digest}  StellaSora-Windows_v1.0.6.exe")
        sums_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"Updated {sums_file}")

    print("\n=== PC BUILD COMPLETE ===")
    print(f"Version: 1.0.6")
    print(f"Size: {size:,} bytes")
    print(f"SHA-256: {digest}")
    return target_dist_exe, digest, size

if __name__ == "__main__":
    build_v106()
