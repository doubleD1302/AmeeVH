"""Core logic package for Stella Sora Launcher."""

from launcher_next_r09.core.config import ConfigManager, PathManager
from launcher_next_r09.core.diagnostics import AdbBridge, DiagnosticsCollector, SystemReport
from launcher_next_r09.core.game_detection import GameDetector
from launcher_next_r09.core.installer import PatchInstaller
from launcher_next_r09.core.network import NetworkService
from launcher_next_r09.core.rollback import RollbackEngine
from launcher_next_r09.core.types import (
    GameInfo,
    NotificationItem,
    OperationEvent,
    OperationPhase,
    SupporterData,
)

__all__ = [
    "ConfigManager",
    "PathManager",
    "AdbBridge",
    "DiagnosticsCollector",
    "SystemReport",
    "GameDetector",
    "PatchInstaller",
    "NetworkService",
    "RollbackEngine",
    "GameInfo",
    "NotificationItem",
    "OperationEvent",
    "OperationPhase",
    "SupporterData",
]
