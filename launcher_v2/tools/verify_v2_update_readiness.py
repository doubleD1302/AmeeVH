#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-specific Seamless Update Readiness verifier for Stella Sora Launcher v2.0.

Checks Gates PC-1 .. PC-5 directly against `StellaSora_VietHoa/launcher_v2/`
without modifying or relying on legacy `StellaSora_VietHoa/launcher/`.

Usage:
  python launcher_v2/tools/verify_v2_update_readiness.py --pre-build
  python launcher_v2/tools/verify_v2_update_readiness.py [--candidate-exe ...] [--json]
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass, field
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Optional
import uuid

DEFAULT_LAUNCHER_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = DEFAULT_LAUNCHER_DIR.parent
DEFAULT_DIST_DIR = DEFAULT_PROJECT_ROOT / "dist"


@dataclass
class GateResult:
    gate: str
    status: str  # "PASS" | "FAIL" | "SKIPPED"
    details: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in ("PASS", "SKIPPED")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest().lower()


def _read_launcher_version(config_py: Path) -> Optional[str]:
    if not config_py.is_file():
        return None
    text = config_py.read_text(encoding="utf-8")
    try:
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
    except SyntaxError:
        pass
    m = re.search(r'LAUNCHER_VERSION\s*(?::\s*str\s*)?=\s*["\']([^"\']+)["\']', text)
    return m.group(1).strip() if m else None


def _parse_version_info_txt(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fv_m = re.search(r"filevers\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    pv_m = re.search(r"prodvers\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", text)
    s_fv = re.search(r"StringStruct\s*\(\s*['\"]FileVersion['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", text)
    s_pv = re.search(r"StringStruct\s*\(\s*['\"]ProductVersion['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", text)
    return {
        "filevers": tuple(int(x) for x in fv_m.groups()) if fv_m else None,
        "prodvers": tuple(int(x) for x in pv_m.groups()) if pv_m else None,
        "FileVersion": s_fv.group(1).strip() if s_fv else None,
        "ProductVersion": s_pv.group(1).strip() if s_pv else None,
    }


def _find_candidate_exe(dist_dir: Path, version: str) -> Optional[Path]:
    if not dist_dir.is_dir():
        return None
    candidates = [
        dist_dir / f"StellaSora-Windows_v{version}.exe",
        dist_dir / f"StellaSora_Launcher_v{version}.exe",
        dist_dir / "StellaSora_Launcher_v2.exe",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    for pattern in ("launcher_v2_candidate*/StellaSora*.exe", "StellaSora*v2*.exe"):
        for match in sorted(dist_dir.glob(pattern)):
            if match.is_file():
                return match
    return None


def _parse_sha256sums(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line)
        if m:
            digest = m.group(1).lower()
            fname = Path(m.group(2).strip()).name
            mapping[fname] = digest
    return mapping


def _load_module_from_path(mod_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def gate_pc1(
    *,
    launcher_dir: Path,
    version_info_path: Optional[Path] = None,
    pre_build: bool = False,
) -> GateResult:
    """Gate PC-1: LAUNCHER_VERSION, notifications.json sync, and version_info.txt alignment."""
    details: list[str] = []
    errors: list[str] = []

    config_py = launcher_dir / "core" / "config.py"
    version = _read_launcher_version(config_py)
    if version != "2.0.0":
        errors.append(
            f"core/config.py LAUNCHER_VERSION must be '2.0.0', got {version!r}"
        )
    else:
        details.append(f"LAUNCHER_VERSION == {version!r}")

    notif_root = launcher_dir / "notifications.json"
    notif_res = launcher_dir / "resources" / "notifications.json"
    if not notif_root.is_file():
        errors.append(f"Missing {notif_root}")
    if not notif_res.is_file():
        errors.append(f"Missing {notif_res}")

    if notif_root.is_file() and notif_res.is_file():
        b_root = notif_root.read_bytes()
        b_res = notif_res.read_bytes()
        if b_root != b_res:
            errors.append("notifications.json and resources/notifications.json are not byte-identical")
        try:
            data = json.loads(b_root.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            errors.append(f"Invalid JSON in notifications.json: {exc}")
            data = None

        if isinstance(data, dict):
            n_ver = data.get("version")
            if version and n_ver != version:
                errors.append(
                    f"notifications.json version={n_ver!r} != LAUNCHER_VERSION={version!r}"
                )
            items = data.get("announcements")
            if not isinstance(items, list) or not items:
                errors.append("notifications.json missing non-empty 'announcements' list")
            else:
                ids = [item.get("id") for item in items if isinstance(item, dict)]
                if len(ids) != len(items):
                    errors.append("notifications.json contains non-object announcement entry")
                if len(ids) != len(set(ids)):
                    errors.append("notifications.json contains duplicate announcement IDs")
                bad_fields = [
                    item.get("id")
                    for item in items
                    if isinstance(item, dict)
                    and not all(isinstance(item.get(k), str) and item.get(k).strip() for k in ("id", "title", "content"))
                ]
                if bad_fields:
                    errors.append(f"notifications.json entries missing id/title/content: {bad_fields}")
                ver_tag = f"v{version}" if version else "v2.0.0"
                has_release = any(
                    isinstance(item, dict)
                    and item.get("type") == "release"
                    and ver_tag in str(item.get("title", ""))
                    for item in items
                )
                if not has_release:
                    errors.append(
                        f"notifications.json lacks type=='release' entry with {ver_tag!r} in title"
                    )
                else:
                    details.append(
                        f"notifications.json synced ({len(items)} items, release entry for {ver_tag} verified)"
                    )

    vi_path = version_info_path or (launcher_dir / "version_info.txt")
    if not vi_path.is_file():
        if pre_build:
            details.append(f"version_info.txt absent ({vi_path.name}) — SKIPPED (pre-build)")
        else:
            errors.append(f"Missing version_info.txt in full mode: {vi_path}")
    else:
        parsed = _parse_version_info_txt(vi_path)
        ver_parts = tuple(int(p) for p in (version or "0.0.0").split(".")[:3])
        fv = parsed.get("filevers")
        pv = parsed.get("prodvers")
        s_fv = parsed.get("FileVersion")
        s_pv = parsed.get("ProductVersion")
        if fv is None or fv[:3] != ver_parts:
            errors.append(f"version_info.txt filevers={fv} does not match {ver_parts}")
        if pv is None or pv[:3] != ver_parts:
            errors.append(f"version_info.txt prodvers={pv} does not match {ver_parts}")
        expected_prefix = f"{version}." if version else "2.0.0."
        if not s_fv or (s_fv != version and not s_fv.startswith(expected_prefix)):
            errors.append(f"version_info.txt FileVersion={s_fv!r} does not match {version!r}")
        if not s_pv or (s_pv != version and not s_pv.startswith(expected_prefix)):
            errors.append(f"version_info.txt ProductVersion={s_pv!r} does not match {version!r}")
        if not errors:
            details.append(f"version_info.txt verified: filevers={fv}, FileVersion={s_fv!r}")

    return GateResult(
        gate="PC-1",
        status="FAIL" if errors else "PASS",
        details=details,
        errors=errors,
    )


def _ast_imports_qt(py_file: Path) -> list[str]:
    found: list[str] = []
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(("PySide6", "PyQt")):
                    found.append(f"{py_file.name}:{node.lineno} import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith(("PySide6", "PyQt")):
                found.append(f"{py_file.name}:{node.lineno} from {mod}")
    return found


def gate_pc2(*, launcher_dir: Path) -> GateResult:
    """Gate PC-2: 4-step self_update tokens, pre-Qt app.py routing, zero Qt in core/."""
    details: list[str] = []
    errors: list[str] = []

    su_path = launcher_dir / "core" / "self_update.py"
    if not su_path.is_file():
        errors.append(f"Missing {su_path}")
    else:
        su_code = su_path.read_text(encoding="utf-8")
        required_tokens = (
            "SYNCHRONIZE",
            "QueryFullProcessImageNameW",
            "taskkill",
            "target.rename",
            "sha256_file",
            "Popen",
        )
        missing = [tok for tok in required_tokens if tok not in su_code]
        if missing:
            errors.append(f"self_update.py missing required tokens: {missing}")
        else:
            details.append("self_update.py contains all 4-step lock/replace/relaunch tokens")

        try:
            su_tree = ast.parse(su_code, filename=str(su_path))
            fn_names = {n.name for n in su_tree.body if isinstance(n, ast.FunctionDef)}
            for req_fn in ("apply_job", "schedule_update"):
                if req_fn not in fn_names:
                    errors.append(f"self_update.py missing function {req_fn}()")
        except SyntaxError as exc:
            errors.append(f"self_update.py syntax error: {exc}")

    # Zero Qt imports anywhere in launcher_v2/core/*.py
    core_dir = launcher_dir / "core"
    qt_in_core: list[str] = []
    for py_file in sorted(core_dir.glob("*.py")):
        qt_in_core.extend(_ast_imports_qt(py_file))
    if qt_in_core:
        errors.append(f"Qt imports detected in core/: {qt_in_core}")
    else:
        details.append("core/*.py verified 100% Qt-free (0 PySide6/PyQt imports)")

    # Verify app.py has no top-level PySide6 import and routes CLI fast-paths before run_gui
    app_py = launcher_dir / "app.py"
    if not app_py.is_file():
        errors.append(f"Missing {app_py}")
    else:
        app_code = app_py.read_text(encoding="utf-8")
        app_tree = ast.parse(app_code, filename=str(app_py))
        top_qt = []
        main_fn = None
        for node in app_tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(("PySide6", "PyQt")):
                        top_qt.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(("PySide6", "PyQt")):
                top_qt.append(node.module)
            elif isinstance(node, ast.FunctionDef) and node.name == "main":
                main_fn = node
        if top_qt:
            errors.append(f"app.py has top-level Qt imports: {top_qt}")
        if main_fn is None:
            errors.append("app.py missing main() function")
        else:
            # Verify --smoke, --tls-check, --apply-update appear before run_gui() inside main()
            flag_lines: dict[str, int] = {}
            run_gui_line: Optional[int] = None
            for node in ast.walk(main_fn):
                if isinstance(node, ast.Attribute) and node.attr in ("smoke", "tls_check", "apply_update"):
                    flag_lines.setdefault(node.attr, node.lineno)
                elif isinstance(node, ast.Call):
                    func = node.func
                    fname = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                    if fname == "run_gui":
                        run_gui_line = min(run_gui_line, node.lineno) if run_gui_line else node.lineno
            for flag in ("smoke", "tls_check", "apply_update"):
                if flag not in flag_lines:
                    errors.append(f"app.py main() missing fast-path check for {flag}")
                elif run_gui_line is not None and flag_lines[flag] >= run_gui_line:
                    errors.append(f"app.py main() checks {flag} after run_gui()")
            if not errors:
                details.append("app.py routes --smoke/--tls-check/--apply-update strictly before run_gui() / PySide6")

        # Runtime subprocess check confirming PySide6 is not loaded on --smoke / --tls-check
        with tempfile.TemporaryDirectory(prefix="ssv2_pc2_") as tmp_dir:
            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            probe_script = (
                "import sys; "
                f"sys.path.insert(0, {str(launcher_dir.parent)!r}); "
                "from launcher_v2 import app; "
                f"rc1 = app.entry(['--smoke', '--app-data-dir', {tmp_dir!r}]); "
                "assert rc1 == 0, rc1; "
                "assert 'PySide6' not in sys.modules, 'PySide6 imported on --smoke'; "
                "rc2 = app.entry(['--tls-check']); "
                "assert rc2 == 0, rc2; "
                "assert 'PySide6' not in sys.modules, 'PySide6 imported on --tls-check'; "
                "print('FASTPATH_NO_QT_OK')"
            )
            proc = subprocess.run(
                [sys.executable, "-c", probe_script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                timeout=30,
            )
            if proc.returncode != 0 or "FASTPATH_NO_QT_OK" not in proc.stdout:
                errors.append(
                    f"Runtime pre-Qt fast-path check failed (rc={proc.returncode}): {proc.stdout} {proc.stderr}".strip()
                )
            else:
                details.append("Runtime verified: --smoke & --tls-check exit 0 without importing PySide6")

    return GateResult(
        gate="PC-2",
        status="FAIL" if errors else "PASS",
        details=details,
        errors=errors,
    )


def gate_pc3(
    *,
    launcher_dir: Path,
    manifest_path: Optional[Path] = None,
) -> GateResult:
    """Gate PC-3: patch_manifest.json wildcard '*' & update_notice.matches() behavior."""
    details: list[str] = []
    errors: list[str] = []

    man_file = manifest_path or (launcher_dir.parent / "dist" / "patch_manifest.json")
    if not man_file.is_file():
        errors.append(f"Missing manifest: {man_file}")
        return GateResult(gate="PC-3", status="FAIL", details=details, errors=errors)

    try:
        man = json.loads(man_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"Invalid manifest JSON {man_file}: {exc}")
        return GateResult(gate="PC-3", status="FAIL", details=details, errors=errors)

    res_ver = man.get("resource_version")
    client_ver = man.get("client_game_version")
    if not isinstance(client_ver, str) or not client_ver.strip():
        errors.append(f"manifest missing non-empty client_game_version: {client_ver!r}")
    if not isinstance(res_ver, str) or "*" not in [p.strip() for p in re.split(r"[,;|]", res_ver) if p.strip()]:
        errors.append(f"manifest resource_version missing wildcard '*': {res_ver!r}")
    else:
        details.append(f"Manifest client_game_version={client_ver!r}, resource_version={res_ver!r}")

    try:
        un_mod = _load_module_from_path("_v2_gate_update_notice", launcher_dir / "core" / "update_notice.py")
        if not un_mod.matches("2611999999", str(res_ver or "")):
            errors.append("update_notice.matches('2611999999', manifest['resource_version']) returned False")
        if not un_mod.matches("2610201624", str(res_ver or "")):
            errors.append("update_notice.matches('2610201624', manifest['resource_version']) returned False")
        if un_mod.matches("unknown", "*"):
            errors.append("update_notice.matches('unknown', '*') returned True (must reject 'unknown')")
        if un_mod.matches("*", "*"):
            errors.append("update_notice.matches('*', '*') returned True (must reject wildcard observed)")
        if not errors:
            details.append("update_notice.matches() accepts '*' for valid revisions and rejects 'unknown'")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Failed testing update_notice.matches(): {exc}")

    return GateResult(
        gate="PC-3",
        status="FAIL" if errors else "PASS",
        details=details,
        errors=errors,
    )


def gate_pc4(
    *,
    launcher_dir: Path,
    candidate_exe: Optional[Path] = None,
    sha256sums_path: Optional[Path] = None,
    pre_build: bool = False,
) -> GateResult:
    """Gate PC-4: Source & built-EXE --smoke --app-data-dir <tmp>, --tls-check, and SHA256SUMS."""
    details: list[str] = []
    errors: list[str] = []

    app_py = launcher_dir / "app.py"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    with tempfile.TemporaryDirectory(prefix="ssv2_pc4_src_") as tmp_dir:
        smoke_proc = subprocess.run(
            [sys.executable, str(app_py), "--smoke", "--app-data-dir", tmp_dir],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30,
        )
        if smoke_proc.returncode != 0 or "OK: SMOKE TEST PASSED" not in smoke_proc.stdout:
            errors.append(
                f"app.py --smoke failed (rc={smoke_proc.returncode}): {smoke_proc.stdout} {smoke_proc.stderr}".strip()
            )
        else:
            details.append("app.py --smoke --app-data-dir <tmp> passed")

        tls_proc = subprocess.run(
            [sys.executable, str(app_py), "--tls-check"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30,
        )
        if tls_proc.returncode != 0 or "trusted_roots" not in tls_proc.stdout:
            errors.append(
                f"app.py --tls-check failed (rc={tls_proc.returncode}): {tls_proc.stdout} {tls_proc.stderr}".strip()
            )
        else:
            details.append("app.py --tls-check passed")

    version = _read_launcher_version(launcher_dir / "core" / "config.py") or "2.0.0"
    dist_dir = launcher_dir.parent / "dist"

    if pre_build and candidate_exe is None:
        details.append("Built candidate EXE & SHA256SUMS.txt verification — SKIPPED (pre-build)")
        return GateResult(
            gate="PC-4",
            status="FAIL" if errors else "PASS",
            details=details,
            errors=errors,
        )

    exe_path = candidate_exe or _find_candidate_exe(dist_dir, version)
    if exe_path is None or not exe_path.is_file():
        errors.append(f"Candidate EXE not found for v{version} (checked {exe_path or dist_dir})")
        return GateResult(gate="PC-4", status="FAIL", details=details, errors=errors)

    sums_path = sha256sums_path
    if sums_path is None:
        sibling = exe_path.parent / "SHA256SUMS.txt"
        sums_path = sibling if sibling.is_file() else (dist_dir / "SHA256SUMS.txt")
    if not sums_path.is_file():
        errors.append(f"Missing SHA256SUMS.txt: {sums_path}")
        return GateResult(gate="PC-4", status="FAIL", details=details, errors=errors)

    sums = _parse_sha256sums(sums_path)
    actual_sha = sha256_file(exe_path)
    expected_sha = None
    for key in (exe_path.name, f"StellaSora-Windows_v{version}.exe", "StellaSora_Launcher.exe"):
        if key in sums:
            expected_sha = sums[key]
            break

    if expected_sha is None:
        errors.append(f"{sums_path.name} has no entry for {exe_path.name}")
        return GateResult(gate="PC-4", status="FAIL", details=details, errors=errors)
    if expected_sha != actual_sha:
        errors.append(
            f"SHA256 mismatch for {exe_path.name}: expected {expected_sha}, got {actual_sha}"
        )
        return GateResult(gate="PC-4", status="FAIL", details=details, errors=errors)
    details.append(f"Candidate EXE SHA256 verified ({exe_path.name}: {actual_sha[:16]}...)")

    with tempfile.TemporaryDirectory(prefix="ssv2_pc4_exe_") as exe_tmp:
        try:
            exe_smoke = subprocess.run(
                [str(exe_path), "--smoke", "--app-data-dir", exe_tmp],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            if exe_smoke.returncode != 0 or "OK: SMOKE TEST PASSED" not in exe_smoke.stdout:
                errors.append(
                    f"Candidate EXE --smoke failed (rc={exe_smoke.returncode}): {exe_smoke.stdout} {exe_smoke.stderr}".strip()
                )
            else:
                details.append(f"{exe_path.name} --smoke --app-data-dir <tmp> passed")

            exe_tls = subprocess.run(
                [str(exe_path), "--tls-check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            if exe_tls.returncode != 0 or "trusted_roots" not in exe_tls.stdout:
                errors.append(
                    f"Candidate EXE --tls-check failed (rc={exe_tls.returncode}): {exe_tls.stdout} {exe_tls.stderr}".strip()
                )
            else:
                details.append(f"{exe_path.name} --tls-check passed")
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"Candidate EXE execution failed: {exc}")

    return GateResult(
        gate="PC-4",
        status="FAIL" if errors else "PASS",
        details=details,
        errors=errors,
    )


def _terminate_pid_best_effort(pid: Any) -> None:
    if not isinstance(pid, int) or pid <= 0 or pid == os.getpid():
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception:  # noqa: BLE001
            pass


def _pick_runnable_pe_pair(work_dir: Path) -> tuple[Path, Path]:
    """Create two distinct valid Windows PE files in work_dir for self-update simulation."""
    base_dir = Path(sys.base_prefix).resolve()
    py_exe = base_dir / "python.exe"
    if not py_exe.is_file():
        py_exe = Path(sys.executable).resolve()
    pyw_exe = py_exe.with_name("pythonw.exe")
    target = work_dir / "StellaSora_Launcher_v134.exe"
    source = work_dir / "StellaSora-Windows_v2.0.0.exe"
    if pyw_exe.is_file() and sha256_file(pyw_exe) != sha256_file(py_exe):
        shutil.copy2(pyw_exe, target)
        shutil.copy2(py_exe, source)
    else:
        shutil.copy2(py_exe, target)
        # Append a harmless trailing overlay byte so SHA256 differs while PE stays runnable
        data = py_exe.read_bytes() + b"\x00"
        source.write_bytes(data)
    return target, source


def gate_pc5(*, launcher_dir: Path) -> GateResult:
    """Gate PC-5: E2E v1.3.4 job -> v2.0 apply_job() simulation + r02 migration -> recover()."""
    details: list[str] = []
    errors: list[str] = []

    parent_dir = str(launcher_dir.parent)
    added_path = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        added_path = True

    try:
        from launcher_v2.core.config import PathManager
        from launcher_v2.core.game_detection import canonicalize_path
        from launcher_v2.core.installer import PatchInstaller
        from launcher_v2.core.migration import migrate_from_r02_if_needed
        from launcher_v2.core.safety import atomic_json
        from launcher_v2.core.self_update import cleanup_all_update_artifacts, cleanup_update_artifacts

        with tempfile.TemporaryDirectory(prefix="ssv2_pc5_") as tmp:
            root = Path(tmp)
            # --- Part A: v1.3.4 job schema -> app.py --apply-update (self_update.apply_job) ---
            upd_dir = root / "self_update_sim"
            upd_dir.mkdir(parents=True)
            target_exe, source_exe = _pick_runnable_pe_pair(upd_dir)
            preimage_sha = sha256_file(target_exe)
            expected_sha = sha256_file(source_exe)

            sim_app_data = root / "sim_appdata"
            helper_dir = sim_app_data / "update_helper"
            helper_dir.mkdir(parents=True)
            job_path = helper_dir / f"{uuid.uuid4().hex}.json"

            # Exact v1.3.4 schedule_update() JSON schema
            job_payload = {
                "source": str(source_exe),
                "target": str(target_exe),
                "sha256": expected_sha,
                "preimage_sha256": preimage_sha,
                "timeout": 20,
                "parent_pid": None,
                "allow_force_close": True,
            }
            atomic_json(job_path, job_payload)

            env = dict(os.environ)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["LOCALAPPDATA"] = str(root / "unused_localappdata")
            env["PATH"] = f"{Path(sys.base_prefix).resolve()}{os.pathsep}{env.get('PATH', '')}"

            spawned_pid = None
            try:
                proc = subprocess.run(
                    [sys.executable, str(launcher_dir / "app.py"), "--apply-update", str(job_path)],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    timeout=30,
                )
                result_path = job_path.with_suffix(".result.json")
                if proc.returncode != 0:
                    errors.append(
                        f"app.py --apply-update failed (rc={proc.returncode}): {proc.stdout} {proc.stderr}".strip()
                    )
                elif not result_path.is_file():
                    errors.append("app.py --apply-update did not write <job>.result.json")
                else:
                    res_data = json.loads(result_path.read_text(encoding="utf-8"))
                    spawned_pid = res_data.get("pid")
                    if res_data.get("status") != "started":
                        errors.append(f"apply_job result status != 'started': {res_data}")
                    if sha256_file(target_exe) != expected_sha:
                        errors.append("Replaced target EXE SHA256 does not match source SHA256")
                    preupdate_files = list(upd_dir.glob(f"{target_exe.name}.preupdate.*"))
                    if len(preupdate_files) != 1 or sha256_file(preupdate_files[0]) != preimage_sha:
                        errors.append("Missing or hash-mismatched .preupdate.<uuid> backup")

                    # Verify cleanup_all_update_artifacts removes temp artifacts while keeping .preupdate.*
                    stale_old = upd_dir / f"{target_exe.name}.old_{uuid.uuid4().hex}"
                    stale_old.write_bytes(b"old")
                    stale_tmp = upd_dir / f".launcher_update_{uuid.uuid4().hex}.exe"
                    stale_tmp.write_bytes(b"tmp")
                    stale_helper = helper_dir / f"helper_{uuid.uuid4().hex}.exe"
                    stale_helper.write_bytes(b"helper")
                    pm_clean = PathManager(app_data_dir=sim_app_data)
                    # Clean upd_dir directly + helper_dir via pm_clean
                    cleanup_update_artifacts(upd_dir)
                    cleanup_all_update_artifacts(pm_clean)
                    if stale_old.exists() or stale_tmp.exists() or stale_helper.exists():
                        errors.append("cleanup_update_artifacts failed to remove stale temp files")
                    if not preupdate_files or not preupdate_files[0].exists():
                        errors.append("cleanup_update_artifacts unexpectedly deleted .preupdate.* backup")
                    if not errors:
                        details.append("v1.3.4 job -> v2.0 --apply-update E2E replacement, readback, .result.json & cleanup passed")
            finally:
                _terminate_pid_best_effort(spawned_pid)

            # --- Part B: r02 -> v2 migration journal backup_dir rewrite + PatchInstaller.recover() ---
            local_app_base = root / "local_app_data"
            r02_dir = local_app_base / "StellaSora_Launcher_Candidate_r02"
            game_root = root / "GameDir"
            (game_root / "Persistent_Store" / "Tables").mkdir(parents=True)
            (game_root / "StellaSora.exe").write_bytes(b"MZ_GAME")

            rel_file = "Persistent_Store/Tables/data.arcx"
            orig_bytes = b"ORIGINAL_EN_DATA"
            patched_bytes = b"PATCHED_VI_DATA"
            (game_root / rel_file).write_bytes(patched_bytes)

            orig_sha = hashlib.sha256(orig_bytes).hexdigest()
            patched_sha = hashlib.sha256(patched_bytes).hexdigest()

            # Compute root hash bucket used by PatchInstaller.get_backup_dir_for_root()
            croot = canonicalize_path(game_root)
            root_bucket = "game_" + hashlib.sha256(croot.encode("utf8")).hexdigest()[:12]
            r02_backup_leaf = r02_dir / "backups" / root_bucket / "backup_20261124_0001"
            (r02_backup_leaf / "Persistent_Store" / "Tables").mkdir(parents=True)
            (r02_backup_leaf / rel_file).write_bytes(orig_bytes)

            (r02_dir / "journals").mkdir(parents=True)
            (r02_dir / "config.json").write_text(
                json.dumps({"version": "1.3.4", "game_path": str(game_root)}),
                encoding="utf-8",
            )
            journal_path = r02_dir / "journals" / "j_pending.json"
            journal_path.write_text(
                json.dumps(
                    {
                        "id": "j_pending",
                        "game_root": croot,
                        "backup_dir": str(r02_backup_leaf),
                        "state": "applying",
                        "previous_receipt": None,
                        "files": {
                            rel_file: {
                                "before": {"exists": True, "size": len(orig_bytes), "sha256": orig_sha},
                                "after": {"exists": True, "size": len(patched_bytes), "sha256": patched_sha},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            old_local = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = str(local_app_base)
            try:
                pm_v2 = PathManager(resource_dir=launcher_dir / "resources")
                mig_res = migrate_from_r02_if_needed(pm_v2)
                if mig_res.get("status") != "migrated" or mig_res.get("journals_rewritten", 0) < 1:
                    errors.append(f"r02 migration failed or did not rewrite journal: {mig_res}")
                else:
                    migrated_j = json.loads((pm_v2.journals_dir / "j_pending.json").read_text(encoding="utf-8"))
                    expected_v2_backup = (pm_v2.backup_root / root_bucket / "backup_20261124_0001").resolve()
                    if Path(migrated_j["backup_dir"]).resolve() != expected_v2_backup:
                        errors.append(
                            f"Journal backup_dir not rewritten to v2 backups: {migrated_j.get('backup_dir')}"
                        )
                    if migrated_j.get("_migrated_from_backup_dir") != str(r02_backup_leaf):
                        errors.append("Journal missing _migrated_from_backup_dir provenance")

                    # Now exercise PatchInstaller.recover() on the migrated v2 AppData
                    installer = PatchInstaller(pm_v2.backup_root, pm_v2.journals_dir)
                    rec_res = installer.recover(game_root)
                    if rec_res.get("status") != "recovered" or (game_root / rel_file).read_bytes() != orig_bytes:
                        errors.append(f"PatchInstaller.recover() failed after migration: {rec_res}")
                    elif not (r02_dir / "journals" / "j_pending.json").is_file():
                        errors.append("Legacy r02 source directory was modified during migration")
                    else:
                        details.append(
                            "r02 migration rewritten journal backup_dir -> PatchInstaller.recover() restored vanilla file cleanly"
                        )
            finally:
                if old_local is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = old_local
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Gate PC-5 simulation raised unexpected error: {exc}")
    finally:
        if added_path and parent_dir in sys.path:
            sys.path.remove(parent_dir)

    return GateResult(
        gate="PC-5",
        status="FAIL" if errors else "PASS",
        details=details,
        errors=errors,
    )


def run_verification(
    *,
    launcher_dir: Path | str | None = None,
    pre_build: bool = False,
    candidate_exe: Path | str | None = None,
    sha256sums_path: Path | str | None = None,
    manifest_path: Path | str | None = None,
    version_info_path: Path | str | None = None,
) -> dict[str, Any]:
    ldir = Path(launcher_dir).resolve() if launcher_dir else DEFAULT_LAUNCHER_DIR
    cand = Path(candidate_exe).resolve() if candidate_exe else None
    sums = Path(sha256sums_path).resolve() if sha256sums_path else None
    man = Path(manifest_path).resolve() if manifest_path else None
    vi = Path(version_info_path).resolve() if version_info_path else None

    results = [
        gate_pc1(launcher_dir=ldir, version_info_path=vi, pre_build=pre_build),
        gate_pc2(launcher_dir=ldir),
        gate_pc3(launcher_dir=ldir, manifest_path=man),
        gate_pc4(launcher_dir=ldir, candidate_exe=cand, sha256sums_path=sums, pre_build=pre_build),
        gate_pc5(launcher_dir=ldir),
    ]
    passed = all(r.ok for r in results)
    return {
        "ok": passed,
        "pre_build": bool(pre_build),
        "launcher_dir": str(ldir),
        "gates": [asdict(r) for r in results],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stella Sora Launcher v2.0 PC Seamless Update Readiness verifier (Gates PC-1..PC-5)"
    )
    parser.add_argument(
        "--pre-build",
        action="store_true",
        help="M6 pre-packaging mode (skips absent version_info.txt and built candidate EXE/SHA256SUMS)",
    )
    parser.add_argument("--candidate-exe", type=Path, help="Explicit path to candidate EXE")
    parser.add_argument("--sha256sums", type=Path, help="Explicit path to SHA256SUMS.txt")
    parser.add_argument("--manifest", type=Path, help="Explicit path to patch_manifest.json")
    parser.add_argument("--version-info", type=Path, help="Explicit path to version_info.txt")
    parser.add_argument("--launcher-dir", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    args = _build_parser().parse_args(argv)
    report = run_verification(
        launcher_dir=args.launcher_dir,
        pre_build=bool(args.pre_build),
        candidate_exe=args.candidate_exe,
        sha256sums_path=args.sha256sums,
        manifest_path=args.manifest,
        version_info_path=args.version_info,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        mode = "PRE-BUILD (M6)" if report["pre_build"] else "FULL RELEASE (M7)"
        print(f"=== STELLA SORA LAUNCHER v2.0 UPDATE READINESS ({mode}) ===")
        for g in report["gates"]:
            icon = "PASS" if g["status"] == "PASS" else ("SKIP" if g["status"] == "SKIPPED" else "FAIL")
            print(f"[{icon}] {g['gate']}")
            for d in g["details"]:
                print(f"   - {d}")
            for err in g["errors"]:
                print(f"   ! ERROR: {err}")
        print("=" * 60)
        print("RESULT:", "ALL GATES PASSED" if report["ok"] else "FAILED")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
