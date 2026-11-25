"""Pure-Python core logic package for Stella Sora Việt Hóa Launcher v2.0."""
from __future__ import annotations

import importlib
from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # M3A: Foundation, Config, Detection, Migration
    "ConfigManager": (".config", "ConfigManager"),
    "PathManager": (".config", "PathManager"),
    "LAUNCHER_VERSION": (".config", "LAUNCHER_VERSION"),
    "SUPPORT_DONATION_ENABLED": (".config", "SUPPORT_DONATION_ENABLED"),
    "GameInfo": (".types", "GameInfo"),
    "NotificationItem": (".types", "NotificationItem"),
    "OperationEvent": (".types", "OperationEvent"),
    "OperationPhase": (".types", "OperationPhase"),
    "SupporterData": (".types", "SupporterData"),
    "SupporterItem": (".types", "SupporterItem"),
    "InstallerError": (".safety", "InstallerError"),
    "GameDetector": (".game_detection", "GameDetector"),
    "migrate_from_r02_if_needed": (".migration", "migrate_from_r02_if_needed"),
    # M2: Official Background Sync
    "BackgroundSyncService": (".bg_sync", "BackgroundSyncService"),
    "BackgroundFrame": (".bg_sync", "BackgroundFrame"),
    "LuminanceProfile": (".bg_sync", "LuminanceProfile"),
    # M3B: Parallel DL, Patching, Rollback, Official Restore
    "PatchInstaller": (".installer", "PatchInstaller"),
    "NetworkService": (".network", "NetworkService"),
    "RollbackEngine": (".rollback", "RollbackEngine"),
    "OfficialClient": (".official_resources", "OfficialClient"),
    "OfficialRestoreEngine": (".official_restore", "OfficialRestoreEngine"),
    "VanillaRestoreEngine": (".vanilla_restore", "VanillaRestoreEngine"),
    # M3C: Self-Update & Update Notice
    "apply_job": (".self_update", "apply_job"),
    "schedule_update": (".self_update", "schedule_update"),
    "cleanup_update_artifacts": (".self_update", "cleanup_update_artifacts"),
    "detect_new_publisher_version": (".update_notice", "detect_new_publisher_version"),
    "translation_state": (".update_notice", "translation_state"),
    # M4: Diagnostics, Error Catalog, Quick-Fix
    "AdbBridge": (".diagnostics", "AdbBridge"),
    "DiagnosticsCollector": (".diagnostics", "DiagnosticsCollector"),
    "SystemReport": (".diagnostics", "SystemReport"),
    "diagnose": (".error_catalog", "diagnose"),
    "lookup": (".error_catalog", "lookup"),
    "ErrorContext": (".error_report", "ErrorContext"),
    "build_report": (".error_report", "build_report"),
    "run_probe": (".net_probe", "run_probe"),
    "QuickFixAction": (".quick_fix", "QuickFixAction"),
    "plan_actions": (".quick_fix", "plan_actions"),
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    spec = _LAZY_EXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod_rel, attr = spec
    try:
        mod = importlib.import_module(mod_rel, __name__)
    except ModuleNotFoundError as exc:
        if exc.name == f"{__name__}{mod_rel}":
            raise AttributeError(
                f"module {__name__!r} attribute {name!r} is unavailable (submodule {mod_rel!r} not present)"
            ) from exc
        raise
    val = getattr(mod, attr)
    globals()[name] = val
    return val


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
