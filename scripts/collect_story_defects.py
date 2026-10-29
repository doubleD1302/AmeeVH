import os
import json
import re
import glob
from collections import defaultdict, Counter

ROOT = r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
OUT_DIR = os.path.join(ROOT, r"work\subagents\remediation_v110_20261029_r01\story")
os.makedirs(OUT_DIR, exist_ok=True)

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

id_to_en = {}
for f in glob.glob(os.path.join(ROOT, r"work\editorial\**\*PROPOSALS*.jsonl"), recursive=True):
    try:
        with open(f, "r", encoding="utf-8") as fp:
            for l in fp:
                d = json.loads(l)
                if d.get("id") and d.get("en"):
                    id_to_en[d["id"]] = d["en"]
    except Exception:
        pass

binary_defects = []
cjk_defects = []
en_defects = []
all_defects = []

for name, rel_path, ftype in files_to_audit:
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        print(f"Skipping missing file: {rel_path}")
        continue
    if ftype == "json_kv":
        with open(full_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k, v in d.items():
            if not isinstance(v, str): continue
            en_text = k if len(k) > 10 and not k.startswith(("ST", "BB", "CG", "DP", "PM", "CharacterArchive")) else id_to_en.get(k, "")
            item = {"file": name, "rel_path": rel_path, "type": ftype, "id": k, "en": en_text, "vi": v}
            has_defect = False
            if BINARY_OPCODE_REGEX.search(v):
                binary_defects.append(item)
                has_defect = True
            if CJK_REGEX.search(v):
                cjk_defects.append(item)
                has_defect = True
            clean_vi = re.sub(r"<[^>]+>|==[^=]+==|[^\w\s]", " ", v).strip().lower()
            words = clean_vi.split()
            if words and not words[0].startswith(("ep_", "story_", "se_", "avg_", "bgm_")):
                en_cnt = sum(1 for w in words if w in EN_STOPWORDS)
                has_vi_diacritics = any(c in v for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")
                if len(words) >= 4 and (en_cnt / len(words) >= 0.28 or en_cnt >= 3) and not has_vi_diacritics:
                    en_defects.append(item)
                    has_defect = True
                elif en_text and v.strip() == en_text.strip() and len(words) >= 4 and not has_vi_diacritics:
                    en_defects.append(item)
                    has_defect = True
    elif ftype == "jsonl":
        with open(full_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip(): continue
                d = json.loads(line)
                k = d.get("id") or d.get("scene_id") or f"line_{line_idx}"
                en_text = d.get("en", "") or id_to_en.get(k, "")
                vi_text = d.get("vi") or d.get("vi_editorial") or ""
                is_tech = d.get("is_tech", False)
                item = {"file": name, "rel_path": rel_path, "type": ftype, "line_idx": line_idx, "id": k, "en": en_text, "vi": vi_text, "key_field": "vi" if "vi" in d else "vi_editorial"}
                if BINARY_OPCODE_REGEX.search(vi_text):
                    binary_defects.append(item)
                if CJK_REGEX.search(vi_text):
                    cjk_defects.append(item)
                if not is_tech:
                    clean_vi = re.sub(r"<[^>]+>|==[^=]+==|[^\w\s]", " ", vi_text).strip().lower()
                    words = clean_vi.split()
                    if words and not words[0].startswith(("ep_", "story_", "se_", "avg_", "bgm_")):
                        en_cnt = sum(1 for w in words if w in EN_STOPWORDS)
                        has_vi_diacritics = any(c in vi_text for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")
                        if len(words) >= 4 and (en_cnt / len(words) >= 0.28 or en_cnt >= 3) and not has_vi_diacritics:
                            en_defects.append(item)
                        elif en_text and vi_text.strip() == en_text.strip() and len(words) >= 4 and not has_vi_diacritics:
                            en_defects.append(item)
    elif ftype == "jsonl_c19":
        with open(full_path, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f):
                if not line.strip(): continue
                d = json.loads(line)
                k = f"global_id_{d.get('global_id')}"
                en_text = d.get("en", "")
                vi_text = d.get("polished_vi") or d.get("original_vi") or ""
                item = {"file": name, "rel_path": rel_path, "type": ftype, "line_idx": line_idx, "id": k, "en": en_text, "vi": vi_text, "key_field": "polished_vi" if "polished_vi" in d else "original_vi"}
                if BINARY_OPCODE_REGEX.search(vi_text):
                    binary_defects.append(item)
                if CJK_REGEX.search(vi_text):
                    cjk_defects.append(item)
                clean_vi = re.sub(r"<[^>]+>|==[^=]+==|[^\w\s]", " ", vi_text).strip().lower()
                words = clean_vi.split()
                if words and not words[0].startswith(("ep_", "story_", "se_", "avg_", "bgm_")):
                    en_cnt = sum(1 for w in words if w in EN_STOPWORDS)
                    has_vi_diacritics = any(c in vi_text for c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")
                    if len(words) >= 4 and (en_cnt / len(words) >= 0.28 or en_cnt >= 3) and not has_vi_diacritics:
                        en_defects.append(item)
                    elif en_text and vi_text.strip() == en_text.strip() and len(words) >= 4 and not has_vi_diacritics:
                        en_defects.append(item)

print(f"Total binary defects found: {len(binary_defects)}")
print(f"Total cjk defects found: {len(cjk_defects)}")
print(f"Total en defects found: {len(en_defects)}")

with open(os.path.join(OUT_DIR, "binary_defects.json"), "w", encoding="utf-8") as f:
    json.dump(binary_defects, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT_DIR, "cjk_defects.json"), "w", encoding="utf-8") as f:
    json.dump(cjk_defects, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT_DIR, "en_defects.json"), "w", encoding="utf-8") as f:
    json.dump(en_defects, f, ensure_ascii=False, indent=2)
print("Finished collecting defects.")
