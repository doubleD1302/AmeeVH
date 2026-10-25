# -*- coding: utf-8 -*-
"""
Core data types and contracts for Stella Sora Launcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class OperationPhase(str, Enum):
    IDLE = "idle"
    PREFLIGHT = "preflight"
    DOWNLOAD = "download"
    VERIFY = "verify"
    BACKUP = "backup"
    APPLY = "apply"
    READBACK = "readback"
    ROLLBACK = "rollback"
    DONE = "done"
    ERROR = "error"


@dataclass
class OperationEvent:
    operation_id: str
    phase: OperationPhase
    message: str
    completed: int = 0
    total: int = 0
    unit: str = "items"
    error_code: Optional[str] = None
    receipt: Optional[dict[str, Any]] = None

    @property
    def percentage(self) -> float:
        if self.total <= 0:
            return 0.0
        return min(100.0, max(0.0, (self.completed / self.total) * 100.0))


@dataclass
class GameInfo:
    installed: bool = False
    game_path: Optional[Path] = None
    canonical_path: Optional[str] = None
    platform: str = "unknown"  # "steam" | "standalone" | "unknown"
    version: str = "unknown"
    is_running: bool = False
    has_vietnamese: bool = False
    vietnamese_version: Optional[str] = None
    installed_receipt: Optional[dict[str, Any]] = None
    backup_count: int = 0
    detection_source: str = "none"


@dataclass
class NotificationItem:
    id: str
    title: str
    summary: str
    content: str
    category: str  # "project", "guide", "notice", "feedback"
    badge: str
    date: str
    link_url: Optional[str] = None
    is_unread: bool = False


@dataclass
class SupporterItem:
    name: str
    tier: str
    date: str
    message: str = ""


@dataclass
class SupporterData:
    status: str  # "unavailable", "empty", "cached", "online"
    supporters: list[SupporterItem] = field(default_factory=list)
    qr_placeholder_text: str = "Kênh ủng hộ hiện chưa mở chính thức. Dự án Stella Sora Việt hóa hoàn toàn phi thương mại và miễn phí."
