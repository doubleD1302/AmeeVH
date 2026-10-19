#!/usr/bin/env python3
"""BAR Archive Adapter (.arcx) for Stella Sora.

Supports unpacking, repacking, and verifying .arcx archives (tables and Lua scripts).
Preserves binary compatibility with GameFramework Archive specification:
- Magic: \x1aBAR (0x5241421a)
- Version: 102 (0x66)
- Flags: 0x111 (Header LZ4 Compressed + XOR Encrypted, Entries LZ4 Compressed)
- XOR Key: '&^^%#$#_$!@![]<_>?GHBFR_7481SDR_' (32 bytes)
- Hash algorithm: xxHash64 (lowercase normalized paths)
"""

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import lz4.block
except ImportError:
    print("Error: 'lz4' package is required. Install via: pip install lz4", file=sys.stderr)
    sys.exit(1)

MAGIC: bytes = b"\x1aBAR"
EXPECTED_VERSION: int = 102
DEFAULT_FLAG: int = 0x111
KEY: bytes = b"&^^%#$#_$!@![]<_>?GHBFR_7481SDR_"

FLAG_HEADER_COMPRESS: int = 0x1
FLAG_HEADER_ENCRYPTED: int = 0x10
FLAG_ENTRY_COMPRESS: int = 0x100
FLAG_ENTRY_ENCRYPTED: int = 0x1000

ENTRY_STRUCT_SIZE: int = 20  # uint64 Hash, uint32 Offset, uint32 OriginSize, uint32 Size


def xor_cipher(data: bytearray, key: bytes = KEY) -> bytearray:
    """In-place cyclical XOR encryption/decryption."""
    k_len = len(key)
    for i in range(len(data)):
        data[i] ^= key[i % k_len]
    return data


class ArcxArchive:
    """Parser and builder for .arcx archive files."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path
        self.version: int = EXPECTED_VERSION
        self.flag: int = DEFAULT_FLAG
        self.origin_size: int = 0
        self.comp_size: int = 0
        self.entry_count: int = 0
        self.entries: List[Dict] = []
        if file_path:
            self.load(file_path)

    def load(self, file_path: Path) -> None:
        """Read and parse an existing .arcx file."""
        self.file_path = file_path
        raw = file_path.read_bytes()

        if len(raw) < 24:
            raise ValueError(f"File too small ({len(raw)} bytes) for BAR header")

        magic = raw[:4]
        if magic != MAGIC:
            raise ValueError(f"Invalid magic: {magic!r}, expected {MAGIC!r}")

        self.version, self.flag, self.origin_size, self.comp_size, self.entry_count = struct.unpack(
            "<IIIII", raw[4:24]
        )

        if self.version != EXPECTED_VERSION:
            print(f"Warning: Unexpected version {self.version} (expected {EXPECTED_VERSION})", file=sys.stderr)

        # Decompress & decrypt directory
        dir_slice = bytearray(raw[24 : 24 + self.comp_size])
        if self.flag & FLAG_HEADER_ENCRYPTED:
            dir_slice = xor_cipher(dir_slice, KEY)

        if self.flag & FLAG_HEADER_COMPRESS:
            dir_uncomp = lz4.block.decompress(bytes(dir_slice), uncompressed_size=self.origin_size)
        else:
            dir_uncomp = bytes(dir_slice)

        if len(dir_uncomp) != self.origin_size:
            raise ValueError(
                f"Directory decompressed size mismatch: got {len(dir_uncomp)}, expected {self.origin_size}"
            )

        self.entries = []
        for i in range(self.entry_count):
            off = i * ENTRY_STRUCT_SIZE
            h, entry_off, entry_orig_sz, entry_sz = struct.unpack(
                "<QIII", dir_uncomp[off : off + ENTRY_STRUCT_SIZE]
            )
            self.entries.append(
                {
                    "index": i,
                    "hash": h,
                    "hash_hex": f"0x{h:016x}",
                    "offset": entry_off,
                    "origin_size": entry_orig_sz,
                    "compressed_size": entry_sz,
                }
            )

    def extract_entry(self, entry: Dict, raw_data: bytes) -> bytes:
        """Extract a single decompressed entry payload."""
        off = entry["offset"]
        sz = entry["compressed_size"]
        orig_sz = entry["origin_size"]

        chunk = bytearray(raw_data[off : off + sz])
        if self.flag & FLAG_ENTRY_ENCRYPTED:
            chunk = xor_cipher(chunk, KEY)

        if self.flag & FLAG_ENTRY_COMPRESS:
            return lz4.block.decompress(bytes(chunk), uncompressed_size=orig_sz)
        return bytes(chunk)

    def unpack_all(self, output_dir: Path) -> Path:
        """Unpack all entries into output directory with manifest."""
        output_dir.mkdir(parents=True, exist_ok=True)
        raw = self.file_path.read_bytes()

        manifest = {
            "archive_name": self.file_path.name,
            "version": self.version,
            "flag": self.flag,
            "entry_count": self.entry_count,
            "entries": [],
        }

        files_dir = output_dir / "entries"
        files_dir.mkdir(parents=True, exist_ok=True)

        for entry in self.entries:
            data = self.extract_entry(entry, raw)
            fname = f"{entry['index']:05d}_{entry['hash_hex']}.bin"
            fpath = files_dir / fname
            fpath.write_bytes(data)

            manifest["entries"].append(
                {
                    "index": entry["index"],
                    "hash": entry["hash"],
                    "hash_hex": entry["hash_hex"],
                    "filename": fname,
                    "origin_size": entry["origin_size"],
                }
            )

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Successfully unpacked {self.entry_count} entries to {output_dir}")
        return manifest_path


def repack_archive(input_dir: Path, output_file: Path) -> Path:
    """Repack entries from directory into a valid .arcx file."""
    manifest_path = input_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest.json in {input_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries_meta = manifest["entries"]
    files_dir = input_dir / "entries"

    version = manifest.get("version", EXPECTED_VERSION)
    flag = manifest.get("flag", DEFAULT_FLAG)
    entry_count = len(entries_meta)

    # 1. Compress all entries
    compressed_entries = []
    current_payload_offset = 0

    entries_binary_records = []
    payload_buffer = bytearray()

    for item in entries_meta:
        fname = item["filename"]
        fpath = files_dir / fname
        content = fpath.read_bytes()
        orig_sz = len(content)

        if flag & FLAG_ENTRY_COMPRESS:
            comp = lz4.block.compress(content, mode="fast", store_size=False)
        else:
            comp = content

        if flag & FLAG_ENTRY_ENCRYPTED:
            comp = bytes(xor_cipher(bytearray(comp), KEY))

        compressed_sz = len(comp)
        compressed_entries.append((item["hash"], orig_sz, compressed_sz, comp))

    # 2. Build uncompressed directory table
    uncomp_dir = bytearray()
    origin_size = entry_count * ENTRY_STRUCT_SIZE

    # Pre-calculate payload start offset:
    # Header: 24 bytes
    # Compressed directory size: to be determined
    # Compress directory first with dummy offset, then adjust?
    # Notice: Offset stored in directory entry is the file offset where the entry payload begins.
    # Therefore, payload starts immediately after Directory block + padding!

    # Let's first compress a dummy directory to determine compressed size:
    dummy_dir = bytearray(origin_size)
    comp_dir_dummy = lz4.block.compress(bytes(dummy_dir), mode="high_compression", store_size=False)
    # The actual compressed directory size will be close, but let's test realistic offsets:
    # In original data.arcx:
    # Header (24) + Directory Comp (17810) = 17834.
    # Payload starts at 18833 (alignment padding: 18833 - 17834 = 999 bytes).
    # In lua.arcx:
    # Header (24) + Directory Comp (49269) = 49293.
    # Payload starts at 52023 (alignment padding).
    # The exact payload start offset is specified in each entry.Offset!

    # Let's compress directory iteratively to stabilize sizes:
    # We will place payload starting at (24 + comp_dir_len + padding).
    # To keep it simple and clean, we can align payload to 4-byte or 16-byte boundary:
    # Let's estimate:
    estimated_comp_len = len(comp_dir_dummy)

    # Iterate until stable:
    for iteration in range(3):
        dir_comp_raw = lz4.block.compress(
            bytes(bytearray(origin_size)), mode="high_compression", store_size=False
        )
        payload_start = 24 + len(dir_comp_raw)
        # 16-byte align
        if payload_start % 16 != 0:
            payload_start += 16 - (payload_start % 16)

        # Build actual directory
        actual_dir = bytearray()
        cur_off = payload_start
        for h, orig_sz, comp_sz, comp_bytes in compressed_entries:
            actual_dir.extend(struct.pack("<QIII", h, cur_off, orig_sz, comp_sz))
            cur_off += comp_sz

        # Now compress actual directory
        final_comp_dir = bytearray(
            lz4.block.compress(bytes(actual_dir), mode="high_compression", store_size=False)
        )
        if len(final_comp_dir) <= len(dir_comp_raw):
            break

    # Build final archive
    comp_size = len(final_comp_dir)
    padding_len = payload_start - (24 + comp_size)
    if padding_len < 0:
        payload_start = 24 + comp_size
        padding_len = 0

    # Encrypt directory if flag set
    if flag & FLAG_HEADER_ENCRYPTED:
        final_comp_dir = xor_cipher(final_comp_dir, KEY)

    # Re-build directory with exact payload_start:
    actual_dir = bytearray()
    cur_off = payload_start
    payload_buffer = bytearray()
    for h, orig_sz, comp_sz, comp_bytes in compressed_entries:
        actual_dir.extend(struct.pack("<QIII", h, cur_off, orig_sz, comp_sz))
        payload_buffer.extend(comp_bytes)
        cur_off += comp_sz

    final_comp_dir = bytearray(
        lz4.block.compress(bytes(actual_dir), mode="high_compression", store_size=False)
    )
    comp_size = len(final_comp_dir)
    payload_start = 24 + comp_size + 16  # 16 bytes safe padding
    padding_len = 16

    # Re-pack with final coordinates
    actual_dir = bytearray()
    cur_off = payload_start
    for h, orig_sz, comp_sz, comp_bytes in compressed_entries:
        actual_dir.extend(struct.pack("<QIII", h, cur_off, orig_sz, comp_sz))
        cur_off += comp_sz

    final_comp_dir = bytearray(
        lz4.block.compress(bytes(actual_dir), mode="high_compression", store_size=False)
    )
    comp_size = len(final_comp_dir)
    padding_len = payload_start - (24 + comp_size)
    if padding_len < 0:
        payload_start = 24 + comp_size
        padding_len = 0

    if flag & FLAG_HEADER_ENCRYPTED:
        final_comp_dir = xor_cipher(final_comp_dir, KEY)

    header = struct.pack("<4sIIIII", MAGIC, version, flag, origin_size, comp_size, entry_count)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "wb") as f:
        f.write(header)
        f.write(final_comp_dir)
        if padding_len > 0:
            f.write(b"\x00" * padding_len)
        f.write(payload_buffer)

    print(f"Successfully repacked {entry_count} entries into {output_file} ({output_file.stat().st_size} bytes)")
    return output_file


def verify_roundtrip(arcx_path: Path, work_dir: Path) -> bool:
    """Verify unpack -> repack -> unpack byte integrity."""
    print(f"Testing roundtrip on: {arcx_path}")
    unpack_dir = work_dir / f"unpack_{arcx_path.stem}"
    repack_file = work_dir / f"{arcx_path.stem}_repacked.arcx"
    unpack2_dir = work_dir / f"unpack2_{arcx_path.stem}"

    # Step 1: Unpack original
    arc = ArcxArchive(arcx_path)
    arc.unpack_all(unpack_dir)

    # Step 2: Repack
    repack_archive(unpack_dir, repack_file)

    # Step 3: Unpack repacked
    arc2 = ArcxArchive(repack_file)
    arc2.unpack_all(unpack2_dir)

    # Step 4: Compare entries
    print("Verifying content identity across all entries...")
    manifest1 = json.loads((unpack_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest2 = json.loads((unpack2_dir / "manifest.json").read_text(encoding="utf-8"))

    if len(manifest1["entries"]) != len(manifest2["entries"]):
        print("Mismatch in entry count!", file=sys.stderr)
        return False

    for e1, e2 in zip(manifest1["entries"], manifest2["entries"]):
        if e1["hash"] != e2["hash"] or e1["origin_size"] != e2["origin_size"]:
            print(f"Metadata mismatch on entry {e1['index']}!", file=sys.stderr)
            return False

        b1 = (unpack_dir / "entries" / e1["filename"]).read_bytes()
        b2 = (unpack2_dir / "entries" / e2["filename"]).read_bytes()
        if b1 != b2:
            print(f"Content mismatch on entry {e1['index']} (Hash: {e1['hash_hex']})!", file=sys.stderr)
            return False

    print("ALL ENTRIES MATCH 100%! Roundtrip verification PASSED PERFECTLY!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Stella Sora BAR (.arcx) Archive Adapter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Unpack command
    p_unpack = subparsers.add_parser("unpack", help="Unpack .arcx into directory")
    p_unpack.add_argument("archive", type=Path, help="Input .arcx file")
    p_unpack.add_argument("output", type=Path, help="Output directory")

    # Repack command
    p_repack = subparsers.add_parser("repack", help="Repack directory into .arcx")
    p_repack.add_argument("input_dir", type=Path, help="Input directory containing manifest.json")
    p_repack.add_argument("output", type=Path, help="Output .arcx file")

    # Verify command
    p_verify = subparsers.add_parser("verify", help="Verify roundtrip unpack/repack integrity")
    p_verify.add_argument("archive", type=Path, help="Input .arcx file to test")
    p_verify.add_argument(
        "--work-dir", type=Path, default=Path("work/research/roundtrip_test"), help="Temporary work directory"
    )

    args = parser.parse_args()

    if args.command == "unpack":
        arc = ArcxArchive(args.archive)
        arc.unpack_all(args.output)
    elif args.command == "repack":
        repack_archive(args.input_dir, args.output)
    elif args.command == "verify":
        success = verify_roundtrip(args.archive, args.work_dir)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
