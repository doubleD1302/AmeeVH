"""Isolated deterministic PyInstaller --onefile builder for Stella Sora Launcher v2.0."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_BUILD_PACKAGES = (
    "PySide6",
    "PySide6_Essentials",
    "PySide6_Addons",
    "shiboken6",
    "PyInstaller",
    "pefile",
    "Pillow",
    "certifi",
    "pyinstaller-hooks-contrib",
    "altgraph",
    "packaging",
    "pywin32-ctypes",
)

COHERENT_QT_PACKAGES = ("PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6")

SCRUBBED_ENV_KEYS = (
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
    "QT_OPENGL",
    "QSG_RHI_BACKEND",
    "QT_QPA_PLATFORM",
    "QT_SCALE_FACTOR",
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "PYTHONUSERBASE",
)


def _read_config_version(config_py: Path) -> str:
    text = config_py.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(config_py))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "LAUNCHER_VERSION":
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value.strip()
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "LAUNCHER_VERSION":
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    return node.value.value.strip()
    raise SystemExit(f"Could not read LAUNCHER_VERSION from {config_py}")


def _verify_version_info(version_info: Path, launcher_version: str) -> dict[str, str]:
    text = version_info.read_text(encoding="utf-8")
    fv_m = re.search(r"filevers\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    pv_m = re.search(r"prodvers\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    s_fv = re.search(r"StringStruct\s*\(\s*['\"]FileVersion['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", text)
    s_pv = re.search(r"StringStruct\s*\(\s*['\"]ProductVersion['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", text)
    if not (fv_m and pv_m and s_fv and s_pv):
        raise SystemExit(f"Invalid version_info.txt format: {version_info}")
    ver_parts = tuple(int(p) for p in launcher_version.split(".")[:3])
    fv = tuple(int(x) for x in fv_m.groups())
    pv = tuple(int(x) for x in pv_m.groups())
    file_ver = s_fv.group(1).strip()
    prod_ver = s_pv.group(1).strip()
    if fv[:3] != ver_parts or pv[:3] != ver_parts:
        raise SystemExit(f"version_info.txt numeric versions {fv}/{pv} do not match {launcher_version}")
    prefix = f"{launcher_version}."
    if (file_ver != launcher_version and not file_ver.startswith(prefix)) or (
        prod_ver != launcher_version and not prod_ver.startswith(prefix)
    ):
        raise SystemExit(f"version_info.txt string versions {file_ver!r}/{prod_ver!r} do not match {launcher_version!r}")
    return {"filevers": str(fv), "prodvers": str(pv), "FileVersion": file_ver, "ProductVersion": prod_ver}


def _snapshot_pycache(base: Path) -> dict[Path, float]:
    snap: dict[Path, float] = {}
    for p in base.rglob("__pycache__"):
        for f in p.rglob("*"):
            if f.is_file():
                snap[f.resolve()] = f.stat().st_mtime
    return snap


def build_candidate(
    revision: str = "r01",
    exe_name: str | None = None,
    clean_work: bool = False,
) -> dict[str, object]:
    if not re.fullmatch(r"r\d{2,3}[A-Za-z0-9_-]*", revision):
        raise SystemExit(f"Invalid revision tag: {revision!r}")

    src = Path(__file__).resolve().parent
    root = src.parent
    launcher_version = _read_config_version(src / "core" / "config.py")
    if not exe_name:
        exe_name = f"StellaSora-Windows_v{launcher_version}"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", exe_name):
        raise SystemExit(f"Invalid exe_name (spaces/special chars forbidden): {exe_name!r}")

    venv_py = root / ".venv" / "Scripts" / "python.exe"

    if (
        venv_py.is_file()
        and Path(sys.executable).resolve() != venv_py.resolve()
        and not os.environ.get("STELLA_BUILD_REEXEC")
    ):
        env_re = dict(os.environ)
        env_re["STELLA_BUILD_REEXEC"] = "1"
        env_re["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd_reexec = [str(venv_py), "-B", str(Path(__file__).resolve()), "--revision", revision, "--exe-name", exe_name]
        if clean_work:
            cmd_reexec.append("--clean-work")
        r = subprocess.run(cmd_reexec, cwd=root, env=env_re)
        raise SystemExit(r.returncode)

    versions: dict[str, str] = {}
    for pkg in REQUIRED_BUILD_PACKAGES:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError as exc:
            raise SystemExit(f"Required package {pkg!r} is missing in {sys.executable}: {exc}") from exc

    if len({versions[n] for n in COHERENT_QT_PACKAGES}) != 1:
        raise SystemExit(f"PySide6/Shiboken versions are not coherent: { {n: versions[n] for n in COHERENT_QT_PACKAGES} }")

    # Version & resource coherence checks before touching disk
    if not re.fullmatch(r"2\.\d+\.\d+", launcher_version):
        raise SystemExit(f"Expected v2 semver LAUNCHER_VERSION (2.x.y), got {launcher_version!r}")
    version_info_meta = _verify_version_info(src / "version_info.txt", launcher_version)

    notif_root = src / "notifications.json"
    notif_res = src / "resources" / "notifications.json"
    if not notif_root.is_file() or not notif_res.is_file():
        raise SystemExit("Missing notifications.json or resources/notifications.json")
    if notif_root.read_bytes() != notif_res.read_bytes():
        raise SystemExit("notifications.json and resources/notifications.json are not byte-identical")

    qt = Path(importlib.metadata.distribution("PySide6_Essentials").locate_file("PySide6")).resolve()
    windows = Path(os.environ.get("SystemRoot", "C:/Windows")).resolve()
    system_icu = windows / "System32" / "icuuc.dll"
    if not system_icu.is_file():
        raise SystemExit(f"Missing Windows System32 ICU provider: {system_icu}")
    if not (qt / "opengl32sw.dll").is_file():
        raise SystemExit(f"Missing software OpenGL fallback DLL: {qt / 'opengl32sw.dll'}")
    if not (src / "resources" / "branding" / "app_icon.ico").is_file():
        raise SystemExit("Missing resources/branding/app_icon.ico")

    out = root / "dist" / f"launcher_v2_candidate_{revision}"
    work = root / "work" / f"build_launcher_v2_{revision}"
    cache = root / "work" / f"launcher_v2_qt_build_{revision}" / "pyinstaller-cache"
    report = src / "reports" / f"launcher_v2_candidate_{revision}"

    for p in (out, work, cache, report):
        p.mkdir(parents=True, exist_ok=True)

    exe_path = out / f"{exe_name}.exe"
    if exe_path.exists():
        raise SystemExit(f"Refuse overwriting existing candidate EXE: {exe_path}")
    if any(work.iterdir()):
        raise SystemExit(f"Fresh work directory required (non-empty): {work}")

    raw_allowlist = [
        windows / "System32",
        windows,
        Path(sys.executable).resolve().parent,
        Path(sys.base_prefix).resolve(),
        Path(sys.base_prefix).resolve() / "DLLs",
        qt,
    ]
    dedup_allowlist: list[str] = []
    seen_dirs: set[str] = set()
    for p in raw_allowlist:
        if p.is_dir():
            key = str(p).lower()
            if key not in seen_dirs:
                seen_dirs.add(key)
                dedup_allowlist.append(str(p))

    env = dict(os.environ)
    removed: list[str] = []
    for key in SCRUBBED_ENV_KEYS:
        if key in env:
            removed.append(key)
            env.pop(key)

    env.update(
        {
            "PATH": os.pathsep.join(dedup_allowlist),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYINSTALLER_CONFIG_DIR": str(cache),
            "STELLA_PACKAGING_REPORT_DIR": str(report),
            "STELLA_V2_EXE_NAME": exe_name,
        }
    )

    environment = {
        "revision": revision,
        "version": launcher_version,
        "version_info": version_info_meta,
        "path_allowlist": dedup_allowlist,
        "removed_variable_names": removed,
        "python": sys.executable,
        "base_python": sys.base_prefix,
        "qt_wheel_dir": str(qt),
        "versions": versions,
        "shared_venv_modified": False,
        "application_executed": False,
    }
    (report / "BUILD_ENVIRONMENT.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2),
        encoding="utf8",
    )

    before_pycache = _snapshot_pycache(src)
    command = [
        sys.executable,
        "-B",
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(out),
        "--workpath",
        str(work),
        str(src / "StellaSora_Launcher_v2.spec"),
    ]
    build_log_path = report / "build.log"
    with build_log_path.open("w", encoding="utf8") as log:
        proc = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise SystemExit(f"PyInstaller failed with exit code {proc.returncode}. See {build_log_path}")

    if not exe_path.is_file():
        raise SystemExit(f"Expected EXE was not produced: {exe_path}")

    # Verify zero launcher_v2/ pollution (no build/, no dist/, no new __pycache__/.pyc)
    if (src / "build").exists() or (src / "dist").exists():
        raise SystemExit("PyInstaller polluted launcher_v2/ with build/ or dist/")
    after_pycache = _snapshot_pycache(src)
    new_pyc = [str(p) for p, mtime in after_pycache.items() if before_pycache.get(p) != mtime]
    if new_pyc:
        raise SystemExit(f"Build generated new bytecode inside launcher_v2/: {new_pyc[:5]}")

    digest = hashlib.sha256(exe_path.read_bytes()).hexdigest().lower()
    (out / "SHA256SUMS.txt").write_text(f"{digest} *{exe_path.name}\n", encoding="utf8")

    receipt = {
        "revision": revision,
        "version": launcher_version,
        "command": command,
        "working_directory": str(root),
        "exit_code": proc.returncode,
        "exe": str(exe_path),
        "bytes": exe_path.stat().st_size,
        "sha256": digest,
        "sha256sums": str(out / "SHA256SUMS.txt"),
        "dependencies": versions,
        "environment": str(report / "BUILD_ENVIRONMENT.json"),
        "dependency_provenance": str(report / "DEPENDENCY_PROVENANCE.json"),
        "build_log": str(build_log_path),
    }
    (report / "BUILD_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf8",
    )

    if clean_work and work.is_dir():
        shutil.rmtree(work, ignore_errors=True)

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Stella Sora Viet Hoa Launcher v2.0 candidate EXE")
    parser.add_argument("--revision", default="r01", help="Candidate revision tag (default: r01)")
    parser.add_argument("--exe-name", default=None, help="Output EXE base name (default: StellaSora-Windows_v<LAUNCHER_VERSION>)")
    parser.add_argument("--clean-work", action="store_true", help="Remove temporary PyInstaller work dir after build")
    args = parser.parse_args()
    build_candidate(revision=args.revision, exe_name=args.exe_name, clean_work=args.clean_work)


if __name__ == "__main__":
    main()
