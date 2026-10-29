import os, json, re

ROOT = r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa"

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

exact_audit_rules = [
    ("TERM_MONOLITH", re.compile(r"Cự Thạch|núi nguyên khối|Thành phố ngàn khối đá|\bMonolith\b", re.IGNORECASE)),
    ("TERM_NEW_STAR_GUILD", re.compile(r"Hội Ngôi sao Mới|Công Hội Tân Tinh", re.IGNORECASE)),
    ("TERM_SOUL_STONE", re.compile(r"Hòn Hồn Thạch|Viên Hồn Thạch|Viên đá Linh hồn|đá linh hồn|\bSoul Stone\b|\bSoulstone\b", re.IGNORECASE)),
    ("TERM_GRACE_IMPERIUM", re.compile(r"Ý Chí Ân Tứ|Kim Khố Ý Chí Ân Tứ", re.IGNORECASE)),
    ("TERM_DUSK_ARBITER", re.compile(r"Trọng Tài Hoàng Hôn|Trọng Tài Chạng Vạng", re.IGNORECASE)),
    ("ARBITER_CALQUE_TRONG_TAI", re.compile(r"Trọng tài (Gerie|Hoàng Hôn|Chạng Vạng)", re.IGNORECASE)),
    ("MENTOR_CALQUE_BAC_SI", re.compile(r"Thưa bác sĩ", re.IGNORECASE)),
    ("PARTNER_CALQUE_BAN_DOI", re.compile(r"bạn đời", re.IGNORECASE)),
    ("PARTY_CALQUE_BUA_TIEC", re.compile(r"bữa tiệc bất ngờ|bữa tiệc tham gia|bữa tiệc ký kết|bữa tiệc đối tác", re.IGNORECASE)),
    ("CAPTAIN_CALQUE_THUYEN_TRUONG", re.compile(r"Thuyền trưởng (Fuyuka|Nazuka|Nazuna|Gerie|Narida)", re.IGNORECASE)),
    ("LADY_CALQUE_BA_ANGIE", re.compile(r"Bà Angie|Quý Cô Angie", re.IGNORECASE)),
    ("BOSS_CALQUE_ONG_CHU", re.compile(r"\bông chủ\b", re.IGNORECASE)),
    ("BOSS_ACCORD_HIEP_DINH", re.compile(r"Hiệp định của ông chủ", re.IGNORECASE)),
    ("BOSS_ACCORD_HALF_TRANSLATED", re.compile(r"Sếp Accord|Hiệp Ước Boss", re.IGNORECASE)),
    ("BOSS_CUA_BAN", re.compile(r"BOSS CỦA BẠN", re.IGNORECASE)),
    ("CALQUE_WELL_WELL", re.compile(r"Vâng, tốt\.|Tốt, tốt\.", re.IGNORECASE)),
    ("CALQUE_FIRST_THINGS_FIRST", re.compile(r"điều đầu tiên trước tiên", re.IGNORECASE)),
    ("CALQUE_HIGHWAY_ROBBERY", re.compile(r"vụ cướp đường cao tốc", re.IGNORECASE)),
    ("CALQUE_SAVED_THE_ONE", re.compile(r"cứu người khỏi bữa tiệc", re.IGNORECASE)),
    ("CALQUE_FISH_FRY", re.compile(r"con cá bột", re.IGNORECASE)),
    ("CALQUE_WHITE_LIE", re.compile(r"lời nói dối trắng trợn", re.IGNORECASE)),
    ("CALQUE_TURNED_BACK_ON", re.compile(r"quay lưng của [^\s]+ lại với", re.IGNORECASE)),
    ("CALQUE_TREE_SPIRIT", re.compile(r"tinh thần cây tuyết|thần cây tuyết|Tuyết Thụ Linh", re.IGNORECASE)),
    ("CALQUE_MOBILE_WORKSHOP", re.compile(r"hội thảo di động", re.IGNORECASE)),
    ("CALQUE_FROZEN_RUINS", re.compile(r"tàn tích đông lạnh", re.IGNORECASE)),
    ("CALQUE_GET_OUT_OF_THERE", re.compile(r"RA KHỎI ĐÓ—!", re.IGNORECASE)),
]

counts = {name: 0 for name, _ in exact_audit_rules}

for _, rel_path, ftype in files_to_audit:
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path): continue
    texts = []
    if ftype == "json_kv":
        with open(full_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            texts = [v for v in d.values() if isinstance(v, str)]
    else:
        with open(full_path, "r", encoding="utf-8") as f:
            for l in f:
                if not l.strip(): continue
                d = json.loads(l)
                t = d.get("vi") or d.get("vi_editorial") or d.get("polished_vi") or ""
                if t: texts.append(t)
    for t in texts:
        for name, regex in exact_audit_rules:
            if regex.search(t):
                counts[name] += 1

print("=== EXACT AUDIT MATCH COUNTS ===")
for name, c in counts.items():
    print(f"{name:30}: {c}")
