#!/usr/bin/env python3
"""
Polish and standardize Stella Sora terminology across Talent and FateCard tables:
- Standardize elemental stats: Kháng hệ X, Xuyên Kháng hệ X
- Fix Lữ khách hệ X order
- Replace "Tấn công tự động" with "Đòn đánh thường"
- Replace "sát thương tối đa" with "Sát thương Tuyệt kỹ"
- Replace "chiêu cuối" with "Tuyệt kỹ"
- Ensure 100% token preservation
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "work" / "research" / "data_decrypted" / "entries"
CACHE_PATH = ROOT / "work" / "batches" / "talent_fatecard_translation_cache.json"

sys_path = ROOT / "tools"
import sys
sys.path.insert(0, str(sys_path))
from translate_subagent_4a import extract_tokens, shield_tokens, unshield_tokens

def polish_entry(text: str) -> str:
    sh, toks = shield_tokens(text)

    # 1. Ultimate terms
    sh = re.sub(r'\bsát thương tối đa\b', 'Sát thương Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bchiêu cuối\b', 'Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bChiêu cuối\b', 'Tuyệt kỹ', sh)

    # 2. Auto Attack terms
    sh = re.sub(r'\bsát thương Tấn công tự động\b', 'Sát thương Đòn đánh thường', sh, flags=re.I)
    sh = re.sub(r'\bsát thương tấn công tự động\b', 'Sát thương Đòn đánh thường', sh, flags=re.I)
    sh = re.sub(r'\bTấn công tự động\b', 'Đòn đánh thường', sh)
    sh = re.sub(r'\btấn công tự động\b', 'đòn đánh thường', sh)

    # 3. Phrasing cleanups
    sh = re.sub(r'\bsử dụng Tuyệt kỹ\b', 'thi triển Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bthi triển Tuyệt kỹ của mình\b', 'thi triển Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bbằng Tuyệt kỹ của mình\b', 'bằng Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bthời gian hồi chiêu của Tuyệt kỹ\b', 'thời gian hồi chiêu Tuyệt kỹ', sh, flags=re.I)
    sh = re.sub(r'\bsát thương cho hệ ([A-Z][a-zà-ỹ]+)\b', r'Sát thương hệ \1', sh, flags=re.I)
    sh = re.sub(r'\bsát thương hệ ([A-Z][a-zà-ỹ]+)\b', r'Sát thương hệ \1', sh)
    sh = re.sub(r'\bsát thương Kỹ năng\b', 'Sát thương Kỹ năng', sh)
    sh = re.sub(r'\bsát thương Tuyệt kỹ\b', 'Sát thương Tuyệt kỹ', sh)
    sh = re.sub(r'\bsát thương Đòn đánh thường\b', 'Sát thương Đòn đánh thường', sh)

    # 4. PEN and RES terms
    for elem in ["Hỏa", "Thủy", "Phong", "Địa", "Quang", "Ám"]:
        sh = re.sub(rf'\bhệ {elem} PEN\b', f'Xuyên Kháng hệ {elem}', sh, flags=re.I)
        sh = re.sub(rf'\bhệ {elem} RES\b', f'Kháng hệ {elem}', sh, flags=re.I)
        sh = re.sub(rf'\bhệ {elem} Lữ khách\b', f'Lữ khách hệ {elem}', sh, flags=re.I)
        sh = re.sub(rf'\b(Dấu ấn|Dấu) hệ {elem}\b', f'Ấn ký {elem}', sh, flags=re.I)

    sh = re.sub(r'\bsát thương RES\b', 'Kháng sát thương', sh, flags=re.I)
    sh = re.sub(r'\bSPD Tấn công\b', 'Tốc độ đánh', sh, flags=re.I)
    sh = re.sub(r'\bTốc độ Tấn công\b', 'Tốc độ đánh', sh, flags=re.I)

    # Clean whitespace and punctuation
    sh = re.sub(r'\s+([,.:;?!%])', r'\1', sh)
    sh = re.sub(r'[ \t]{2,}', ' ', sh)

    restored = unshield_tokens(sh, toks)
    return restored

def main():
    print("=" * 70)
    print("POLISHING TALENT & FATECARD LOCALIZATION (V2)")
    print("=" * 70)

    talent_path = ENTRIES / "00680_0x3f0bd5f8db2389b6.bin"
    fate_path = ENTRIES / "00560_0x788d8a3db60dd08a.bin"

    talent = json.loads(talent_path.read_text(encoding="utf-8"))
    fate = json.loads(fate_path.read_text(encoding="utf-8"))
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    # Polish cache
    polished_cache = {}
    for en_key, vi_val in cache.items():
        pol = polish_entry(vi_val)
        orig_toks = extract_tokens(en_key)
        pol_toks = extract_tokens(pol)
        if orig_toks == pol_toks:
            polished_cache[en_key] = pol
        else:
            print(f"Token mismatch while polishing cache key: {en_key}")
            polished_cache[en_key] = vi_val

    CACHE_PATH.write_text(json.dumps(polished_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated cache: {len(polished_cache)} entries")

    # Polish Talent
    polished_talent = {}
    t_err = 0
    for k, v in talent.items():
        pol = polish_entry(v)
        orig_toks = extract_tokens(v)
        pol_toks = extract_tokens(pol)
        if orig_toks == pol_toks:
            polished_talent[k] = pol
        else:
            t_err += 1
            polished_talent[k] = v

    # Polish FateCard
    polished_fate = {}
    f_err = 0
    for k, v in fate.items():
        pol = polish_entry(v)
        orig_toks = extract_tokens(v)
        pol_toks = extract_tokens(pol)
        if orig_toks == pol_toks:
            polished_fate[k] = pol
        else:
            f_err += 1
            polished_fate[k] = v

    print(f"Polished Talent entries: {len(polished_talent)} (Token errors: {t_err})")
    print(f"Polished FateCard entries: {len(polished_fate)} (Token errors: {f_err})")

    assert t_err == 0, f"Talent has {t_err} token errors after polishing!"
    assert f_err == 0, f"FateCard has {f_err} token errors after polishing!"

    # Write files back
    talent_path.write_text(json.dumps(polished_talent, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Overwrote polished Talent: {talent_path} ({talent_path.stat().st_size:,} bytes)")

    fate_path.write_text(json.dumps(polished_fate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Overwrote polished FateCard: {fate_path} ({fate_path.stat().st_size:,} bytes)")

    print("POLISHING V2 COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
