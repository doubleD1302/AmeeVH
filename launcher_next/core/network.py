"""Network services for Stella Sora Launcher.

Handles:
- Notification / Announcement loading (remote with local offline fallback)
- Self-update checking (check only, never auto-apply)
- Supporter / Sponsor listing (strictly unavailable / empty state when no API)
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import List, Optional

from launcher_next.core.types import NotificationItem, SupporterData

logger = logging.getLogger("launcher.network")

DEFAULT_NOTIFICATIONS = [
    NotificationItem(
        id="notif_01",
        title="Bản Việt Hóa Stella Sora v0.9.8",
        summary="Cập nhật giao diện Starlit Glass hoàn toàn mới, đồng bộ dữ liệu cốt truyện & thẻ nhân vật.",
        content=(
            "Chào mừng bạn đến với phiên bản Việt Hóa v0.9.8 dành cho Stella Sora!\n\n"
            "Các điểm nổi bật:\n"
            "- Giao diện Launcher Starlit Glass hiện đại, tương thích độ phân giải cao.\n"
            "- Cơ chế cài đặt an toàn hai pha (Preimage Snapshot + Atomic Staging).\n"
            "- Khôi phục nguyên trạng (Rollback) ràng buộc chặt chẽ với thư mục game gốc.\n"
            "- Đồng bộ toàn bộ dữ liệu thẻ kỹ năng và mô tả 20 nhân vật mới nhất."
        ),
        category="project",
        badge="Bản phát hành",
        date="2026-10-25",
        is_unread=True,
    ),
    NotificationItem(
        id="notif_02",
        title="Lưu ý khi cập nhật game qua Steam / Yostar Launcher",
        summary="Khuyến nghị khôi phục nguyên trạng trước khi để client chính thức cập nhật.",
        content=(
            "Khi game Stella Sora có bản cập nhật mới trên Steam hoặc Yostar Launcher:\n\n"
            "1. Mở Stella Sora Launcher và nhấn 'Khôi phục nguyên trạng' để đưa game về gốc.\n"
            "2. Để Steam / Yostar hoàn tất tải và cập nhật phiên bản mới.\n"
            "3. Mở lại Stella Sora Launcher và tiến hành 'Cài đặt Việt Hóa' bản tương thích mới nhất.\n\n"
            "Việc này giúp tránh xung đột tệp và đảm bảo tính toàn vẹn của dữ liệu."
        ),
        category="guide",
        badge="Hướng dẫn",
        date="2026-10-24",
        is_unread=False,
    ),
    NotificationItem(
        id="notif_03",
        title="Cộng đồng Việt Hóa Stella Sora",
        summary="Tham gia thảo luận, báo lỗi và đóng góp ý kiến tại nhóm cộng đồng.",
        content=(
            "Cảm ơn sự đồng hành và ủng hộ nhiệt tình của cộng đồng người chơi Stella Sora tại Việt Nam!\n\n"
            "Nếu bạn gặp lỗi dịch thuật hoặc sự cố kỹ thuật trong quá trình trải nghiệm, "
            "vui lòng sử dụng tính năng Chẩn đoán hệ thống hoặc liên hệ với đội ngũ phát triển."
        ),
        category="notice",
        badge="Cộng đồng",
        date="2026-10-20",
        is_unread=False,
    ),
]


class NetworkService:
    """Manages external network queries with offline fallbacks."""

    def __init__(self, update_url: Optional[str] = None, notifications_url: Optional[str] = None):
        self.update_url = update_url
        self.notifications_url = notifications_url

    def fetch_notifications(self, fallback_path: Optional[str] = None) -> List[NotificationItem]:
        """Fetch announcements from remote or fall back to local bundled/default items."""
        if self.notifications_url:
            try:
                req = urllib.request.Request(
                    self.notifications_url,
                    headers={"User-Agent": "StellaSora-Launcher/0.9.8"},
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        items = []
                        for entry in data.get("notifications", []):
                            items.append(
                                NotificationItem(
                                    id=str(entry.get("id", "")),
                                    title=str(entry.get("title", "")),
                                    summary=str(entry.get("summary", "")),
                                    content=str(entry.get("content", "")),
                                    category=str(entry.get("category", "notice")),
                                    badge=str(entry.get("badge", "Thông báo")),
                                    date=str(entry.get("date", "")),
                                    link_url=entry.get("link_url"),
                                    is_unread=bool(entry.get("is_unread", False)),
                                )
                            )
                        if items:
                            return items
            except Exception as e:
                logger.warning(f"Failed to fetch remote notifications: {e}")

        # Try fallback file if provided
        if fallback_path:
            try:
                with open(fallback_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = []
                    for entry in data.get("notifications", []):
                        items.append(
                            NotificationItem(
                                id=str(entry.get("id", "")),
                                title=str(entry.get("title", "")),
                                summary=str(entry.get("summary", "")),
                                content=str(entry.get("content", "")),
                                category=str(entry.get("category", "notice")),
                                badge=str(entry.get("badge", "Thông báo")),
                                date=str(entry.get("date", "")),
                                link_url=entry.get("link_url"),
                                is_unread=bool(entry.get("is_unread", False)),
                            )
                        )
                    if items:
                        return items
            except Exception as e:
                logger.debug(f"Could not read local notification fallback {fallback_path}: {e}")

        return DEFAULT_NOTIFICATIONS

    def check_for_updates(self, current_version: str = "0.9.8") -> dict:
        """Check for updates online. Returns status dictionary. Never applies automatically."""
        result = {
            "has_update": False,
            "latest_version": current_version,
            "download_url": None,
            "changelog": "",
            "message": "Bạn đang sử dụng phiên bản mới nhất.",
        }

        if not self.update_url:
            return result

        try:
            req = urllib.request.Request(
                self.update_url,
                headers={"User-Agent": f"StellaSora-Launcher/{current_version}"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    latest = data.get("latest_version", current_version)
                    if latest != current_version:
                        result["has_update"] = True
                        result["latest_version"] = latest
                        result["download_url"] = data.get("download_url")
                        result["changelog"] = data.get("changelog", "")
                        result["message"] = f"Có phiên bản mới {latest}. Hãy tải từ kênh chính thức."
        except Exception as e:
            logger.info(f"Update check failed (offline or unreachable): {e}")
            result["message"] = "Không thể kết nối đến máy chủ kiểm tra cập nhật."

        return result

    def get_supporter_data(self) -> SupporterData:
        """Fetch supporter info.
        
        Strictly returns unavailable state with an empty list unless a verified
        live backend is integrated. Never returns mock or fake donor lists.
        """
        return SupporterData(
            status="unavailable",
            supporters=[],
            qr_placeholder_text=(
                "Hệ thống danh sách người ủng hộ chưa kết nối API máy chủ chính thức.\n"
                "Dữ liệu đóng góp đang được bảo lưu an toàn."
            ),
        )
