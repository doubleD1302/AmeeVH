# -*- mode: python ; coding: utf-8 -*-

import os
import json
import sys
import hashlib
from pathlib import Path
import importlib.metadata
import pefile

block_cipher = None

spec_root = Path(SPECPATH).resolve()
project_root = spec_root.parent
resources_dir = spec_root / "resources"

# System ICU C ABI is supplied by Windows, not by an unrelated Poppler/Conda DLL.
# Read PE tables only: do not import QtWidgets/QtCore or execute the app here.
qt_dir = Path(importlib.metadata.distribution('PySide6_Essentials').locate_file('PySide6')).resolve()
windows_dir = Path(os.environ.get('SystemRoot', 'C:/Windows')).resolve()
report_dir = Path(os.environ.get('STELLA_PACKAGING_REPORT_DIR', str(project_root / 'reports/launcher_ui_candidate_r09/implementer')))
report_dir.mkdir(parents=True, exist_ok=True)
def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()
def imports_for(path, dependency):
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=100000)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
        return [i.name.decode('ascii') for item in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []) if item.dll.decode('ascii').lower() == dependency.lower() for i in item.imports if i.name]
    finally: pe.close()
def exported_names(path):
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=100000)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
        return {item.name.decode('ascii') for item in getattr(getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None), 'symbols', []) if item.name}
    finally: pe.close()
qt_icu_symbols = imports_for(qt_dir / 'Qt6Core.dll', 'icuuc.dll')
system_icu = windows_dir / 'System32' / 'icuuc.dll'
if not system_icu.is_file(): raise RuntimeError('Required Windows ICU system provider is missing. No third-party replacement will be bundled.')
missing_icu = sorted(set(qt_icu_symbols) - exported_names(system_icu))
if missing_icu: raise RuntimeError('Windows ICU provider does not expose Qt ABI: ' + ', '.join(missing_icu))


datas = [
    (str(resources_dir / "ui"), "resources/ui"),
    (str(resources_dir / "branding"), "resources/branding"),
]

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "launcher",
    "launcher.core",
    "launcher.ui",
]

a = Analysis(
    [str(spec_root / "app.py")],
    pathex=[str(project_root), str(spec_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "notebook", "pytest", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Apply a source allowlist after dependency discovery. The launcher's files and
# graphics runtime must not be pulled from an installed game or another tool.
approved_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), windows_dir]
def under(path, root):
    try: path.relative_to(root); return True
    except ValueError: return False
system_icu_names = {'icuuc.dll', 'icuin.dll', 'icudt.dll', 'icu.dll'}
excluded = []
kept = []
for destination, source, kind in a.binaries:
    source_path = Path(source).resolve()
    if Path(destination).name.lower() in system_icu_names:
        excluded.append({'destination': destination, 'source': str(source_path), 'reason': 'OS ICU is resolved from Windows System32; never bundle a conflicting private ICU'})
        continue
    if not any(under(source_path, approved) for approved in approved_roots):
        raise RuntimeError('Dependency outside approved Python/Qt/Windows roots: ' + str(source_path))
    kept.append((destination, source, kind))
a.binaries = kept
provenance = {
    'method': 'static PE tables and PyInstaller binary source allowlist; no Qt/app execution',
    'system_icu': {'path': str(system_icu), 'sha256': file_sha(system_icu), 'qt_required_named_exports': qt_icu_symbols, 'missing_exports': missing_icu, 'bundled': False},
    'excluded': excluded,
    'approved_roots': [str(p) for p in approved_roots],
    'binaries': [{'destination': d, 'source': str(Path(s).resolve()), 'type': t, 'sha256': file_sha(s)} for d, s, t in a.binaries],
}
(report_dir / 'DEPENDENCY_PROVENANCE.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf8')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="StellaSora_Launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(resources_dir / "branding" / "app_icon.ico"),
    version=str(spec_root / "version_info.txt"),
)
