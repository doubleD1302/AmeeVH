# -*- coding: utf-8 -*-
"""Version and compatibility decisions for the visible update controls."""
from __future__ import annotations
import os
import re
import time
from datetime import datetime
from pathlib import Path
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


def has_game_patch_conflict_in_log(game_info=None) -> bool:
    """Checks if game recently failed to patch publisher update due to modified files."""
    log_path = Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\YOSTAR (HONG KONG) LIMITED\StellaSora\Player.log"))
    if not log_path.is_file():
        return False
    try:
        log_mtime = log_path.stat().st_mtime
        if (time.time() - log_mtime) > 86400:
            return False

        # Ignore stale Player.log if ss_win.mani or patch receipt is newer than Player.log
        gpath = getattr(game_info, "game_path", None) if game_info is not None else None
        if isinstance(gpath, (str, os.PathLike)):
            gp = Path(gpath)
            mani = gp / "Persistent_Store" / "ss_win.mani"
            if mani.is_file() and mani.stat().st_mtime > log_mtime:
                return False
            rp = gp / ".vietnamese_patch_receipt.json"
            if rp.is_file() and rp.stat().st_mtime > log_mtime:
                return False

        receipt = getattr(game_info, "installed_receipt", None) if game_info is not None else None
        if isinstance(receipt, dict) and isinstance(receipt.get("installed_at"), str):
            try:
                inst_ts = datetime.fromisoformat(receipt["installed_at"].replace("Z", "+00:00")).timestamp()
                if inst_ts > log_mtime:
                    return False
            except ValueError:
                pass

        with log_path.open("r", encoding="utf-8", errors="ignore") as f:
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
    supported_game_ver = str(manifest.get("client_game_version", "2.1.0") or "2.1.0")
    supported_res_str = str(manifest.get("resource_version", "*") or "*")

    # 1. Check local game version vs supported game version(s) (supports comma-separated list and '*')
    local_game_ver = str(getattr(game_info, "version", "") or "").strip()
    if local_game_ver and local_game_ver != "unknown":
        game_candidates = [g.strip() for g in re.split(r"[,;|]", supported_game_ver) if g.strip()]
        if "*" not in game_candidates and not matches(local_game_ver, supported_game_ver):
            local_parts = version_parts(local_game_ver)
            supported_parts = [version_parts(g) for g in game_candidates if version_parts(g) is not None]
            if local_parts is not None and supported_parts and local_parts > max(supported_parts):
                return True, f"Phiên bản game hiện tại ({local_game_ver}) mới hơn bản dịch hỗ trợ ({supported_game_ver})"

    # 2. Check local resource version (supports comma-separated list and '*')
    local_res_ver = str(getattr(game_info, "resource_version", "") or "").strip()
    if local_res_ver and local_res_ver != "unknown":
        if not matches(local_res_ver, supported_res_str):
            known_nums = [int(p) for p in re.findall(r"\b\d{8,}\b", supported_res_str)]
            if known_nums and local_res_ver.isdigit():
                if int(local_res_ver) > max(known_nums):
                    return True, f"Tài nguyên game ({local_res_ver}) mới hơn phiên bản bản dịch hỗ trợ"

    # 3. Check for recent patch failure in Player.log
    if has_game_patch_conflict_in_log(game_info):
        return True, "Phát hiện game vừa gặp xung đột khi tải bản vá mới từ nhà phát hành"

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
    if getattr(game, 'receipt_stale', False):
        return {
            'available': True,
            'can_install': True,
            'message': f'Game vừa cập nhật tệp gốc — cần bấm Cập nhật Việt hoá ({version}) để áp dụng lại. {version_note}',
            'version': version,
            'version_note': version_note,
        }
    if not receipt:
        return {
            'available': False,
            'can_install': True,
            'message': f'Bản Việt hoá: {version}. Chưa có biên bản cài để đối chiếu phiên bản. {version_note}',
            'version_note': version_note,
        }
    current = receipt.get('version')
    if version_parts(version) is None or version_parts(current) is None:
        return {'available': False, 'can_install': False, 'message': f'Không thể so sánh phiên bản đã cài ({current}) với bản trong bảng kê ({version}).'}
    if newer(version, current):
        return {
            'available': True,
            'can_install': True,
            'message': f'Có bản Việt hoá {version} mới hơn bản đã cài {current}. {version_note}',
            'version': version,
            'version_note': version_note,
        }
    if version_parts(version) == version_parts(current):
        sync_sha = sync.get('manifest_sha256')
        rec_sha = receipt.get('manifest_sha256')
        legacy_sha = sync.get('legacy_manifest_sha256')
        if sync_sha and rec_sha and rec_sha != sync_sha and (not legacy_sha or rec_sha != legacy_sha):
            return {
                'available': True,
                'can_install': True,
                'message': f'Có bản vá dữ liệu/hình ảnh mới trong gói {version}! Bấm Cập nhật Việt hoá để đồng bộ. {version_note}',
                'version': version,
                'version_note': version_note,
            }
        return {
            'available': False,
            'can_install': True,
            'message': f'Bản đã cài: {current} (mới nhất). Bạn có thể bấm Cài lại để làm mới dữ liệu. {version_note}',
            'version': version,
            'version_note': version_note,
        }
    return {
        'available': False,
        'can_install': False,
        'message': f'Bản đã cài ({current}) mới hơn bảng kê ({version}). Hạ cấp bị từ chối. {version_note}',
        'version': version,
        'version_note': version_note,
    }
