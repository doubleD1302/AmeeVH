# -*- coding: utf-8 -*-
"""Version and compatibility decisions for the visible update controls."""
import os
import re
import urllib.request
from typing import Optional

def version_parts(value):
    match = re.fullmatch(r'v?(\d+(?:\.\d+){0,3})', str(value or '').strip(), re.I)
    if not match:
        return None
    parts = tuple(int(p) for p in match.group(1).split('.'))
    return parts + (0,) * (4 - len(parts))

def newer(latest, installed):
    latest, installed = version_parts(latest), version_parts(installed)
    return latest is not None and installed is not None and latest > installed

def matches(observed, expected):
    observed, expected = str(observed or '').strip(), str(expected or '').strip()
    if not observed or not expected or observed.lower() in ('unknown', '*', 'all'):
        return False
    expected_list = [e.strip() for e in re.split(r'[,;|]', expected) if e.strip()]
    return observed in expected_list or '*' in expected_list

def check_remote_publisher_headers() -> dict:
    """Queries official publisher CDN manifest header with a small byte-range request."""
    url = "https://nova-static.stellasora.global/res/win/145/73d0a5ed73c7b5507c8ffb0fd25af693/ss_win.mani"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UnityPlayer/2022.3.48f1", "Range": "bytes=0-2048"}
    )
    out = {}
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            for line in text.splitlines():
                line = line.strip().lstrip("$")
                m = re.match(r"^(GAME_VER|CLIENT_VER|RES_VER|RESOURCE_VER)[:=\s]+([0-9A-Za-z_.-]+)", line)
                if m:
                    out[m.group(1)] = m.group(2)
    except Exception:
        pass
    return out

def has_game_patch_conflict_in_log() -> bool:
    """Checks if game recently failed to patch publisher update due to modified files."""
    log_path = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\YOSTAR (HONG KONG) LIMITED\StellaSora\Player.log")
    if not os.path.exists(log_path):
        return False
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Check last 200 lines
            lines = f.readlines()[-200:]
            for l in lines:
                if any(err in l for err in ("BinDiffPatchError", "Patch file verification failed", "no found patch target bundle")):
                    return True
    except Exception:
        pass
    return False

def detect_new_publisher_version(game_info, manifest_meta: Optional[dict] = None) -> tuple[bool, str]:
    """
    Detects if the game publisher has published a newer game version or resource update
    that requires running vanilla game updater first before patching.
    Returns (has_new_publisher_update, reason_message).
    """
    if not getattr(game_info, "installed", False):
        return False, ""

    manifest = manifest_meta or {}
    supported_game_ver = manifest.get("client_game_version", "2.0.1")
    supported_res_str = manifest.get("resource_version", "2610291554")

    # 1. Check local game version vs supported game version
    local_game_ver = getattr(game_info, "version", "")
    if local_game_ver and local_game_ver != "unknown":
        if newer(local_game_ver, supported_game_ver):
            return True, f"Phiên bản game hiện tại ({local_game_ver}) mới hơn bản dịch hỗ trợ ({supported_game_ver})"

    # 2. Check local resource version
    local_res_ver = getattr(game_info, "resource_version", "")
    if local_res_ver and local_res_ver != "unknown":
        if not matches(local_res_ver, supported_res_str):
            # Parse supported numbers
            known_nums = [int(p) for p in re.findall(r"\b\d{8,}\b", supported_res_str)]
            if known_nums and local_res_ver.isdigit():
                if int(local_res_ver) > max(known_nums):
                    return True, f"Tài nguyên game ({local_res_ver}) mới hơn phiên bản bản dịch hỗ trợ"

    # 3. Check for patch failure in Player.log (means game tried to update from Yostar and aborted)
    if has_game_patch_conflict_in_log():
        return True, "Phát hiện game vừa gặp xung đột khi tải bản vá mới từ nhà phát hành"

    # 4. Check remote publisher headers on CDN
    remote_headers = check_remote_publisher_headers()
    if remote_headers:
        remote_game = remote_headers.get("GAME_VER")
        if remote_game and newer(remote_game, supported_game_ver):
            return True, f"Nhà phát hành vừa ra mắt bản game mới ({remote_game})"
        remote_res = remote_headers.get("RES_VER")
        if remote_res and remote_res.isdigit():
            known_nums = [int(p) for p in re.findall(r"\b\d{8,}\b", supported_res_str)]
            if known_nums and int(remote_res) > max(known_nums):
                return True, f"Nhà phát hành vừa phát hành gói tài nguyên mới ({remote_res})"

    return False, ""

def translation_state(sync, game):
    if sync.get('release_status') != 'online' or sync.get('manifest_status') != 'online':
        return {'available': False, 'can_install': False, 'message': 'Chưa có bảng kê bản Việt hoá đáng tin cậy.'}
    version = sync.get('translation_version')
    receipt = getattr(game, 'installed_receipt', None)
    if not getattr(game, 'installed', False):
        return {'available': False, 'can_install': False, 'message': f'Bản Việt hoá: {version}. Hãy chọn thư mục game.'}
    if matches(getattr(game, 'version', ''), sync.get('translation_game')) and matches(getattr(game, 'resource_version', ''), sync.get('translation_resource')):
        version_note = 'Phiên bản game và tài nguyên khớp bảng kê; chưa xác minh hiển thị trong game.'
    else:
        version_note = 'Phiên bản game hoặc tài nguyên khác bảng kê hoặc chưa đọc được; chưa xác minh tương thích.'
    if version_parts(version) is None:
        return {'available': False, 'can_install': False, 'message': 'Phiên bản bản Việt hoá trong bảng kê không hợp lệ.'}
    if not receipt:
        return {'available': False, 'can_install': True, 'message': f'Bản Việt hoá: {version}. Chưa có biên bản cài để đối chiếu phiên bản. {version_note}', 'version_note': version_note}
    current = receipt.get('version')
    if version_parts(version) is None or version_parts(current) is None:
        return {'available': False, 'can_install': False, 'message': f'Không thể so sánh phiên bản đã cài ({current}) với bản trong bảng kê ({version}).'}
    if newer(version, current):
        return {'available': True, 'can_install': True, 'message': f'Có bản Việt hoá {version} mới hơn bản đã cài {current}. {version_note}', 'version': version, 'version_note': version_note}
    if version_parts(version) == version_parts(current):
        return {'available': False, 'can_install': True, 'message': f'Bản đã cài: {current} (mới nhất). Bạn có thể bấm Cài lại để làm mới dữ liệu. {version_note}', 'version': version, 'version_note': version_note}
    return {'available': False, 'can_install': False, 'message': f'Bản đã cài ({current}) mới hơn bảng kê ({version}). Hạ cấp bị từ chối. {version_note}', 'version': version, 'version_note': version_note}
