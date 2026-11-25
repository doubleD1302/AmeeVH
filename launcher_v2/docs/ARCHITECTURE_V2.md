# Stella Sora Việt Hóa PC Launcher v2.0 — Architecture Specification (`ARCHITECTURE_V2`)

**Version Target:** `2.0.0` (`LAUNCHER_VERSION = "2.0.0"`)  
**Workspace Root:** `StellaSora_VietHoa/launcher_v2/` (strictly isolated from legacy `StellaSora_VietHoa/launcher/`)  
**Stage:** Stage 1 Revision r5 Architecture Specification (Baseline for Stage 2 Implementation & Stage 3 Packaging)  
**Source Authority:** `PROJECT.md`, Stage 1A Explorers (`official_bg_and_assets_report.md`, `core_compat_audit.md`, `ui_ux_audit.md`), Stage 1r3 `native_ui_surface_spec.md`, Stage 1r4 & 1r5 User Gate Feedback, `stella-launcher-auto-update-assurance/SKILL.md`, `docs/ERROR_CODES.md`.

---

## 1. Design Goals & Architectural Invariants

1. **Strict Legacy Isolation:** All v2.0 source code, assets, previews, tests, build specs, and tools reside exclusively under `StellaSora_VietHoa/launcher_v2/`. Legacy `StellaSora_VietHoa/launcher/` (v1.3.4) and live game files (`Persistent_Store`, `StellaSora_Data`, `Patch_Store`, executables, DLLs, manifests) MUST NOT be modified during development or automated verification.
2. **Pure Core / Modular UI Separation:**
   - `launcher_v2/core/` is **100% pure Python** (zero `PySide6` / Qt imports) so all patching, network, official CDN, self-update, migration, background sync, diagnostics, and quick-fix logic is deterministically unit-testable without a display server.
   - `launcher_v2/ui/` decomposes v1.3.4's monolithic 1,224-line `main_window.py` into `app_controller.py` (state & async worker orchestration), `main_shell.py` (frameless window & canvas), `theme/`, `widgets/`, `screens/`, and `dialogs/`.
3. **Single-File Portable EXE (`--onefile`):** Packaged via PyInstaller (`upx=False`, `console=False`), requiring zero external runtimes (no Electron, no `onedir`, no WebView2 Runtime). Compatible with Windows 10 1809+ and Windows 11.
4. **Seamless v1.3.4 → v2.0 In-App Self-Update:** Preserves the exact `--apply-update <job.json>` pre-Qt CLI contract, 4-step Windows file-lock protocol, and `resource_version` wildcard `*` so existing v1.3.4 users upgrade directly inside the launcher.
5. **Append-Only Error Catalog Contract:** Preserves all **36 shared PC+Android** and **28 Android-only** `E-*` codes unmodified, keeps all **33 existing PC-only** codes stable, and appends **7 new PC-only v2 codes**.

---

## 2. Module Architecture Tree (`StellaSora_VietHoa/launcher_v2/`)

```text
StellaSora_VietHoa/launcher_v2/
├── app.py                              # Pre-Qt CLI (--apply-update, --smoke, --tls-check, --safe-graphics, --app-data-dir), faulthandler, crash sentinel, DPI awareness, Qt bootstrap
├── notifications.json                  # Canonical v2.0.0 release & announcement feed (synced with resources/notifications.json)
├── build.py                            # Isolated candidate builder (strict PATH allowlist, env scrub, coherent PySide6 check, SHA256SUMS, BUILD_RECEIPT.json)
├── StellaSora_Launcher_v2.spec         # PyInstaller --onefile windowed spec (System32 ICU ABI check, binary root allowlist, QML/Quick/PDF exclusion, opengl32sw.dll retained)
├── version_info.txt                    # Windows PE VSVersionInfo (2.0.0.0)
├── requirements-lock.txt               # Runtime dependencies lock (PySide6==6.12.0, Pillow==12.3.0, certifi==2026.7.22)
├── requirements-build-lock.txt         # Build dependencies lock (PyInstaller==6.22.3, pefile==2024.8.26, etc.)
│
├── docs/                               # Stage 1B–1r5 specifications
│   ├── ARCHITECTURE_V2.md              # This specification
│   ├── OFFICIAL_BG_SYNC_SPEC.md        # Yostar v1.6.0 API/CDN reverse-spec, 3-tier sync, luminance & scrim math
│   └── ASSET_INVENTORY_V2.md           # Legacy vs curated resource audit (~82.99 MiB -> ~5.76 MB) & pixel/9-slice rendering rules
│
├── preview/                            # Stage 1B–1r5 interactive preview & DPI screenshot gate
│   ├── index.html                      # Self-contained interactive HTML5/CSS/JS preview (all 8 screens/dialogs, Light/Dark, 100%/150%/compact, reduced_motion, DL sim, header close/Esc, SUPPORT_DONATION_ENABLED compact modal)
│   ├── styles.css / app.js / data.js   # Preview styling, interactive state machine & data model
│   ├── render_screenshots.py           # Deterministic headless Chrome/Edge screenshot renderer (100% & 150% DPI)
│   ├── assets/game/                    # Curated authentic game AssetBundle sprites, 9-slice headers/buttons, Tyrant chibis & ASAR SVGs (74 assets + manifest.json)
│   └── screenshots/                    # Static PNG captures at 100% & 150% DPI for User Approval Gate
│
├── resources/                          # Curated ~5.76 MB runtime asset bundle (packed into EXE)
│   ├── notifications.json              # Offline fallback announcement feed (v2.0.0)
│   ├── branding/
│   │   ├── app_icon.ico                # 256x256 RGBA launcher executable icon
│   │   ├── app_icon.png                # 1254x1254 RGBA high-res app badge
│   │   ├── background_native_2048x1451.png  # Tier 3 bundled key-art master (2048x1451 RGBA)
│   │   └── logo_ultrahd_2152x856.png   # 4x Lanczos game logo master (2152x856 RGBA)
│   ├── fonts/
│   │   ├── BeVietnamPro-Regular.ttf    # Primary Vietnamese UI font (400)
│   │   ├── BeVietnamPro-Medium.ttf     # Primary Vietnamese UI font (500)
│   │   ├── BeVietnamPro-SemiBold.ttf   # Primary Vietnamese UI font (600)
│   │   ├── BeVietnamPro-Bold.ttf       # Primary Vietnamese UI font (700)
│   │   └── OFL.txt                     # SIL Open Font License 1.1
│   ├── game/                           # Authentic game sprites, 9-slice headers/buttons, Tyrant chibis & ASAR SVGs (74 assets + manifest.json, ~429 KB)
│   ├── icons/                          # Minimal unmapped fallback SVG icon set from skin_r05/svg/icons/ (<=25 SVGs, 48x48 viewBox, ~30-40 KB)
│   ├── spinner/                        # Curated SVG spinner frames (spinner_00..11.svg)
│   └── support/
│       ├── techcombank_qr.png          # 526x526 RGB exact pixel crop
│       ├── momo_qr.png                 # 453x453 RGB exact pixel crop
│       ├── payment_methods.json        # Verified donation metadata & SHA256s
│       ├── QR_EXTRACTION.json          # Crop provenance metadata
│       └── help_content.json           # Searchable Guide & FAQ structured data
│
├── core/                               # 100% pure Python business logic (ZERO Qt imports)
│   ├── __init__.py
│   ├── types.py                        # OperationPhase, OperationEvent (with speed_bps/eta_seconds), GameInfo, NotificationItem, SupporterData
│   ├── config.py                       # PathManager (new %LOCALAPPDATA%\StellaSora_VietHoa_Launcher + --app-data-dir), ConfigManager, SUPPORT_DONATION_ENABLED = False flag, graphics_mode, derived_github_endpoints
│   ├── safety.py                       # InstallerError, sha256_file, atomic_json, safe_path (junction/symlink/reparse guards), manifest normalization
│   ├── tls.py                          # Windows Certificate Store + certifi Mozilla root bundle merger
│   ├── bg_sync.py                      # 3-Tier Official Background Sync (Yostar API/CDN, Local IDB/ASAR fallback, Tier 3 master, LuminanceProfile)
│   ├── migration.py                    # Non-destructive one-time migration from v1.3.4 StellaSora_Launcher_Candidate_r02 (journal backup_dir rewrite + corrupt config preservation)
│   ├── game_detection.py               # Yostar Standalone & Steam (4813850) discovery, find_game_exe_hint, Win32 Toolhelp32 running check, launch
│   ├── network.py                      # GitHub Release/notifications/manifest sync + ThreadPoolExecutor parallel download w/ 206 Range resume, EWMA MB/s & ETA
│   ├── installer.py                    # Transactional PatchInstaller (msvcrt lock, preimage SHA256, atomic journal, Catch-22 recovery, backup pruning)
│   ├── rollback.py                     # Unified rollback facade (official CDN restore default vs local backup restore)
│   ├── official_resources.py           # Yostar EN CDN client (nova-static.stellasora.global), bcrypt.dll AES-128-CBC, protobuf, delta resolver
│   ├── bsdiff40.py                     # Bounded pure-Python BSDIFF40 delta reconstruction
│   ├── official_restore.py             # OfficialRestoreEngine & check_official_update (Persistent_Store/ss_win.mani)
│   ├── vanilla_restore.py              # Offline vanilla restore (*.orig_en / unmodded backup / explicit vanilla_dir)
│   ├── self_update.py                  # Pre-Qt 4-step Windows EXE self-update helper (--apply-update) & schedule_update()
│   ├── update_notice.py                # SemVer comparison, wildcard '*' resource_version matching, Player.log patch conflict detection
│   ├── shortcut.py                     # Unicode-safe .lnk creator (OneDrive Desktop registry + UTF-16LE .vbs + Base64 PowerShell fallback)
│   ├── net_probe.py                    # Bounded (~8s) DNS + TCP:443 diagnostic probe (GitHub vs Microsoft vs 1.1.1.1) + captive portal HTML probe
│   ├── diagnostics.py                  # SystemReport collector (OS, DPI, disk, ACL/CFA writability, game state, AdbBridge)
│   ├── error_catalog.py                # 104 static E-* codes (76 PC + 28 Android-only) + dynamic E-HTTP-<nnn> + INTERNAL_MAP + classifiers
│   ├── error_report.py                 # PII-redacted human & dev diagnostic report builder + Win32 native clipboard copy
│   └── quick_fix.py                    # Pure QuickFixAction planner mapping E-* + ErrorContext to 8 contextual 1-click actions
│
├── ui/                                 # Modular PySide6 6.12.0 QWidget + QPainter UI layer (Stage 1r3 Stella Sora Porcelain & Hairline Grammar)
│   ├── __init__.py
│   ├── app_controller.py               # QThread/QRunnable worker orchestration, state store, quick-fix execution dispatcher
│   ├── main_shell.py                   # Frameless QMainWindow, custom titlebar, 3-tier cross-fade QPainter background canvas, underline nav rail, QStackedWidget, DPI change hooks
│   ├── theme/
│   │   ├── __init__.py
│   │   ├── tokens.py                   # Semantic Light Porcelain (#F6F9FD/#FFFFFF/#264278) & Overview Dark Navy tokens (eliminates v1.3.4 TEXT_WHITE=#304679 contradictions)
│   │   ├── adaptive_scrim.py           # AdaptiveScrim: adaptive linear/radial scrim (incl. top-left atmospheric vignette on light backdrops for floating logo) driven by LuminanceProfile
│   │   ├── qss_builder.py              # Clean dynamic QSS generator from tokens (no silent hex rewriting, zero nested glowing borders)
│   │   └── typography.py               # Be Vietnam Pro loader (4 weights), tabular-nums helper, zero +2px offset hack
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── asset_renderer.py           # Master-to-device QPainter renderer, draw_nine_slice helper (Unity m_Border L,B,R,T -> Qt L,T,R,B), QSvgRenderer DPR cache (incl. #1E3254 navy variants), pixel-exact QR painter
│   │   ├── porcelain_window_frame.py   # PorcelainWindowFrame: single outer #F6F9FD/#FFFFFF surface, #264278 navy header bar w/ optional cyan diagonal slash, uniform far-right close (×) button (btn_common_close_01.png / asar_close.svg) + Esc -> Overview on ALL subscreens & modals, 1px cosmetic hairline edge
│   │   ├── hairline_table.py           # HairlineTable / QStyledItemDelegate: flat #FFFFFF/#EEF4FA zebra rows, 1px #D5E0EE dividers, #D7F1F6 + 3px #12B8C4 selection bar (zero nested rounded cards)
│   │   ├── glass_card.py               # Translucent Overview dock surface (dark-navy Official-style panel w/ top accent edge, zero nested per-row boxes)
│   │   ├── action_button.py            # 9-slice faceted game CTA (btn_common_db_l_1/2/3), white-navy faceted secondary & borderless segment buttons w/ reduced_motion support
│   │   ├── progress_panel.py           # Inline recessed download strip (%, MB downloaded/total, MB/s speed, ETA, inline file status, cancel button)
│   │   ├── status_badge.py             # Compact inline platform/version tags & left-accented status strips (no glowing pill clutter)
│   │   ├── path_selector.py            # Flat hairline-framed Unicode path bar + context menu + borderless detect/browse triggers
│   │   └── toast_banner.py             # Non-blocking inline toast / notification strip
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── overview_screen.py          # Hub: clean floating Logo (no wrap box), unboxed star Free-Translation subtitle, flat 3-row Latest Notices, Control Dock, unified utility strip
│   │   ├── notifications_screen.py     # PorcelainWindowFrame, search, underline filter tabs, 2-col hairline master-detail split w/ watermarked reading pane
│   │   ├── guide_screen.py             # PorcelainWindowFrame, underline topic tabs, flat 3-step strip, HairlineTable steps + unified FAQ accordion table
│   │   ├── support_screen.py           # PorcelainWindowFrame (when SUPPORT_DONATION_ENABLED=True): payment tabs, 3-row HairlineTable & pixel-exact QR (QR/bank assets preserved in resources/support/ for 1-flag re-enable)
│   │   ├── settings_screen.py          # PorcelainWindowFrame, 4 flat #EEF4FA left-accented sections, hairline form rows, flat segmented control, 2-row migration table
│   │   └── tools_screen.py             # PorcelainWindowFrame, 2-column 4+4 HairlineTable (Dữ liệu game & Tiện ích/Chẩn đoán) w/ white-navy action buttons
│   └── dialogs/
│       ├── __init__.py
│       ├── support_locked_dialog.py    # Compact centered Light Porcelain modal (~520-580px, content-hugging) shown when SUPPORT_DONATION_ENABLED=False (keeps active screen visible behind subtle scrim; NO credits table)
│       ├── smart_error_dialog.py       # PorcelainWindowFrame alert header (#264278/#E11D48), plain-language steps, 3x3 HairlineTable diagnostic grid, async net_probe, 8 quick-fix buttons w/ navy ASAR SVGs
│       ├── game_selection_dialog.py    # PorcelainWindowFrame, flat #FFF8E1 wrong-folder strip, unified HairlineTable Steam/Yostar install rows
│       ├── confirmation_dialog.py      # PorcelainWindowFrame modal with cached Pillow/downscale backdrop blur (no QGraphicsBlurEffect)
│       ├── install_completed_dialog.py # Post-install summary + shortcut + launch game action
│       └── update_notice_dialog.py     # Launcher self-update prompt + release notes + 1-click upgrade trigger
│
├── tools/
│   └── verify_v2_update_readiness.py   # PC-specific Seamless Update Readiness gate verifier (Gates PC-1..PC-5)
│
└── tests/                              # Independent QA & fault-injection test suite (Role 5)
    ├── __init__.py
    ├── test_bg_sync.py                 # Tier 1/2/3 sync, MD5 signing, 403 UA header, IDB/ASAR fallback, luminance, reduced_motion
    ├── test_parallel_download.py       # ThreadPoolExecutor pool, 206 Range resume, EWMA MB/s & ETA calculation
    ├── test_migration.py               # r02 -> v2 migration, journal backup_dir rewrite, corrupt config preservation, --app-data-dir skip
    ├── test_self_update_v2.py          # v1.3.4 -> v2.0 --apply-update job schema, 4-step file lock, rollback, cleanup
    ├── test_error_and_quick_fix.py     # 104 error codes parity, captive portal, CFA detection, PII redaction, 8 quick-fix plans
    ├── test_core_parity.py             # Ported core tests (safety, installer, rollback, official_resources, bsdiff40, shortcut, update_notice)
    ├── test_ui_dpi_and_screens.py      # Offscreen PySide6 smoke tests at 100%/150%/200% DPI, adaptive scrim contrast, QR exactness
    └── test_packaging_gates.py         # verify_v2_update_readiness.py + EXE --smoke --app-data-dir test
```

---

## 3. Strict 5-Role File Ownership Matrix (Stage 2 & Stage 3)

Every file and directory under `StellaSora_VietHoa/launcher_v2/` has **exactly one** designated writer role. Cross-role edits are prohibited; cross-module integration happens strictly through the contracts defined in §5–§7 and `PROJECT.md`.

| Role ID | Role Title | Exclusive Write Ownership | Milestones | Forbidden Targets |
|---|---|---|---|---|
| **Role 1** | **Architect & Coordinator** | `PROJECT.md`, `launcher_v2/docs/ARCHITECTURE_V2.md`, `STATUS.json` / `CHECKPOINT.json` updates (orchestrator only) | M1–M7 | Application source/UI/test files |
| **Role 2** | **Official Background & Asset Researcher** | `launcher_v2/docs/OFFICIAL_BG_SYNC_SPEC.md`, `launcher_v2/docs/ASSET_INVENTORY_V2.md`, `launcher_v2/resources/**/*`, `launcher_v2/core/bg_sync.py` | M1, M2 (Stage 2A) | `core/*` (except `bg_sync.py`), `ui/*`, `app.py`, `launcher/` |
| **Role 3** | **UI/UX Designer & Preview Builder** | `launcher_v2/preview/**/*`, `launcher_v2/ui/**/*` (`app_controller.py`, `main_shell.py`, `theme/*`, `widgets/*`, `screens/*`, `dialogs/*`) | M1, M5 (Stage 2D) | `core/*`, `app.py`, `resources/*`, `tests/*`, `launcher/` |
| **Role 4** | **Core, Compatibility & Diagnostics Engineer** | `launcher_v2/app.py`, `launcher_v2/notifications.json`, `launcher_v2/core/*` (all modules **except** `bg_sync.py`), `StellaSora_VietHoa/docs/ERROR_CODES.md` (append-only PC-only rows) | M3, M4 (Stage 2B–2C) | `core/bg_sync.py`, `ui/*`, `resources/*`, `launcher/`, existing shared/Android codes in `ERROR_CODES.md` |
| **Role 5** | **QA & Packaging Verifier** | `launcher_v2/tests/**/*`, `launcher_v2/tools/verify_v2_update_readiness.py`, `launcher_v2/build.py`, `launcher_v2/StellaSora_Launcher_v2.spec`, `launcher_v2/version_info.txt`, `launcher_v2/requirements*.txt`, `dist/` candidate artifacts (plus independent Reviewer/Challenger/Auditor gates) | M6, M7 (Stage 2E–3) | Modifying `core/` or `ui/` directly (defects are reported back to Role 2/3/4); overwriting `launcher/` or game data |

---

## 4. UI / Rendering Solution Evaluation Matrix

### 4.1 Candidate Stack Comparison

| Candidate Stack | Single-File Portable EXE (No Electron / No Runtime) | Win10 1809+ / Win11 & Weak-GPU Resilience | Multi-DPI (100%–200%, Mixed Monitors) | Custom Glass / Cross-Fade / Direct Master Crispness | Verdict |
|---|---|---|---|---|---|
| **1. PySide6 6.12.0 `QWidget` + Direct `QPainter` + `QSvgRenderer` + `Pillow 12.3.0`** | **YES** — Proven in project `.venv` (`PySide6 6.12.0` + `PyInstaller 6.22.3` `--onefile`); zero external runtime; ~85–105 MB after pruning unused Qt modules & resources | **HIGHEST** — `QWidget` raster backing store renders without DirectX/OpenGL shader compilation; ships `opengl32sw.dll` (19.68 MB) for software OpenGL fallback; replacing `QGraphicsBlurEffect` with cached Pillow/downscale blur removes driver glitches | **EXCELLENT** — Native `SetProcessDpiAwareness(2)` (Per-Monitor V2) + `PassThrough` rounding + direct master-to-device `QPainter.drawPixmap` (eliminates v1.3.4 `QGraphicsView` proxy blur) | **EXCELLENT** — 350 ms `QVariantAnimation` cross-fade, exact luminance scrims, crisp `QSvgRenderer` icons at `logical * dpr`, nearest-neighbor QR painting | **SELECTED** |
| **2. PySide6 + `PySide6-Fluent-Widgets` (`qfluentwidgets`)** | **YES**, but **absent from `.venv`** (only in system Python) and adds heavy Win11 styling that fights Stella Sora key art | **MEDIUM** — Acrylic/Mica DWM hooks glitch on Win10 1809, RDP, and software OpenGL mode | **GOOD** | **MEDIUM** — Forces overriding library QSS to achieve translucent Starlit layout | **REJECTED** |
| **3. PySide6 `QtQuick` / QML** | **YES** (+12.5 MB `Qt6Quick.dll` + `Qt6Qml.dll` + `Qt6QmlModels.dll`) | **LOW–MEDIUM** — Relies on RHI D3D11/OpenGL; weak/old GPU drivers crash unless `QSG_RHI_BACKEND=software` | **GOOD** | **EXCELLENT** (when GPU works) | **REJECTED** (violates R5 weak-GPU resilience) |
| **4. PySide6 `QtWebEngine` / `pywebview` (WebView2)** | **NO / RISKY** — `QtWebEngine` adds >150 MB Chromium; `WebView2` requires external Edge WebView2 Runtime on Win10 1809 | **POOR** — Violates R5 ("không đòi cài thêm runtime ngoài") | **GOOD** | **EXCELLENT** | **DISQUALIFIED** (violates R1 & R5) |
| **5. Tkinter / CustomTkinter** | **YES** (~15 MB) | **HIGH** | **POOR** — Blurry bitmap scaling and broken per-monitor DPI V2 | **POOR** — No native alpha compositing, smooth cross-fade, or translucent glass | **DISQUALIFIED** (fails R2/R3/R5 visual & DPI requirements) |

### 4.2 Packaging, DLL Hygiene & Size Optimization (`build.py` + `StellaSora_Launcher_v2.spec`)

1. **Preserve r03 System32 ICU & PATH Hygiene (Mandatory):**
   - `r02` crashed with `ImportError: DLL load failed while importing QtWidgets: The specified procedure could not be found` because ambient `PATH` pulled an incompatible `icuuc.dll` missing the 20 bare C ABI `ucnv_*` symbols required by `Qt6Core.dll`.
   - `build.py` MUST scrub `PYTHONPATH`, `PYTHONHOME`, `QT_PLUGIN_PATH`, `QT_QPA_PLATFORM_PLUGIN_PATH`, `QML2_IMPORT_PATH`, `QML_IMPORT_PATH`, `QT_DEBUG_PLUGINS`, and `CONDA_*`, and enforce a strict `PATH` allowlist containing only `[System32, Windows, .venv\Scripts, base_prefix, base_prefix\DLLs, qt_wheel_dir]`.
   - `StellaSora_Launcher_v2.spec` MUST inspect `Qt6Core.dll` and `C:\Windows\System32\icuuc.dll` with `pefile` at build time (no Qt execution), verify all 20 ICU symbols exist, strip `icuuc.dll`, `icuin.dll`, `icudt.dll`, `icu.dll` from `a.binaries`, and raise `RuntimeError` if any collected binary originates outside `[sys.prefix, sys.base_prefix, Windows]`.
2. **Exclude Unused Qt Submodules While Keeping `opengl32sw.dll`:**
   - v1.3.4 `DEPENDENCY_PROVENANCE.json` proved PyInstaller auto-collected unused `Qt6Quick.dll` (6.44 MB), `Qt6Qml.dll` (5.14 MB), `Qt6Pdf.dll` (4.41 MB), `Qt6QmlModels.dll` (0.97 MB) (~17 MB) plus WebEngine hooks if present.
   - `StellaSora_Launcher_v2.spec` MUST add `PySide6.QtQml`, `PySide6.QtQuick`, `PySide6.QtQuickWidgets`, `PySide6.QtPdf`, `PySide6.QtWebEngineCore`, `PySide6.QtWebEngineWidgets`, `tkinter`, `matplotlib`, `scipy`, `notebook`, `pytest`, `unittest` to `excludes` and filter out `Qt6Quick*`, `Qt6Qml*`, `Qt6Pdf*`, `Qt6WebEngine*` from `a.binaries` / `a.datas`.
   - `StellaSora_Launcher_v2.spec` MUST **explicitly retain `opengl32sw.dll` (19.68 MB)** and `PySide6.QtSvg` / `imageformats` (`qpng`, `qjpeg`, `qwebp`, `qsvg`, `qico`) so software OpenGL fallback and all Yostar/bundled image formats work on every Windows 10 1809+ / 11 machine.
   - Combined with curating `launcher_v2/resources/` from `82.99 MiB` to `~5.76 MB`, single-file EXE size drops from **126.4 MB** to an estimated **~43–53 MB**.

### 4.3 Pre-Qt Bootstrap, Crash Sentinel & Software Rendering Fallback (`app.py`)

Before importing **any** `PySide6` module, `launcher_v2/app.py` executes in strict order:

1. **CLI Pre-Qt Fast Paths:**
   - `--smoke`: prints `OK: SMOKE TEST PASSED` (or validates non-Qt `PathManager`/`ConfigManager` if `--app-data-dir` is also given) and returns `0`.
   - `--tls-check`: prints `tls.info()` and returns `0`.
   - `--apply-update <job.json>`: invokes `core.self_update.apply_job(job_path)` and exits **without ever loading Qt DLLs** (ensuring self-update succeeds even if a previous DLL/GPU failure occurred).
2. **Pre-Qt Crash Catcher & `faulthandler`:**
   - Resolve early `app_data_dir` via `--app-data-dir` (or `%LOCALAPPDATA%\StellaSora_VietHoa_Launcher`) using stdlib only.
   - Open `<app_data_dir>/logs/native_crash.log` and call `faulthandler.enable(file=..., all_threads=True)` to capture native C++/Qt segfaults/access violations.
3. **Graphics Compatibility & Crash Sentinel Check (Pre-Qt):**
   - Check three triggers using stdlib `json`:
     1. CLI flag `--safe-graphics`
     2. `config.json` has `"graphics_mode": "software"`
     3. `<app_data_dir>/.graphics_boot_pending` sentinel file already exists (meaning the previous launch crashed natively before completing GUI startup!).
   - If any trigger is active:
     - Set `os.environ["QT_OPENGL"] = "software"`
     - Set `os.environ["QSG_RHI_BACKEND"] = "software"`
     - Set flag `software_rendering = True` so `QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)` is called before `QApplication(sys.argv)`.
     - If triggered by `.graphics_boot_pending` (uncleaned native crash), persist `"graphics_mode": "software"` (unless config is `_corrupt`), record `E-GPU-RENDER` startup warning, and display a gentle status toast once the window opens.
   - Create `<app_data_dir>/.graphics_boot_pending` before `QApplication(...)`; remove it via `QTimer.singleShot(3000, ...)` after `main_shell.show()` succeeds.
4. **Per-Monitor V2 DPI & `PassThrough` Scaling:**
   - Call `ctypes.windll.shcore.SetProcessDpiAwareness(2)` (fallback `SetProcessDPIAware()`) and `SetCurrentProcessExplicitAppUserModelID('stellasora.viethoa.launcher')`.
   - Call `QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)` before `QApplication(sys.argv)`.
5. **Startup Migration & Update Cleanup:**
   - Run `cleanup_update_artifacts()` on `exe_dir`, `<v2_app_data>/update_helper`, and `<r02_app_data>/update_helper`.
   - Run `core.migration.migrate_from_r02_if_needed(pm)` (skipped when `--app-data-dir` is explicitly provided).

### 4.4 Responsive Layout & Multi-DPI Rules (1366×768 → 4K, 100%–200%)

- **No `QGraphicsView` / `OverviewViewport` proxy scaling:** `MainShell` uses responsive `QWidget` layouts in logical DIPs, painting backgrounds and logos directly from full-resolution masters onto device pixels (`target_rect * dpr`).
- **No `QGraphicsBlurEffect`:** Modal scrims/cards use either solid translucent glass fills (`rgba(...)`) or a one-time downscale-and-Gaussian-blur snapshot via `Pillow 12.3.0` (automatically bypassed when `reduced_motion=True` or `software_rendering=True`).
- **DPI Breakpoints & Monitor Dragging:**
  - `1366×768 @ 100%` (`1366×768` DIP): default `1160×700` DIP.
  - `1366×768 @ 125%` (`1093×614` DIP): clamps to `1077×598` DIP (`availableGeometry() - 16px`), compact vertical spacing, zero horizontal overflow.
  - `1920×1080 @ 150%` (`1280×720` DIP): clamps to `1200×704` DIP, unclipped Overview with zero vertical scroll.
  - `1920×1080 @ 200%` (`960×540` DIP): activates **Compact Breakpoint (`width < 1000` or `height < 620` DIP)** — nav rail compacts, Overview stacks vertically inside a vertical `QScrollArea` (horizontal scrollbar strictly `ScrollBarAlwaysOff`), 2-column modals collapse to 1 column below `780 DIP`.
  - Hook `windowHandle().screenChanged` and `QEvent.Type.DevicePixelRatioChange` to re-clamp geometry inside `screen.availableGeometry()` and trigger crisp SVG/pixmap repaint when moving between monitors of different DPI.

### 4.5 Subscreen Close Contract & Support Feature Flag (`PorcelainWindowFrame`, `core/config.py`)

1. **Universal `PorcelainWindowFrame` Close Button & `Esc` Shortcut:**
   - **ALL** `PorcelainWindowFrame` subscreens (`Notifications`, `Guide`, `Settings`, `Tools`, plus `Support` when `SUPPORT_DONATION_ENABLED = True`) and modals (`SmartErrorDialog`, `GameSelectionDialog`, `SupportLockedDialog`) MUST include a crisp Close (`×`) button (`btn_common_close_01.png`, fallback `asar_close.svg`) on the far right of their `#264278` navy header bar.
   - On `SettingsScreen` (which places `Mặc định` and `Lưu & Đồng bộ` in the header), the Close (`×`) button sits at the **far right** after those controls, separated by a `1px solid rgba(255, 255, 255, 0.18)` vertical divider and clean gap so buttons never crowd or overlap.
   - Clicking any panel/modal Close (`×`) button or pressing `Esc` (`QShortcut(QKeySequence.StandardKey.Cancel)` / `keyPressEvent`) closes the active subscreen/modal and returns cleanly to the underlying screen (`Overview` for full-pane subscreens, or the preserved active screen behind `SupportLockedDialog`).
2. **Temporary Donation Lock (`SUPPORT_DONATION_ENABLED = False` in `core/config.py`):**
   - `core/config.py` defines `SUPPORT_DONATION_ENABLED: bool = False` as the default feature flag.
   - When `SUPPORT_DONATION_ENABLED` is `False`, clicking the `Ủng hộ` nav tab **MUST NOT** render a full-pane screen or display any QR codes, bank/wallet account numbers, payment method tabs, copy-account controls, or a `"Đội ngũ thực hiện"` / credits table. Instead, it opens `SupportLockedDialog` — a **compact, centered Light Porcelain (`#FFFFFF`) modal dialog** (`~520–580px` width, content-hugging height) over a subtle translucent scrim, keeping the currently active screen visible behind the modal without losing user context.
   - `SupportLockedDialog` Header: `#264278` Navy header bar with `Ủng hộ dự án`, `Tạm đóng` status tag, and far-right Close `×` button (`btn_common_close_01.png`, fallback `asar_close.svg`). Dismissible via `×`, `Esc`, backdrop click, or the footer `Đã hiểu` button without losing the underlying screen.
   - `SupportLockedDialog` Body: **NO `"Đội ngũ thực hiện"` / credits table**; clean, balanced composition with Chibi Ma Vương (`playerhead_main_ccc.png`), title `Chức năng ủng hộ hiện đang tạm đóng`, prominent affirmation **Bản Việt hóa Stella Sora luôn hoàn toàn miễn phí (cho đến khi hết kinh phí duy trì)**, concise anti-scam reminder against paid resellers, and a compact footer with the `Đã hiểu` CTA.
   - Verified donation assets (`resources/support/techcombank_qr.png`, `resources/support/momo_qr.png`, `resources/support/payment_methods.json`) remain safely preserved and SHA256-verified inside `resources/` so donations can be re-enabled cleanly by toggling `SUPPORT_DONATION_ENABLED = True` without rebuilding assets or UI code.

---

## 5. R4 Interface Contracts (Core Engine, Parallel DL, Self-Update & Migration)

### 5.1 Game Detection & Launch (`core/game_detection.py`)

Preserves 100% of v1.3.4 contracts:
- Discovery priority: (0) `exe_dir` and `exe_dir.parent`; (1) Steam libraries (`HKLM\SOFTWARE\WOW6432Node\Valve\Steam`, `HKLM\SOFTWARE\Valve\Steam`, `HKCU\Software\Valve\Steam`, `libraryfolders.vdf`, common `<Drive>:\Steam` / `SteamLibrary`); (2) fixed/removable drives `C..Z` via `GetLogicalDrives` + `GetDriveTypeW` (skipping network drives); (3) Windows Uninstall registry (`InstallLocation`, `InstallLocation\StellaSora_EN`).
- Steam AppID `4813850` detection (`"steamapps" in path.lower()` or `steam_appid.txt`), launching via `os.startfile("steam://rungameid/4813850")` with `DETACHED_PROCESS` fallback.
- `find_game_exe_hint(chosen_dir)` scans parent + up to 80 child dirs for `StellaSora.exe` and feeds `GameSelectionDialog` wrong-folder hint banner and `E-NO-EXE` summary.
- `is_game_process_running()` uses 64-bit Win32 Toolhelp32 snapshot + `tasklist` fallback.

### 5.2 Parallel Download Engine with Speed & ETA (`core/network.py`, `core/official_resources.py`, `core/types.py`)

Upgrades v1.3.4 sequential loops (`network.py:622-637` and `OfficialDownloader.prepare()`) to satisfy R4:
- **`OperationEvent` backward-compatible extension (`core/types.py`):**
  ```python
  @dataclass
  class OperationEvent:
      operation: str
      phase: OperationPhase
      message: str
      completed: int = 0
      total: int = 0
      unit: str = ""
      # v2.0 telemetry fields (optional defaults preserve v1.3.4 callers/tests)
      speed_bps: float = 0.0
      eta_seconds: float | None = None
      files_completed: int = 0
      files_total: int = 0
  ```
- **Bounded `ThreadPoolExecutor` Pool:**
  - `NetworkService.prepare_payload()` and `OfficialDownloader.prepare()` use `ThreadPoolExecutor(max_workers=min(4, max(1, len(pending_files))))` (configurable `max_workers=3..4`).
  - Each worker retains strict per-file `.part` HTTP `206 Partial Content` `Range` resume, `Content-Range` (`bytes start-end/size`) + `Content-Length` validation, `416` cleanup, up to 5 retries with exponential backoff, and SHA256 verification.
  - **Captive Portal Detection:** Before parsing JSON or accepting a binary payload, if HTTP `200` returns `Content-Type: text/html` or body starts with `<!doctype html` / `<html`, raise `InstallerError(..., "NET_CAPTIVE")` (mapped to `E-NET-CAPTIVE`) rather than generic `E-DATA-JSON`.
- **Thread-Safe `DownloadProgressAggregator`:**
  - Pre-sums `total_bytes = sum(item.size for item in items)` (already-cached/resumed `.part` bytes counted up front).
  - Protected by `threading.Lock()`, updates `bytes_done` on every 256 KB chunk across all active workers, computes a 2.5-second sliding-window EWMA `speed_bps`, computes `eta_seconds = (total_bytes - bytes_done) / speed_bps` when `speed_bps > 1024`, and throttles UI `OperationEvent` emissions to ~10 Hz (every 100 ms or on file completion).
  - Cancellation (`cancel_event.set()`) cleanly halts pending futures and aborts active streams without deleting valid `.part` resume data.
  - On pool-wide disk I/O or simultaneous multi-worker abort, wraps inner cause into `InstallerError(..., "PARALLEL_DL")` (`E-PARALLEL-DL`) while preserving the underlying `ErrorContext`.

### 5.3 Patching, Rollback & Official Publisher Integration

Preserves 100% of v1.3.4 transactional guarantees:
- `PatchInstaller` (`core/installer.py`): `msvcrt` exclusive file lock, preimage SHA256 verification, atomic journal write (`atomic_json` clearing hidden/readonly attrs), `.vietnamese_patch_receipt.json` (`schema: 2`), `verify_installed()`, `recover()`, `_recover_journal_superseded_aware()`, backup pruning preserving vanilla preimages.
- `OfficialClient` / `OfficialRestoreEngine` (`core/official_resources.py`, `core/official_restore.py`, `core/bsdiff40.py`): `https://nova-static.stellasora.global`, Windows CNG `bcrypt.dll` AES-128-CBC decryption, protobuf manifest parsing, bounded BSDIFF40 delta reconstruction, `check_official_update()` reading `Persistent_Store/ss_win.mani`, and `auto_restore_before_game_update` flow.
- `VanillaRestoreEngine` (`core/vanilla_restore.py`) & `RollbackEngine` (`core/rollback.py`): supports both `"official"` CDN restore and `"local_backup"` / `*.orig_en` offline restore.
- `update_notice.py`: wildcard `*` matching in `matches(observed, expected)` (splitting on `[,;|]`) and `Player.log` game patch conflict detection.
- `shortcut.py`: OneDrive Desktop Registry resolution + UTF-16LE `.vbs` (`cscript.exe`) + UTF-16LE Base64 PowerShell fallback for Unicode paths.

### 5.4 v1.3.4 → v2.0 Self-Update Contract (`core/self_update.py` + `app.py`)

When a v1.3.4 user clicks **"Cập nhật ngay"** to upgrade to `v2.0.0`, v1.3.4 downloads `StellaSora-Windows_v2.0.0.exe`, copies that **v2.0.0 EXE** to `<r02_app_data>/update_helper/helper_<uuid>.exe`, writes `<uuid>.json`, and executes:
```text
helper_<uuid>.exe --apply-update <job.json>
```
Therefore, `launcher_v2/app.py` and `launcher_v2/core/self_update.py` MUST satisfy this immutable contract:

1. **Exact Job JSON Input Schema:**
   ```json
   {
     "source": "<path_to_downloaded_v2_exe>",
     "target": "<path_to_running_v134_exe>",
     "sha256": "<lowercase_sha256_of_source>",
     "preimage_sha256": "<lowercase_sha256_of_target>",
     "timeout": 60,
     "parent_pid": 12345,
     "allow_force_close": true
   }
   ```
2. **4-Step Windows File-Lock Protocol (`apply_job`):**
   - **Step 1 (`parent_pid` Wait):** Wait on single integer `parent_pid` (ignore legacy `parent_pids` lists; never touch `explorer.exe`) via Win32 `OpenProcess(SYNCHRONIZE)` + `WaitForSingleObject` up to `3.0s` (when `allow_force_close=True`).
   - **Step 2 (Verified `taskkill`):** If still alive, verify `QueryFullProcessImageNameW(handle) == target.resolve()` before calling `taskkill /F /PID <parent_pid>` (`CREATE_NO_WINDOW`, no `/T`), then wait until exit.
   - **Step 3 (Rename-Before-Replace & Backup):** Verify `source` and `target` SHA256s; create `target.preupdate.<uuid>` backup; stage `.launcher_update_<uuid>.exe`; attempt `os.replace(tmp, target)`; on `PermissionError` execute `target.rename(old_target)` (`.old_<uuid>`) followed by `os.replace(tmp, target)`, rolling back `old_target.rename(target)` if `os.replace` fails.
   - **Step 4 (SHA256 Readback & Survival Relaunch):** Verify `sha256_file(target) == job['sha256']`; spawn `subprocess.Popen([str(target)], cwd=str(target.parent))`; sleep `0.7s`; verify `proc.poll() in (None, 0)`. On relaunch failure, atomically restore from `.preupdate.<uuid>` (or raise `UPDATE_RECOVERY_REQUIRED`). Write `<job>.result.json` (`status: 'started' | 'error' | 'recovery_required'`).
3. **Publishing & Notification Gates (`verify_v2_update_readiness.py`):**
   - **Gate PC-1:** `launcher_v2/core/config.py:LAUNCHER_VERSION` == `launcher_v2/version_info.txt` == `launcher_v2/notifications.json` (`version` + `type == "release"` item with `f"v{LAUNCHER_VERSION}"` in `title`).
   - **Gate PC-2:** `launcher_v2/core/self_update.py` contains `SYNCHRONIZE`, `QueryFullProcessImageNameW`, `taskkill`, `target.rename`, `sha256_file`, and `Popen`; `launcher_v2/app.py` routes `--apply-update` before any `PySide6` import.
   - **Gate PC-3:** `patch_manifest.json` contains `*` in `resource_version` and `update_notice.matches()` accepts `*`.
   - **Gate PC-4:** Built candidate EXE matches `SHA256SUMS.txt` and passes `--smoke --app-data-dir <tmp>`.
   - **Gate PC-5:** Automated end-to-end simulation of v1.3.4 `schedule_update()` invoking v2.0 `apply_job()` on a test EXE + post-upgrade migration.

### 5.5 Non-Destructive v1.3.4 Data Migration (`core/migration.py`)

- **Paths:**
  - Legacy v1.3.4 `app_data_dir`: `%LOCALAPPDATA%\StellaSora_Launcher_Candidate_r02`
  - New v2.0 `app_data_dir`: `%LOCALAPPDATA%\StellaSora_VietHoa_Launcher`
- **Guardrail:** If `--app-data-dir` (or `override_app_data`) is passed, migration is **strictly skipped** so test/smoke runs remain 100% isolated.
- **Idempotency:** If `<target>/.migrated_from_r02.json` already exists, migration is skipped (unless missing critical artifacts and user triggers manual re-check). If legacy `r02` directory does not exist, write `.migrated_from_r02.json` with `status: "fresh_install"` and skip.
- **Non-Destructive Copy Protocol (Never Deletes `r02`):**
  1. **`config.json` & corrupt configs:** Copy any existing `config.corrupt.*.json` files. If `r02/config.json` exists and `v2/config.json` does not, copy `r02/config.json` byte-for-byte **even if invalid JSON**. (`ConfigManager.load()` then preserves `_corrupt=True` and triggers `E-MIGRATION` / `E-CONFIG-CHANNEL` guidance without silently discarding user settings.) Update `"version"` only on clean save.
  2. **`backups/`:** Copy directory tree (`shutil.copytree(..., dirs_exist_ok=True)`), preserving original modification times and SHA256s.
  3. **`journals/*.json` (`backup_dir` Path Rewriting — Critical):**
     - `PatchInstaller.recover()` (`installer.py:125-128`) validates `Path(j['backup_dir']).resolve().relative_to(self.get_backup_dir_for_root(root).resolve())`.
     - If a migrated journal's `backup_dir` still points to `...\StellaSora_Launcher_Candidate_r02\backups\<hash>`, `recover()` in v2.0 would fail with `BACKUP_INVALID`!
     - Therefore, during migration of `journals/*.json`, `migration.py` MUST inspect `j.get('backup_dir')` (and any `entries[*].backup_path` if present): if it resolves under `r02_dir / 'backups'`, rewrite the prefix cleanly to `v2_dir / 'backups'` via `atomic_json()`, while recording the original path in `j['_migrated_from_backup_dir']`.
  4. **`official_check.json` & `payload_cache/shared_downloads/`:** Copy if present and target absent (skip `update_helper/` and `logs/`).
  5. **Completion Marker & Partial-Failure Handling:** Write `<v2_dir>/.migrated_from_r02.json` containing timestamp, copied file counts, journal rewrite count, and any per-file warnings. If any copy fails (e.g., file locked/permission error) or `config.json` was corrupt, raise/surface non-fatal `E-MIGRATION` warning so the user sees the Smart Error Assistant while keeping both `r02` and copied files intact.

---

## 6. R5 Error Catalog & 8-Action Smart Error Assistant Contracts

### 6.1 `ERROR_CODES.md` Append-Only Rule & Code Inventory

- **Total Static Codes in v2.0:** **104 static codes** + dynamic `E-HTTP-<nnn>`:
  - **36 Shared PC + Android codes (IMMUTABLE):** `E-CONFIG-CHANNEL`, `E-DATA-JSON`, `E-DATA-SCHEMA`, `E-DATA-UNVERIFIED`, `E-HTTP-404`, `E-HTTP-4XX`, `E-HTTP-5XX`, `E-HTTP-RATE`, `E-NET`, `E-NET-DNS`, `E-NET-OFFLINE`, `E-NET-REFUSED`, `E-NET-RESET`, `E-NET-TIMEOUT`, `E-NET-TLS`, `E-NET-TLS-CERT`, `E-SYNC-PENDING`, `E-DL-RANGE`, `E-DL-RESPONSE`, `E-DL-TIMEOUT`, `E-DL-VERIFY`, `E-MANIFEST-INVALID`, `E-SECURITY`, `E-BACKUP`, `E-BUSY`, `E-FILE-CHANGED`, `E-FILE-MISMATCH`, `E-GAME-RUNNING`, `E-JOURNAL`, `E-NO-RECEIPT`, `E-RECOVERY-REQUIRED`, `E-STORAGE`, `E-VERIFY-WRITE`, `E-CANCELLED`, `E-INTERNAL`, `E-UNKNOWN`.
  - **28 Android-Only codes (IMMUTABLE):** `E-ADB`, `E-ADB-AUTH`, `E-ADB-INPUT`, `E-ADB-KEY`, `E-ADB-NOT-CONNECTED`, `E-ADB-PAIR`, `E-ADB-START`, `E-ADB-TIMEOUT`, `E-APK-INVALID`, `E-APK-NONE`, `E-APK-SIGNATURE`, `E-APK-VERIFY`, `E-BIND-MISMATCH`, `E-DEVOPT`, `E-DL-OVERSIZE`, `E-DL-PARAM`, `E-GAME-ROOT-CHANGED`, `E-GAME-STATE`, `E-GAME-VERSION`, `E-NO-GAME`, `E-NO-PACKAGE`, `E-NO-RECOVERY`, `E-PKG-MISMATCH`, `E-STORAGE-ACCESS`, `E-TIMEOUT`, `E-UI-BLOCKED`, `E-VER-CHANGED`, `E-VERIFY`.
  - **33 Existing PC-Only codes (STABLE):** `E-CONFIG-SAVE`, `E-NET-BLOCKED`, `E-NET-PROXY`, `E-RELEASE`, `E-DL-FAILED`, `E-DOWNGRADE`, `E-LOCAL-PAYLOAD`, `E-MANIFEST-MISSING`, `E-MANIFEST-PLATFORM`, `E-MANIFEST-VERSION`, `E-GAME-NOT-FOUND`, `E-LAUNCH-FAILED`, `E-NO-EXE`, `E-NO-GAME-FOLDER`, `E-ROOT-MISMATCH`, `E-FILE-DENIED`, `E-FILE-IN-USE`, `E-FILE-MISSING`, `E-INSTALL-ROLLED-BACK`, `E-RECEIPT-MISMATCH`, `E-UPDATE-INVALID`, `E-UPDATE-RECOVERY`, `E-UPDATE-RELAUNCH`, `E-UPDATE-TIMEOUT`, `E-UPDATE-UNSUPPORTED`, `E-OFFICIAL-CRYPTO`, `E-OFFICIAL-FORMAT`, `E-OFFICIAL-INCONSISTENT`, `E-OFFICIAL-NET`, `E-OFFICIAL-NOTFOUND`, `E-OFFICIAL-REGION`, `E-MEMORY`, `E-SHORTCUT`.
  - **7 New PC-Only v2.0 Codes (APPEND-ONLY to `launcher_v2/core/error_catalog.py` & `docs/ERROR_CODES.md` PC-only rows):**

| Code | Level | Internal Map Key(s) | Root Cause | Default Quick-Fix Actions |
|---|---|---|---|---|
| `E-STARTUP-DLL` | `error` | `STARTUP_DLL` | Pre-GUI startup failure (`ImportError` / `OSError` WinError 126/127/193 loading Qt/ICU/plugin DLLs) | `open_logs_dir`, `switch_safe_graphics`, `copy_report` |
| `E-GPU-RENDER` | `warning` | `GPU_RENDER` | Previous launch left `.graphics_boot_pending` crash sentinel or OpenGL/RHI context failure | `switch_safe_graphics`, `reset_config`, `copy_report` |
| `E-BG-SYNC` | `info` | `BG_SYNC` | Tier 1 & Tier 2 background sync failed; safely displaying Tier 3 bundled master | `probe_network`, `open_settings`, `copy_report` |
| `E-MIGRATION` | `warning` | `MIGRATION` | Migration from `StellaSora_Launcher_Candidate_r02` encountered partial error or corrupt `config.json` (preserved) | `reset_config`, `open_app_data_dir`, `copy_report` |
| `E-NET-CAPTIVE` | `error` | `NET_CAPTIVE` | HTTP `200` returned HTML login/captive portal page instead of JSON/binary payload | `probe_network`, `copy_report` |
| `E-CFA-BLOCKED` | `error` | `CFA_BLOCKED` | Controlled Folder Access / AV write block (`WinError 5`/`EACCES` on writable ACL directory) | `relaunch_admin`, `open_game_dir`, `copy_report` |
| `E-PARALLEL-DL` | `error` | `PARALLEL_DL` | Multi-worker download pool aborted on disk I/O or concurrent failure (preserves inner cause) | `probe_network`, `open_game_dir`, `copy_report` |

### 6.2 `core/quick_fix.py` — 8 1-Click Error Assistant Actions

`quick_fix.plan_actions(error_code: str, ctx: ErrorContext) -> list[QuickFixAction]` returns up to 3 contextual action descriptors plus the always-present `copy_report` action:

| # | Action ID | Vietnamese Button Label | Triggering `E-*` Codes | Execution Contract (`app_controller.py`) |
|---|---|---|---|---|
| 1 | `close_game` | **Đóng game đang chạy** | `E-GAME-RUNNING`, `E-FILE-IN-USE` | Confirms with user, verifies process image path via `QueryFullProcessImageNameW == <game_root>\StellaSora.exe`, requests termination / guides Task Manager if elevated, re-polls `is_game_process_running()`. |
| 2 | `relaunch_admin` | **Chạy lại bằng quyền Quản trị** | `E-FILE-DENIED`, `E-CFA-BLOCKED`, `E-CONFIG-SAVE`, `E-SHORTCUT` | Invokes `ShellExecuteW(None, "runas", sys.executable, args_with_app_data_dir, None, 1)` and closes non-elevated instance if launched. |
| 3 | `probe_network` | **Kiểm tra kết nối & DNS** | `E-NET*`, `E-HTTP-*`, `E-NET-CAPTIVE`, `E-OFFICIAL-NET`, `E-PARALLEL-DL`, `E-BG-SYNC` | Runs `net_probe.run_probe()` + `tls.info()` asynchronously in worker thread and renders live DNS/TCP:443/TLS verdict inline inside `SmartErrorDialog`. |
| 4 | `open_game_dir` | **Mở thư mục game** | `E-NO-EXE`, `E-FILE-*`, `E-NO-RECEIPT`, `E-RECEIPT-MISMATCH`, `E-CFA-BLOCKED` | Calls `os.startfile(game_dir)` (falling back to parent directory if leaf missing). |
| 5 | `switch_safe_graphics` | **Chuyển chế độ đồ họa tương thích** | `E-STARTUP-DLL`, `E-GPU-RENDER` | Persists `"graphics_mode": "software"` and `"reduced_motion": true` in `config.json` (when not `_corrupt`) and restarts launcher with `--safe-graphics`. |
| 6 | `reset_config` | **Khôi phục cấu hình mặc định** | `E-CONFIG-CHANNEL`, `E-LOCAL-PAYLOAD`, `E-MIGRATION`, corrupt `config.json` | Calls `ConfigManager.preserve_corrupt_and_reset()` (renames corrupt file to `config.corrupt.<uuid>.json`, never deletes preimage) and refreshes controller state. |
| 7 | `restore_official` | **Tải lại bản gốc sạch từ Yostar** | `E-BACKUP`, `E-FILE-MISMATCH`, `E-RECEIPT-MISMATCH`, `E-OFFICIAL-NOTFOUND`, `E-DOWNGRADE` | Prompts confirmation and launches `OfficialRestoreEngine` clean vanilla restore workflow. |
| 8 | `copy_report` | **Sao chép gói báo lỗi gọn cho Dev** | **All error codes (always shown)** | Builds PII-redacted `ErrorReport` (`%USERPROFILE%` & username redacted, URL query/credentials stripped, Win32/HTTP codes, target file/URL, `net_probe`, disk free GB, `StellaSora.exe` state, folder writability/CFA result, last 30 log lines) and copies via `copy_text_native()` + optional `.txt`/`.json` export. |

---

## 7. Verification Criteria

- Every module in §2 maps 1:1 to a single owner in §3.
- Every interface signature (`--apply-update`, `bg_sync`, `migration`, `quick_fix`, `error_catalog`, `OperationEvent`) aligns with `PROJECT.md`.
- Stage 2E tests (`test_migration.py`, `test_self_update_v2.py`, `test_parallel_download.py`, `test_error_and_quick_fix.py`) and Stage 3 `verify_v2_update_readiness.py` + `--smoke --app-data-dir <tmp>` verify compliance before user handover.
