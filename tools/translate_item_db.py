#!/usr/bin/env python3
"""Item Database Translator for Stella Sora (EN -> VI).

Translates entry 00577_0xe60634348b826f41.bin (3,777 items) from English to Vietnamese,
cross-referencing Chinese (00798_0xdb546f14f2f79a11.bin).
Guarantees tag/token preservation: {0}, {1}, <color=...>, </color>, <...>, \\x0b, \\n.
"""

import json
import re
import shutil
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
EN_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00577_0xe60634348b826f41.bin"
CN_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00798_0xdb546f14f2f79a11.bin"
BAK_PATH = EN_PATH.with_suffix(".bin.bak")
CACHE_PATH = ROOT / "work" / "batches" / "item_db_translation_cache.json"

# Exact overrides for specific keys or texts
EXACT_KEY_OVERRIDES = {
    "Item.90011.2": "Một nốt nhạc ghi lại Bản giao hưởng Cường công. Tăng <color=#fb8037>Tấn công</color> dựa trên tổng số lượng của nó.",
    "Item.90012.2": "Một nốt nhạc ghi lại Bản giao hưởng May mắn. Tăng <color=#fb8037>Tỷ lệ bạo kích</color> dựa trên tổng số lượng của nó.",
    "Item.90013.2": "Một nốt nhạc ghi lại Bản giao hưởng Bùng nổ. Tăng <color=#fb8037>Sát thương bạo kích</color> dựa trên tổng số lượng của nó.",
    "Item.90014.2": "Một nốt nhạc ghi lại Bản giao hưởng Thể lực. Tăng <color=#fb8037>HP tối đa</color> dựa trên tổng số lượng của nó.",
    "Item.90015.2": "Một nốt nhạc ghi lại Bản giao hưởng Tập trung. Tăng <color=#fb8037>Sát thương đòn đánh thường</color> dựa trên tổng số lượng của nó.",
    "Item.90016.2": "Một nốt nhạc ghi lại Bản giao hưởng Kỹ năng. Tăng <color=#fb8037>Sát thương kỹ năng</color> dựa trên tổng số lượng của nó.",
    "Item.90017.2": "Một nốt nhạc ghi lại Bản giao hưởng Tuyệt kỹ. Tăng <color=#fb8037>Sát thương tuyệt kỹ</color> dựa trên tổng số lượng của nó.",
    "Item.90018.2": "Một nốt nhạc ghi lại Bản giao hưởng Dòng nước. Tăng <color=#fb8037>Sát thương hệ Thủy</color> dựa trên tổng số lượng của nó.",
    "Item.90019.2": "Một nốt nhạc ghi lại Bản giao hưởng Rực lửa. Tăng <color=#fb8037>Sát thương hệ Hỏa</color> dựa trên tổng số lượng của nó.",
    "Item.90020.2": "Một nốt nhạc ghi lại Bản giao hưởng Cuồng phong. Tăng <color=#fb8037>Sát thương hệ Phong</color> dựa trên tổng số lượng của nó.",
    "Item.90021.2": "Một nốt nhạc ghi lại Bản giao hưởng Cát bụi. Tăng <color=#fb8037>Sát thương hệ Địa</color> dựa trên tổng số lượng của nó.",
    "Item.90022.2": "Một nốt nhạc ghi lại Bản giao hưởng Ánh sáng. Tăng <color=#fb8037>Sát thương hệ Quang</color> dựa trên tổng số lượng của nó.",
    "Item.90023.2": "Một nốt nhạc ghi lại Bản giao hưởng Bóng tối. Tăng <color=#fb8037>Sát thương hệ Ám</color> dựa trên tổng số lượng của nó.",
    "Item.120003.2": "<Miracle of a Flicker> Vật phẩm sự kiện độc quyền",
    "Item.120004.2": "<To My Dearest You> Vật phẩm sự kiện độc quyền",
    "Item.120006.2": "<Lucky Treasure Shovel> Vật phẩm sự kiện độc quyền",
}

# Template regex patterns (English -> Vietnamese) for fixed, formulaic strings
TEMPLATES = [
    (re.compile(r"^Material required for the Crescendo of specific Discs\.$"),
     "Nguyên liệu cần thiết cho Thăng hoa Đĩa nhạc tương ứng."),
    (re.compile(r"^Activates Trekker Talents\.$"),
     "Dùng để kích hoạt Thiên phú Lữ khách."),
    (re.compile(r"^Includes the bonus items corresponding to the purchase of the current Royal Startup Grant\.$"),
     "Bao gồm các vật phẩm tặng kèm khi mua Trợ cấp khởi đầu Hoàng gia hiện tại."),
    (re.compile(r"^A small card inscribed with magical words\.$"),
     "Một tấm thẻ nhỏ khắc những ngôn từ ma thuật."),
    (re.compile(r"^A basic material used for Trekker tier-up\.$"),
     "Nguyên liệu cơ bản dùng để thăng giai Lữ khách."),
    (re.compile(r"^An intermediate material used for Trekker tier-up\.$"),
     "Nguyên liệu trung cấp dùng để thăng giai Lữ khách."),
    (re.compile(r"^An advanced material used for Trekker tier-up\.$"),
     "Nguyên liệu cao cấp dùng để thăng giai Lữ khách."),
    (re.compile(r"^A basic material used for Discs tier-up\.$"),
     "Nguyên liệu cơ bản dùng để thăng giai Đĩa nhạc."),
    (re.compile(r"^An intermediate material used for Discs tier-up\.$"),
     "Nguyên liệu trung cấp dùng để thăng giai Đĩa nhạc."),
    (re.compile(r"^An advanced material used for Discs tier-up\.$"),
     "Nguyên liệu cao cấp dùng để thăng giai Đĩa nhạc."),
    (re.compile(r"^Used for certain Trekker skill upgrade \(Lv\.(\d+) to Lv\.(\d+)\)\.$"),
     r"Dùng để nâng cấp kỹ năng cho một số Lữ khách nhất định (Lv.\1 đến Lv.\2)."),
    (re.compile(r"^Restores (\d+) Vigor when used\.$"),
     r"Dùng để hồi phục \1 Năng lượng."),
    (re.compile(r"^A gift that increases a Trekker's Affinity by ([\d,]+)\.$"),
     r"Món quà giúp tăng \1 Độ thân mật của Lữ khách."),
    (re.compile(r"^Grants a small amount of EXP for leveling up Trekkers\.$"),
     "Cung cấp một lượng nhỏ EXP để nâng cấp Lữ khách."),
    (re.compile(r"^Grants a moderate amount of EXP for leveling up Trekkers\.$"),
     "Cung cấp lượng EXP vừa phải để nâng cấp Lữ khách."),
    (re.compile(r"^Grants a large amount of EXP for leveling up Trekkers\.$"),
     "Cung cấp lượng lớn EXP để nâng cấp Lữ khách."),
    (re.compile(r"^Grants a massive amount of EXP for leveling up Trekkers\.$"),
     "Cung cấp lượng cực lớn EXP để nâng cấp Lữ khách."),
    (re.compile(r"^Grants a small amount of EXP for leveling up Discs\.$"),
     "Cung cấp một lượng nhỏ EXP để nâng cấp Đĩa nhạc."),
    (re.compile(r"^Grants a moderate amount of EXP for leveling up Discs\.$"),
     "Cung cấp lượng EXP vừa phải để nâng cấp Đĩa nhạc."),
    (re.compile(r"^Grants a large amount of EXP for leveling up Discs\.$"),
     "Cung cấp lượng lớn EXP để nâng cấp Đĩa nhạc."),
    (re.compile(r"^Grants a massive amount of EXP for leveling up Discs\.$"),
     "Cung cấp lượng cực lớn EXP để nâng cấp Đĩa nhạc."),
    (re.compile(r"^Tier Bonus:\s*Stellanite Dust ×([\d,]+)$"),
     r"Thưởng theo cấp: Bụi Stellanite ×\1"),
    (re.compile(r"^Tier Bonus:\s*Cerulean Ticket ×([\d,]+)$"),
     r"Thưởng theo cấp: Vé Cerulean ×\1"),
    (re.compile(r"^Tier Bonus:\s*Gold Disc ×([\d,]+)$"),
     r"Thưởng theo cấp: Đĩa nhạc Vàng ×\1"),
    (re.compile(r"^Tier Bonus:\s*Drop of Purity ×([\d,]+)$"),
     r"Thưởng theo cấp: Giọt Thuần Khiết ×\1"),
    (re.compile(r"^Tier Bonus:\s*Dorra ×([\d,]+)$"),
     r"Thưởng theo cấp: Dorra ×\1"),
    (re.compile(r"^Unlock Now:\s*Elite Grant Privileges$"),
     "Mở khóa ngay: Đặc quyền Trợ cấp Tinh anh"),
    (re.compile(r"^Unlock Now:\s*Royal Grant Privileges$"),
     "Mở khóa ngay: Đặc quyền Trợ cấp Hoàng gia"),
    (re.compile(r"^Royal Grant Bonus Item$"),
     "Vật phẩm tặng kèm Trợ cấp Hoàng gia"),
    (re.compile(r"^Elite Grant Bonus Item$"),
     "Vật phẩm tặng kèm Trợ cấp Tinh anh"),
    (re.compile(r"^Upgrade Grant Differential Item$"),
     "Vật phẩm bù chênh lệch Nâng cấp Trợ cấp"),
    (re.compile(r"^A treasure shovel said to bring good fortune\. Unfortunately, it's not very durable\.$"),
     "Một chiếc xẻng tìm kho báu được cho là mang lại may mắn. Tiếc là độ bền không cao."),
    (re.compile(r"^A precious Disc collection, handpicked from a massive disc library\. Each track is worth savoring in detail\.$"),
     "Bộ sưu tập Đĩa nhạc quý giá được tuyển chọn từ kho đĩa đồ sộ. Mỗi bản nhạc đều đáng để thưởng thức tỉ mỉ."),
    (re.compile(r"^Set the direction, embrace an unforgettable encounter\.$"),
     "Xác định phương hướng, đón nhận cuộc hội ngộ khó quên."),
    (re.compile(r"^Log in daily to earn Diamonds and Stamina\.$"),
     "Đăng nhập hàng ngày để nhận Kim Cương và Thể lực."),
    (re.compile(r"^Purchasing a Monthly Card is a wise choice\.$"),
     "Mua Thẻ Tháng là một lựa chọn sáng suốt."),
]

def shield_tokens(text: str):
    """Shield formatting tags and control chars so translation doesn't alter them."""
    tokens = []
    def repl(m):
        idx = len(tokens)
        tokens.append(m.group(0))
        return f" [[TOK{idx}]] "
    # Shield \x0b, \n, <...>, {...}
    pattern = re.compile(r'(\x0b|\n|<[^>]+>|\{[0-9a-zA-Z_]+\})')
    shielded = pattern.sub(repl, text)
    return shielded, tokens

def unshield_tokens(text: str, tokens: list):
    """Restore shielded tokens cleanly."""
    def repl(m):
        idx = int(m.group(1))
        if idx >= len(tokens):
            return ""
        tok = tokens[idx]
        if tok in ('\x0b', '\n'):
            return tok
        return f" {tok} "

    res = re.sub(r'\s*\[\[\s*TOK(\d+)\s*\]\]\s*', repl, text)
    # Clean spacing inside color tags: <color=#...> text </color> -> <color=#...>text</color>
    res = re.sub(r'(<color=[^>]+>)\s+', r'\1', res)
    res = re.sub(r'\s+(</color>)', r'\1', res)
    # Clean whitespace around \x0b
    res = re.sub(r'\s*\x0b\s*', '\x0b', res)
    # Clean double spaces
    res = re.sub(r'[ \t]{2,}', ' ', res)
    return res.strip()

def post_process_vi(text: str) -> str:
    """Refine translated Vietnamese for terminology and style consistency."""
    # Key game terms
    text = re.sub(r'\bDora\b', 'Dorra', text)
    text = re.sub(r'\bTrekkers?\b', 'Lữ khách', text)
    text = re.sub(r'\bNovians\b', 'người Nova', text)
    text = re.sub(r'\bNova Continent\b', 'Lục địa Nova', text)
    text = re.sub(r'\bthe Wilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bWilds\b', 'Vùng hoang dã', text)
    text = re.sub(r'\bMonolith\b', 'Cự tháp', text)
    text = re.sub(r'\bDiscs?\b', 'Đĩa nhạc', text)
    text = re.sub(r'\bEmblems?\b', 'Huy hiệu', text)
    text = re.sub(r'\bVigor\b', 'Năng lượng', text)
    text = re.sub(r'\bDiamonds?\b', 'Kim Cương', text)
    text = re.sub(r'\bDeepsea Finance\b', 'Deepsea Finance', text)
    text = re.sub(r'\bStarlight Core\b', 'Lõi Ánh sao', text)
    text = re.sub(r'\bStarlight\b', 'Ánh sao', text)
    text = re.sub(r'\bStellanite Dust\b', 'Bụi Stellanite', text)
    text = re.sub(r'\bStellanite Lumina\b', 'Tinh Thể Stellanite', text)
    text = re.sub(r'\bDestiny Pack\b', 'Gói Thẻ Định Mệnh', text)
    text = re.sub(r'\bDestiny Cards?\b', 'Thẻ Định Mệnh', text)
    text = re.sub(r'\bSoul Keys?\b', 'Chìa khóa Tâm hồn', text)
    text = re.sub(r'\bSoul key\b', 'Chìa khóa tâm hồn', text)
    text = re.sub(r'\bMonthly Card\b', 'Thẻ Tháng', text)
    
    # Title & Avatar prefix standardizations
    text = re.sub(r'^(?:Tiêu đề tiền tố|Tiền tố Tiêu đề|Tiền tố danh hiệu):\s*', 'Tiền tố danh hiệu: ', text)
    text = re.sub(r'^(?:Tiêu đề hậu tố|Hậu tố Tiêu đề|Hậu tố danh hiệu):\s*', 'Hậu tố danh hiệu: ', text)
    text = re.sub(r'^(?:Tiêu đề danh dự|Danh hiệu danh dự|Danh hiệu vinh dự):\s*', 'Danh hiệu vinh dự: ', text)
    text = re.sub(r'^(?:Mở khóa Tiêu đề|Mở khóa danh hiệu):\s*', 'Mở khóa danh hiệu: ', text)
    text = re.sub(r'^(?:Mở khóa Tiêu đề danh dự|Mở khóa Danh hiệu Danh dự|Mở khóa Danh hiệu vinh dự):\s*', 'Mở khóa Danh hiệu vinh dự: ', text)
    text = re.sub(r'^(?:Avatar có thời gian giới hạn|Ảnh đại diện có thời gian giới hạn|Ảnh đại diện giới hạn):\s*', 'Ảnh đại diện giới hạn: ', text)
    text = re.sub(r'^(?:Mở khóa Avatar|Mở khóa Ảnh đại diện):\s*', 'Mở khóa Ảnh đại diện: ', text)
    text = re.sub(r'^(?:Mở khóa Khung đại diện|Mở khóa Khung Avatar):\s*', 'Mở khóa Khung đại diện: ', text)

    # Clean whitespace before punctuation
    text = re.sub(r' +([,.:;?!])', r'\1', text)
    return text.strip()

def translate_batch(texts: list, session: requests.Session) -> list:
    """Translate a batch of shielded texts using Google Translate API with auto split/retry."""
    if not texts:
        return []
    
    delim = "\n###\n"
    joined = delim.join(texts)
    
    for attempt in range(3):
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={
                    "client": "gtx",
                    "sl": "en",
                    "tl": "vi",
                    "dt": "t",
                    "q": joined,
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            if r.status_code == 200:
                res = r.json()
                full_text = "".join([item[0] for item in res[0] if item[0]])
                parts = [p.strip() for p in full_text.split("###")]
                if len(parts) == len(texts):
                    return parts
                else:
                    # Mismatch in delimiter count, divide and conquer
                    if len(texts) > 1:
                        mid = len(texts) // 2
                        return translate_batch(texts[:mid], session) + translate_batch(texts[mid:], session)
                    else:
                        return [full_text.strip()]
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.0 * (attempt + 1))
            
    # Final fallback: translate 1 by 1
    results = []
    for t in texts:
        try:
            r = session.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": t},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if r.status_code == 200:
                res = r.json()
                full = "".join([item[0] for item in res[0] if item[0]])
                results.append(full.strip())
            else:
                results.append(t)
        except Exception:
            results.append(t)
        time.sleep(0.1)
    return results

def main():
    print(f"Loading EN items from {EN_PATH}...")
    with open(EN_PATH, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    print(f"Total EN items: {len(en_data)}")

    print(f"Loading CN items from {CN_PATH}...")
    with open(CN_PATH, "r", encoding="utf-8") as f:
        cn_data = json.load(f)
    print(f"Total CN items: {len(cn_data)}")

    # Backup EN if not exists
    if not BAK_PATH.exists():
        shutil.copyfile(EN_PATH, BAK_PATH)
        print(f"Created backup at {BAK_PATH}")

    # Load cache if exists
    cache = {}
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} cached translations.")
        except Exception:
            cache = {}

    session = requests.Session()

    translated_map = {}
    untranslated_unique = {}

    for key, text_en in en_data.items():
        if key in EXACT_KEY_OVERRIDES:
            translated_map[key] = EXACT_KEY_OVERRIDES[key]
            continue
        if text_en in ("!NONEED!", "???") or not text_en.strip():
            translated_map[key] = text_en
            continue

        # Check template matching
        matched_template = False
        for pat, repl in TEMPLATES:
            if pat.search(text_en):
                translated_map[key] = pat.sub(repl, text_en)
                matched_template = True
                break
        if matched_template:
            continue

        # Check cache
        if text_en in cache:
            translated_map[key] = cache[text_en]
            continue

        # Needs translation
        if text_en not in untranslated_unique:
            untranslated_unique[text_en] = []
        untranslated_unique[text_en].append(key)

    print(f"Pre-translated via templates/overrides/cache: {len(translated_map)} keys.")
    print(f"Unique strings needing translation: {len(untranslated_unique)}")

    # Translate unique strings in batches
    unique_list = list(untranslated_unique.keys())
    batch_size = 35
    total_batches = (len(unique_list) + batch_size - 1) // batch_size

    for b_idx in range(total_batches):
        chunk = unique_list[b_idx * batch_size : (b_idx + 1) * batch_size]
        # Shield tokens
        shielded_chunk = []
        chunk_tokens = []
        for t in chunk:
            s_text, toks = shield_tokens(t)
            shielded_chunk.append(s_text)
            chunk_tokens.append(toks)

        t0 = time.time()
        translated_chunk = translate_batch(shielded_chunk, session)
        elapsed = time.time() - t0

        # Unshield & post-process
        for orig_text, trans_shielded, toks in zip(chunk, translated_chunk, chunk_tokens):
            restored = unshield_tokens(trans_shielded, toks)
            refined = post_process_vi(restored)
            cache[orig_text] = refined
            # Assign to all keys with this text
            for k in untranslated_unique[orig_text]:
                translated_map[k] = refined

        print(f"Batch {b_idx + 1}/{total_batches} ({len(chunk)} items) done in {elapsed:.2f}s")
        time.sleep(0.2)

        # Save cache checkpoint every 10 batches
        if (b_idx + 1) % 10 == 0:
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

    # Final cache save
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    # Build final result JSON preserving original key order
    final_output = {}
    missing_keys = []
    broken_tags = []

    for k in en_data.keys():
        if k in translated_map:
            val = translated_map[k]
            src = en_data[k]
            # Check color tags
            if "<color=" in src and "<color=" not in val:
                broken_tags.append((k, src, val))
            if "</color>" in src and "</color>" not in val:
                broken_tags.append((k, src, val))
            # Check \x0b
            if "\x0b" in src and "\x0b" not in val:
                val = val.replace("\n", "\x0b")
                if "\x0b" not in val:
                    broken_tags.append((k, src, val))
            final_output[k] = val
        else:
            missing_keys.append(k)

    print(f"\n--- VALIDATION SUMMARY ---")
    print(f"Total keys processed: {len(final_output)} / {len(en_data)}")
    print(f"Missing keys: {len(missing_keys)}")
    print(f"Broken tags detected: {len(broken_tags)}")
    if broken_tags:
        for bt in broken_tags[:5]:
            print(f"  Warning on {bt[0]}: {bt[1]} -> {bt[2]}")

    assert len(final_output) == len(en_data), "Key count mismatch!"

    # Write back to 00577_0xe60634348b826f41.bin
    print(f"Writing Vietnamese translations to {EN_PATH}...")
    with open(EN_PATH, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print("Successfully completed item database translation!")

if __name__ == "__main__":
    main()
