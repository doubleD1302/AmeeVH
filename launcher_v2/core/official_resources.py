# -*- coding: utf-8 -*-
"""Read-only access to the OFFICIAL Stella Sora PC resource servers.

The launcher uses this module to learn which resource version the publisher serves
and to download/rebuild exact official copies of text resources (data.arcx, lua.arcx,
subtitles) and bundles. It never uploads anything and never executes downloaded data.

Protocol (verified against the live regional CDN, same as tools/stella_hot_update.py):
  /meta/win.html        AES-128-CBC encrypted protobuf: [(file name, md5, version, folder)]
  /meta/serverlist.html AES-128-CBC encrypted protobuf: field 1 = server data version
  /res/win/<version>/<folder>/<name>  plain files, MD5 listed in the manifests
  ss_win.mani + ss_win_add.mani + p_<n>_m.ss_win.mani  text manifests; the last one is final
A resource is either a full file or a chain  base + BSDIFF40 delta(s); every step is
checked against the MD5/size from the manifests.
"""
from __future__ import annotations

import collections
import hashlib
import http.client
import math
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import CancelledError as FuturesCancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from . import tls
from .bsdiff40 import BsdiffError, apply_bsdiff
from .safety import InstallerError
from .types import OperationEvent, OperationPhase

REGIONS = {
    "EN": ("https://nova-static.stellasora.global", b"ma5Dn2FhC*Xhxy%c"),
}
USER_AGENT = "StellaSoraVietHoaLauncher/2.0 (official-text-restore)"
MAX_META_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
TEXT_ARCHIVES = ("data.arcx", "lua.arcx")

_TLS_LOCK = threading.Lock()
_TLS_READY = False


def _ensure_tls() -> None:
    global _TLS_READY
    if _TLS_READY:
        return
    with _TLS_LOCK:
        if _TLS_READY:
            return
        if urllib.request._opener is None:
            tls.install()
        _TLS_READY = True


def _header_value(headers, name: str) -> str:
    if not headers:
        return ""
    if isinstance(headers, dict):
        target = name.lower()
        for k, v in headers.items():
            if str(k).lower() == target:
                return str(v or "")
        return ""
    getter = getattr(headers, "get", None)
    if callable(getter):
        return str(getter(name) or "")
    return ""


def _url_has_html_suffix(url: str) -> bool:
    path = urllib.parse.urlparse(url).path.lower()
    return path.endswith((".html", ".htm"))


def _is_html_content_type(headers) -> bool:
    ct = _header_value(headers, "Content-Type").split(";", 1)[0].strip().lower()
    return ct in ("text/html", "application/xhtml+xml")


def _is_html_body(data: bytes) -> bool:
    if not data:
        return False
    head = data[:512].lstrip(b" \t\r\n\xef\xbb\xbf").lower()
    if head.startswith((b"<!doctype html", b"<html", b"<head", b"<body", b"<title", b"<meta", b"<script")):
        return True
    if head.startswith((b"<!--", b"<?xml")) and (b"<html" in head or b"<!doctype html" in head):
        return True
    return False


def _looks_like_html_markup(data: bytes) -> bool:
    if _is_html_body(data):
        return True
    if not data:
        return False
    sample = data[:512]
    stripped = sample.lstrip(b" \t\r\n\xef\xbb\xbf")
    if not stripped.startswith(b"<") or b">" not in stripped:
        return False
    if b"</" not in stripped and b"/>" not in stripped:
        return False
    decoded: Optional[str] = None
    for trim in range(4):
        chunk = sample[: len(sample) - trim] if trim else sample
        if not chunk:
            break
        try:
            decoded = chunk.decode("utf-8")
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        return False
    return all(ch in ("\t", "\n", "\r") or ord(ch) >= 32 for ch in decoded)


class OfficialResourceError(InstallerError):
    pass


# --------------------------------------------------------------------------- crypto
def _bcrypt_aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    """AES-CBC (no padding removal) through the Windows CNG provider; no third-party dependency."""
    import ctypes
    from ctypes import wintypes

    bcrypt = ctypes.WinDLL("bcrypt")
    bcrypt.BCryptOpenAlgorithmProvider.argtypes = [ctypes.POINTER(ctypes.c_void_p), wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.ULONG]
    bcrypt.BCryptSetProperty.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG]
    bcrypt.BCryptGenerateSymmetricKey.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, wintypes.ULONG, ctypes.c_char_p, wintypes.ULONG, wintypes.ULONG]
    bcrypt.BCryptDecrypt.argtypes = [ctypes.c_void_p, ctypes.c_char_p, wintypes.ULONG, ctypes.c_void_p, ctypes.c_void_p, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG), wintypes.ULONG]
    bcrypt.BCryptDestroyKey.argtypes = [ctypes.c_void_p]
    bcrypt.BCryptCloseAlgorithmProvider.argtypes = [ctypes.c_void_p, wintypes.ULONG]

    alg, handle = ctypes.c_void_p(), ctypes.c_void_p()
    if bcrypt.BCryptOpenAlgorithmProvider(ctypes.byref(alg), "AES", None, 0) != 0:
        raise OfficialResourceError("Không mở được bộ giải mã AES của Windows.", "CRYPTO_UNAVAILABLE")
    try:
        mode = ctypes.create_unicode_buffer("ChainingModeCBC")
        if bcrypt.BCryptSetProperty(alg, "ChainingMode", mode, ctypes.sizeof(mode), 0) != 0:
            raise OfficialResourceError("Không đặt được chế độ AES-CBC.", "CRYPTO_UNAVAILABLE")
        if bcrypt.BCryptGenerateSymmetricKey(alg, ctypes.byref(handle), None, 0, key, len(key), 0) != 0:
            raise OfficialResourceError("Không tạo được khoá AES.", "CRYPTO_UNAVAILABLE")
        try:
            iv_buf = ctypes.create_string_buffer(iv, 16)
            out = ctypes.create_string_buffer(len(data))
            written = wintypes.ULONG(0)
            status = bcrypt.BCryptDecrypt(handle, data, len(data), None, iv_buf, 16, out, len(data), ctypes.byref(written), 0)
            if status != 0:
                raise OfficialResourceError("Giải mã metadata thất bại (0x%08X)." % (status & 0xFFFFFFFF), "METADATA_DECRYPT")
            return out.raw[: written.value]
        finally:
            bcrypt.BCryptDestroyKey(handle)
    finally:
        bcrypt.BCryptCloseAlgorithmProvider(alg, 0)


def aes_cbc_decrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    if len(data) % 16:
        raise OfficialResourceError("Độ dài metadata mã hoá không hợp lệ.", "METADATA_FORMAT")
    try:  # optional accelerators when present in a developer environment
        from Crypto.Cipher import AES  # type: ignore

        return AES.new(key, AES.MODE_CBC, iv).decrypt(data)
    except ImportError:
        pass
    if os.name != "nt":
        raise OfficialResourceError("Chưa có bộ giải mã AES trên hệ điều hành này.", "CRYPTO_UNAVAILABLE")
    return _bcrypt_aes_cbc_decrypt(key, iv, data)


def decrypt_metadata(data: bytes, region: str = "EN", decrypt: Optional[Callable[[bytes, bytes, bytes], bytes]] = None) -> bytes:
    if region not in REGIONS:
        raise OfficialResourceError("Khu vực chưa hỗ trợ: " + region, "REGION_UNSUPPORTED")
    if len(data) < 32 or len(data) % 16:
        raise OfficialResourceError("Metadata mã hoá có độ dài không hợp lệ.", "METADATA_FORMAT")
    plain = (decrypt or aes_cbc_decrypt)(REGIONS[region][1], data[:16], data[16:])
    n = plain[-1] if plain else 0
    if not 1 <= n <= 16 or plain[-n:] != bytes([n]) * n:
        raise OfficialResourceError("Metadata sai đệm/sai khu vực.", "METADATA_FORMAT")
    return plain[:-n]


# --------------------------------------------------------------------------- protobuf
def _varint(data: bytes, offset: int) -> tuple[int, int]:
    number = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise OfficialResourceError("Metadata bị cắt cụt.", "METADATA_FORMAT")
        value = data[offset]
        offset += 1
        number |= (value & 127) << shift
        if value < 128:
            return number, offset
    raise OfficialResourceError("Metadata varint quá lớn.", "METADATA_FORMAT")


def protobuf_fields(data: bytes) -> dict[int, list[tuple[int, object]]]:
    result: dict[int, list[tuple[int, object]]] = {}
    pos = 0
    while pos < len(data):
        tag, pos = _varint(data, pos)
        field_no, wire = tag >> 3, tag & 7
        if not field_no:
            raise OfficialResourceError("Metadata có field 0.", "METADATA_FORMAT")
        if wire == 0:
            value, pos = _varint(data, pos)
        elif wire in (1, 2, 5):
            if wire == 2:
                size, pos = _varint(data, pos)
            else:
                size = {1: 8, 5: 4}[wire]
            if pos + size > len(data):
                raise OfficialResourceError("Metadata bị cắt cụt.", "METADATA_FORMAT")
            value = data[pos:pos + size]
            pos += size
        else:
            raise OfficialResourceError("Metadata có wire type lạ.", "METADATA_FORMAT")
        result.setdefault(field_no, []).append((wire, value))
    return result


def _decode_diff(plain: bytes, root: str) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for wire, raw in protobuf_fields(plain).get(1, []):
        if wire != 2:
            raise OfficialResourceError("FileDiff sai wire.", "METADATA_FORMAT")
        f = protobuf_fields(raw)

        def one(no: int, w: int):
            a = f.get(no, [])
            if len(a) != 1 or a[0][0] != w:
                raise OfficialResourceError("FileDiff thiếu trường.", "METADATA_FORMAT")
            return a[0][1]

        name = one(1, 2).decode("utf8")
        checksum = one(2, 2).decode("ascii")
        version = one(3, 0)
        folder = one(4, 2).decode("ascii")
        if "/" in name or "\\" in name or name in (".", "..") or not re.fullmatch(r"[a-zA-Z0-9_. -]+", name):
            raise OfficialResourceError("Tên tệp trong metadata không an toàn.", "METADATA_FORMAT")
        if not re.fullmatch(r"[a-f0-9]{1,32}", checksum) or not re.fullmatch(r"[a-f0-9]{1,32}", folder):
            raise OfficialResourceError("Checksum/thư mục trong metadata không hợp lệ.", "METADATA_FORMAT")
        if name in records:
            raise OfficialResourceError("Metadata trùng tệp.", "METADATA_FORMAT")
        records[name] = {
            "name": name,
            "checksum": checksum.zfill(32),
            "version": version,
            "url": f"{root}/res/win/{version}/{folder}/" + urllib.parse.quote(name),
        }
    return records


# --------------------------------------------------------------------------- manifests
def parse_manifest(data: bytes | str) -> tuple[dict, dict, dict]:
    """Return (headers, files, patches). Raises OfficialResourceError on malformed lines."""
    text = data.decode("utf-8-sig") if isinstance(data, (bytes, bytearray)) else data
    headers: dict = {}
    files: dict = {}
    patches: dict = {}
    for line in text.splitlines():
        if not line:
            continue
        try:
            if line.startswith("$"):
                key, sep, value = line[1:].partition(":")
                if not sep:
                    raise ValueError("header")
                if key == "BIN_DIFF_PATCH_FILE":
                    p = value.split("|")
                    if len(p) < 5:
                        raise ValueError("patch")
                    patches[p[0]] = {"name": p[0], "checksum": p[1].zfill(32), "size": int(p[2]), "old_checksum": p[3].removeprefix("@").zfill(32), "kind": p[4]}
                elif key == "BIN_DIFF_PATCH_INFO":
                    headers.setdefault(key, []).append(value)
                else:
                    headers[key] = value
            else:
                p = line.split("|")
                if len(p) < 4:
                    raise ValueError("record")
                if p[0] in files:
                    raise ValueError("duplicate")
                files[p[0]] = {
                    "name": p[0],
                    "checksum": p[1].zfill(32),
                    "size": int(p[2]),
                    "tag": p[4].strip() if len(p) > 4 else "",
                }
        except ValueError as exc:
            raise OfficialResourceError(f"Manifest không hợp lệ ({exc}).", "MANIFEST_FORMAT")
    return headers, files, patches


def official_relative_path(name: str) -> str:
    """Path of a resource under Persistent_Store, matching Stella Sora's DownloadStore layout 1:1."""
    if name == "data.arcx":
        return "Tables/" + name
    if name in ("lua.arcx", "hotfix.arch"):
        return "Scripts/" + name
    if name.endswith((".srt", ".mp4", ".config")):
        return "Videos/" + name
    if name.endswith(".media.wem"):
        return "SoundBanks/Media/" + name[:-10] + ".wem"
    if name.endswith(".cn.bnk"):
        return "SoundBanks/Chinese/" + name[:-7] + ".bnk"
    if name.endswith(".en.bnk"):
        return "SoundBanks/English/" + name[:-7] + ".bnk"
    if name.endswith(".jp.bnk"):
        return "SoundBanks/Japanese/" + name[:-7] + ".bnk"
    if name.endswith((".bnk", ".wem")):
        return "SoundBanks/" + name
    return "AssetBundles/" + name


def manifest_name_from_relative(rel: str) -> Optional[str]:
    """Inverse of official_relative_path(): map Persistent_Store/<subpath> back to its manifest key."""
    if not isinstance(rel, str) or not rel:
        return None
    norm = rel.replace("\\", "/").lstrip("/")
    if norm.startswith("Persistent_Store/"):
        sub = norm[len("Persistent_Store/"):]
    else:
        sub = norm
    if not sub or "/" not in sub or ".." in sub.split("/"):
        return None
    if sub == "Tables/data.arcx":
        return "data.arcx"
    if sub in ("Scripts/lua.arcx", "Scripts/hotfix.arch"):
        return sub.split("/", 1)[1]
    if sub.startswith("Videos/"):
        fname = sub[len("Videos/"):]
        if "/" not in fname and fname.endswith((".srt", ".mp4", ".config")):
            return fname
        return None
    if sub.startswith("AssetBundles/"):
        fname = sub[len("AssetBundles/"):]
        if "/" not in fname and fname.endswith(".unity3d"):
            return fname
        return None
    if sub.startswith("SoundBanks/"):
        rest = sub[len("SoundBanks/"):]
        if "/" not in rest:
            return rest if rest.endswith((".bnk", ".wem")) else None
        folder, fname = rest.split("/", 1)
        if "/" in fname:
            return None
        if folder == "Media" and fname.endswith(".wem"):
            return fname[:-4] + ".media.wem"
        if folder == "Chinese" and fname.endswith(".bnk"):
            return fname[:-4] + ".cn.bnk"
        if folder == "English" and fname.endswith(".bnk"):
            return fname[:-4] + ".en.bnk"
        if folder == "Japanese" and fname.endswith(".bnk"):
            return fname[:-4] + ".jp.bnk"
        return None
    return None


def md5_file(path: str | Path, block: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(block), b""):
            h.update(b)
    return h.hexdigest()


# --------------------------------------------------------------------------- catalog
@dataclass
class OfficialCatalog:
    region: str
    root: str
    client_version: str
    game_version: str
    resource_version: str
    server_data_version: int
    manifest_sha256: str
    final_files: dict            # name -> {checksum,size}  (latest official state)
    diff: dict                   # name -> {checksum,version,url}
    versions: dict               # (name, checksum) -> {checksum,size}
    patch_index: dict            # (name, checksum_of_new_file) -> patch record
    evidence: list = field(default_factory=list)
    base_res_version: str = ""
    base_files: dict = field(default_factory=dict)
    patch_steps: list = field(default_factory=list)  # [{step, res_ver, targets: set[str]}]

    def knows(self, name: str, checksum: str) -> bool:
        return (name, checksum) in self.versions

    def step_for_resource_version(self, local_res_version: Optional[str]) -> Optional[int]:
        """Return exact BinDiff patch step number for `local_res_version` (0 = base), or None if unknown."""
        local_res = str(local_res_version or "").strip()
        if not local_res:
            return None
        if local_res == self.base_res_version:
            return 0
        for st in self.patch_steps:
            if str(st.get("res_ver") or "").strip() == local_res:
                return int(st.get("step", 0))
        return None

    def pending_patch_names(self, local_res_version: Optional[str]) -> set[str]:
        """Return every filename touched by CDN BinDiff patches newer than `local_res_version`."""
        if not self.patch_steps:
            return set()
        local_res = str(local_res_version or "").strip()
        if local_res and local_res == self.resource_version:
            return set()
        if local_res.isdigit() and str(self.resource_version or "").isdigit():
            if int(local_res) >= int(self.resource_version):
                return set()
        exact = self.step_for_resource_version(local_res)
        if exact is not None:
            local_step = exact
        else:
            local_step = 0
            if local_res.isdigit():
                lr_int = int(local_res)
                for st in self.patch_steps:
                    rv = str(st.get("res_ver") or "").strip()
                    if rv.isdigit() and int(rv) <= lr_int:
                        local_step = max(local_step, int(st.get("step", 0)))
        out: set[str] = set()
        for st in self.patch_steps:
            if int(st.get("step", 0)) > local_step:
                out.update(st.get("targets") or ())
        return out

    def resolve(self, name: str, checksum: str, trail: tuple = ()) -> dict:
        """Return a plan item: {'path','size','algorithm','checksum','url'} or with base/patch chain."""
        key = (name, checksum)
        if key in trail:
            raise OfficialResourceError("Chuỗi bản vá tuần hoàn.", "RESOLVE_FAILED")
        if len(trail) > 64:
            raise OfficialResourceError("Chuỗi bản vá quá sâu.", "RESOLVE_FAILED")
        record = self.versions.get(key)
        if record is None:
            raise OfficialResourceError(f"Máy chủ chính thức không có bản {name} ({checksum}).", "NOT_FOUND")
        out = {"path": official_relative_path(name), "size": record["size"], "algorithm": "md5", "checksum": checksum}
        current = self.diff.get(name)
        if current and current["checksum"] == checksum:
            out["url"] = current["url"]
            return out
        patch = self.patch_index.get(key)
        if patch is None:
            raise OfficialResourceError(f"Không dựng được {name} ({checksum}) từ máy chủ.", "RESOLVE_FAILED")
        remote = self.diff.get(patch["name"])
        if remote is None or remote["checksum"] != patch["checksum"]:
            raise OfficialResourceError("Metadata bản vá không khớp.", "RESOLVE_FAILED")
        if patch["kind"] == "N":
            if remote["checksum"] != checksum:
                raise OfficialResourceError("Tệp mới không khớp manifest.", "RESOLVE_FAILED")
            out["url"] = remote["url"]
            return out
        if patch["kind"] != "U":
            raise OfficialResourceError("Kiểu bản vá chưa hỗ trợ: " + str(patch["kind"]), "RESOLVE_FAILED")
        out["base"] = self.resolve(name, patch["old_checksum"], trail + (key,))
        out["patch"] = {"path": patch["name"], "size": patch["size"], "algorithm": "md5", "checksum": patch["checksum"], "url": remote["url"]}
        out["url"] = remote["url"]
        return out


Opener = Callable[..., object]


class OfficialClient:
    """Small HTTP + metadata client; `opener` and `decrypt` are injectable for tests."""

    def __init__(self, region: str = "EN", opener: Optional[Opener] = None, decrypt=None, timeout: float = 30.0, retries: int = 3, sleep=time.sleep):
        if region not in REGIONS:
            raise OfficialResourceError("Khu vực chưa hỗ trợ: " + region, "REGION_UNSUPPORTED")
        self.region = region
        self.root = REGIONS[region][0]
        if opener is None:
            _ensure_tls()
            self.opener = urllib.request.urlopen
        else:
            self.opener = opener
        self.decrypt = decrypt
        self.timeout = timeout
        self.retries = max(1, retries)
        self._sleep = sleep

    # -- network ------------------------------------------------------------------
    def check_url(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not (url == self.root or url.startswith(self.root + "/")):
            raise OfficialResourceError("URL không thuộc máy chủ chính thức: " + url, "UNTRUSTED_URL")

    def request(self, url: str, headers: Optional[dict] = None):
        self.check_url(url)
        h = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity", "Cache-Control": "no-cache"}
        h.update(headers or {})
        return self.opener(urllib.request.Request(url, headers=h), timeout=self.timeout)

    def read(self, url: str, cap: int = MAX_META_BYTES) -> bytes:
        # Publisher metadata endpoints (/meta/win.html, /meta/serverlist.html) end with .html
        # so the CDN legitimately sends Content-Type: text/html for AES-CBC binary payloads.
        # For those URLs, detect captive portals by inspecting the actual response body.
        allow_html_ct = _url_has_html_suffix(url)
        last: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                with self.request(url) as response:
                    resp_headers = getattr(response, "headers", None)
                    is_html_ct = _is_html_content_type(resp_headers)
                    if is_html_ct and not allow_html_ct:
                        raise OfficialResourceError(
                            "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì dữ liệu từ máy chủ chính thức.",
                            "NET_CAPTIVE",
                        )
                    data = response.read(cap + 1)
                if _is_html_body(data) or (is_html_ct and _looks_like_html_markup(data)):
                    raise OfficialResourceError(
                        "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì dữ liệu từ máy chủ chính thức.",
                        "NET_CAPTIVE",
                    )
                if len(data) > cap:
                    raise OfficialResourceError("Phản hồi vượt giới hạn kích thước.", "METADATA_FORMAT")
                return data
            except OfficialResourceError:
                raise
            except (OSError, http.client.HTTPException) as exc:  # URLError/HTTPError/timeout/IncompleteRead
                last = exc
                if attempt + 1 < self.retries:
                    self._sleep(min(4, 1 + attempt))
        raise OfficialResourceError("Không kết nối được máy chủ tài nguyên chính thức: " + str(last), "NETWORK")

    # -- metadata -----------------------------------------------------------------
    def server_data_version(self) -> int:
        token = str(time.time_ns())
        plain = decrypt_metadata(self.read(f"{self.root}/meta/serverlist.html?nocache={token}"), self.region, self.decrypt)
        version = protobuf_fields(plain).get(1)
        if not version or len(version) != 1 or version[0][0] != 0:
            raise OfficialResourceError("Serverlist thiếu phiên bản dữ liệu.", "METADATA_FORMAT")
        return int(version[0][1])

    def fetch_catalog(self) -> OfficialCatalog:
        root = self.root
        token = str(time.time_ns())
        encrypted = self.read(f"{root}/meta/win.html?nocache={token}")
        plain = decrypt_metadata(encrypted, self.region, self.decrypt)
        diff = _decode_diff(plain, root)
        if not diff:
            raise OfficialResourceError("Metadata trống.", "METADATA_FORMAT")
        server_version = self.server_data_version()
        if max(x["version"] for x in diff.values()) != server_version:
            raise OfficialResourceError("Serverlist và metadata tài nguyên chưa đồng bộ; hãy thử lại sau ít phút.", "METADATA_INCONSISTENT")

        def manifest(name: str):
            item = diff.get(name)
            if item is None:
                raise OfficialResourceError("Thiếu manifest " + name, "MANIFEST_FORMAT")
            data = self.read(item["url"])
            if hashlib.md5(data).hexdigest() != item["checksum"]:
                raise OfficialResourceError("Manifest sai MD5: " + name, "HASH_MISMATCH")
            return name, data, parse_manifest(data)

        base = manifest("ss_win.mani")
        count = int(base[2][0].get("BIN_DIFF_PATCH_VER", "0"))
        names = (["ss_win_add.mani"] if "ss_win_add.mani" in diff else []) + [f"p_{i}_m.ss_win.mani" for i in range(1, count + 1)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            extra = list(pool.map(manifest, names))
        everything = [base] + extra
        final = next((m for m in extra if m[0] == f"p_{count}_m.ss_win.mani"), base)
        base_files = dict(base[2][1])
        if "ss_win_add.mani" in names:
            base_files.update(next(m for m in extra if m[0] == "ss_win_add.mani")[2][1])
        final_files = dict(base_files)
        final_files.update(final[2][1])

        versions: dict = {}
        patch_index: dict = {}
        patch_steps: list[dict] = []
        for mname, _data, (mhead, files, patches) in everything:
            for record in files.values():
                versions[(record["name"], record["checksum"])] = record
            step_targets: set[str] = set()
            for patch_name, patch in patches.items():
                match = re.fullmatch(r"p_\d+_[un]\.(.+)", patch_name)
                if not match or match[1] not in files:
                    raise OfficialResourceError("Bản vá không có tệp đích: " + patch_name, "MANIFEST_FORMAT")
                patch_index[(match[1], files[match[1]]["checksum"])] = patch
                step_targets.add(match[1])
            step_match = re.fullmatch(r"p_(\d+)_m\.ss_win\.mani", mname)
            if step_match:
                patch_steps.append({
                    "step": int(step_match.group(1)),
                    "res_ver": str(mhead.get("RES_VER") or "").strip(),
                    "targets": step_targets,
                })
        patch_steps.sort(key=lambda x: x["step"])
        head = final[2][0]
        if not all(head.get(x) for x in ("CLIENT_VER", "GAME_VER", "RES_VER")):
            raise OfficialResourceError("Manifest cuối thiếu phiên bản.", "MANIFEST_FORMAT")
        if count:
            info = next((s.split("|") for s in base[2][0].get("BIN_DIFF_PATCH_INFO", []) if s.split("|")[0] == str(count)), None)
            if not info or head.get("RES_VER") != info[1]:
                raise OfficialResourceError("Phiên bản bản vá cuối không khớp.", "MANIFEST_FORMAT")
        # Refuse a snapshot that moved while it was being read.
        if self.server_data_version() != server_version:
            raise OfficialResourceError("Máy chủ vừa cập nhật trong lúc đọc; hãy thử lại.", "METADATA_INCONSISTENT")
        return OfficialCatalog(
            region=self.region,
            root=root,
            client_version=head["CLIENT_VER"],
            game_version=head["GAME_VER"],
            resource_version=head["RES_VER"],
            server_data_version=server_version,
            manifest_sha256=hashlib.sha256(final[1]).hexdigest(),
            final_files=final_files,
            diff=diff,
            versions=versions,
            patch_index=patch_index,
            base_res_version=str(base[2][0].get("RES_VER") or "").strip(),
            base_files=base_files,
            patch_steps=patch_steps,
        )


# --------------------------------------------------------------------------- download
ProgressCb = Callable[[int, int, str], None]


class CancelledError(OfficialResourceError):
    pass


class _PoolAborted(Exception):
    pass


class _InflightNode:
    def __init__(self) -> None:
        self.event = threading.Event()
        self.path: Optional[Path] = None
        self.error: Optional[BaseException] = None


class OfficialDownloader:
    """Resumable, hash-checked parallel download + DAG-safe delta reconstruction into a content-addressed cache.

    cache layout:  <cache>/inputs/<md5>.base|.delta   intermediate downloads
                   <cache>/final/<md5>.bin            verified full official files
    Nothing here touches the game folder.
    """

    def __init__(
        self,
        client: OfficialClient,
        cache_dir: str | Path,
        progress: Optional[ProgressCb] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
        max_workers: int = 4,
        cancel_event: Optional[threading.Event] = None,
        event_cb: Optional[Callable[[OperationEvent], None]] = None,
        operation_id: str = "official_download",
    ):
        self.client = client
        self.cache = Path(cache_dir)
        self.inputs = self.cache / "inputs"
        self.final = self.cache / "final"
        for d in (self.inputs, self.final):
            d.mkdir(parents=True, exist_ok=True)
        self.progress = progress
        self.should_cancel = should_cancel
        self.max_workers = max(1, int(max_workers))
        self.cancel_event = cancel_event
        self.event_cb = event_cb
        self.operation_id = operation_id
        self.total_bytes = 0
        self.done_bytes = 0
        self.downloaded_bytes = 0
        self.files_total = 0
        self.files_completed = 0

        self._progress_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._dag_lock = threading.Lock()
        self._internal_abort = threading.Event()
        self._transfer_locks: dict[Path, threading.Lock] = {}
        self._inflight_nodes: dict[str, _InflightNode] = {}
        self._failed_nodes: Optional[dict[str, BaseException]] = None
        self._samples: collections.deque[tuple[float, int]] = collections.deque()
        self._transfer_start_ts: float = time.monotonic()
        self._last_ewma_ts: Optional[float] = None
        self._ewma_speed: float = 0.0
        self._last_emit_ts: float = 0.0
        self._emitted_once: bool = False

    def _is_cancelled(self) -> bool:
        return bool((self.cancel_event is not None and self.cancel_event.is_set()) or (self.should_cancel is not None and self.should_cancel()))

    def _should_abort(self) -> bool:
        return self._is_cancelled() or self._internal_abort.is_set()

    def _lock_for(self, destination: Path) -> threading.Lock:
        resolved = destination.resolve()
        with self._state_lock:
            lock = self._transfer_locks.get(resolved)
            if lock is None:
                lock = threading.Lock()
                self._transfer_locks[resolved] = lock
            return lock

    # -- planning -------------------------------------------------------------------
    def final_path(self, item: dict) -> Path:
        return self.final / (item["checksum"] + ".bin")

    def _cached_ok(self, path: Path, item: dict) -> bool:
        try:
            return path.is_file() and path.stat().st_size == item["size"] and md5_file(path) == item["checksum"]
        except OSError:
            return False

    def estimate_download(self, items: list[dict]) -> int:
        """Bytes that still have to be downloaded (reusing verified cache)."""
        seen: set = set()
        total = 0

        def walk(item: dict):
            nonlocal total
            key = (item["checksum"], item["size"], "patch" in item)
            if key in seen:
                return
            seen.add(key)
            if "patch" in item:
                if self._cached_ok(self.final_path(item), item):
                    return
                walk(item["base"])
                d = self.inputs / (item["patch"]["checksum"] + ".delta")
                if not self._cached_ok(d, item["patch"]):
                    total += item["patch"]["size"]
            else:
                if not self._cached_ok(self.final_path(item), item):
                    total += item["size"]

        for item in items:
            walk(item)
        return total

    def _compute_speed_eta_locked(self, now: float) -> tuple[float, Optional[float]]:
        cutoff = now - 2.5
        while self._samples and self._samples[0][0] <= cutoff:
            self._samples.popleft()
        window_bytes = sum(b for _, b in self._samples)
        if window_bytes <= 0:
            inst_speed = 0.0
        else:
            window_start = max(self._transfer_start_ts, cutoff)
            dt_window = max(now - window_start, 0.05)
            inst_speed = window_bytes / dt_window
        if self._last_ewma_ts is None:
            self._ewma_speed = inst_speed
            self._last_ewma_ts = now
        else:
            dt_step = now - self._last_ewma_ts
            if dt_step > 0:
                alpha = 1.0 - math.exp(-dt_step / 1.0)
                self._ewma_speed = alpha * inst_speed + (1.0 - alpha) * self._ewma_speed
                self._last_ewma_ts = now
        speed_bps = self._ewma_speed if self._ewma_speed >= 1.0 else 0.0
        remaining = max(0, self.total_bytes - self.done_bytes)
        eta_seconds = (remaining / speed_bps) if speed_bps > 1024.0 else None
        return speed_bps, eta_seconds

    def _emit_telemetry(self, label: str, force: bool = False) -> None:
        progress_args: Optional[tuple[int, int, str]] = None
        event_obj: Optional[OperationEvent] = None
        with self._progress_lock:
            now = time.monotonic()
            speed_bps, eta_seconds = self._compute_speed_eta_locked(now)
            should_emit = force or not self._emitted_once or (now - self._last_emit_ts >= 0.1)
            if should_emit:
                self._last_emit_ts = now
                self._emitted_once = True
                done = self.done_bytes
                total = self.total_bytes
                if self.progress:
                    progress_args = (done, total, label)
                if self.event_cb:
                    msg = f"Đang tải bản gốc: {label} ({done / 1048576:.1f}/{max(total, 1) / 1048576:.1f} MB)"
                    event_obj = OperationEvent(
                        self.operation_id,
                        OperationPhase.DOWNLOAD,
                        msg,
                        done,
                        max(total, 1),
                        "bytes",
                        speed_bps=speed_bps,
                        eta_seconds=eta_seconds,
                        files_completed=self.files_completed,
                        files_total=self.files_total,
                    )
        if progress_args is not None and self.progress:
            self.progress(*progress_args)
        if event_obj is not None and self.event_cb:
            self.event_cb(event_obj)

    def _tick(self, n: int, label: str, force: bool = False):
        if self._is_cancelled():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
        if self._internal_abort.is_set():
            raise _PoolAborted()
        with self._progress_lock:
            now = time.monotonic()
            if n > 0:
                self._samples.append((now, n))
            self.done_bytes += n
            self.downloaded_bytes += n
        self._emit_telemetry(label, force=force)
        if self._is_cancelled():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
        if self._internal_abort.is_set():
            raise _PoolAborted()

    def _mark_item_completed(self, label: str) -> None:
        with self._progress_lock:
            self.files_completed += 1
        self._emit_telemetry(label, force=True)

    # -- transfer -------------------------------------------------------------------
    def _transfer(self, item: dict, destination: Path, label: str) -> None:
        size = int(item["size"])
        if size < 0 or size > MAX_FILE_BYTES:
            raise OfficialResourceError("Kích thước tệp trong manifest không hợp lệ.", "MANIFEST_FORMAT")
        dest_lock = self._lock_for(destination)
        with dest_lock:
            if destination.exists():
                if self._cached_ok(destination, item):
                    return
                destination.unlink()
            destination.parent.mkdir(parents=True, exist_ok=True)
            part = destination.with_name(destination.name + ".part")
            if part.is_symlink():
                raise OfficialResourceError("Từ chối tệp tạm là symlink.", "UNSAFE_PATH")
            last: Optional[Exception] = None
            for attempt in range(self.client.retries):
                if self._is_cancelled():
                    raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                if self._internal_abort.is_set():
                    raise _PoolAborted()
                try:
                    offset = part.stat().st_size if part.exists() else 0
                    if offset > size:
                        part.unlink()
                        offset = 0
                    if size == 0 or not part.exists() or offset != size:
                        headers = {"Range": f"bytes={offset}-"} if offset else {}
                        with self.client.request(item["url"], headers) as response:
                            status = getattr(response, "status", 200)
                            resp_headers = getattr(response, "headers", None)
                            if status in (200, 206) and _is_html_content_type(resp_headers):
                                raise OfficialResourceError(
                                    "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì tài nguyên chính thức.",
                                    "NET_CAPTIVE",
                                )
                            if offset and status == 206:
                                cr = _header_value(resp_headers, "Content-Range")
                                m = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", cr)
                                if not m:
                                    part.unlink(missing_ok=True)
                                    raise OfficialResourceError("Content-Range bất thường.", "NETWORK")
                                start, end, total = map(int, m.groups())
                                cl = _header_value(resp_headers, "Content-Length") or None
                                if (
                                    start != offset
                                    or total != size
                                    or not 0 <= start <= end < size
                                    or (cl is not None and (not re.fullmatch(r"\d+", cl) or int(cl) != end - start + 1))
                                ):
                                    part.unlink(missing_ok=True)
                                    raise OfficialResourceError("Content-Range bất thường.", "NETWORK")
                            elif status == 200:
                                cl = _header_value(resp_headers, "Content-Length") or None
                                if cl is not None and (not re.fullmatch(r"\d+", cl) or int(cl) != size):
                                    probe = response.read(512)
                                    if probe and _is_html_body(probe):
                                        raise OfficialResourceError(
                                            "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì tài nguyên chính thức.",
                                            "NET_CAPTIVE",
                                        )
                                    raise OfficialResourceError(
                                        f"Kích thước từ máy chủ không khớp manifest ({cl}/{size}).",
                                        "SIZE_MISMATCH",
                                    )
                                offset = 0
                            else:
                                raise OfficialResourceError(f"Máy chủ trả mã {status}.", "NETWORK")

                            first_block = response.read(1024 * 1024)
                            if first_block and _is_html_body(first_block):
                                raise OfficialResourceError(
                                    "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì tài nguyên chính thức.",
                                    "NET_CAPTIVE",
                                )
                            if self._is_cancelled():
                                raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                            if self._internal_abort.is_set():
                                raise _PoolAborted()

                            count = offset
                            with open(part, "ab" if offset else "wb") as stream:
                                try:
                                    block = first_block
                                    while block:
                                        if self._is_cancelled():
                                            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                                        if self._internal_abort.is_set():
                                            raise _PoolAborted()
                                        count += len(block)
                                        if count > size:
                                            raise OfficialResourceError("Tải vượt kích thước manifest.", "HASH_MISMATCH")
                                        stream.write(block)
                                        self._tick(len(block), label)
                                        block = response.read(1024 * 1024)
                                finally:
                                    stream.flush()
                                    os.fsync(stream.fileno())
                    if self._is_cancelled():
                        raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                    if self._internal_abort.is_set():
                        raise _PoolAborted()
                    if part.stat().st_size != size or md5_file(part) != item["checksum"]:
                        part.unlink(missing_ok=True)
                        raise OfficialResourceError(f"Sai mã MD5/kích thước sau khi tải: {label}", "HASH_MISMATCH")
                    os.replace(part, destination)
                    return
                except (CancelledError, _PoolAborted):
                    raise
                except OfficialResourceError as exc:
                    if exc.code in ("NET_CAPTIVE", "SIZE_MISMATCH", "UNSAFE_PATH", "MANIFEST_FORMAT"):
                        raise
                    if exc.code in ("HASH_MISMATCH", "NETWORK"):
                        if exc.code == "HASH_MISMATCH":
                            part.unlink(missing_ok=True)
                        last = exc
                    else:
                        raise
                except (OSError, http.client.HTTPException) as exc:
                    if getattr(exc, "code", None) == 416:
                        part.unlink(missing_ok=True)
                    last = exc
                if self._is_cancelled():
                    raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                if self._internal_abort.is_set():
                    raise _PoolAborted()
                if attempt + 1 < self.client.retries:
                    delay = min(4, 1 + attempt)
                    if self.cancel_event is not None and self.client._sleep is time.sleep:
                        self.cancel_event.wait(delay)
                    else:
                        self.client._sleep(delay)
            if isinstance(last, OfficialResourceError):
                raise last
            raise OfficialResourceError(f"Không tải được {label}: {last}", "NETWORK")

    def materialize(
        self,
        item: dict,
        label: Optional[str] = None,
        depth: int = 0,
        *,
        _pinned_roots: Optional[set[str]] = None,
        _pending_dependents: Optional[dict[str, int]] = None,
        _trail: frozenset[str] = frozenset(),
    ) -> Path:
        """Return the cached path of the verified full file described by `item`."""
        if depth > 64:
            raise OfficialResourceError("Chuỗi bản vá quá sâu.", "RESOLVE_FAILED")
        cs = item["checksum"]
        if cs in _trail:
            raise OfficialResourceError("Chuỗi bản vá tuần hoàn.", "RESOLVE_FAILED")
        if self._is_cancelled():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
        if self._internal_abort.is_set():
            raise _PoolAborted()

        label = label or Path(item["path"]).name
        pinned = _pinned_roots if _pinned_roots is not None else {cs}
        dependents = _pending_dependents if _pending_dependents is not None else {}

        # Single-flight coordination by checksum
        failed_exc: Optional[BaseException] = None
        leader = False
        with self._state_lock:
            if self._failed_nodes is not None and cs in self._failed_nodes:
                failed_exc = self._failed_nodes[cs]
            else:
                node = self._inflight_nodes.get(cs)
                if node is None:
                    node = _InflightNode()
                    self._inflight_nodes[cs] = node
                    leader = True

        if failed_exc is not None:
            if self._is_cancelled():
                raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
            if self._internal_abort.is_set():
                raise _PoolAborted()
            raise failed_exc

        if not leader:
            while not node.event.wait(0.1):
                if self._is_cancelled():
                    raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
                if self._internal_abort.is_set():
                    raise _PoolAborted()
            if node.error is not None:
                raise node.error
            assert node.path is not None
            return node.path

        try:
            target = self.final_path(item)
            if self._cached_ok(target, item):
                node.path = target
                return target
            if "patch" not in item:
                self._transfer(item, target, label)
                node.path = target
                return target

            base_item = item["base"]
            base_cs = base_item["checksum"]
            base_path = self.materialize(
                base_item,
                label,
                depth + 1,
                _pinned_roots=pinned,
                _pending_dependents=dependents,
                _trail=_trail | {cs},
            )
            delta = self.inputs / (item["patch"]["checksum"] + ".delta")
            self._transfer(item["patch"], delta, label + " (bản vá)")
            tmp = target.with_name(f".rebuild_{uuid.uuid4().hex}")
            rebuild_ok = False
            try:
                try:
                    apply_bsdiff(base_path, delta, tmp, item["size"])
                except (BsdiffError, OSError) as exc:
                    raise OfficialResourceError(f"Không dựng được {label} từ bản vá: {exc}", "PATCH_FAILED") from exc
                if tmp.stat().st_size != item["size"] or md5_file(tmp) != item["checksum"]:
                    raise OfficialResourceError(f"Bản dựng lại của {label} sai MD5/kích thước.", "HASH_MISMATCH")
                os.replace(tmp, target)
                rebuild_ok = True
            finally:
                tmp.unlink(missing_ok=True)
                with self._dag_lock:
                    if base_cs in dependents:
                        dependents[base_cs] = max(0, dependents[base_cs] - 1)
                    rem = dependents.get(base_cs, 0)
                    if rebuild_ok and rem <= 0 and base_cs not in pinned and base_path != target:
                        base_path.unlink(missing_ok=True)
            node.path = target
            return target
        except BaseException as exc:
            node.error = exc
            raise
        finally:
            with self._state_lock:
                if node.error is not None and self._failed_nodes is not None and not isinstance(node.error, _PoolAborted):
                    self._failed_nodes.setdefault(cs, node.error)
                if self._inflight_nodes.get(cs) is node:
                    self._inflight_nodes.pop(cs, None)
            node.event.set()

    def prepare(self, items: list[dict]) -> dict[str, Path]:
        """Materialise every item in parallel; returns {checksum: cached path}. Raises before touching any game file."""
        if self._is_cancelled():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
        self._internal_abort.clear()

        unique_items: list[dict] = []
        seen_top: dict[str, dict] = {}
        for item in items:
            cs = item["checksum"]
            existing = seen_top.get(cs)
            if existing is not None:
                if existing["size"] != item["size"]:
                    raise OfficialResourceError("Manifest chứa hai mục trùng checksum nhưng khác kích thước.", "MANIFEST_FORMAT")
                continue
            seen_top[cs] = item
            unique_items.append(item)

        pinned_roots: set[str] = set(seen_top.keys())
        pending_dependents: dict[str, int] = {}
        seen_dag: set[tuple[str, int, bool]] = set()

        def _count_dag(node_item: dict) -> None:
            key = (node_item["checksum"], node_item["size"], "patch" in node_item)
            if key in seen_dag:
                return
            seen_dag.add(key)
            if "patch" in node_item:
                if self._cached_ok(self.final_path(node_item), node_item):
                    return
                base_item = node_item["base"]
                pending_dependents[base_item["checksum"]] = pending_dependents.get(base_item["checksum"], 0) + 1
                _count_dag(base_item)

        for it in unique_items:
            _count_dag(it)

        with self._progress_lock:
            self.total_bytes = self.estimate_download(unique_items)
            self.done_bytes = 0
            self.downloaded_bytes = 0
            self.files_total = len(unique_items)
            self.files_completed = 0
            self._samples.clear()
            self._transfer_start_ts = time.monotonic()
            self._last_ewma_ts = None
            self._ewma_speed = 0.0
            self._last_emit_ts = 0.0
            self._emitted_once = False

        if not unique_items:
            return {}

        pool_workers = min(self.max_workers, max(1, len(unique_items)))
        out: dict[str, Path] = {}
        out_lock = threading.Lock()
        errors: list[BaseException] = []
        cancelled = False

        def _worker(it: dict) -> tuple[str, Path]:
            lbl = Path(it["path"]).name
            path = self.materialize(
                it,
                label=lbl,
                _pinned_roots=pinned_roots,
                _pending_dependents=pending_dependents,
            )
            self._mark_item_completed(lbl)
            return it["checksum"], path

        with self._state_lock:
            self._failed_nodes = {}
        try:
            with ThreadPoolExecutor(max_workers=pool_workers) as pool:
                futures = [pool.submit(_worker, it) for it in unique_items]
                for fut in as_completed(futures):
                    try:
                        cs, p = fut.result()
                        with out_lock:
                            out[cs] = p
                    except (_PoolAborted, FuturesCancelledError):
                        pass
                    except BaseException as exc:
                        if isinstance(exc, CancelledError) or self._is_cancelled():
                            cancelled = True
                        else:
                            errors.append(exc)
                        self._internal_abort.set()
                        for other in futures:
                            other.cancel()
        finally:
            with self._state_lock:
                self._failed_nodes = None
                self._internal_abort.clear()

        if cancelled or self._is_cancelled():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")
        if errors:
            distinct_errors: list[BaseException] = []
            seen_err_ids: set[int] = set()
            for err in errors:
                eid = id(err)
                if eid not in seen_err_ids:
                    seen_err_ids.add(eid)
                    distinct_errors.append(err)
            if len(distinct_errors) == 1 and isinstance(distinct_errors[0], OfficialResourceError):
                raise distinct_errors[0]
            if all(isinstance(e, OfficialResourceError) and e.code == "NET_CAPTIVE" for e in distinct_errors):
                raise distinct_errors[0]
            raise OfficialResourceError(
                f"Tải song song thất bại ({len(distinct_errors)} lỗi): {distinct_errors[0]}",
                "PARALLEL_DL",
            ) from distinct_errors[0]

        self._emit_telemetry("Hoàn tất tải tài nguyên gốc.", force=True)
        return out

    def cleanup(self) -> None:
        import shutil

        for d in (self.inputs, self.final):
            shutil.rmtree(d, ignore_errors=True)
