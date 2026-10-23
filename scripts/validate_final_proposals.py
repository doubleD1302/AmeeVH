import json
import os
import unicodedata
import hashlib
import re

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

jsonl_path = "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"

forbidden_slang_patterns = [
    r"\bquẩy\b",
    r"\bbựa đời\b",
    r"\bbay màu\b",
    r"\bcà khịa\b",
    r"\bchuẩn đét\b",
    r"\bvãi\b",
    r"\bảo ma\b",
    r"\bnói toang\b"
]

forbidden_mt_patterns = [
    r"Ý Chí Ân Tứ",
    r"Lai Phúc Oasis",
    r"mất khả năng lao động",
    r"Sao nhổ",
    r"Kim Khố Ý Chí Ân Tứ"
]

def validate():
    print("=== FINAL VALIDATION OF UNIFIED STORY PROPOSALS ===")
    print(f"Target file: {jsonl_path}")
    print(f"SHA256: {sha256_file(jsonl_path)}")

    total_lines = 0
    token_checks = 0
    token_failures = []
    nfc_failures = []
    slang_hits = []
    mt_hits = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            total_lines += 1
            data = json.loads(line)
            lid = data["id"]
            vi = data["vi"]
            tokens = data.get("tokens", [])

            # NFC check
            if vi != unicodedata.normalize("NFC", vi):
                nfc_failures.append(lid)

            # Token check
            for t in tokens:
                token_checks += 1
                if t not in vi:
                    token_failures.append((lid, t, vi))

            # Slang check (skip pure engine tags)
            if not lid.startswith(("ep_", "fx_", "qstory_", "story_")):
                for pat in forbidden_slang_patterns:
                    if re.search(pat, vi, re.IGNORECASE):
                        slang_hits.append((lid, pat, vi))
                for pat in forbidden_mt_patterns:
                    if re.search(pat, vi, re.IGNORECASE):
                        mt_hits.append((lid, pat, vi))

    print(f"Total lines validated: {total_lines}")
    print(f"Tokens verified: {token_checks}")
    print(f"Token failures: {len(token_failures)}")
    print(f"NFC failures: {len(nfc_failures)}")
    print(f"Forbidden slang hits: {len(slang_hits)}")
    print(f"Forbidden MT hits: {len(mt_hits)}")

    assert total_lines == 5558, f"Expected 5558 lines, got {total_lines}"
    assert len(token_failures) == 0, f"Token failures detected: {token_failures[:5]}"
    assert len(nfc_failures) == 0, f"NFC failures detected: {nfc_failures[:5]}"
    assert len(slang_hits) == 0, f"Slang hits detected: {slang_hits[:5]}"
    assert len(mt_hits) == 0, f"MT hits detected: {mt_hits[:5]}"

    print("\n>>> ALL VALIDATION GATES PASSED WITH 100% SUCCESS! <<<")

if __name__ == "__main__":
    validate()
