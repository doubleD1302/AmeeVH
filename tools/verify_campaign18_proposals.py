import json, re, sys

PATH_A = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PROPOSALS_PARTITION_A.jsonl"
PATH_B = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PROPOSALS_PARTITION_B.jsonl"
PATH_ALL_SRC = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/CAMPAIGN_18_SOURCE_ALL.json"
OUT_UNIFIED = "StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/UNIFIED_CAMPAIGN_18_PROPOSALS.jsonl"

print("=== STARTING INDEPENDENT QA AUDIT FOR CAMPAIGN 18 ===")

with open(PATH_ALL_SRC, "r", encoding="utf-8") as f:
    src_all = json.load(f)
src_map = {x["id"]: x for x in src_all}
print(f"Loaded master source: {len(src_all)} items.")

items_a = []
with open(PATH_A, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            items_a.append(json.loads(line))
print(f"Loaded Partition A: {len(items_a)} items.")

items_b = []
with open(PATH_B, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            items_b.append(json.loads(line))
print(f"Loaded Partition B: {len(items_b)} items.")

combined = items_a + items_b
print(f"Total Combined Proposals: {len(combined)} items.")

blockers = []
majors = []
minors = []

# 1. Total items check
if len(combined) != len(src_all):
    blockers.append(f"Item count mismatch: expected {len(src_all)}, got {len(combined)}")

# 2. Key/ID presence
seen_ids = set()
for item in combined:
    iid = item["id"]
    if iid in seen_ids:
        blockers.append(f"Duplicate proposal ID: {iid}")
    seen_ids.add(iid)
    if iid not in src_map:
        blockers.append(f"Unknown proposal ID not in source: {iid}")

missing_ids = set(src_map.keys()) - seen_ids
if missing_ids:
    blockers.append(f"Missing {len(missing_ids)} items from source. Sample: {list(missing_ids)[:5]}")

# 3. Token preservation
TAG_PATTERN = re.compile(r'<[^>]+>|==[a-zA-Z0-9_.-]+==|\{[0-9]+\}|_NOT_IN_LOG_')

for item in combined:
    iid = item["id"]
    en = item["en"]
    vi = item["proposed_vi"]

    src_tokens = TAG_PATTERN.findall(en)
    tgt_tokens = TAG_PATTERN.findall(vi)

    if src_tokens != tgt_tokens:
        blockers.append(f"Token mismatch [{iid}]:\n  EN: {src_tokens}\n  VI: {tgt_tokens}")

# 4. Banned terms check
BANNED_BLOCKERS = [
    (r"chết tiệt", "Chết tiệt (Banned calque)"),
    (r"cái quái gì", "Cái quái gì (Banned calque)"),
    (r"làm sao mà", "Làm sao mà (Banned calque)"),
    (r"bạn biết đấy", "Bạn biết đấy (Banned calque)"),
    (r"khoảng không quảng cáo", "Khoảng không quảng cáo (Banned MT)"),
    (r"chụp nhanh bộ nhớ", "Chụp nhanh bộ nhớ (Banned MT)"),
    (r"Bạo Quân", "Bạo Quân (Phải là Bạo Chúa)"),
    (r"Ma Vương", "Ma Vương (Banned MT)"),
    (r"người đi bộ", "Người đi bộ (Phải là Du Hành Giả)"),
    (r"Hội Ngôi Sao Mới", "Hội Ngôi Sao Mới (Phải là Lữ Đoàn Tân Tinh)"),
    (r"Hiệp hội Ngôi sao Mới", "Hiệp hội Ngôi sao Mới (Phải là Lữ Đoàn Tân Tinh)"),
    (r"Hổ phách", "Hổ phách (Phải là Amber)"),
    (r"Diên vĩ", "Diên vĩ (Phải là Iris)"),
    (r"\bLiễu\b", "Liễu (Phải giữ tên riêng Willow)"),
]

for item in combined:
    iid = item["id"]
    vi = item["proposed_vi"]
    for pat, desc in BANNED_BLOCKERS:
        if re.search(pat, vi):
            majors.append(f"Banned term [{iid}] ({desc}): {vi}")

# 5. Untranslated check
for item in combined:
    iid = item["id"]
    en = item["en"].strip()
    vi = item["proposed_vi"].strip()
    # Check if identical to EN and has > 2 words and not kinetic typography
    if en == vi and len(en.split()) > 2 and "_NOT_IN_LOG_" not in en:
        minors.append(f"Untranslated sentence [{iid}]: {en}")

print("\n=== AUDIT RESULTS ===")
print(f"Blockers: {len(blockers)}")
for b in blockers[:10]:
    print(f"  [BLOCKER] {b}")

print(f"Majors: {len(majors)}")
for m in majors[:10]:
    print(f"  [MAJOR] {m}")

print(f"Minors: {len(minors)}")
for mi in minors[:10]:
    print(f"  [MINOR] {mi}")

if blockers or majors or minors:
    print("\n>>> AUDIT FAILED! Please resolve all defects before proceeding. <<<")
    sys.exit(1)

print("\n>>> AUDIT PASSED WITH ZERO DEFECTS! <<<")

# Write UNIFIED file
with open(OUT_UNIFIED, "w", encoding="utf-8") as f:
    for item in combined:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Unified deliverable successfully written to {OUT_UNIFIED} ({len(combined)} items)")
