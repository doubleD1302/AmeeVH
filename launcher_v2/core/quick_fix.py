"""Pure contextual Quick-Fix action planner for SmartErrorDialog (Milestone M4).

Maps an ``E-*`` catalog code and optional :class:`ErrorContext` to up to 3
contextual 1-click actions followed by the always-present ``copy_report`` action
(strictly ``1 <= len(actions) <= 4``).

100% pure Python (zero Qt / PySide6 imports).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .diagnostics import is_process_admin
from .error_report import ErrorContext

CANONICAL_ACTION_IDS: tuple[str, ...] = (
    'close_game',
    'relaunch_admin',
    'probe_network',
    'open_game_dir',
    'switch_safe_graphics',
    'reset_config',
    'restore_official',
    'copy_report',
)

ACTION_ICON_KEYS: dict[str, str] = {
    'close_game': 'power',
    'relaunch_admin': 'repair',
    'probe_network': 'proxy',
    'open_game_dir': 'path',
    'switch_safe_graphics': 'settings',
    'reset_config': 'reset',
    'restore_official': 'back',
    'copy_report': 'copy',
}


@dataclass(frozen=True)
class QuickFixAction:
    action_id: str
    label: str
    description: str = ''
    priority: int = 100
    requires_confirm: bool = False
    requires_admin: bool = False
    enabled: bool = True
    disabled_reason: str = ''
    icon_name: str = ''
    params: dict[str, Any] = field(default_factory=dict)


def _sget(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    except Exception:  # noqa: BLE001
        return default


def _sbool(value: Any, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def _sstr(value: Any, default: str = '') -> str:
    if value is None:
        return default
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return default


def _sint(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(_sstr(value).strip())
    except Exception:  # noqa: BLE001
        return None


def _resolve_target_dir(code: str, ctx: Optional[ErrorContext]) -> str:
    if ctx is None:
        return ''
    game = _sget(ctx, 'game', None)
    gpath = _sstr(_sget(game, 'game_path', None))
    if code in ('E-CONFIG-SAVE', 'E-MIGRATION', 'E-STARTUP-DLL', 'E-GPU-RENDER'):
        pm = _sget(ctx, 'path_manager', None)
        if pm is not None:
            try:
                if code == 'E-STARTUP-DLL':
                    return _sstr(pm.logs_dir)
                return _sstr(pm.app_data_dir)
            except Exception:  # noqa: BLE001
                pass
    if gpath:
        return gpath
    tfile = _sstr(_sget(ctx, 'target_file', ''))
    if tfile:
        try:
            return str(Path(tfile).parent)
        except Exception:  # noqa: BLE001
            pass
    pm = _sget(ctx, 'path_manager', None)
    if pm is not None:
        try:
            return _sstr(pm.app_data_dir)
        except Exception:  # noqa: BLE001
            pass
    return ''


def _is_network_code(code: str) -> bool:
    if code.startswith(('E-NET', 'E-HTTP-')):
        return True
    return code in (
        'E-DL-FAILED',
        'E-DL-TIMEOUT',
        'E-DL-RANGE',
        'E-DL-RESPONSE',
        'E-DL-VERIFY',
        'E-OFFICIAL-NET',
        'E-OFFICIAL-INCONSISTENT',
        'E-RELEASE',
        'E-DATA-JSON',
        'E-DATA-SCHEMA',
        'E-SYNC-PENDING',
        'E-PARALLEL-DL',
        'E-BG-SYNC',
    )


def _is_file_or_folder_code(code: str) -> bool:
    if code.startswith('E-FILE-'):
        return True
    return code in (
        'E-NO-EXE',
        'E-NO-GAME-FOLDER',
        'E-GAME-NOT-FOUND',
        'E-NO-RECEIPT',
        'E-RECEIPT-MISMATCH',
        'E-CFA-BLOCKED',
        'E-ROOT-MISMATCH',
        'E-LAUNCH-FAILED',
        'E-STORAGE',
        'E-VERIFY-WRITE',
        'E-PARALLEL-DL',
        'E-LOCAL-PAYLOAD',
        'E-JOURNAL',
        'E-RECOVERY-REQUIRED',
        'E-BACKUP',
    )


def _is_already_admin(ctx: Optional[ErrorContext]) -> bool:
    sr = _sget(ctx, 'system_report', None)
    raw_sr_admin = _sget(sr, 'is_admin', None) if sr is not None else None
    sr_admin = _sbool(raw_sr_admin, False) if raw_sr_admin is not None else False
    try:
        proc_admin = bool(is_process_admin())
    except Exception:  # noqa: BLE001
        proc_admin = False
    return proc_admin or sr_admin


def _make_action(action_id: str, *, priority: int, ctx: Optional[ErrorContext], code: str) -> QuickFixAction:
    icon = ACTION_ICON_KEYS.get(action_id, '')
    if action_id == 'close_game':
        return QuickFixAction(
            action_id='close_game',
            label='Đóng game đang chạy',
            description='Đóng tiến trình StellaSora.exe đang mở để mở khóa tệp game.',
            priority=priority,
            requires_confirm=True,
            icon_name=icon,
        )
    if action_id == 'relaunch_admin':
        already_admin = _is_already_admin(ctx)
        return QuickFixAction(
            action_id='relaunch_admin',
            label='Chạy lại bằng quyền Quản trị',
            description='Khởi chạy lại launcher với quyền Administrator (UAC) để ghi vào thư mục được bảo vệ.',
            priority=priority,
            requires_admin=True,
            enabled=not already_admin,
            disabled_reason='Launcher đã chạy với quyền Quản trị.' if already_admin else '',
            icon_name=icon,
        )
    if action_id == 'probe_network':
        return QuickFixAction(
            action_id='probe_network',
            label='Kiểm tra kết nối & DNS',
            description='Chạy kiểm tra DNS, cổng 443, Captive Portal và chứng chỉ TLS tới máy chủ.',
            priority=priority,
            icon_name=icon,
        )
    if action_id == 'open_game_dir':
        target_dir = _resolve_target_dir(code, ctx)
        params = {'target_dir': target_dir} if target_dir else {}
        return QuickFixAction(
            action_id='open_game_dir',
            label='Mở thư mục game',
            description='Mở thư mục đích trong Windows Explorer để kiểm tra tệp hoặc thuộc tính quyền ghi.',
            priority=priority,
            icon_name=icon,
            params=params,
        )
    if action_id == 'switch_safe_graphics':
        return QuickFixAction(
            action_id='switch_safe_graphics',
            label='Chuyển chế độ đồ họa tương thích',
            description='Bật kết xuất phần mềm (Software OpenGL) và giảm hiệu ứng chuyển động rồi khởi động lại.',
            priority=priority,
            icon_name=icon,
        )
    if action_id == 'reset_config':
        return QuickFixAction(
            action_id='reset_config',
            label='Khôi phục cấu hình mặc định',
            description='Lưu giữ bản cấu hình cũ/hỏng sang tệp riêng và khôi phục cài đặt mặc định an toàn.',
            priority=priority,
            requires_confirm=True,
            icon_name=icon,
        )
    if action_id == 'restore_official':
        return QuickFixAction(
            action_id='restore_official',
            label='Tải lại bản gốc sạch từ Yostar',
            description='Tải và khôi phục nguyên vẹn tệp dữ liệu gốc từ máy chủ chính thức của Yostar.',
            priority=priority,
            requires_confirm=True,
            icon_name=icon,
        )
    return QuickFixAction(
        action_id='copy_report',
        label='Sao chép gói báo lỗi gọn cho Dev',
        description='Sao chép báo cáo chẩn đoán đã ẩn thông tin cá nhân vào clipboard.',
        priority=999,
        icon_name=ACTION_ICON_KEYS['copy_report'],
    )


def _collect_candidates(code: str, ctx: Optional[ErrorContext]) -> list[QuickFixAction]:
    candidates: dict[str, QuickFixAction] = {}

    def _add(aid: str, prio: int) -> None:
        if aid == 'copy_report':
            return
        try:
            act = _make_action(aid, priority=prio, ctx=ctx, code=code)
        except Exception:  # noqa: BLE001
            act = QuickFixAction(
                action_id=aid,
                label=aid,
                priority=prio,
                icon_name=ACTION_ICON_KEYS.get(aid, ''),
            )
        prev = candidates.get(aid)
        if prev is None or act.priority < prev.priority:
            candidates[aid] = act

    game = _sget(ctx, 'game', None)
    game_running = _sbool(_sget(game, 'is_running', False))
    win32_err = _sint(_sget(ctx, 'win32_error', None))
    cfg = _sget(ctx, 'config', None)
    extra = _sget(ctx, 'extra', None)
    ch = _sget(ctx, 'channel', None)
    writability = _sget(ctx, 'writability', None)
    sr = _sget(ctx, 'system_report', None)

    corrupt_cfg = _sbool(_sget(cfg, '_corrupt', False)) or _sbool(_sget(extra, 'corrupt_config', False))
    cfa_suspected = (
        _sbool(_sget(writability, 'cfa_suspected', False))
        or _sbool(_sget(sr, 'cfa_suspected', False))
        or _sstr(_sget(writability, 'status', '')) == 'cfa_blocked'
    )
    repo_val = _sstr(_sget(ch, 'repo', ''))
    has_custom_channel = bool(
        _sstr(_sget(cfg, 'custom_manifest_url', ''))
        or _sstr(_sget(ch, 'manifest_url', ''))
        or (
            repo_val
            and repo_val not in ('doubleD1302/AmeeVH',)
        )
    )

    # 1. Close running game
    if code in ('E-GAME-RUNNING', 'E-FILE-IN-USE', 'E-FILE-CHANGED') or (
        game_running and not _is_network_code(code)
    ):
        _add('close_game', 10)

    # 2. Graphics / Startup DLL compatibility
    if code in ('E-STARTUP-DLL', 'E-GPU-RENDER'):
        _add('switch_safe_graphics', 10)

    # 3. Admin / ACL / CFA
    if (
        code in ('E-FILE-DENIED', 'E-CFA-BLOCKED', 'E-CONFIG-SAVE', 'E-SHORTCUT')
        or cfa_suspected
        or (win32_err == 5 and not _is_network_code(code))
    ):
        # If already admin, push relaunch_admin after open_game_dir so actionable fixes rank higher
        sr_admin = _is_already_admin(ctx)
        _add('relaunch_admin', 40 if sr_admin else 15)

    # 4. Network / TLS / Captive / Parallel DL / BG Sync
    if _is_network_code(code):
        _add('probe_network', 20)

    # 5. Open game/target directory
    if _is_file_or_folder_code(code) or code in ('E-STARTUP-DLL', 'E-CONFIG-SAVE', 'E-MIGRATION', 'E-PKG-MISMATCH'):
        _add('open_game_dir', 25)

    # 6. Config / Migration / Custom channel reset
    if (
        code in ('E-CONFIG-CHANNEL', 'E-LOCAL-PAYLOAD', 'E-MIGRATION', 'E-GPU-RENDER')
        or corrupt_cfg
        or (code in ('E-HTTP-404', 'E-MANIFEST-MISSING', 'E-RELEASE') and has_custom_channel)
    ):
        _add('reset_config', 30)

    # 7. Official clean restore
    if code in (
        'E-BACKUP',
        'E-FILE-MISMATCH',
        'E-RECEIPT-MISMATCH',
        'E-OFFICIAL-NOTFOUND',
        'E-DOWNGRADE',
        'E-RECOVERY-REQUIRED',
        'E-JOURNAL',
        'E-INSTALL-ROLLED-BACK',
    ) or (code == 'E-PKG-MISMATCH' and _sbool(_sget(game, 'has_vietnamese', False))):
        _add('restore_official', 35)

    order_index = {aid: idx for idx, aid in enumerate(CANONICAL_ACTION_IDS)}
    return sorted(candidates.values(), key=lambda a: (a.priority, order_index.get(a.action_id, 99)))


def plan_actions(error_code: Optional[str], ctx: Optional[ErrorContext] = None) -> list[QuickFixAction]:
    """Return up to 3 contextual Quick-Fix actions plus always-present ``copy_report``."""
    code = (_sstr(error_code) or 'E-UNKNOWN').strip().upper() or 'E-UNKNOWN'
    try:
        candidates = _collect_candidates(code, ctx)
    except Exception:  # noqa: BLE001
        candidates = []
    seen: set[str] = {'copy_report'}
    selected: list[QuickFixAction] = []
    for act in candidates:
        if act.action_id not in seen:
            seen.add(act.action_id)
            selected.append(act)
            if len(selected) >= 3:
                break
    try:
        copy_act = _make_action('copy_report', priority=999, ctx=ctx, code=code)
    except Exception:  # noqa: BLE001
        copy_act = QuickFixAction(
            action_id='copy_report',
            label='Sao chép gói báo lỗi gọn cho Dev',
            description='Sao chép báo cáo chẩn đoán đã ẩn thông tin cá nhân vào clipboard.',
            priority=999,
            icon_name=ACTION_ICON_KEYS['copy_report'],
        )
    selected.append(copy_act)
    return selected


def secondary_actions(error_code: Optional[str], ctx: Optional[ErrorContext] = None) -> list[QuickFixAction]:
    """Return remaining canonical actions not already in :func:`plan_actions`."""
    code = (_sstr(error_code) or 'E-UNKNOWN').strip().upper() or 'E-UNKNOWN'
    primary_ids = {a.action_id for a in plan_actions(code, ctx)}
    out: list[QuickFixAction] = []
    for idx, aid in enumerate(CANONICAL_ACTION_IDS):
        if aid in primary_ids:
            continue
        try:
            out.append(_make_action(aid, priority=100 + idx, ctx=ctx, code=code))
        except Exception:  # noqa: BLE001
            out.append(
                QuickFixAction(
                    action_id=aid,
                    label=aid,
                    priority=100 + idx,
                    icon_name=ACTION_ICON_KEYS.get(aid, ''),
                )
            )
    return out
