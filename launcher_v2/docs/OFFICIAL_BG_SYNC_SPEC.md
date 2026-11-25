# Official Background Sync & Adaptive Scrim Specification (`OFFICIAL_BG_SYNC_SPEC`)

**Module Owner:** Role 2 (`launcher_v2/core/bg_sync.py`)  
**Target Integration:** `launcher_v2/ui/main_shell.py`, `launcher_v2/ui/theme/adaptive_scrim.py`  
**Stage:** Stage 1B Technical Specification  
**Source Evidence:** Strictly read-only inspection of `C:\YostarGames\StellaSora_EN_Gamelauncher\resources\app.asar` (`v1.6.0`) and `C:\Users\chann\AppData\Roaming\StellaSora_EN_Gamelauncher\` (`official_bg_and_assets_report.md`).

---

## 1. Verified Yostar Official Launcher (`v1.6.0`) Findings

### 1.1 Runtime & Local Cache Layout
- **Install Root:** `C:\YostarGames\StellaSora_EN_Gamelauncher\`
  - `resources\app.asar` (`70,148,654` bytes): Electron app (`version: "1.6.0"`, Node `16.17.1`, Vue 3 + Pinia + `axios/1.5.0`, Swiper `11.1.4`).
  - `resources\app-update.yml`: `provider: generic`, `url: https://launcher-pkg-ss-en.yo-star.com/install_pkg/game_launcher/StellaSora_EN/`.
- **AppData Cache (`%APPDATA%\StellaSora_EN_Gamelauncher\`):**
  - `IndexedDB\file__0.indexeddb.blob\1\00\5` (`1,444,337` B): Cached live background stored as `data:image/png;base64,...` keyed by `hash: "11498888707738615662"` (decoded PNG: `1280×734` RGB, `1,083,199` B). Note: Official Launcher's `useIDB` stores base64 blobs indefinitely without pruning old entries.
  - `Cache\Cache_Data\f_000001..f_000014`: Cached `460×220` PNG carousel/banner images (`125–222` KB each).
  - `Local Storage\leveldb\000003.log`: Keys `download-task`, `downloadPath`, `close-choice`, `close-choice-save`, `proxy-config`.
- **Zero Video Backgrounds in v1.6.0:** `0` occurrences of `<video>`, `.mp4`, `.webm`, or `lottie` in `app.asar` renderer bundles.
- **Bundled ASAR Fallback Images:**
  - Main window: `out/renderer/assets/bg-df33ba5f.png` (actually a **JPEG**, `1280×734` RGB, `749,163` B), triggered by CSS `.app-container.bg::before` when `launcher_background_img` is empty or fails.
  - Updater window: `out/renderer/assets/bg-7cac1ac5.png` (actually a **JPEG**, `710×442` RGB, `276,106` B).

### 1.2 API Endpoints & `Authorization` Signing Algorithm

- **API Base URL:** `https://api-launcher-en.yo-star.com` (official timeout: `30000` ms).
- **Mandatory Headers:**
  - `Content-Type: application/json;charset=UTF-8`
  - `Authorization`: Compact JSON string produced identically to `node_modules/@launcher/utils/src/crypto.ts`:
    ```python
    import hashlib, json, time

    YOSTAR_AUTH_SALT = "DE7108E9B2842FD460F4777702727869"

    def build_yostar_auth_header(data: str = "", version: str = "1.6.0") -> str:
        head = {
            "game_tag": "StellaSora_EN",
            "time": int(time.time()),
            "version": version,
        }
        # Compact JSON (no whitespace) matching JavaScript JSON.stringify(head)
        head_json = json.dumps(head, separators=(",", ":"), ensure_ascii=False)
        sign_str = f"{head_json}{data}{YOSTAR_AUTH_SALT}"
        sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()  # lowercase hex
        return json.dumps({"head": head, "sign": sign}, separators=(",", ":"), ensure_ascii=False)
    ```
    For `GET` requests, `data` is `""`.

- **Verified Live Endpoints:**
  1. **`GET /api/launcher/base/config`** (primary background source):
     ```json
     {
       "code": 200,
       "msg": "OK",
       "data": {
         "launcher_background_img": "https://launcher-pkg-ss-en.yo-star.com/prod/StellaSora_EN/launcher_background_img/d6ef5b7a1069be8d0e0819775a81d5db.png",
         "launcher_background_img_crc64": "11498888707738615662",
         "config_open": true,
         "user_agreement": "https://stellasora.global/agreement",
         "privacy_policy": "https://stellasora.global/privacy_policy",
         "copyright_information": "© Yostar",
         "notice_pop_open": false,
         "notice_content": "<p>...</p>",
         "exit_launcher_open": true
       }
     }
     ```
  2. **`GET /api/launcher/operations/resource`**: Returns `operations_banner_list` (`460×220` PNG `banner_img`, `jump_url`, `remark`, `start_at`, `end_at`) and `notice_list` (`News`, `Events`, `Notices`).
  3. **`GET /api/launcher/social/media/resource`** & **`GET /api/launcher/game/config`**: Return official social URLs and latest game version/package metadata (`game_lowest_version`, `game_latest_version`, `game_latest_file_path`, `decompression_size`).

### 1.3 CDN `User-Agent` 403 Quirk & Caching Headers

- **Verified CDN Defect with Default Python `urllib`:**
  - Fetching `https://launcher-pkg-ss-en.yo-star.com/...` (Aliyun OSS) with Python's default `User-Agent: Python-urllib/3.10` returns **`HTTP 403 Forbidden`**.
  - Sending **`User-Agent: axios/1.5.0`** (or `StellaSora-VietHoa-Launcher/2.0 (axios-compat)` / `Mozilla/5.0`) returns **`HTTP 200 OK`** (and `206 Partial Content` on `Range`) along with caching headers:
    - `ETag: "CBEC160166D25651B620AB20CF0C2C72"`
    - `x-oss-hash-crc64ecma: 11498888707738615662`
    - `Content-Length: 1083199`
    - `Last-Modified: Fri, 13 Nov 2026 07:08:11 GMT`
    - `Cache-Control: public, max-age=14400`
- **Requirement:** `core/bg_sync.py` MUST set explicit `User-Agent: axios/1.5.0` (or `Mozilla/5.0` fallback) on all `api-launcher-en.yo-star.com` and `launcher-pkg-ss-en.yo-star.com` requests.

---

## 2. 3-Tier Non-Blocking Sync Architecture (`core/bg_sync.py`)

### 2.1 Public Module Contracts (Pure Python, Zero Qt Imports)

```python
@dataclass(frozen=True)
class LuminanceProfile:
    y_all: float      # Mean perceived sRGB luminance [0.0, 1.0]
    y_top: float      # Top 0%-20% (Title bar & Nav rail zone)
    y_bottom: float   # Bottom 50%-100% (CTA & Notices zone)
    mode: str         # "light" if y_all >= 0.52 or y_top >= 0.58 else "dark"

@dataclass(frozen=True)
class BackgroundFrame:
    tier: int                         # 1 = Online Official, 2 = Local Official Cache/ASAR, 3 = Bundled Master
    source_label: str                 # "online_official" | "local_official_idb" | "local_official_asar" | "bundled_master"
    image_path: Path                  # Local readable PNG/JPG/WEBP path
    crc64: str                        # CRC64-ECMA or SHA256 cache identifier
    etag: str                         # HTTP ETag if Tier 1, else ""
    width: int
    height: int
    luminance: LuminanceProfile
    warning_code: str | None = None   # e.g., "E-BG-SYNC" if Tier 1 & Tier 2 both failed

class BackgroundSyncService:
    def __init__(self, app_data_dir: Path, resource_dir: Path,
                 official_install_dir: Path | None = None,
                 official_appdata_dir: Path | None = None) -> None: ...

    def load_initial(self) -> BackgroundFrame:
        """Instant Frame 0 lookup (< 16 ms, zero network I/O):
        1. Validated v2 bg_cache/meta.json image on disk, else
        2. Tier 3 bundled background_native_2048x1451.png."""

    def sync_async(self, on_ready: Callable[[BackgroundFrame], None],
                   auto_sync_enabled: bool = True) -> None:
        """Runs Tier 1 -> Tier 2 -> Tier 3 resolution on a daemon worker thread.
        Invokes on_ready(frame) only when the resolved frame differs from initial or status changed."""

    def sync_blocking(self, auto_sync_enabled: bool = True) -> BackgroundFrame:
        """Deterministic synchronous entry used by sync_async and unit tests."""
```

### 2.2 Frame 0 Guarantee & Resolution Waterfall

1. **Frame 0 Instant Paint (`< 16 ms`):**
   - `load_initial()` checks `<app_data_dir>/bg_cache/meta.json`. If the referenced cached file exists, passes magic-byte header verification, and its cached `LuminanceProfile` is valid, it paints on Frame 0 immediately.
   - Otherwise `load_initial()` immediately returns Tier 3 (`resources/branding/background_native_2048x1451.png`) so the window **never** flashes black or blank.

2. **Tier 1 — Online Sync (Non-Blocking Background Thread):**
   - Skipped if `config['auto_sync_official_bg'] == False` (falls back cleanly to Tier 2/3).
   - **Network & TLS Guardrails:** Uses `core/tls.build_context()` (Windows Cert Store + `certifi`), `connect=4.0s`, `read=8.0s` (hard cap `12.0s`), `User-Agent: axios/1.5.0`, and `Authorization` MD5 header.
   - **Metadata Dedup:** Calls `GET /api/launcher/base/config`. Extracts `img_url = data["launcher_background_img"]` and `crc64 = str(data["launcher_background_img_crc64"])`.
     - Validates `img_url` scheme is `https://` and host matches `yo-star.com` / `stellasora.global` allowlist.
     - If `(crc64, img_url)` matches `<app_data_dir>/bg_cache/meta.json` and cached file exists & validates -> **0 bytes transferred**, return existing Tier 1 frame.
   - **Conditional Download & Validation:**
     - Sends `GET img_url` with `If-None-Match: <cached_etag>` when URL matches. On `304 Not Modified`, keeps cached file.
     - On `200 OK`, streams to `.tmp` with a **25 MB max size cap**.
     - Validates: (a) magic bytes (`PNG`, `JPEG`, `WEBP`), (b) `Content-Length` exact match (if provided), (c) Pillow `Image.open` decode & `verify()` with minimum dimensions `width >= 800, height >= 450` (rejects HTML error/captive portal pages), (d) optional `x-oss-hash-crc64ecma` verification.
     - Atomically moves to `<app_data_dir>/bg_cache/bg_<crc64>.<ext>`, updates `meta.json` via `atomic_json()`, and **prunes historical backgrounds to retain max 2 files**.

3. **Tier 2 — Local Official Launcher Cache Fallback (Strictly Read-Only):**
   - Triggered when Tier 1 fails (offline, DNS/TLS, timeout, 403/5xx, captive portal) and no valid Tier 1 image is cached in `bg_cache/`.
   - **Step 2a (IndexedDB Blob Scan):**
     - Scans `%APPDATA%\StellaSora_EN_Gamelauncher\IndexedDB\file__0.indexeddb.blob\*\*\*` **read-only** (never opens Chromium `LOCK` or `Cache_Data\data_0` which throw `PermissionError` while Official Launcher is running).
     - Searches for `b"data:image/"` + `b";base64,"`, base64-decodes the payload, validates via Pillow (`width >= 1024, height >= 576`), copies to `<app_data_dir>/bg_cache/local_idb_<sha12>.<ext>`, and returns `tier=2, source_label="local_official_idb"`.
   - **Step 2b (In-Memory ASAR Extraction):**
     - If IndexedDB blob is absent/unreadable, opens `C:\YostarGames\StellaSora_EN_Gamelauncher\resources\app.asar` read-only in binary mode, parses the 16-byte Chromium ASAR pickle header + JSON file tree (`offset`, `size`), locates `out/renderer/assets/bg-df33ba5f.png` (fallback `bg-7cac1ac5.png`), slices bytes directly in memory without creating temp files in Official Launcher's folder, validates with Pillow, and caches into `bg_cache/local_asar_<sha12>.jpg` (`tier=2, source_label="local_official_asar"`).

4. **Tier 3 — Bundled High-Res Fallback:**
   - Returns `resources/branding/background_native_2048x1451.png` (`2048×1451` RGBA, `2,756,561` B).
   - If Tier 1 and Tier 2 both failed while `auto_sync_enabled=True`, attaches non-fatal `warning_code="E-BG-SYNC"` (logged silently as `info` without popping a blocking modal).

---

## 3. Zone Luminance Profiler & Adaptive Scrim/Glass Formulas

### 3.1 Zone Luminance Calculation (`bg_sync.py` + `Pillow`)

Computed off the UI thread when any background loads:
1. Downsample image to a fast `160×90` RGB proxy (`Image.Resampling.BILINEAR`).
2. Compute per-pixel relative sRGB luminance:
   $$Y = \frac{0.2126 \cdot R + 0.7152 \cdot G + 0.0722 \cdot B}{255.0}$$
3. Aggregate three layout-critical zones:
   - `y_all`: mean `Y` across `0%..100%` height.
   - `y_top`: mean `Y` across `0%..20%` height (Title Bar + Navigation Rail).
   - `y_bottom`: mean `Y` across `50%..100%` height (Overview Hero Notice Pill, Action Card, Notifications Card).

### 3.2 Measured Profiles on Real Stella Sora Backgrounds

| Background Source | Native Size | `y_all` | `y_top (0–20%)` | `y_bottom (50–100%)` | Classification |
|---|---:|---:|---:|---:|---|
| Bundled `background_native_2048x1451.png` | `2048×1451` | `0.491` | **`0.600`** | `0.351` | **Mixed** (bright sky top, dark lower half) |
| Yostar Live IndexedDB Cached | `1280×734` | `0.367` | `0.398` | `0.337` | **Dark** key art |
| Yostar ASAR Fallback `bg-df33ba5f.png` | `1280×734` | **`0.697`** | **`0.754`** | **`0.669`** | **Bright / Light** key art |

### 3.3 Adaptive Scrim & Card Glass Formulas (`ui/theme/adaptive_scrim.py`)

Every zone and glass card enforces **WCAG AA >= 4.5:1** text contrast against the active backdrop:

1. **Dark Glass Mode (Default Translucent Dark-Slate / Deep-Navy Glass with `#F8FAFC` / `#E2E8F0` ink):**

   | Zone Luminance Bucket | Top Scrim (`0% -> 22%` linear alpha) | Bottom Vignette (`45% -> 100%` linear/radial alpha) | Card Glass Fill (`RGBA`) | Hairline Border |
   |---|---|---|---|---|
   | **Bright (`Y_zone >= 0.58`)** | `rgba(7, 18, 36, 0.62) -> rgba(7, 18, 36, 0.18)` | `rgba(7, 18, 36, 0.00) -> rgba(7, 18, 36, 0.72)` | `rgba(7, 22, 44, 0.86)` | `rgba(255, 255, 255, 0.18)` |
   | **Mid (`0.40 <= Y_zone < 0.58`)** | `rgba(8, 22, 44, 0.45) -> rgba(8, 22, 44, 0.10)` | `rgba(8, 22, 44, 0.00) -> rgba(8, 22, 44, 0.58)` | `rgba(9, 28, 56, 0.80)` | `rgba(56, 189, 248, 0.24)` |
   | **Dark (`Y_zone < 0.40`)** | `rgba(10, 28, 52, 0.26) -> rgba(10, 28, 52, 0.05)` | `rgba(10, 28, 52, 0.00) -> rgba(10, 28, 52, 0.42)` | `rgba(10, 32, 60, 0.72)` | `rgba(56, 189, 248, 0.30)` |

2. **Light Frosted Mode (Optional / Light Theme Preview & Bright Backdrop Variant with `#0F2242` navy ink):**
   - Card glass fill: `rgba(246, 250, 255, 0.84)` with `1px` border `rgba(15, 34, 66, 0.14)`.
   - When `Y_zone < 0.45` (dark backdrop underneath light cards), apply soft light-mist top/bottom scrim `rgba(235, 244, 255, 0.55)` so dark navy `#0F2242` headers and titlebar controls remain `>= 4.5:1` readable.

---

## 4. `reduced_motion` Degradation Rules

`is_reduced_motion(cfg)` returns `True` if **either**:
1. `config.json["reduced_motion"] is True`, **or**
2. Windows OS disables client animations (`ctypes.windll.user32.SystemParametersInfoW(0x1042 /* SPI_GETCLIENTAREAANIMATION */, 0, byref(enabled), 0)` returns `enabled == 0`).

When `reduced_motion` is active:
- **Background Cross-Fade:** `350 ms` alpha cross-fade animation (`QVariantAnimation`) is **disabled** (`duration = 0 ms`, instant atomic swap).
- **Progress Spinner:** Frozen on frame 0 (`spinner_00.svg` / static icon); timer animation stopped.
- **Backdrop Blur & Hover Transitions:** Modal snapshot Gaussian blur is skipped (solid high-opacity glass scrim used instead); card hover elevation animations are disabled.
- **Future Video/Animated Banners:** Any animated/video source MUST downgrade immediately to a static high-res poster frame.
