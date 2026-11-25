# Stella Sora Launcher v2.0 — Asset Inventory, Curation & Rendering Rules (`ASSET_INVENTORY_V2`)

**Module Owner:** Role 2 (`launcher_v2/resources/` & `launcher_v2/preview/assets/game/`)  
**Stage:** Stage 1 Revision r3 — Authentic Game, Header/Close 9-Slice & Light-Porcelain Asset Specification  
**Source Evidence:** Direct read-only inspection of `Persistent_Store/AssetBundles/` (`ui_commonex.en.unity3d`, `ui_commonex.unity3d`, `ui_big_sprites.unity3d`, `ui_eventreminder.unity3d`), `C:\YostarGames\StellaSora_EN_Gamelauncher\resources\app.asar`, `StellaSora_VietHoa/work/tyrant_extract/`, `StellaSora_VietHoa/launcher/resources/`, `dist/StellaSora_Gacha_Assets/`, `android/app/src/main/assets/`, and `official_bg_and_assets_report.md`.

---

## 1. Legacy vs Curated Footprint Summary

| Metric | Legacy `launcher/resources/` (v1.3.4) | Curated `launcher_v2/resources/` (v2.0 + Authentic Game Assets) | Delta |
|---|---:|---:|---:|
| **File Count** | `1,480` files | `~103–128` files (Core branding/fonts/support/spinner + `75` files in `resources/game/` incl. `manifest.json`; optional pruned `<= 25` fallback `icons/` subset) | **`-91%` to `-93%`** |
| **Total Size** | `87,018,048 B` (`82.99 MiB`) | **`~5.49–5.53 MiB` (`~5.76–5.80 MB`)** (`~5.30 MiB` base kept assets + `396,814 B` / `~387.5 KiB` authentic game/ASAR pack + `32,481 B` `manifest.json`; stays lean within **`~5.5–7 MB`** even with optional official light/dark fallback or pruned `<= 25` SVG subset) | **`~77.2–77.5 MiB` saved** |
| **Root Cause of Legacy Bloat & Blur** | Bundles `69.37 MiB` of unused `journey_r01` + `journey_panels_r01` AI mockups, duplicate `background.png`, 970 redundant pre-rasterized PNGs, unused `Nunito`, forced `Baloo 2` (+2px hack), and `assets.py:56` prioritizing blurry/heavy PNGs over SVGs | Zero AI paper panels, zero generic Lucide/Feather icon replacements where authentic game/ASAR assets exist, zero duplicate wallpapers, single primary Vietnamese font (`Be Vietnam Pro` OFL), direct master-to-device rendering | Clean, authentic & crisp 100%–200% DPI |

---

## 2. Complete Asset Curation Table

### 2.1 `launcher/resources/` Disposition Matrix

| Legacy Source Path (`launcher/resources/...`) | Files | Size | Format / Dimensions | SHA256 (Verified) | Action | `launcher_v2/resources/` Target & Role |
|---|---:|---:|---|---|---|---|
| `branding/app_icon.ico` | 1 | `114,342 B` | ICO `256×256` RGBA | `03e3a1fa9d26434f074061139e14f84a75b5a2e15c6ddc0c9d85101abecb9b5a` | **KEEP** | `branding/app_icon.ico` — Windows PE EXE & taskbar icon |
| `branding/app_icon.png` | 1 | `1,072,844 B` | PNG `1254×1254` RGBA | `03a7ba6b5a58061ad651b85fec5c2d4a48ca0d4311718e3385dc47e988626d40` | **KEEP** | `branding/app_icon.png` — Titlebar & window badge (drawn directly from master; optional lossless PNG crush/512px badge reduces ~700 KB) |
| `ui/skin_r05/branding/background_native_2048x1451.png` | 1 | `2,756,561 B` | PNG `2048×1451` RGBA | `29c8f65779ca439ee93e0f372ab0debd810c8cea579643faa84c78ba08608e10` | **KEEP** | `branding/background_native_2048x1451.png` — Tier 3 bundled key-art master |
| `ui/background.png` | 1 | `2,756,561 B` | PNG `2048×1451` RGBA | `29c8f65779ca439ee93e0f372ab0debd810c8cea579643faa84c78ba08608e10` | **DROP** | Byte-for-byte duplicate of `background_native_2048x1451.png` |
| `ui/skin_r05/branding/logo_ultrahd_2152x856.png` | 1 | `591,828 B` | PNG `2152×856` RGBA | `22821025c1bdbf4ff6bb31dafe2378b2427fa0fecd22f9d044043059f53c4646` | **KEEP** | `branding/logo_ultrahd_2152x856.png` — Primary Overview game logo (4× Lanczos master) |
| `ui/logo.png` | 1 | `60,425 B` | PNG `538×214` RGBA | `cd9b91902d33bd50804d4388cd63710b180ef735fa4c7a843d12612075f47ae1` | **DROP** | Low-res atlas crop superseded by `logo_ultrahd_2152x856.png` |
| `ui/skin_r05/fonts/BeVietnamPro-Regular.ttf` | 1 | `132,948 B` | TTF (SIL OFL 1.1) | `cd1ef6e9d7db28ad5cdb88a65ccbe693870e60d340b791f349d248342b4fe4c3` | **KEEP** | `fonts/BeVietnamPro-Regular.ttf` — Primary UI body font (`400`) |
| `ui/skin_r05/fonts/BeVietnamPro-Medium.ttf` | 1 | `135,980 B` | TTF (SIL OFL 1.1) | `b60832bfa0fcd015158112c64d7e3fdad3b0c6287d1823f85a3103636e845268` | **KEEP** | `fonts/BeVietnamPro-Medium.ttf` — Primary UI medium label font (`500`) |
| `ui/skin_r05/fonts/BeVietnamPro-SemiBold.ttf` | 1 | `136,736 B` | TTF (SIL OFL 1.1) | `bd8e27eb02720b9d91e59e4f10a90878643219f25ce6a8d9a4f06a8a88d3bb71` | **KEEP** | `fonts/BeVietnamPro-SemiBold.ttf` — Primary UI button/card title font (`600`) |
| `ui/skin_r05/fonts/BeVietnamPro-Bold.ttf` | 1 | `140,300 B` | TTF (SIL OFL 1.1) | `7f738fe5c43c8872807b20e2d30d42163618de8a4daf7f48a939adac32c16847` | **KEEP** | `fonts/BeVietnamPro-Bold.ttf` — Primary UI hero/heading font (`700`) |
| `ui/skin_r05/fonts/OFL.txt` | 1 | `4,397 B` | Text (SIL OFL 1.1) | `6b7f8f73609a25ea78c891e34cf37b06f8a676b7ea986e941e43b009110f2a85` | **KEEP** | `fonts/OFL.txt` — Font license compliance |
| `ui/typography_r08/*` (`Nunito[wght].ttf`, etc.) | 5 | `284,513 B` | Variable TTF + meta | — | **DROP** | Superseded by 4 static weights of `Be Vietnam Pro` |
| `ui/journey_r01/fonts/Baloo2.ttf` | 1 | `683,200 B` | TTF | `d47a6852548059b1db49a1319d06d499d546c3fa2237cf9eee9c43c8abb025c2` | **DROP** | Overly rounded display font from v1.x `+2px` hack |
| `ui/support_r09/techcombank_qr.png` | 1 | `79,984 B` | PNG `526×526` RGB | `170de1dba2a1863e19e51c876c50d430d3f6f299986eb6e61adf98bef00509cd` | **KEEP** | `support/techcombank_qr.png` — Exact pixel crop Donate QR (Techcombank) |
| `ui/support_r09/momo_qr.png` | 1 | `81,722 B` | PNG `453×453` RGB | `482e9b41fbf84e4f2fcc42b3675cb406a552d572fa2907314d6dae58cab75ce8` | **KEEP** | `support/momo_qr.png` — Exact pixel crop Donate QR (MoMo) |
| `ui/support_r09/payment_methods.json` | 1 | `1,385 B` | JSON | `67b5c80e2cb074e065f3e59a8db31ed77d9cb03dde58afa97ed53f55edf79a07` | **KEEP** | `support/payment_methods.json` — Verified donation accounts & QR SHA256s |
| `ui/support_r09/QR_EXTRACTION.json` | 1 | `1,330 B` | JSON | `cc61963c1585589414abe643466ec54d819e6a6a60c78e817fdf9923b8127fbf` | **KEEP** | `support/QR_EXTRACTION.json` — Crop provenance audit |
| `ui/support_r09/help_content.json` | 1 | `8,988 B` | JSON | `386ad4d99bf8f8315e289dda5043e2d4f8188ca959c22b90badec17da8ef8b71` | **KEEP** | `support/help_content.json` — Guide & FAQ content (4 sections, 12 FAQs) |
| `ui/notifications.json` | 1 | `15,745 B` | JSON | `9dc208e9982ac233909b66297d4e722d13353a1655e281fc7b4b0c69ee5a49a8` | **KEEP (Update to v2.0.0)** | `notifications.json` — Offline fallback synced with `launcher_v2/notifications.json` (`version: "2.0.0"`) |
| `ui/skin_r05/svg/icons/*.svg` | 148 | `181,644 B` | SVG (`48×48` viewBox) | — | **KEEP (Minimal Fallback Only)** | `icons/` — Superseded for primary navigation/actions by authentic game sprites & `app.asar` SVGs in `game/`; retain only unmapped utility SVGs (`<= 25` files, `~30–40 KB`) during Stage 2A |
| `ui/skin_r05/svg/buttons/*.svg` & `panels/*.svg` | 35 | `53,827 B` | SVG | — | **DROP** | Replaced by crisp native `QPainter` / QSS glass cards & vector buttons |
| `ui/svg/animation/spinner_00..11.svg` | 12 | `24,168 B` | SVG | — | **KEEP** | `spinner/spinner_00..11.svg` — Loading spinner frames (frame 0 static in `reduced_motion`) |
| `ui/svg/*` (other 201 SVGs) | 201 | `234,979 B` | SVG | — | **DROP** | Legacy v1 badges/buttons/duplicate icons superseded by `skin_r05/svg/icons/` |
| `ui/skin_r05/png/{1x,2x,4x}/*` | 544 | `2,657,649 B` | PNG | — | **DROP** | Redundant pre-rasterized PNGs of `skin_r05/svg/` |
| `ui/png/*` | 426 | `1,897,612 B` | PNG | — | **DROP** | Legacy v1 raster icons/chrome |
| `ui/supplemental/*` | 25 | `625,543 B` | PNG + SVG | — | **DROP** | Decorative AI washes/petals unnecessary in minimalist Starlit v2 glass |
| `ui/journey_r01/*` | 55 | `60,651,034 B` (`57.84 MiB`) | PNG `1536×1024` | — | **DROP** | Massive AI raster icons/mockups (fixes `assets.py:56` legacy override bug) |
| `ui/journey_panels_r01/*` | 8 | `12,084,962 B` (`11.53 MiB`) | PNG `1498×1050` | — | **DROP** | Static paper panel frames wasting 25–40% content area |

### 2.2 External High-Resolution Project Assets Evaluated (`dist/`, `work/`, `android/`)

| Source Path | Dimensions / Size | Evaluation & Verdict for `launcher_v2` |
|---|---|---|
| `dist/StellaSora_Gacha_Assets/02_Gacha_Covers/*/bg_*.png` | `2048×1451` RGBA (15+ covers, 2.5–4.4 MB each) | **AVAILABLE OPTIONAL** — Valid official 2K game backgrounds; NOT bundled by default to keep EXE lean (~4.6 MB resources), but usable as optional local theme gallery / preview testing. |
| `work/tyrant_extract/{Nam,Nu}/Live2D/createplayer2_{m,f}.png` | `4096×4096` RGBA (6.9 / 7.9 MB) | **DO NOT BUNDLE** — Too large for portable single-file EXE; unnecessary for minimalist v2 layout. |
| `android/app/src/main/assets/ui/art/background.png` | `941×1672` RGB | **REJECT** — Portrait mobile crop; incompatible with landscape desktop launcher. |
| `work/textures/texture_full_20261122_r01/tmp_check/off_ui_big_sprites__zs_login_logo.png` | `538×214` RGBA | **REJECT** — Provenance confirmation of `ui/logo.png` low-res source; superseded by `logo_ultrahd_2152x856.png` (`2152×856`). |

### 2.3 Authentic Game & Yostar Official Launcher Asset Manifest (`preview/assets/game/` → Stage 2 `launcher_v2/resources/game/`)

All **74** authentic assets below were extracted 100% read-only from `Persistent_Store/AssetBundles/` (via `UnityPy` Sprite rect/alpha extraction — zero giant atlas sheets), `StellaSora_VietHoa/work/tyrant_extract/`, and `C:\YostarGames\StellaSora_EN_Gamelauncher\resources\app.asar`, and indexed in `preview/assets/game/manifest.json` (`32,481 B`, `version: "2.0.0-s1r3"`). Total curated game/ASAR payload is **`396,814 B`** (`387.5 KiB`; **`429,295 B`** / `419.2 KiB` including `manifest.json`).

#### Tinting, 9-Slice & Light-Porcelain Rules for Game Sprites & ASAR SVGs
1. **Dark Navy Game Sprites (`btn_login_repair.png`, `btn_menu_s_toolbox.png`):** Original Unity sprites use dark navy RGB `~(38, 66, 120)` meant for light surfaces in-game. Never hand-redraw or AI-recreate them. Use the **raw navy sprites** directly on light porcelain surfaces (`#F6F9FD` / `#FFFFFF`), and use the alpha-preserving light-tinted variants (`*_light.png`, `#E8F1FF` `(232, 241, 255)` with original alpha intact) strictly on dark-glass Overview chrome.
2. **Standalone `app.asar` SVGs (`asar_*.svg` & `asar_*_navy.svg`):** Preserve exact `<path>` geometry and native `viewBox` (`0 0 W H`) from `app.asar`. Icons with `fill="#E8F1FF"` (`asar_path`, `asar_tools`, `asar_notice`, `asar_proxy`, `asar_power`, `asar_info`) and `#CACACA` (`asar_set`) are paired with explicit **`#1E3254` navy variants (`asar_*_navy.svg`, 7 files)** so light porcelain buttons and headers render crisp `#1E3254` icons natively via `<img>` or `QSvgRenderer` without CSS filter hacks. Icons with fixed ASAR styling (`asar_minus`, `asar_close`, `asar_checkbox`, `asar_play`) retain their original fills.
3. **Authentic Unity 9-Slice Header Ribbons & Close Buttons (Stage 1r3):** `db_common_title_8.png` (`m_Border=(33,0,17,0)`), `db_common_title_1.png` (`m_Border=(131,0,16,0)`), `db_menu_title.png` (`m_Border=(6,0,144,0)`), and `zs_common_pop_01.png` (`m_Border=(12,0,237,0)`) provide authentic slanted parallelogram facets and diamond halftone textures for `PorcelainWindowFrame` headers and section ribbons; `btn_common_close_blue.png` (`41×43`) serves light porcelain headers while `btn_common_close_01.png` (`47×50`) serves `#264278` navy / `#E11D48` coral header bars.

#### Stage 2 Bundle Size Impact (`launcher_v2/resources/`)
- Base kept resources (§2.1: `branding/`, `fonts/`, `support/`, `notifications.json`, `spinner/`): `5,299,258 B` (`5.05 MiB`)
- Authentic game & ASAR bundle (`resources/game/` — `74` assets + `manifest.json` = `75` files): `429,295 B` (`0.41 MiB`)
- Optional unmapped fallback SVGs (`icons/` pruned subset `<= 25` files): `~30–40 KB` (`~0.04 MiB`)
- **Total Stage 2 `launcher_v2/resources/` footprint:** **`~5.76 MB` (`~5.49 MiB`)** — well within the **`~5.5–7 MB`** lean target (**`~81.25 MB` / `~93.4%` smaller** than legacy v1.3.4 `87,018,048 B`).

#### Complete Authentic Asset Manifest (`74` Assets)

| File (`preview/assets/game/`) | Type | Source Provenance | Dimensions | `m_Border` `(L,B,R,T)` | Size | SHA256 | Intended UI Slot |
|---|---|---|---:|---|---:|---|---|
| `zs_common_star_l_1.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_common_star_l_1` | `85×90` | — | `6,966 B` | `5d0af7119a55483b3685683757781f9f5de2885a2592008a2d4ea391466fcd99` | `free_badge_star_gold` (replaces `✦`) |
| `zs_common_star_l_2.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_common_star_l_2` | `85×90` | — | `8,054 B` | `d4accf9ef37d68f36655345738ee6117367556795c6dd4be283a9f0e307d020c` | `titlebar_star_cyan` |
| `zs_agent_logo_1.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_agent_logo_1` | `94×94` | — | `4,777 B` | `9750080e9862e70742403f2787176666fefe4f2bef22f2849293c7a6a2118bc1` | `platform_stella_emblem` |
| `icon_stage_home.png` | Unity Sprite PNG | `ui_commonex.unity3d#icon_stage_home` | `46×51` | — | `640 B` | `a6225d7c6170b9f0f3a6ba0a3cd68ca64720000e118aad38b1ccb0a0bbe7d54c` | `nav_overview` |
| `icon_stage_home_slc.png` | Unity Sprite PNG | `ui_commonex.unity3d#icon_stage_home_slc` | `50×55` | — | `1,473 B` | `dd40c633d72ff17363b939df6bd68b6d9ccf8a6741d1be3d6c6e5acfe082bd2e` | `nav_overview_active` |
| `btn_main_system_notice.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_main_system_notice` | `55×60` | — | `1,568 B` | `86c7c213704ad475a09e2ea2ece8881691a8aeb9069a398f0412c39547635e14` | `nav_notifications` |
| `zs_mail_mailbox.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_mail_mailbox` | `70×58` | — | `1,046 B` | `36dae50efa85231b956c12c084a77336152cbfdd6113acfa44ebddacce60def8` | `notifications_mailbox` |
| `icon_dict_dictionary.png` | Unity Sprite PNG | `ui_commonex.unity3d#icon_dict_dictionary` | `91×71` | — | `5,199 B` | `7d6d234bddfa3ae57452a5ff4a37c47655dd87d1ac7bc1d99a3e0a7e1d3239a0` | `nav_guide` |
| `btn_icon_help_2.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_help_2` | `54×57` | — | `2,950 B` | `530c31f973097322555d5df9af9100b01e3e3d9b788fcc46e94a0ee110ed529a` | `guide_help_icon` |
| `zs_mainchara_good_opinion.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_mainchara_good_opinion` | `56×56` | — | `2,349 B` | `7c70e0ce5fb702838991b4a9d04f8157d0830d4fe4fdef4ac364062ddf11aeef` | `nav_support` |
| `Common_Favour_Heart.png` | Unity Sprite PNG | `ui_commonex.unity3d#Common_Favour_Heart` | `40×40` | — | `1,843 B` | `32bbcf7598aa599bf28b109829cd3ff01f9b1475c2852d100dde93be8d64f18b` | `support_heart` |
| `btn_icon_main_setting.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_main_setting` | `58×58` | — | `3,126 B` | `5e95819311e442585d6f58eb0a505cd27089eb40507374c482f38a5df601e378` | `nav_settings` |
| `btn_menu_l_setting.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_menu_l_setting` | `115×91` | — | `8,483 B` | `0a0af0aed34cbf3f8fcc3bffbb9e7d22f856fc2bbecfb8ae23b791c71eb595a2` | `settings_header_accent` |
| `btn_login_repair.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_login_repair` | `59×57` | — | `1,852 B` | `9023d9d0c5478cd0a572fc82e267db0e9c8d43ae7431e66ce6b21ab0dbe08f42` | `nav_tools_raw_dark` (light porcelain surfaces) |
| `btn_login_repair_light.png` | Tinted Sprite PNG | `ui_commonex.unity3d#btn_login_repair` (`#E8F1FF`) | `59×57` | — | `1,688 B` | `0b669eb7ae41591defea81afbc8a7b4e998e60746a0179b64d5c6d505f5cfd55` | `nav_tools` (dark-glass contrast) |
| `btn_menu_s_toolbox.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_menu_s_toolbox` | `52×58` | — | `1,099 B` | `672f4e8b3c7f75c742160f8e79b083e5cfe1032c42654e296e05b1897a3c33a2` | `tools_toolbox_raw_dark` (light porcelain surfaces) |
| `btn_menu_s_toolbox_light.png` | Tinted Sprite PNG | `ui_commonex.unity3d#btn_menu_s_toolbox` (`#E8F1FF`) | `52×58` | — | `1,042 B` | `7cdd7c47132d10cb4879ec3adcd34b1c13b7552ae2c612b5c397a7ab088acbb4` | `tools_header_icon` (dark-glass contrast) |
| `zs_stage_warning_icon.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_stage_warning_icon` | `122×118` | — | `11,175 B` | `9ef1166de547f1e443ad7a010758c98b2e022a06f18fd142f84e04d7e794ea46` | `error_dialog_warning_lg` |
| `zs_stage_warning_icon_s.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_stage_warning_icon_s` | `45×37` | — | `749 B` | `8d87463e4b201f7d095a8763aa295703d21aff889bb755adb17808f6139a72c7` | `nav_error_warning_sm` |
| `zs_survivor_warning.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_survivor_warning` | `49×40` | — | `701 B` | `c0f2c5f8bcd6efc5f8fab7f3825d4d3b7723734f72be3f63e761c76eed731062` | `warning_badge_white` |
| `zs_common_search.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_common_search` | `39×39` | — | `716 B` | `8884883585da7d01e5cffca1f359312c6db08e9b956a652fa4948730bba7779c` | `search_magnifier` |
| `icon_th_main_magnifier.png` | Unity Sprite PNG | `ui_commonex.unity3d#icon_th_main_magnifier` | `115×137` | — | `9,166 B` | `f8ddab7fe8bd52d9a0e8cc6a178fe0132da79c546f1c81c801d4f068aba79a35` | `detect_magnifier_lg` |
| `btn_icon_download.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_download` | `42×42` | — | `513 B` | `effd9895db571e4dbd583085b548364a597d4f3f706d0a6b6c59e148931b3506` | `action_download` |
| `btn_icon_play.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_play` | `21×32` | — | `300 B` | `52c13d9c001a8369f841e9e059fdaf28f8d90f5d5c43d725323a4ed5b07113f7` | `action_play` |
| `btn_common_check.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_check` | `75×62` | — | `4,287 B` | `1e3310cc64893e831efedadaf8f3eae57ab26ebc9ce66d5b7ca78a545aaaa78b` | `action_verify_check` |
| `btn_icon_tick.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_tick` | `39×32` | — | `545 B` | `6f6e2ec1f3fd66fdd83852b7cc7c03488b524b10dcc1c565caea7a113124a656` | `status_tick` |
| `btn_icon_back.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_back` | `58×69` | — | `1,244 B` | `523b9bc9698e57bad73c26089a53bdc12ffed14e0326771e610faf6a0fc8217d` | `action_restore_back` |
| `btn_icon_reset.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_reset` | `39×36` | — | `790 B` | `582cb67f7b05aaaa04966984abf2f8e80f3766a164bf1aacbc0b4b385c9050b4` | `action_reset` |
| `btn_common_refresh.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_refresh` | `40×39` | — | `1,757 B` | `2aa67348e4d860d452e223d3ae9b2fe7fafc248dbbb8a3be930c7e8d5175e937` | `action_refresh` |
| `btn_icon_copy.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_copy` | `28×28` | — | `265 B` | `cbe17a157245bf5f1c4c1fb0e67dffb8e98d72fe64c85555c50aba1b19dedd27` | `action_copy` |
| `btn_icon_main_next.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_icon_main_next` | `30×44` | — | `1,030 B` | `93dc47aae928b514ca821b894202a75798e671ead7d48b3b8cfd414a8c926631` | `action_next_arrow` |
| `btn_common_stop.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_stop` | `49×60` | — | `1,000 B` | `4c40661b80dbdb114937e0410a40f47d3e73f7c880244567f2119f22210f38a5` | `action_stop` |
| `btn_common_close.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_close` | `41×43` | — | `1,794 B` | `fb20a9403d451e83c26bbd2378421e11dd48539cf67d91414a9891ae3f34c65e` | `action_close` |
| `btn_common_close_blue.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_close_blue` | `41×43` | — | `1,756 B` | `8c5b72aaa05167064b6fd22a7b300ae5ed59fd51437adca23c0e43aefca183da` | `action_close_navy` (light porcelain headers) |
| `btn_common_close_01.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_close_01` | `47×50` | — | `1,585 B` | `f769e2fc63def34d9210ab5161fa07b0622bdbb95dd6c86ca66923d9465663c1` | `action_close_white_outline` (navy/coral header bars) |
| `icon_common_details.png` | Unity Sprite PNG | `ui_commonex.unity3d#icon_common_details` | `54×54` | — | `1,243 B` | `3fb5da406a62e728590180a5aeb3325b6e674e73cccc22261df48a67097c9f5e` | `info_details` |
| `zs_common_new_1.png` | Localized Sprite PNG | `ui_commonex.en.unity3d#zs_common_new_1` | `99×35` | — | `4,936 B` | `19189141f780b143f31959a6c3c86b0d6741550a438fb638cb501ccade782562` | `overview_notif_new_badge` ("MỚI!!") |
| `zs_common_new_4.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_common_new_4` | `30×30` | — | `994 B` | `7cf2b6b3cab01421ee469d65fd362e43d6bdec462a6d362e876c9b8dbb027b64` | `notif_new_dot` |
| `btn_common_db_l_1.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_db_l_1` | `382×117` | `(0,0,0,0)` (visual `24,30,28,30`) | `11,608 B` | `58acf0df073cfdffa751695c4b0e1ba2df56407871057000ffb2b70ec2099c6a` | `btn_faceted_cyan` (Primary Install/Update CTA) |
| `btn_common_db_l_2.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_db_l_2` | `382×117` | `(0,0,0,0)` (visual `24,30,28,30`) | `9,762 B` | `a036e1efc4f08fbad9322ed2097e2a7695d5a359af7fff6642835e91d465b3c3` | `btn_faceted_ice` (Launch CTA / light porcelain button) |
| `btn_common_db_l_3.png` | Unity Sprite PNG | `ui_commonex.unity3d#btn_common_db_l_3` | `382×117` | `(0,0,0,0)` (visual `24,30,28,30`) | `10,671 B` | `ba5633d9184907d97cd0f4104b09d558d7fd08c2605b530fc1f9c213b258fa8f` | `btn_faceted_coral` (Danger / Stop / Error CTA) |
| `db_common_title_8.png` | Unity 9-Slice PNG | `ui_commonex.unity3d#db_common_title_8` | `118×46` | `(33, 0, 17, 0)` | `1,247 B` | `e14c2d5ff64913cdcd04f43f10678b94d57f952ac73ee548565ab916b2298c53` | `header_ribbon_navy_9slice` (`#264278` slanted header ribbon) |
| `db_common_title_1.png` | Unity 9-Slice PNG | `ui_commonex.unity3d#db_common_title_1` | `168×44` | `(131, 0, 16, 0)` | `2,595 B` | `f2def6d8aff14813278afcdb266e7545d62226f9f8d52b7b05d01a1871ed3d85` | `header_ribbon_cyan_9slice` (`#0BACC3` slanted highlight ribbon) |
| `db_menu_title.png` | Unity 9-Slice PNG | `ui_commonex.unity3d#db_menu_title` | `149×77` | `(6, 0, 144, 0)` | `9,817 B` | `24866d3719b3867eb4a38cee74d1ea79500c0c5c15306639c181c29c0e8639fe` | `header_halftone_cyan_9slice` (cyan diamond halftone fade) |
| `zs_common_pop_01.png` | Unity 9-Slice PNG | `ui_commonex.unity3d#zs_common_pop_01` | `256×71` | `(12, 0, 237, 0)` | `5,497 B` | `820aff2494f9e4f5ba9667922bb70832490be4552021d45f5703f49532468d52` | `header_halftone_white_9slice` (white diamond halftone accent) |
| `Common_Line_03.png` | Unity Sprite PNG | `ui_commonex.unity3d#Common_Line_03` | `512×16` | — | `1,086 B` | `5cae92195804c9aaf84bf83d868cb2bbd36b0a91cdf9efd1de53bec33247e316` | `divider_luminous_long` |
| `Common_Line_04.png` | Unity Sprite PNG | `ui_commonex.unity3d#Common_Line_04` | `247×14` | — | `944 B` | `8bc5e2a53bbc90a54fc1b4e880eb46a25d6842ab0d662fe64cb799788f6832ad` | `divider_luminous_short` |
| `zs_sf_popup_head_1.png` | Unity Sprite PNG | `ui_big_sprites.unity3d#zs_sf_popup_head_1` | `233×233` | — | `69,247 B` | `9125ffd6b9703a40151232e072eb1679950f9ad3ef677761c9c79842105c5c4c` | `tyrant_popup_head` |
| `zs_mail_bear_3.png` | Unity Sprite PNG | `ui_commonex.unity3d#zs_mail_bear_3` | `251×217` | — | `12,896 B` | `52209a74a25ba2c7a39961bafe61c2ecd59a4a7d3ef0ec1ad7e9bd83795ea7a4` | `watermark_mail_bear` |
| `zs_eventreminder_bird.png` | Unity Sprite PNG | `ui_eventreminder.unity3d#zs_eventreminder_bird` | `117×120` | — | `14,777 B` | `ac3b14854e6908571ad669bcfcb92d15f36560e4f9f4eac627daa47908f91c66` | `watermark_event_bird` |
| `playerhead_main_bbb.png` | Project Tyrant PNG | `work/tyrant_extract/.../playerhead_main_bbb.png` | `158×240` | — | `31,895 B` | `0bded8c3bbe842cd46ef9f3acf9065bd87b3b833f6217d1cadaa579dd6aebb93` | `game_selection_tyrant_magnifier` |
| `playerhead_main_ccc.png` | Project Tyrant PNG | `work/tyrant_extract/.../playerhead_main_ccc.png` | `214×237` | — | `34,904 B` | `71bdb23a6f631aed88cdb23d5e633ff124fcaec24b05f062fa7ed6f72bd56d80` | `support_tyrant_wink_star` |
| `playerhead_main_b.png` | Project Tyrant PNG | `work/tyrant_extract/.../playerhead_main_b.png` | `162×247` | — | `33,325 B` | `65944fff3aab991c73c056cbadf5802a5657190638a91dff80c12011cb282782` | `error_assistant_tyrant_checklist` |
| `btn_start-28a42cf7.png` | ASAR PNG | `app.asar/out/renderer/assets/btn_start-28a42cf7.png` | `264×72` | — | `12,331 B` | `28a42cf72cbb6d4179bcf6043a5a5c6558525986c6f37564f4e9fc20b0efca4f` | `official_launch_btn` (reference/faceted) |
| `btn_site-c883c5e6.png` | ASAR PNG | `app.asar/out/renderer/assets/btn_site-c883c5e6.png` | `264×72` | — | `12,863 B` | `c883c5e67bc08a7ccdc8b23c6dd9e3d1ad5e189d48e3142020ff00b8ac89f83c` | `official_site_btn` |
| `notification-8be8201c.png` | ASAR PNG | `app.asar/out/renderer/assets/notification-8be8201c.png` | `212×97` | — | `6,514 B` | `8be8201cd91b3a6b53d54d77471d60a2a71eaf0d28a718660ef2534a8d52b08a` | `notifications_star_watermark` |
| `asar_path.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconSettingPath` | `14×12` | — | `431 B` | `07f572c217c5b91cc90b99d02aedf35336e9848e0a343c30e55bb435a85e7575` | `folder_select_open` (`#E8F1FF`) |
| `asar_path_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconSettingPath` (`#1E3254`) | `14×12` | — | `431 B` | `45734ff8adf158d2f7396f025c40e42eaa104100b469b2df051a02dc84c99aa4` | `folder_select_open_navy` (light porcelain) |
| `asar_set.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconSet` | `18×18` | — | `1,800 B` | `c43b5d604275e4f84f7642a9423ee88a009ea8fd3b39f8931251e63973fc0666` | `settings_gear_icon` (`#CACACA`) |
| `asar_set_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconSet` (`#1E3254`) | `18×18` | — | `1,800 B` | `1cbd2cfa1df22740c36fe13a5873e87db75ec7db9228ace7b95fe99aa9550172` | `settings_gear_icon_navy` (light porcelain) |
| `asar_tools.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconSetting` | `16×16` | — | `779 B` | `68f8af2ddcd24557d27addc06debc5bd55372248722ca5f515b9879b3e15dcd9` | `tools_wrench_screwdriver` (`#E8F1FF`) |
| `asar_tools_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconSetting` (`#1E3254`) | `16×16` | — | `779 B` | `fc9d0b85a86c82fc8e3085841bc4fbad51dd4e3f371360d40a632227760f74da` | `tools_wrench_screwdriver_navy` (light porcelain) |
| `asar_notice.svg` | ASAR SVG | `app.asar/.../windowDrag-f6cb1e61.js#IconNotification` | `28×28` | — | `649 B` | `6f034feef8bd25b9e3e91bba93ddb0d5f60fd03a3ef9e1d952549979fae8096c` | `notifications_clipboard` (`#E8F1FF`) |
| `asar_notice_navy.svg` | ASAR SVG (Navy) | `app.asar/.../windowDrag-f6cb1e61.js#IconNotification` (`#1E3254`) | `28×28` | — | `649 B` | `ae4fff4e4c537b1790bd9dcc4aecb3c972af201e1a7646fc5e147490dd247c04` | `notifications_clipboard_navy` (light porcelain) |
| `asar_proxy.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconSettingProxy` | `16×16` | — | `995 B` | `919ef8b37bfc5bde2736bba547598f3cd082af5d7bd10ca307b18a1458af868d` | `network_server_dns` (`#E8F1FF`) |
| `asar_proxy_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconSettingProxy` (`#1E3254`) | `16×16` | — | `995 B` | `c550b6f74da9ee1c7788cd1a3f00720a66d9f5c02d2b6682d256537bc63422a7` | `network_server_dns_navy` (light porcelain) |
| `asar_power.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconSettingClose` | `16×18` | — | `1,161 B` | `c2c960de7ce2620cfb484cb6d40d02c94a46170116d0dd9788ec5b2479f444bc` | `quick_fix_close_game` (`#E8F1FF`) |
| `asar_power_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconSettingClose` (`#1E3254`) | `16×18` | — | `1,161 B` | `cd5bfb5d29c30955c672e67e5e2aa7f59fccb0da3824f7d9afa0c354afc85d2b` | `quick_fix_close_game_navy` (light porcelain) |
| `asar_info.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconInfo` | `10×18` | — | `661 B` | `ece17149d3a3569da772c60b79511f2ad2e0f544639598c11a6cdc2764f3cd38` | `info_tooltip_icon` (`#E8F1FF`) |
| `asar_info_navy.svg` | ASAR SVG (Navy) | `app.asar/.../main-49716b2d.js#IconInfo` (`#1E3254`) | `10×18` | — | `661 B` | `1f84b71c8620b3ab9a3b6c705df849152feb7fba5b324f371790b28526aeb673` | `info_tooltip_icon_navy` (light porcelain) |
| `asar_minus.svg` | ASAR SVG | `app.asar/.../windowDrag-f6cb1e61.js#IconMinus` | `18×18` | — | `166 B` | `16db81e8c975fc12991b35710e41070e953eadb279909125a2a5bc3b09e762d2` | `titlebar_minimize` (`#CACACA`) |
| `asar_close.svg` | ASAR SVG | `app.asar/.../windowDrag-f6cb1e61.js#IconClose` | `18×18` | — | `259 B` | `660fd58e8cfbc5cf312f685a1c815a861fcb094a11f5d9aa914507d60b451823` | `titlebar_close` (`#CACACA`) |
| `asar_play.svg` | ASAR SVG | `app.asar/.../Download-768da8ca.js#IconPlay` | `28×28` | — | `385 B` | `030c3d357d9e357b1b0877749013dd3093b8a6e16b2b57b6318092245f68ac78` | `action_play_circle` (`#EBEDF1`/`#A5A8B3`) |
| `asar_checkbox.svg` | ASAR SVG | `app.asar/.../main-49716b2d.js#IconCheckbox` | `10×8` | — | `372 B` | `51c7c1914814ba009738aa22211c6acafb7ea3b12eab5c295035e34d54fd03ec` | `checkbox_tick` (`#FFF`) |

---

## 3. Direct Master-to-Device Rendering Rules (Zero Blurry Scaling)

1. **Full-Resolution Background & Logo Painting (`ui/widgets/asset_renderer.py`):**
   - Load `background_native_2048x1451.png`, Tier 1/2 official `1280×734` artwork, and `logo_ultrahd_2152x856.png` **once** at native resolution (`QImage` / `QPixmap`).
   - **FORBIDDEN:** Never call `pixmap.scaled(logical_w, logical_h)` to cache a logical-size bitmap before `paintEvent`. On 125% / 150% / 200% DPI Windows displays, Qt upscales that pre-shrunk logical bitmap, causing double-resampling blur.
   - **REQUIRED:** Compute aspect-fill (`cover`) crop rect in source master coordinates (`source_rect: QRectF`) and paint directly onto `target_rect: QRectF(widget.rect())` inside `paintEvent` with `QPainter.RenderHint.SmoothPixmapTransform | QPainter.RenderHint.Antialiasing`. Qt automatically maps straight from master pixels to physical device pixels (`target_rect * dpr`).
2. **SVG Icon Rasterization & Navy Light-Surface Rendering:**
   - Render `game/asar_*.svg` (`asar_*_navy.svg` on `#F6F9FD`/`#FFFFFF` porcelain buttons and headers; `#E8F1FF` variants on dark Overview chrome) and `icons/*.svg` (`48×48` viewBox) using `QtSvg.QSvgRenderer` into an image sized `(round(logical_w * dpr), round(logical_h * dpr))` with `pixmap.setDevicePixelRatio(dpr)`.
   - Cache in memory keyed by `(icon_name, logical_size, round(dpr, 2))` and invalidate/re-render cleanly on `QEvent.Type.DevicePixelRatioChange`.
3. **9-Slice Header Ribbons & Faceted Buttons (`draw_nine_slice` helper in `ui/widgets/asset_renderer.py`):**
   - Subdivide 9-slice sprites (`db_common_title_8.png`, `db_common_title_1.png`, `db_menu_title.png`, `zs_common_pop_01.png`, `btn_common_db_l_1/2/3.png`) into 9 `QRectF` regions using exact Unity `m_Border` `(L, B, R, T)` converted to Qt `(L, T, R, B)`.
   - Corner caps render unstretched at logical DIPs (`border / 2` or `1x` at `200%` DPI) while only the interior span stretches, keeping slanted facet edges and diamond halftone dots razor-sharp across `100%–200%` DPI.
4. **Typography (`Be Vietnam Pro` OFL, Zero `+2px` Hack):**
   - Register all 4 weights (`Regular`, `Medium`, `SemiBold`, `Bold`) via `QFontDatabase.addApplicationFont` at startup.
   - Use exact declared pixel/point sizes (no `size + 2` offset hack from v1.3.4 `typography.py:11`), NFC-normalized Vietnamese strings, and `QFont.StyleStrategy.PreferAntialias` + tabular numerals (`font-variant-numeric: tabular-nums` / fixed-width numeric cells) for download MB, MB/s speed, ETA, and version tags.

---

## 4. Pixel-Exact QR Rendering Rules (`ui/screens/support_screen.py`)

Donation QR codes (`techcombank_qr.png` `526×526` RGB, `momo_qr.png` `453×453` RGB) MUST remain 100% scannable by banking/wallet cameras at every DPI (100%–200%):

1. **Runtime SHA256 Integrity Check:** Before displaying a QR image, verify its SHA256 against `support/payment_methods.json` (`170de1db...` for Techcombank, `482e9b41...` for MoMo). Refuse to render if tampered/mismatched.
2. **No Smoothing / No Upscaling:**
   - Disable `QPainter.RenderHint.SmoothPixmapTransform` (`painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)`) when painting QR pixmaps so black/white finder modules stay razor-sharp without gray anti-aliased fringes.
   - Cap logical display size at `<= floor(native_px / dpr)` (or integer downscale) and preserve strict `1:1` aspect ratio (`width == height`) so a `453×453` or `526×526` QR is never upscaled past its native pixel grid.
3. **Mandatory `#FFFFFF` Quiet Zone:** Render the QR inside an opaque pure-white `#FFFFFF` container with **`>= 20 DIP` padding** on all four sides (never translucent glass behind the QR matrix, which breaks dark-backdrop camera contrast).
