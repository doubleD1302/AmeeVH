"""Core logic package for Stella Sora Launcher."""

from launcher_next.core.config import ConfigManager, PathManager
from launcher_next.core.diagnostics import AdbBridge, DiagnosticsCollector, SystemReport
from launcher_next.core.game_detection import GameDetector
from launcher_next.core.installer import PatchInstaller
from launcher_next.core.network import NetworkService
from launcher_next.core.rollback import RollbackEngine
from launcher_next.core.types import (
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
