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

import hashlib
import os
import re
import time
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .bsdiff40 import BsdiffError, apply_bsdiff
from .safety import InstallerError

REGIONS = {
    "EN": ("https://nova-static.stellasora.global", b"ma5Dn2FhC*Xhxy%c"),
}
USER_AGENT = "StellaSoraVietHoaLauncher/1.3 (official-text-restore)"
MAX_META_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
TEXT_ARCHIVES = ("data.arcx", "lua.arcx")


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
                files[p[0]] = {"name": p[0], "checksum": p[1].zfill(32), "size": int(p[2])}
        except ValueError as exc:
            raise OfficialResourceError(f"Manifest không hợp lệ ({exc}).", "MANIFEST_FORMAT")
    return headers, files, patches


def official_relative_path(name: str) -> str:
    """Path of a resource under Persistent_Store, as the game itself lays it out."""
    if name == "data.arcx":
        return "Tables/" + name
    if name == "lua.arcx":
        return "Scripts/" + name
    if name.endswith(".srt"):
        return "Videos/" + name
    return "AssetBundles/" + name


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

    def knows(self, name: str, checksum: str) -> bool:
        return (name, checksum) in self.versions

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
        self.opener = opener or urllib.request.urlopen
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
        last: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                with self.request(url) as response:
                    data = response.read(cap + 1)
                if len(data) > cap:
                    raise OfficialResourceError("Phản hồi vượt giới hạn kích thước.", "METADATA_FORMAT")
                return data
            except OfficialResourceError:
                raise
            except OSError as exc:  # URLError/HTTPError/timeout are OSError subclasses
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
        final_files = dict(base[2][1])
        if "ss_win_add.mani" in names:
            final_files.update(next(m for m in extra if m[0] == "ss_win_add.mani")[2][1])
        final_files.update(final[2][1])

        versions: dict = {}
        patch_index: dict = {}
        for _name, _data, (_head, files, patches) in everything:
            for record in files.values():
                versions[(record["name"], record["checksum"])] = record
            for patch_name, patch in patches.items():
                match = re.fullmatch(r"p_\d+_[un]\.(.+)", patch_name)
                if not match or match[1] not in files:
                    raise OfficialResourceError("Bản vá không có tệp đích: " + patch_name, "MANIFEST_FORMAT")
                patch_index[(match[1], files[match[1]]["checksum"])] = patch
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
        )


# --------------------------------------------------------------------------- download
ProgressCb = Callable[[int, int, str], None]


class CancelledError(OfficialResourceError):
    pass


class OfficialDownloader:
    """Resumable, hash-checked download + delta reconstruction into a content-addressed cache.

    cache layout:  <cache>/inputs/<md5>.base|.delta   intermediate downloads
                   <cache>/final/<md5>.bin            verified full official files
    Nothing here touches the game folder.
    """

    def __init__(self, client: OfficialClient, cache_dir: str | Path, progress: Optional[ProgressCb] = None, should_cancel: Optional[Callable[[], bool]] = None):
        self.client = client
        self.cache = Path(cache_dir)
        self.inputs = self.cache / "inputs"
        self.final = self.cache / "final"
        for d in (self.inputs, self.final):
            d.mkdir(parents=True, exist_ok=True)
        self.progress = progress
        self.should_cancel = should_cancel
        self.total_bytes = 0
        self.done_bytes = 0
        self.downloaded_bytes = 0

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

    def _tick(self, n: int, label: str):
        self.done_bytes += n
        self.downloaded_bytes += n
        if self.progress:
            self.progress(self.done_bytes, self.total_bytes, label)
        if self.should_cancel and self.should_cancel():
            raise CancelledError("Đã huỷ tải tài nguyên.", "CANCELLED")

    # -- transfer -------------------------------------------------------------------
    def _transfer(self, item: dict, destination: Path, label: str) -> None:
        size = int(item["size"])
        if size < 0 or size > MAX_FILE_BYTES:
            raise OfficialResourceError("Kích thước tệp trong manifest không hợp lệ.", "MANIFEST_FORMAT")
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
            try:
                offset = part.stat().st_size if part.exists() else 0
                if offset > size:
                    part.unlink()
                    offset = 0
                if offset != size:
                    headers = {"Range": f"bytes={offset}-"} if offset else {}
                    with self.client.request(item["url"], headers) as response:
                        status = getattr(response, "status", 200)
                        if offset and status == 206:
                            if response.headers.get("Content-Range", "") != f"bytes {offset}-{size - 1}/{size}":
                                raise OfficialResourceError("Content-Range bất thường.", "NETWORK")
                        elif status == 200:
                            offset = 0
                        else:
                            raise OfficialResourceError(f"Máy chủ trả mã {status}.", "NETWORK")
                        count = offset
                        with open(part, "ab" if offset else "wb") as stream:
                            for block in iter(lambda: response.read(1024 * 1024), b""):
                                count += len(block)
                                if count > size:
                                    raise OfficialResourceError("Tải vượt kích thước manifest.", "HASH_MISMATCH")
                                stream.write(block)
                                self._tick(len(block), label)
                if part.stat().st_size != size or md5_file(part) != item["checksum"]:
                    part.unlink(missing_ok=True)
                    raise OfficialResourceError(f"Sai mã MD5/kích thước sau khi tải: {label}", "HASH_MISMATCH")
                os.replace(part, destination)
                return
            except CancelledError:
                raise
            except OfficialResourceError as exc:
                if exc.code == "HASH_MISMATCH":
                    last = exc
                elif exc.code == "NETWORK":
                    last = exc
                else:
                    raise
            except OSError as exc:
                last = exc
            if attempt + 1 < self.client.retries:
                self.client._sleep(min(4, 1 + attempt))
        if isinstance(last, OfficialResourceError):
            raise last
        raise OfficialResourceError(f"Không tải được {label}: {last}", "NETWORK")

    def materialize(self, item: dict, label: Optional[str] = None, depth: int = 0) -> Path:
        """Return the cached path of the verified full file described by `item`."""
        if depth > 64:
            raise OfficialResourceError("Chuỗi bản vá quá sâu.", "RESOLVE_FAILED")
        label = label or Path(item["path"]).name
        target = self.final_path(item)
        if self._cached_ok(target, item):
            return target
        if "patch" not in item:
            self._transfer(item, target, label)
            return target
        base_path = self.materialize(item["base"], label, depth + 1)
        delta = self.inputs / (item["patch"]["checksum"] + ".delta")
        self._transfer(item["patch"], delta, label + " (bản vá)")
        tmp = target.with_name(f".rebuild_{uuid.uuid4().hex}")
        try:
            try:
                apply_bsdiff(base_path, delta, tmp, item["size"])
            except (BsdiffError, OSError) as exc:
                raise OfficialResourceError(f"Không dựng được {label} từ bản vá: {exc}", "PATCH_FAILED")
            if tmp.stat().st_size != item["size"] or md5_file(tmp) != item["checksum"]:
                raise OfficialResourceError(f"Bản dựng lại của {label} sai MD5/kích thước.", "HASH_MISMATCH")
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        # The base of a delta is an intermediate version: free its disk space once the next link exists.
        if base_path != target:
            base_path.unlink(missing_ok=True)
        return target

    def prepare(self, items: list[dict]) -> dict[str, Path]:
        """Materialise every item; returns {checksum: cached path}. Raises before touching any game file."""
        self.total_bytes = self.estimate_download(items)
        self.done_bytes = 0
        out: dict[str, Path] = {}
        for item in items:
            out[item["checksum"]] = self.materialize(item)
        return out

    def cleanup(self) -> None:
        import shutil

        for d in (self.inputs, self.final):
            shutil.rmtree(d, ignore_errors=True)
