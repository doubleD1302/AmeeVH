# -*- coding: utf-8 -*-
"""Version and compatibility decisions for the visible update controls."""
from __future__ import annotations

import importlib
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_FALLBACK_TITLES: dict[str, str] = {
    "E-NET": "Không kết nối được máy chủ",
    "E-NET-OFFLINE": "Máy chưa có đường ra Internet",
    "E-NET-DNS": "Không tìm ra địa chỉ GitHub (lỗi DNS)",
    "E-NET-TIMEOUT": "GitHub phản hồi quá chậm",
    "E-NET-REFUSED": "Máy chủ từ chối kết nối",
    "E-NET-RESET": "Kết nối bị ngắt giữa chừng",
    "E-NET-BLOCKED": "Windows hoặc phần mềm bảo mật chặn launcher dùng mạng",
    "E-NET-TLS-CERT": "Chứng chỉ bảo mật không được tin cậy",
    "E-NET-TLS": "Không thiết lập được kết nối an toàn (HTTPS)",
    "E-NET-PROXY": "Proxy từ chối hoặc chặn yêu cầu",
    "E-NET-CAPTIVE": "Mạng đang chặn hoặc chuyển hướng đăng nhập (Captive Portal)",
    "E-HTTP-RATE": "GitHub đang giới hạn lượt truy cập",
    "E-HTTP-404": "Không tìm thấy tệp trên GitHub",
    "E-HTTP-5XX": "GitHub đang gặp sự cố",
    "E-HTTP-4XX": "GitHub từ chối yêu cầu",
    "E-SYNC-PENDING": "Launcher đang đọc thông tin từ GitHub",
    "E-CONFIG-CHANNEL": "Nguồn GitHub trong Cài đặt chưa hợp lệ",
    "E-LOCAL-PAYLOAD": "Gói bản dịch cục bộ không dùng được",
    "E-RELEASE": "Chưa có bản phát hành dùng được",
    "E-DATA-SCHEMA": "Dữ liệu GitHub trả về sai định dạng",
    "E-DATA-JSON": "Dữ liệu tải về không đọc được",
    "E-DATA-UNVERIFIED": "Tệp phát hành chưa có mã xác minh",
    "E-MANIFEST-MISSING": "Bản phát hành chưa có bảng kê bản dịch",
    "E-MANIFEST-INVALID": "Bảng kê bản dịch bị lỗi",
    "E-MANIFEST-VERSION": "Không so sánh được phiên bản bản dịch",
    "E-MANIFEST-PLATFORM": "Gói bản dịch không dành cho Windows",
    "E-SECURITY": "Launcher từ chối vì không an toàn",
    "E-DOWNGRADE": "Gói bản dịch cũ hơn bản đang cài",
    "E-PKG-MISMATCH": "Phiên bản game chưa khớp gói Việt hoá",
    "E-NO-GAME-FOLDER": "Chưa chọn thư mục game",
    "E-UNKNOWN": "Lỗi chưa xác định",
}

_FALLBACK_HTTP_FAMILY = (
    (lambda c: c in (403, 429), "E-HTTP-RATE"),
    (lambda c: c == 404, "E-HTTP-404"),
    (lambda c: 500 <= c <= 599, "E-HTTP-5XX"),
    (lambda c: 400 <= c <= 499, "E-HTTP-4XX"),
)


def _get_error_catalog():
    pkg = __package__
    if not pkg:
        return None
    target = f"{pkg}.error_catalog"
    try:
        return importlib.import_module(".error_catalog", pkg)
    except ModuleNotFoundError as exc:
        if exc.name == target:
            return None
        raise


def _lookup_title(code: str) -> str:
    cat = _get_error_catalog()
    if cat is not None:
        return cat.lookup(code).title
    norm = str(code or "E-UNKNOWN")
    title = _FALLBACK_TITLES.get(norm)
    if title is None:
        m = re.fullmatch(r"E-HTTP-(\d{3})", norm)
        if m:
            status = int(m.group(1))
            for pred, fam in _FALLBACK_HTTP_FAMILY:
                if pred(status):
                    title = f"{_FALLBACK_TITLES[fam]} (HTTP {status})"
                    break
    return title or _FALLBACK_TITLES["E-UNKNOWN"]


def _fallback_classify_text(text: str) -> Optional[str]:
    t = str(text or "")
    if not t:
        return None
    low = t.lower()
    m = re.search(r"http error (\d{3})|\bhttp (\d{3})\b|mã (\d{3})\b", low)
    if m:
        raw_status = next(g for g in m.groups() if g)
        try:
            return f"E-HTTP-{int(raw_status)}"
        except (TypeError, ValueError):
            return "E-NET"
    checks = (
        (("getaddrinfo failed", "name or service not known", "nodename nor servname",
          "temporary failure in name resolution", "[errno 11001]", "[errno 11002]",
          "[errno 11004]", "winerror 11001"), "E-NET-DNS"),
        (("certificate_verify_failed", "certificate verify failed", "self signed certificate",
          "unable to get local issuer"), "E-NET-TLS-CERT"),
        (("tunnel connection failed", "proxyerror", "proxy authentication"), "E-NET-PROXY"),
        ((r"\bssl\b", r"\btls\b", "sslerror"), "E-NET-TLS"),
        (("timed out", "timeout", "winerror 10060", "[errno 10060]", "quá thời hạn"), "E-NET-TIMEOUT"),
        (("connection refused", "winerror 10061", "[errno 10061]", "actively refused"), "E-NET-REFUSED"),
        (("winerror 10013", "[errno 10013]", "forbidden by its access permissions"), "E-NET-BLOCKED"),
        (("network is unreachable", "no route to host", "winerror 10051", "winerror 10065",
          "[errno 10051]", "[errno 10065]"), "E-NET-OFFLINE"),
        (("forcibly closed", "connection reset", "connection aborted", "remotedisconnected",
          "incompleteread", "winerror 10054", "winerror 10053", "broken pipe"), "E-NET-RESET"),
    )
    for needles, code in checks:
        for n in needles:
            if (n.startswith("\\b") and re.search(n, low)) or (not n.startswith("\\b") and n in low):
                return code
    return None


def _classify_text(text: str) -> Optional[str]:
    cat = _get_error_catalog()
    if cat is not None:
        return cat.classify_text(text)
    return _fallback_classify_text(text)


def version_parts(value) -> Optional[tuple[int, int, int, int]]:
    match = re.fullmatch(r"v?(\d+(?:\.\d+){0,3})", str(value or "").strip(), re.I)
    if not match:
        return None
    parts = tuple(int(p) for p in match.group(1).split("."))
    return parts + (0,) * (4 - len(parts))


def newer(latest, installed) -> bool:
    latest_parts, installed_parts = version_parts(latest), version_parts(installed)
    return latest_parts is not None and installed_parts is not None and latest_parts > installed_parts


def matches(observed, expected) -> bool:
    observed_s, expected_s = str(observed or "").strip(), str(expected or "").strip()
    if not observed_s or not expected_s or observed_s.lower() in ("unknown", "*", "all"):
        return False
    expected_list = [e.strip() for e in re.split(r"[,;|]", expected_s) if e.strip()]
    return observed_s in expected_list or "*" in expected_list


def has_game_patch_conflict_in_log(game_info=None) -> bool:
    """Checks if game recently failed to patch publisher update due to modified files (Yostar + Steam)."""
    log_candidates = (
        Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\YOSTAR (HONG KONG) LIMITED\StellaSora\Player.log")),
        Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\YOSTAR (HONG KONG) LIMITED\StellaSora_steam\Player.log")),
    )
    gpath = getattr(game_info, "game_path", None) if game_info is not None else None
    receipt = getattr(game_info, "installed_receipt", None) if game_info is not None else None
    inst_ts: Optional[float] = None
    if isinstance(receipt, dict) and isinstance(receipt.get("installed_at"), str):
        try:
            inst_ts = datetime.fromisoformat(receipt["installed_at"].replace("Z", "+00:00")).timestamp()
        except ValueError:
            inst_ts = None

    for log_path in log_candidates:
        if not log_path.is_file():
            continue
        try:
            log_mtime = log_path.stat().st_mtime
            if (time.time() - log_mtime) > 86400:
                continue

            # Ignore stale Player.log if ss_win.mani, official_restored marker or patch receipt is newer
            if isinstance(gpath, (str, os.PathLike)):
                gp = Path(gpath)
                mani = gp / "Persistent_Store" / "ss_win.mani"
                if mani.is_file() and mani.stat().st_mtime > log_mtime:
                    continue
                restored_state = gp / "Persistent_Store" / "viethoa_installed.json"
                if restored_state.is_file() and restored_state.stat().st_mtime > log_mtime:
                    continue
                rp = gp / ".vietnamese_patch_receipt.json"
                if rp.is_file() and rp.stat().st_mtime > log_mtime:
                    continue

            if inst_ts is not None and inst_ts > log_mtime:
                continue

            with log_path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-200:]
                for line in lines:
                    if any(
                        err in line
                        for err in (
                            "BinDiffPatchError",
                            "Patch file verification failed",
                            "Data check fail",
                            "no found patch target bundle",
                        )
                    ):
                        return True
        except Exception:
            continue
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
            supported_parts = [p for g in game_candidates if (p := version_parts(g)) is not None]
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


def _blocked(code: str, detail: str = "", **extra: Any) -> dict[str, Any]:
    """State dict for "install not allowed" carrying the catalog code that explains why."""
    title = _lookup_title(code)
    message = title + (f" — {detail}" if detail else "") + f" [{code}]"
    return {
        "available": False,
        "can_install": False,
        "message": message,
        "blocker_code": code,
        "blocker_detail": detail,
        **extra,
    }


def sync_blocker(sync) -> Optional[tuple[str, str]]:
    """(code, detail) when the GitHub sync state does not allow installing, else ``None``."""
    sync = sync or {}
    if sync.get("release_status") == "online" and sync.get("manifest_status") == "online":
        return None
    if sync.get("configuration_error"):
        return "E-CONFIG-CHANNEL", str(sync["configuration_error"])
    if sync.get("error_code"):
        return str(sync["error_code"]), str(sync.get("message", ""))
    if "release_status" not in sync:
        return "E-SYNC-PENDING", str(sync.get("message", ""))
    if sync.get("release_status") != "online":
        err = str(sync.get("release_error") or "")
        return (sync.get("release_error_code") or _classify_text(err) or "E-NET"), err
    err = str(sync.get("manifest_error") or "")
    return (sync.get("manifest_error_code") or _classify_text(err) or "E-MANIFEST-MISSING"), err


def summarize_declared_versions(declared: Any, *, for_resource: bool = False) -> str:
    """Formats comma/semicolon-separated manifest version specs cleanly for end users."""
    raw = str(declared or "").strip()
    if not raw:
        return "?"
    items: list[str] = []
    has_wildcard = False
    for tok in re.split(r"[,;|]", raw):
        s = tok.strip()
        if not s:
            continue
        if s == "*":
            has_wildcard = True
        elif re.fullmatch(r"[0-9][0-9A-Za-z_.-]*", s):
            items.append(s)
    if for_resource and has_wildcard:
        return f"{items[-1]} · mọi hotfix" if items else "mọi phiên bản tài nguyên"
    if not items:
        return "mọi phiên bản" if has_wildcard else raw
    if len(items) <= 2:
        return ", ".join(items)
    return f"{items[0]} … {items[-1]}"


def diagnose_version_mismatch(
    local_game: Any,
    local_res: Any,
    declared_game: Any,
    declared_res: Any,
) -> dict[str, Any]:
    """Direction-aware compatibility diagnosis between installed game and translation manifest.

    Returns a dict with ``kind`` in:
    ``'match' | 'game_older' | 'game_newer' | 'resource_mismatch' | 'unknown'``
    along with plain-Vietnamese ``title``, ``summary``, and ``steps``.
    """
    lg = str(local_game or "").strip()
    lr = str(local_res or "").strip()
    dg = str(declared_game or "").strip()
    dr = str(declared_res or "").strip()
    sup_g = summarize_declared_versions(dg, for_resource=False)
    sup_r = summarize_declared_versions(dr, for_resource=True)

    base = {
        "kind": "unknown",
        "local_game": lg,
        "local_res": lr,
        "supported_game": sup_g,
        "supported_res": sup_r,
        "title": "Phiên bản game chưa khớp gói Việt hoá",
        "summary": "",
        "steps": (),
    }
    if not lg or lg.lower() in ("unknown", "*", "all") or not dg:
        return base

    game_ok = matches(lg, dg)
    res_known = bool(lr and lr.lower() not in ("unknown", "*", "all"))
    res_ok = (not dr) or (not res_known) or matches(lr, dr)
    if game_ok and res_ok:
        base["kind"] = "match"
        return base

    if not game_ok:
        lp = version_parts(lg)
        cands = [version_parts(tok.strip()) for tok in re.split(r"[,;|]", dg) if tok.strip() and tok.strip() != "*"]
        valid_cands = [c for c in cands if c is not None]
        if lp is not None and valid_cands and lp > max(valid_cands):
            kind = "game_newer"
        else:
            kind = "game_older"
        base["kind"] = kind
        res_note = f" (tài nguyên {lr})" if res_known else ""
        if kind == "game_older":
            base["title"] = f"Game trên máy đang ở bản cũ (v{lg} → cần v{sup_g})"
            base["summary"] = (
                f"Stella Sora trên máy tính đang ở phiên bản v{lg}{res_note}, cũ hơn gói Việt hoá mới nhất trên GitHub (v{sup_g}).\n\n"
                "Đây KHÔNG phải lỗi hỏng game — launcher tạm dừng cài để tránh game báo lỗi xác minh tệp (BinDiff / Data check fail) ngay khi mở."
            )
            base["steps"] = (
                f"Mở Stella Sora (hoặc mở qua Yostar Launcher / Steam) để game tự tải bản cập nhật mới nhất lên v{sup_g} vào tới màn hình đăng nhập/chính.",
                "Thoát hẳn Stella Sora (đảm bảo không còn tiến trình StellaSora.exe chạy ngầm).",
                "Quay lại launcher, bấm \"Kiểm tra phiên bản Việt hoá\" (hoặc chọn lại thư mục game) rồi bấm \"Cài Việt hoá\".",
            )
        else:
            base["title"] = f"Game trên máy (v{lg}) mới hơn gói Việt hoá (v{sup_g})"
            base["summary"] = (
                f"Stella Sora trên máy tính đã cập nhật lên v{lg}{res_note}, trong khi gói Việt hoá hiện tại trên GitHub mới hỗ trợ đến v{sup_g}.\n\n"
                "Launcher tạm dừng cài để không ghi đè dữ liệu cũ làm văng hoặc lỗi game."
            )
            base["steps"] = (
                "Dữ liệu game của bạn hoàn toàn an toàn — bạn vẫn có thể chơi bản tiếng Anh bình thường trong lúc chờ.",
                f"Chờ nhóm dịch phát hành gói Việt hoá tương thích v{lg} (theo dõi mục Thông báo trong launcher).",
                "Khi có bản mới, bấm \"Kiểm tra phiên bản Việt hoá\" rồi cài lại như bình thường.",
            )
        return base

    base["kind"] = "resource_mismatch"
    base["title"] = f"Tài nguyên game (RES {lr}) chưa khớp gói Việt hoá"
    base["summary"] = (
        f"Phiên bản game đã khớp (v{lg}) nhưng mã tài nguyên trên máy (RES {lr}) khác với danh sách gói Việt hoá hỗ trợ ({sup_r})."
    )
    base["steps"] = (
        "Mở Stella Sora cho game tự tải đủ bản vá tài nguyên mới nhất, sau đó thoát hẳn game.",
        "Quay lại launcher bấm \"Kiểm tra phiên bản Việt hoá\" rồi thử cài lại.",
    )
    return base


def translation_state(sync, game) -> dict[str, Any]:
    blocker = sync_blocker(sync)
    if blocker:
        return _blocked(*blocker)
    version = sync.get("translation_version")
    receipt = getattr(game, "installed_receipt", None)
    if not getattr(game, "installed", False):
        return _blocked("E-NO-GAME-FOLDER", f"Bản Việt hoá: {version}")
    local_game = str(getattr(game, "version", "") or "").strip()
    local_res = str(getattr(game, "resource_version", "") or "").strip()
    decl_game = str(sync.get("translation_game") or "").strip()
    decl_res = str(sync.get("translation_resource") or "").strip()
    diag = diagnose_version_mismatch(local_game, local_res, decl_game, decl_res)
    if diag["kind"] in ("game_older", "game_newer", "resource_mismatch"):
        detail = diag["title"]
        return _blocked(
            "E-PKG-MISMATCH",
            detail,
            version=version,
            mismatch_kind=diag["kind"],
            local_game=diag["local_game"],
            local_resource=diag["local_res"],
            supported_game=diag["supported_game"],
            supported_resource=diag["supported_res"],
            version_note=diag["summary"],
        )
    if diag["kind"] == "match":
        version_note = "Phiên bản game và tài nguyên khớp bảng kê; chưa xác minh hiển thị trong game."
    else:
        version_note = "Phiên bản game hoặc tài nguyên chưa đọc được đầy đủ; chưa xác minh tương thích."
    if version_parts(version) is None:
        return _blocked("E-MANIFEST-VERSION", f"Phiên bản trong bảng kê: {version!r}")
    if getattr(game, "receipt_stale", False):
        return {
            "available": True,
            "can_install": True,
            "message": f"Game vừa cập nhật tệp gốc — cần bấm Cập nhật Việt hoá ({version}) để áp dụng lại. {version_note}",
            "version": version,
            "version_note": version_note,
        }
    if not receipt:
        return {
            "available": False,
            "can_install": True,
            "message": f"Bản Việt hoá: {version}. Chưa có biên bản cài để đối chiếu phiên bản. {version_note}",
            "version_note": version_note,
        }
    current = receipt.get("version")
    if version_parts(version) is None or version_parts(current) is None:
        return _blocked("E-MANIFEST-VERSION", f"Đã cài {current!r}, bảng kê {version!r}")
    if newer(version, current):
        return {
            "available": True,
            "can_install": True,
            "message": f"Có bản Việt hoá {version} mới hơn bản đã cài {current}. {version_note}",
            "version": version,
            "version_note": version_note,
        }
    if version_parts(version) == version_parts(current):
        sync_sha = sync.get("manifest_sha256")
        rec_sha = receipt.get("manifest_sha256")
        legacy_sha = sync.get("legacy_manifest_sha256")
        if sync_sha and rec_sha and rec_sha != sync_sha and (not legacy_sha or rec_sha != legacy_sha):
            return {
                "available": True,
                "can_install": True,
                "message": f"Có bản vá dữ liệu/hình ảnh mới trong gói {version}! Bấm Cập nhật Việt hoá để đồng bộ. {version_note}",
                "version": version,
                "version_note": version_note,
            }
        return {
            "available": False,
            "can_install": True,
            "message": f"Bản đã cài: {current} (mới nhất). Bạn có thể bấm Cài lại để làm mới dữ liệu. {version_note}",
            "version": version,
            "version_note": version_note,
        }
    return _blocked("E-DOWNGRADE", f"Đã cài {current}, bảng kê {version}", version=version, version_note=version_note)
