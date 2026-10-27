"""Core logic package for Stella Sora Launcher."""

from .config import ConfigManager, PathManager
from .diagnostics import AdbBridge, DiagnosticsCollector, SystemReport
from .game_detection import GameDetector
from .installer import PatchInstaller
from .network import NetworkService
from .rollback import RollbackEngine
from .types import (
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
