#!/usr/bin/env python3
"""
Final Verification Gate for Subagent 4A
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "work" / "research" / "data_decrypted" / "entries"

TALENT_PATH = ENTRIES / "00680_0x3f0bd5f8db2389b6.bin"
TALENT_BAK = ENTRIES / "00680_0x3f0bd5f8db2389b6.bin.bak"
TALENT_CN = ENTRIES / "00901_0x2ae3485bc9698293.bin"

FATE_PATH = ENTRIES / "00560_0x788d8a3db60dd08a.bin"
FATE_BAK = ENTRIES / "00560_0x788d8a3db60dd08a.bin.bak"
FATE_CN = ENTRIES / "00781_0x86f53f32d1f74ab6.bin"

TOK_RE = re.compile(r'(\x0b|\n|\r|<[^>]+>|\{[0-9a-zA-Z_]+\}|&[a-zA-Z0-9_]+&|##[^#]+#[0-9]+#|##[^#]+#)')

def extract_tokens(text: str) -> list:
    return TOK_RE.findall(text)

def verify_file(name: str, target_path: Path, orig_path: Path, expected_count: int):
    print(f"\n--- Verifying {name} ---")
    assert target_path.exists(), f"Target file {target_path} does not exist!"
    assert orig_path.exists(), f"Original backup {orig_path} does not exist!"

    target_data = json.loads(target_path.read_text(encoding="utf-8"))
    orig_data = json.loads(orig_path.read_text(encoding="utf-8"))

    print(f"Target count: {len(target_data)} (expected {expected_count})")
    assert len(target_data) == expected_count, f"Count mismatch: {len(target_data)} != {expected_count}"

    key_diff = set(target_data.keys()) ^ set(orig_data.keys())
    print(f"Key differences: {len(key_diff)}")
    assert len(key_diff) == 0, f"Key mismatch count: {len(key_diff)}"

    token_mismatches = []
    empty_entries = []

    for k, orig_text in orig_data.items():
        vi_text = target_data[k]
        if not vi_text.strip():
            empty_entries.append(k)
        orig_toks = extract_tokens(orig_text)
        vi_toks = extract_tokens(vi_text)
        if orig_toks != vi_toks:
            token_mismatches.append((k, orig_toks, vi_toks))

    print(f"Empty text errors: {len(empty_entries)}")
    print(f"Token preservation mismatches: {len(token_mismatches)}")

    assert len(empty_entries) == 0, f"Found empty entries: {empty_entries[:5]}"
    assert len(token_mismatches) == 0, f"Found token mismatches: {token_mismatches[:5]}"

    print(f"PASS: {name} 100% token preservation and structure integrity verified!")

def main():
    print("=" * 70)
    print("SUBAGENT 4A: RUNNING FINAL VERIFICATION GATE")
    print("=" * 70)

    verify_file("Talent (Thiên Phú)", TALENT_PATH, TALENT_BAK, 4250)
    verify_file("FateCard (Thẻ Bài Định Mệnh)", FATE_PATH, FATE_BAK, 468)

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
