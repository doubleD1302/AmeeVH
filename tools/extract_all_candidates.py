import json
import os
import re

entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"
batches_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches"

# Load CN table mapping
cn_tables = {}
for fname in os.listdir(entries_dir):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(entries_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and len(d) > 0:
            first_k = list(d.keys())[0]
            tbl_name = first_k.split(".")[0]
            first_v = str(list(d.values())[0])
            has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in first_v)
            if has_cn:
                cn_tables[tbl_name] = fpath
    except Exception:
        pass

def get_cn_dict(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Load current master glossary
master_glossary_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\config\master_glossary.json"
with open(master_glossary_path, "r", encoding="utf-8") as f:
    master_glossary = json.load(f)

existing_terms = master_glossary.get("terms", {})
existing_terms_lower = {k.lower(): (k, v) for k, v in existing_terms.items()}

# Load 4 pillars
with open(os.path.join(batches_dir, "pillar1_dungeons_monsters.json"), "r", encoding="utf-8") as f: p1 = json.load(f)
with open(os.path.join(batches_dir, "pillar2_voices_characters.json"), "r", encoding="utf-8") as f: p2 = json.load(f)
with open(os.path.join(batches_dir, "pillar3_story_dating_quests.json"), "r", encoding="utf-8") as f: p3 = json.load(f)
with open(os.path.join(batches_dir, "pillar4_system_gacha_shops.json"), "r", encoding="utf-8") as f: p4 = json.load(f)

candidates = {}

def add_candidate(source_en, cn_text, category, table_source, notes=""):
    source_en = source_en.strip()
    if not source_en or len(source_en) > 60:
        return
    # Check if generic number or placeholder
    if source_en in ["!NONEED!", "None", "NULL", "Null"] or source_en.isdigit():
        return
    if source_en.lower() in existing_terms_lower:
        return # Already in master glossary
    
    if source_en not in candidates:
        candidates[source_en] = {
            "en": source_en,
            "cn": cn_text.strip() if cn_text else "",
            "category": category,
            "table": table_source,
            "notes": notes
        }

# ==================== PILLAR 1 ====================
# 1. MonsterManual
mm_cn = get_cn_dict("MonsterManual")
for k, v in p1.get("MonsterManual", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, mm_cn.get(k, ""), "Quái vật & Boss", "MonsterManual")

# 2. RegionBoss & RegionBossAffix
rb_cn = get_cn_dict("RegionBoss")
for k, v in p1.get("RegionBoss", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, rb_cn.get(k, ""), "Boss Khu Vực", "RegionBoss")

rba_cn = get_cn_dict("RegionBossAffix")
for k, v in p1.get("RegionBossAffix", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, rba_cn.get(k, ""), "Chiêu Thức Boss", "RegionBossAffix")

# 3. TravelerDuelBoss & TravelerDuelChallengeAffix
tdb_cn = get_cn_dict("TravelerDuelBoss")
for k, v in p1.get("TravelerDuelBoss", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, tdb_cn.get(k, ""), "Đấu Trường Lữ Khách", "TravelerDuelBoss")

tdca_cn = get_cn_dict("TravelerDuelChallengeAffix")
for k, v in p1.get("TravelerDuelChallengeAffix", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, tdca_cn.get(k, ""), "Từ Tố & Kỹ Năng Boss", "TravelerDuelChallengeAffix")

# 4. SoldierPotential
sp_cn = get_cn_dict("SoldierPotential")
for k, v in p1.get("SoldierPotential", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, sp_cn.get(k, ""), "Thiên Phú Quân Cờ", "SoldierPotential")

# 5. TowerDefensePotential & TowerDefenseItem
tdp_cn = get_cn_dict("TowerDefensePotential")
for k, v in p1.get("TowerDefensePotential", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, tdp_cn.get(k, ""), "Tiềm Năng Thủ Thành", "TowerDefensePotential")

tdi_cn = get_cn_dict("TowerDefenseItem")
for k, v in p1.get("TowerDefenseItem", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, tdi_cn.get(k, ""), "Đạo Cụ Thủ Thành", "TowerDefenseItem")

# 6. JointDrillLevel
jdl_cn = get_cn_dict("JointDrillLevel")
for k, v in p1.get("JointDrillLevel", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, jdl_cn.get(k, ""), "Phụ Bản Liên Hợp", "JointDrillLevel")

# ==================== PILLAR 2 ====================
# 1. CharacterSkin
csk_cn = get_cn_dict("CharacterSkin")
for k, v in p2.get("CharacterSkin", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, csk_cn.get(k, ""), "Trang Phục Nhân Vật", "CharacterSkin")

# 2. CharacterTag
ct_cn = get_cn_dict("CharacterTag")
for k, v in p2.get("CharacterTag", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, ct_cn.get(k, ""), "Đặc Tính & Nhãn Nhân Vật", "CharacterTag")

# 3. CharacterArchiveVoice categories
cav_cn = get_cn_dict("CharacterArchiveVoice")
for k, v in p2.get("CharacterArchiveVoice", {}).get("entries", {}).items():
    if k.endswith(".1"):
        # Strip trailing numbers like 1, 2, 3 to get base cue title
        base_cue = re.sub(r"\s+\d+$", "", v)
        base_cn = re.sub(r"\d+$", "", cav_cn.get(k, ""))
        add_candidate(base_cue, base_cn, "Phân Loại Lồng Tiếng", "CharacterArchiveVoice")
        add_candidate(v, cav_cn.get(k, ""), "Phân Loại Lồng Tiếng", "CharacterArchiveVoice")

# ==================== PILLAR 3 ====================
# 1. DatingLandmark
dl_cn = get_cn_dict("DatingLandmark")
for k, v in p3.get("DatingLandmark", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, dl_cn.get(k, ""), "Địa Danh Hẹn Hò", "DatingLandmark")

# 2. NPCConfig
npc_cn = get_cn_dict("NPCConfig")
for k, v in p3.get("NPCConfig", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, npc_cn.get(k, ""), "Nhân Vật NPC", "NPCConfig")

# 3. NPCAffinityPlot
nap_cn = get_cn_dict("NPCAffinityPlot")
for k, v in p3.get("NPCAffinityPlot", {}).get("entries", {}).items():
    if k.endswith(".2"):
        add_candidate(v, nap_cn.get(k, ""), "Cốt Truyện NPC", "NPCAffinityPlot")

# ==================== PILLAR 4 ====================
# 1. Force & ContentWord
f_cn = get_cn_dict("Force")
for k, v in p4.get("Force", {}).get("entries", {}).items():
    add_candidate(v, f_cn.get(k, ""), "Thế Lực & Tổ Chức", "Force")

cw_cn = get_cn_dict("ContentWord")
for k, v in p4.get("ContentWord", {}).get("entries", {}).items():
    add_candidate(v, cw_cn.get(k, ""), "Thế Lực & Lore", "ContentWord")

# 2. Honor & Title
h_cn = get_cn_dict("Honor")
for k, v in p4.get("Honor", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, h_cn.get(k, ""), "Huy Hiệu & Danh Hiệu", "Honor")

t_cn = get_cn_dict("Title")
for k, v in p4.get("Title", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, t_cn.get(k, ""), "Danh Xưng Người Chơi", "Title")

# 3. Gacha & GachaType
g_cn = get_cn_dict("Gacha")
for k, v in p4.get("Gacha", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, g_cn.get(k, ""), "Kỳ Chiêu Mộ Gacha", "Gacha")

gt_cn = get_cn_dict("GachaType")
for k, v in p4.get("GachaType", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, gt_cn.get(k, ""), "Loại Banner Gacha", "GachaType")

# 4. MallShop & MallMonthlyCard & MallRecommendGroup
ms_cn = get_cn_dict("MallShop")
for k, v in p4.get("MallShop", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, ms_cn.get(k, ""), "Vật Phẩm Cửa Hàng", "MallShop")

mmc_cn = get_cn_dict("MallMonthlyCard")
for k, v in p4.get("MallMonthlyCard", {}).get("entries", {}).items():
    if k.endswith(".1") or k.endswith(".3"):
        add_candidate(v, mmc_cn.get(k, ""), "Thẻ Tháng & Gói Cước", "MallMonthlyCard")

mrg_cn = get_cn_dict("MallRecommendGroup")
for k, v in p4.get("MallRecommendGroup", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, mrg_cn.get(k, ""), "Phân Mục Cửa Hàng", "MallRecommendGroup")

# 5. AgentTab
at_cn = get_cn_dict("AgentTab")
for k, v in p4.get("AgentTab", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, at_cn.get(k, ""), "Hệ Thống Ủy Thác", "AgentTab")

# 6. SubNoteSkill & VampireTalent
sns_cn = get_cn_dict("SubNoteSkill")
for k, v in p4.get("SubNoteSkill", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, sns_cn.get(k, ""), "Kỹ Năng Đĩa Nhạc", "SubNoteSkill")

vt_cn = get_cn_dict("VampireTalent")
for k, v in p4.get("VampireTalent", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, vt_cn.get(k, ""), "Thiên Phú Sinh Tồn", "VampireTalent")

# 7. Production & ProductionType
pt_cn = get_cn_dict("ProductionType")
for k, v in p4.get("ProductionType", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, pt_cn.get(k, ""), "Phân Loại Chế Tạo", "ProductionType")

prod_cn = get_cn_dict("Production")
for k, v in p4.get("Production", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, prod_cn.get(k, ""), "Vật Phẩm Chế Tạo Đặc Biệt", "Production")

# 8. PenguinCardHandRank & GoldenSpyItem
pchr_cn = get_cn_dict("PenguinCardHandRank")
for k, v in p4.get("PenguinCardHandRank", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, pchr_cn.get(k, ""), "Thứ Hạng Bài Cánh Cụt", "PenguinCardHandRank")

gsi_cn = get_cn_dict("GoldenSpyItem")
for k, v in p4.get("GoldenSpyItem", {}).get("entries", {}).items():
    if k.endswith(".1"):
        add_candidate(v, gsi_cn.get(k, ""), "Đạo Cụ Gián Điệp Hoàng Kim", "GoldenSpyItem")

# 9. BoardNPC
bnpc_cn = get_cn_dict("BoardNPC")
for k, v in p4.get("BoardNPC", {}).get("entries", {}).items():
    add_candidate(v, bnpc_cn.get(k, ""), "Nhân Vật Tương Tác Bảng Tin", "BoardNPC")

print(f"\nTotal extracted new candidates: {len(candidates)}")

# Group candidates by category
by_cat = {}
for c in candidates.values():
    cat = c["category"]
    by_cat.setdefault(cat, []).append(c)

for cat, items in sorted(by_cat.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {cat:30}: {len(items):4} candidates")

# Save candidates to a temporary json file for analysis
out_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\candidates_survey.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(candidates, f, ensure_ascii=False, indent=2)
print(f"Saved candidates to {out_path}")
