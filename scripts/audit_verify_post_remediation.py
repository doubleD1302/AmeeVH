import os
import json
import re
import glob
from collections import defaultdict, Counter

ROOT_DIR = r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
CJK_REGEX = re.compile(r"[\u4e00-\u9fff]")
EN_STOPWORDS = set([
    "the", "and", "that", "have", "for", "not", "with", "you", "this", "but", "his", "from",
    "they", "say", "her", "she", "will", "one", "all", "would", "there", "their", "what",
    "out", "about", "who", "get", "which", "when", "make", "can", "like", "time", "just",
    "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them",
    "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us", "are",
    "was", "were", "been", "has", "had", "does", "did", "doing", "wouldn't", "couldn't",
    "shouldn't", "don't", "didn't", "can't", "won't", "i'm", "you're", "he's", "she's", "it's"
])
BINARY_OPCODE_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u05ff]|Gѿ")

PRONOUN_RULES = [
    ("BOSS_CALQUE_ONG_CHU", re.compile(r"\bông chủ\b", re.IGNORECASE)),
    ("BOSS_ACCORD_HIEP_DINH", re.compile(r"Hiệp định của ông chủ", re.IGNORECASE)),
    ("BOSS_ACCORD_HALF_TRANSLATED", re.compile(r"Sếp Accord|Hiệp Ước Boss", re.IGNORECASE)),
    ("BOSS_CUA_BAN", re.compile(r"BOSS CỦA BẠN", re.IGNORECASE)),
    ("CAPTAIN_CALQUE_THUYEN_TRUONG", re.compile(r"Thuyền trưởng (Fuyuka|Nazuka|Nazuna|Gerie|Narida)", re.IGNORECASE)),
    ("ARBITER_CALQUE_TRONG_TAI", re.compile(r"Trọng tài (Gerie|Hoàng Hôn|Chạng Vạng)", re.IGNORECASE)),
    ("LADY_CALQUE_BA_ANGIE", re.compile(r"Bà Angie|Quý Cô Angie", re.IGNORECASE)),
    ("MENTOR_CALQUE_BAC_SI", re.compile(r"Thưa bác sĩ", re.IGNORECASE)),
    ("PARTNER_CALQUE_BAN_DOI", re.compile(r"bạn đời", re.IGNORECASE)),
    ("PARTY_CALQUE_BUA_TIEC", re.compile(r"bữa tiệc bất ngờ|bữa tiệc tham gia|bữa tiệc ký kết|bữa tiệc đối tác", re.IGNORECASE)),
]

MT_CALQUE_RULES = [
    ("CALQUE_HIGHWAY_ROBBERY", re.compile(r"vụ cướp đường cao tốc", re.IGNORECASE)),
    ("CALQUE_FISH_FRY", re.compile(r"con cá bột", re.IGNORECASE)),
    ("CALQUE_ALL_SQUARED_AWAY", re.compile(r"tất cả đã bình phương đi", re.IGNORECASE)),
    ("CALQUE_YOU_BET", re.compile(r"bạn đặt cược", re.IGNORECASE)),
    ("CALQUE_WHITE_LIE", re.compile(r"lời nói dối trắng trợn", re.IGNORECASE)),
    ("CALQUE_RESIGNED_MAN", re.compile(r"người đàn ông từ chức", re.IGNORECASE)),
    ("CALQUE_SHOULDERS_BACK", re.compile(r"vai quay lại", re.IGNORECASE)),
    ("CALQUE_TURNED_BACK_ON", re.compile(r"quay lưng của [^\s]+ lại với", re.IGNORECASE)),
    ("CALQUE_WELL_WELL", re.compile(r"Vâng, tốt\.|Tốt, tốt\.", re.IGNORECASE)),
    ("CALQUE_FIRST_THINGS_FIRST", re.compile(r"điều đầu tiên trước tiên", re.IGNORECASE)),
    ("CALQUE_SAVED_THE_ONE", re.compile(r"cứu người khỏi bữa tiệc", re.IGNORECASE)),
    ("CALQUE_GET_OUT_OF_THERE", re.compile(r"RA KHỎI ĐÓ—!", re.IGNORECASE)),
    ("CALQUE_TREE_SPIRIT", re.compile(r"tinh thần cây tuyết|thần cây tuyết|Tuyết Thụ Linh", re.IGNORECASE)),
    ("CALQUE_FROZEN_RUINS", re.compile(r"tàn tích đông lạnh", re.IGNORECASE)),
    ("CALQUE_MOBILE_WORKSHOP", re.compile(r"hội thảo di động", re.IGNORECASE)),
]

WORLD_TERM_RULES = [
    ("TERM_WELL_OF_WORLDS", re.compile(r"Giếng Thế Giới|Giếng Không Gian|Vạn Giới Tỉnh|\bWell of Worlds\b", re.IGNORECASE)),
    ("TERM_MONOLITH", re.compile(r"Cự Thạch|núi nguyên khối|Thành phố ngàn khối đá|\bMonolith\b", re.IGNORECASE)),
    ("TERM_SOUL_STONE", re.compile(r"Hòn Hồn Thạch|Viên Hồn Thạch|Viên đá Linh hồn|đá linh hồn|\bSoul Stone\b|\bSoulstone\b", re.IGNORECASE)),
    ("TERM_GRACE_IMPERIUM", re.compile(r"Ý Chí Ân Tứ|Kim Khố Ý Chí Ân Tứ", re.IGNORECASE)),
    ("TERM_DUSK_ARBITER", re.compile(r"Trọng Tài Hoàng Hôn|Trọng Tài Chạng Vạng", re.IGNORECASE)),
    ("TERM_NEW_STAR_GUILD", re.compile(r"Hội Ngôi sao Mới|Công Hội Tân Tinh", re.IGNORECASE)),
]

files_to_audit = [
    ("batch:batch_10k_approved.json", "work/batches/batch_10k_approved.json", "json_kv"),
    ("batch:batch_10k_b2_approved.json", "work/batches/batch_10k_b2_approved.json", "json_kv"),
    ("batch:batch_10k_b3_approved.json", "work/batches/batch_10k_b3_approved.json", "json_kv"),
    ("batch:batch_10k_b4_approved.json", "work/batches/batch_10k_b4_approved.json", "json_kv"),
    ("batch:remaining_lua_avg_cache.json", "work/batches/remaining_lua_avg_cache.json", "json_kv"),
    ("batch:dialogue_remaining_avg_approved.json", "work/batches/dialogue_remaining_avg_approved.json", "json_kv"),
    ("campaign:lightnovel_story", "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act1_act2", "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act2_climax", "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act3", "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act3_part1", "work/editorial/act3_part1_story_editorial_20261024_r01/UNIFIED_ACT3_PART1_PROPOSALS.jsonl", "jsonl"),
    ("campaign:act4_final", "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl", "jsonl"),
    ("campaign:side_stories_part1", "work/editorial/side_stories_part1_editorial_20261025_r01/UNIFIED_STSP_PART1_PROPOSALS.jsonl", "jsonl"),
    ("campaign:side_stories_part2", "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part2", "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part3", "work/editorial/event_stories_part3_editorial_20261025_r01/UNIFIED_CAMPAIGN_15_PROPOSALS.jsonl", "jsonl"),
    ("campaign:event_stories_part4", "work/editorial/event_stories_part4_editorial_20261025_r01/UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl", "jsonl"),
    ("campaign:campaign_19_polished", "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl", "jsonl_c19"),
]

def audit():
    total_entries = 0
    total_defective = 0
    cat_counts = Counter()
    sub_counts = Counter()

    for name, rel_path, ftype in files_to_audit:
        full_path = os.path.join(ROOT_DIR, rel_path)
        if not os.path.exists(full_path): continue
        texts = []
        if ftype == "json_kv":
            with open(full_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                texts = [(k, v) for k, v in d.items() if isinstance(v, str)]
        else:
            with open(full_path, "r", encoding="utf-8") as f:
                for lidx, l in enumerate(f):
                    if not l.strip(): continue
                    d = json.loads(l)
                    k = d.get("id") or d.get("scene_id") or f"line_{lidx}"
                    v = d.get("vi") or d.get("vi_editorial") or d.get("polished_vi") or ""
                    if v: texts.append((k, v))
        
        for k, v in texts:
            total_entries += 1
            has_defect = False
            # untrans
            if CJK_REGEX.search(v):
                sub_counts["CJK_LEAK"] += 1
                cat_counts["UNTRANSLATED_LEAK"] += 1
                has_defect = True
            if BINARY_OPCODE_REGEX.search(v):
                sub_counts["BINARY_OPCODE_LEAK"] += 1
                cat_counts["UNTRANSLATED_LEAK"] += 1
                has_defect = True
            # pronoun
            for sub, r in PRONOUN_RULES:
                if r.search(v):
                    sub_counts[sub] += 1
                    cat_counts["PRONOUN_ADDRESSING"] += 1
                    has_defect = True
            # calques
            for sub, r in MT_CALQUE_RULES:
                if r.search(v):
                    sub_counts[sub] += 1
                    cat_counts["MACHINE_TRANSLATION_CALQUE"] += 1
                    has_defect = True
            # world term
            for sub, r in WORLD_TERM_RULES:
                if r.search(v):
                    sub_counts[sub] += 1
                    cat_counts["WORLD_TERMINOLOGY"] += 1
                    has_defect = True
            
            if has_defect:
                total_defective += 1

    print("=" * 60)
    print("AUDIT VERIFICATION SUMMARY POST-REMEDIATION")
    print("=" * 60)
    print(f"Total entries audited: {total_entries}")
    print(f"Total defective lines: {total_defective}")
    print("By category:")
    for cat, c in cat_counts.items():
        print(f"  {cat}: {c}")
    print("By subcategory:")
    for sub, c in sub_counts.items():
        print(f"  {sub}: {c}")
    print("=" * 60)

if __name__ == "__main__":
    audit()
