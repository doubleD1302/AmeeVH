# -*- mode: python ; coding: utf-8 -*-

import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path
import pefile

block_cipher = None

spec_root = Path(SPECPATH).resolve()
project_root = spec_root.parent
resources_dir = spec_root / "resources"
exe_name = os.environ.get("STELLA_V2_EXE_NAME", "StellaSora-Windows_v2.0.0")
report_dir = Path(
    os.environ.get(
        "STELLA_PACKAGING_REPORT_DIR",
        str(spec_root / "reports" / "launcher_v2_candidate_r01"),
    )
).resolve()
report_dir.mkdir(parents=True, exist_ok=True)

# System ICU C ABI is supplied by Windows System32, not by a private/third-party DLL.
# Read PE tables only: do not import PySide6/QtWidgets or execute the app here.
qt_dir = Path(importlib.metadata.distribution("PySide6_Essentials").locate_file("PySide6")).resolve()
windows_dir = Path(os.environ.get("SystemRoot", "C:/Windows")).resolve()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def all_imported_dlls(path):
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=100000)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        return [
            item.dll.decode("ascii", errors="replace").lower()
            for item in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
            if getattr(item, "dll", None)
        ]
    finally:
        pe.close()


def imports_for(path, dependency):
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=100000)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
        return [
            i.name.decode("ascii")
            for item in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
            if item.dll.decode("ascii").lower() == dependency.lower()
            for i in item.imports
            if i.name
        ]
    finally:
        pe.close()


def exported_names(path):
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=100000)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
        return {
            item.name.decode("ascii")
            for item in getattr(getattr(pe, "DIRECTORY_ENTRY_EXPORT", None), "symbols", [])
            if item.name
        }
    finally:
        pe.close()


qt_icu_symbols = imports_for(qt_dir / "Qt6Core.dll", "icuuc.dll")
if len(qt_icu_symbols) > 20:
    raise RuntimeError(f"Unexpected Qt6Core.dll ICU import count ({len(qt_icu_symbols)} > 20): {qt_icu_symbols}")
system_icu = windows_dir / "System32" / "icuuc.dll"
if not system_icu.is_file():
    raise RuntimeError("Required Windows ICU system provider is missing. No third-party replacement will be bundled.")
missing_icu = sorted(set(qt_icu_symbols) - exported_names(system_icu))
if missing_icu:
    raise RuntimeError("Windows ICU provider does not expose Qt ABI: " + ", ".join(missing_icu))

icon_path = resources_dir / "branding" / "app_icon.ico"
if not icon_path.is_file():
    raise RuntimeError(f"Missing launcher icon: {icon_path}")

version_info_path = spec_root / "version_info.txt"
if not version_info_path.is_file():
    raise RuntimeError(f"Missing version_info.txt: {version_info_path}")

datas = [
    (str(resources_dir / "branding"), "resources/branding"),
    (str(resources_dir / "chibis"), "resources/chibis"),
    (str(resources_dir / "fonts"), "resources/fonts"),
    (str(resources_dir / "game"), "resources/game"),
    (str(resources_dir / "icons"), "resources/icons"),
    (str(resources_dir / "spinner"), "resources/spinner"),
    (str(resources_dir / "support"), "resources/support"),
    (str(resources_dir / "notifications.json"), "resources"),
    (str(spec_root / "notifications.json"), "."),
]

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "shiboken6",
    "certifi",
    "PIL",
    "PIL.Image",
    "PIL.ImageFilter",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.WebPImagePlugin",
    "PIL.IcoImagePlugin",
    "launcher_v2",
    "launcher_v2.app",
    "launcher_v2.core",
    "launcher_v2.core.bg_sync",
    "launcher_v2.core.bsdiff40",
    "launcher_v2.core.config",
    "launcher_v2.core.diagnostics",
    "launcher_v2.core.error_catalog",
    "launcher_v2.core.error_report",
    "launcher_v2.core.game_detection",
    "launcher_v2.core.game_guard",
    "launcher_v2.core.installer",
    "launcher_v2.core.migration",
    "launcher_v2.core.net_probe",
    "launcher_v2.core.network",
    "launcher_v2.core.official_resources",
    "launcher_v2.core.official_restore",
    "launcher_v2.core.quick_fix",
    "launcher_v2.core.rollback",
    "launcher_v2.core.safety",
    "launcher_v2.core.self_update",
    "launcher_v2.core.shortcut",
    "launcher_v2.core.tls",
    "launcher_v2.core.types",
    "launcher_v2.core.update_notice",
    "launcher_v2.core.vanilla_restore",
    "launcher_v2.ui",
    "launcher_v2.ui.app_controller",
    "launcher_v2.ui.main_shell",
    "launcher_v2.ui.theme",
    "launcher_v2.ui.theme.adaptive_scrim",
    "launcher_v2.ui.theme.qss_builder",
    "launcher_v2.ui.theme.tokens",
    "launcher_v2.ui.theme.typography",
    "launcher_v2.ui.widgets",
    "launcher_v2.ui.widgets.action_button",
    "launcher_v2.ui.widgets.asset_renderer",
    "launcher_v2.ui.widgets.glass_card",
    "launcher_v2.ui.widgets.hairline_table",
    "launcher_v2.ui.widgets.path_selector",
    "launcher_v2.ui.widgets.porcelain_window_frame",
    "launcher_v2.ui.widgets.progress_panel",
    "launcher_v2.ui.widgets.status_badge",
    "launcher_v2.ui.widgets.toast_banner",
    "launcher_v2.ui.screens",
    "launcher_v2.ui.screens.guide_screen",
    "launcher_v2.ui.screens.notifications_screen",
    "launcher_v2.ui.screens.overview_screen",
    "launcher_v2.ui.screens.settings_screen",
    "launcher_v2.ui.screens.support_screen",
    "launcher_v2.ui.screens.tools_screen",
    "launcher_v2.ui.dialogs",
    "launcher_v2.ui.dialogs.confirmation_dialog",
    "launcher_v2.ui.dialogs.game_selection_dialog",
    "launcher_v2.ui.dialogs.install_completed_dialog",
    "launcher_v2.ui.dialogs.safety_explainer_dialog",
    "launcher_v2.ui.dialogs.smart_error_dialog",
    "launcher_v2.ui.dialogs.support_locked_dialog",
    "launcher_v2.ui.dialogs.update_guard_dialog",
    "launcher_v2.ui.dialogs.update_notice_dialog",
]

excludes = [
    "launcher",
    "launcher_v2.tests",
    "launcher_v2.tools",
    "launcher_v2.preview",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuick3D",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtVirtualKeyboard",
    "PySide6.QtNetwork",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "Crypto",
    "tkinter",
    "_tkinter",
    "matplotlib",
    "scipy",
    "numpy",
    "notebook",
    "IPython",
    "pytest",
    "unittest",
    "UnityPy",
    "pyfmodex",
    "fmod_toolkit",
    "capstone",
    "fonttools",
    "etcpak",
    "astc_encoder",
    "texture2ddecoder",
    "tpk_ar",
    "rapidjson",
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
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Apply strict binary source allowlist and strip unused Qt bloat & private ICU DLLs.
approved_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(), windows_dir]


def under(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


system_icu_names = {"icuuc.dll", "icuin.dll", "icudt.dll", "icu.dll"}
bloat_exact_names = {
    "qpdf.dll",
    "qtvirtualkeyboardplugin.dll",
    "qtuiotouchplugin.dll",
    "qaxwidget.dll",
    "qquickwidget.dll",
    "qwebengineview.dll",
    "pysideplugin.dll",
    "assimp.dll",
    "ffmpegmediaplugin.dll",
    "windowsmediaplugin.dll",
}
bloat_prefixes = (
    "qt6quick",
    "qt6qml",
    "qt6pdf",
    "qt6virtualkeyboard",
    "qt6webengine",
    "qt6network",
    "qt6opengl",
    "qt6shadertools",
    "qt6designer",
    "qt6multimedia",
    "qt6sql",
    "qt6test",
    "qt6xml",
    "qt63d",
    "qt6charts",
    "qt6datavisualization",
    "qt6bluetooth",
    "qt6nfc",
    "qt6positioning",
    "qt6sensors",
    "qt6serialport",
    "qt6webchannel",
    "qt6websockets",
)

excluded_icu = []
excluded_qt_bloat = []
stripped_qt_dll_names = set()
kept_binaries = []

for destination, source, kind in a.binaries:
    source_path = Path(source).resolve()
    dest_norm = destination.replace("\\", "/")
    fname = Path(dest_norm).name.lower()

    if not any(under(source_path, approved) for approved in approved_roots):
        raise RuntimeError("Dependency outside approved Python/Qt/Windows roots: " + str(source_path))

    if fname in system_icu_names or fname.startswith(("icuuc", "icuin", "icudt")):
        excluded_icu.append(
            {
                "destination": dest_norm,
                "source": str(source_path),
                "reason": "OS ICU is resolved from Windows System32; never bundle a conflicting private ICU",
            }
        )
        continue

    if fname in bloat_exact_names or fname.startswith(bloat_prefixes):
        excluded_qt_bloat.append(
            {
                "destination": dest_norm,
                "source": str(source_path),
                "reason": "Unused Qt submodule/plugin stripped to reduce footprint and GPU/driver surface",
            }
        )
        if fname.endswith(".dll"):
            stripped_qt_dll_names.add(fname)
        continue

    kept_binaries.append((destination, source, kind))

a.binaries = kept_binaries

# Filter datas: strip unused PySide6 translations (keep only qtbase_en.qm / qt_en.qm) and any qml/webengine data.
kept_datas = []
excluded_datas_count = 0
kept_qt_translations = []
for destination, source, kind in a.datas:
    dest_norm = destination.replace("\\", "/").lower()
    if "pyside6/translations/" in dest_norm and dest_norm.endswith(".qm"):
        qm_name = Path(dest_norm).name
        if qm_name not in ("qtbase_en.qm", "qt_en.qm"):
            excluded_datas_count += 1
            continue
        kept_qt_translations.append(destination.replace("\\", "/"))
    if dest_norm.startswith(("pyside6/qml", "pyside6/resources/qtwebengine")):
        excluded_datas_count += 1
        continue
    kept_datas.append((destination, source, kind))

a.datas = kept_datas

# Verify mandatory runtime binaries and plugins are retained.
kept_by_name = {Path(d.replace("\\", "/")).name.lower(): (d.replace("\\", "/"), Path(s).resolve()) for d, s, _ in a.binaries}
required_dlls = [
    "opengl32sw.dll",
    "qwindows.dll",
    "qoffscreen.dll",
    "qico.dll",
    "qjpeg.dll",
    "qsvg.dll",
    "qwebp.dll",
    "qsvgicon.dll",
    "qt6core.dll",
    "qt6gui.dll",
    "qt6widgets.dll",
    "qt6svg.dll",
]
if (qt_dir / "plugins" / "styles" / "qmodernwindowsstyle.dll").is_file():
    required_dlls.append("qmodernwindowsstyle.dll")

missing_required = [name for name in required_dlls if name not in kept_by_name]
if missing_required:
    raise RuntimeError(f"Missing required runtime DLLs/plugins after filtering: {missing_required}")

# Verify required resources and certifi CA bundle are present in datas.
data_dests = {d.replace("\\", "/").lower() for d, _, _ in a.datas}
if not any(d.endswith("notifications.json") for d in data_dests):
    raise RuntimeError("notifications.json missing from collected datas")
if not any(d.startswith("resources/branding/") for d in data_dests):
    raise RuntimeError("resources/branding/ missing from collected datas")
if not any(d.endswith("certifi/cacert.pem") for d in data_dests):
    raise RuntimeError("certifi/cacert.pem missing from collected datas")

# Cross-check kept binaries: no kept DLL/PYD may import any stripped Qt6* DLL.
broken_imports = []
for destination, source, _ in a.binaries:
    src_path = Path(source).resolve()
    if src_path.suffix.lower() not in (".dll", ".pyd"):
        continue
    if not under(src_path, qt_dir):
        continue
    for imported_dll in all_imported_dlls(src_path):
        if imported_dll in stripped_qt_dll_names:
            broken_imports.append({"binary": destination.replace("\\", "/"), "imports_stripped_dll": imported_dll})

if broken_imports:
    raise RuntimeError(f"Kept Qt binary imports a stripped DLL: {broken_imports}")

provenance = {
    "method": "static PE tables, PyInstaller binary source allowlist, and kept-DLL dependency cross-check; no Qt/app execution",
    "system_icu": {
        "path": str(system_icu),
        "sha256": file_sha(system_icu),
        "qt_required_named_exports": qt_icu_symbols,
        "qt_required_count": len(qt_icu_symbols),
        "missing_exports": missing_icu,
        "bundled": False,
    },
    "excluded_icu": excluded_icu,
    "excluded_qt_bloat_count": len(excluded_qt_bloat),
    "excluded_qt_bloat": excluded_qt_bloat,
    "excluded_datas_count": excluded_datas_count,
    "kept_qt_translations": kept_qt_translations,
    "retained_required_dlls": {name: kept_by_name[name][0] for name in required_dlls},
    "broken_stripped_imports_check": "PASS (0 broken imports)",
    "approved_roots": [str(p) for p in approved_roots],
    "binaries": [
        {
            "destination": d.replace("\\", "/"),
            "source": str(Path(s).resolve()),
            "type": t,
            "bytes": Path(s).stat().st_size,
            "sha256": file_sha(s),
        }
        for d, s, t in a.binaries
    ],
}
(report_dir / "DEPENDENCY_PROVENANCE.json").write_text(
    json.dumps(provenance, ensure_ascii=False, indent=2),
    encoding="utf8",
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
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
    icon=str(icon_path),
    version=str(version_info_path),
)
