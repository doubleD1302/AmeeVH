import json
import os
import re
import hashlib

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

run_id = "phone_messages_editorial_20261024_r01"
run_dir = f"StellaSora_VietHoa/work/runs/{run_id}"
subagent_base = f"StellaSora_VietHoa/work/subagents/{run_id}"

os.makedirs(run_dir, exist_ok=True)
for sub in ["catalog_engineer", "translator_phone_a", "translator_phone_b", "qa_reviewer_phone"]:
    os.makedirs(os.path.join(subagent_base, sub), exist_ok=True)

# Load batch files
with open("StellaSora_VietHoa/work/batches/batch_10k_partB_mainstory3_phone.json", "r", encoding="utf-8") as f:
    b_partB = json.load(f)
with open("StellaSora_VietHoa/work/batches/batch_10k_b3_partC.json", "r", encoding="utf-8") as f:
    b_partC = json.load(f)

# Combine all PM lines
all_pm_lines = {}
for k, v in b_partB.items():
    if k.startswith("PM"):
        all_pm_lines[k] = v
for k, v in b_partC.items():
    if k.startswith("PM"):
        all_pm_lines[k] = v

print(f"Total PM lines extracted: {len(all_pm_lines)}")

# Group lines by scene ID (e.g. PM10301)
scene_map = {}
for lid, en_text in all_pm_lines.items():
    # lid format: PM10301.1
    sc_id = lid.split(".")[0]
    num = int(lid.split(".")[1]) if "." in lid and lid.split(".")[1].isdigit() else 0
    scene_map.setdefault(sc_id, []).append((num, lid, en_text))

# Sort each scene lines by line index
for sc_id in scene_map:
    scene_map[sc_id].sort(key=lambda x: x[0])

# Character mapping for phone messages
char_meta = {
    "103": ("Amber", "Amber năng nổ, nhiệt tình, ấm áp, nhắn tin biểu cảm, dùng nhiều emoji và dấu chấm than (!), coi Player là người bạn đồng hành đáng tin cậy."),
    "107": ("Tilia", "Tilia công chúa kỵ sĩ thanh cao, ban đầu nhắn tin nghiêm túc như viết báo cáo chính thức, sau đó dần bộc lộ sự ngượng ngùng, dễ thương khi nhắn tin thân thiết."),
    "108": ("Kasimira", "Kasimira tiểu thư quý tộc kiêu kỳ, tự tin, nhắn tin sang chảnh nhưng ẩn chứa sự quan tâm sâu sắc, thích nói về bói toán, điềm may."),
    "110": ("Firenze", "Firenze phong thái quý phái, sắc sảo, tự tin, nhắn tin hóm hỉnh, khéo léo."),
    "111": ("Iris", "Iris dịu dàng, chu đáo, tinh tế, thường xuyên nhắn tin nhắc nhở giờ giấc ăn uống, lo toan tài chính, chỗ dựa vững chắc."),
    "112": ("Noya", "Noya thợ máy lanh lợi, nhí nhảnh, yêu xe cộ, gọi 'Boss' đầy tinh nghịch, nhắn tin hào hứng và dứt khoát."),
    "113": ("Shimiao", "Shimiao trầm tĩnh, đáng tin cậy, giọng điệu điềm đạm, ấm áp."),
    "114": ("Chaton", "Chaton hoạt bát, vui nhộn, thích động vật và những điều nhỏ bé dễ thương."),
    "115": ("Firefly", "Firefly nhẹ nhàng, kín đáo, giọng điệu bay bổng, giàu chất thơ."),
    "116": ("Ridge", "Ridge điềm đạm, thực tế, gắn bó với đất đai nông trại, nói chuyện chân thành."),
    "117": ("Jinglin", "Jinglin kiếm khách kiêm đầu bếp điềm đạm, thanh nhã, nhắn tin ngắn gọn, súc tích, tinh tế."),
    "118": ("Coronis", "Coronis bác sĩ phòng khám ngầm sắc sảo, nghiêm khắc, hài hước thâm thúy (deadpan), hay trêu chọc về sức khỏe."),
    "119": ("Nanoha", "Nanoha hồn nhiên, dễ thương, nhí nhảnh, giàu tình cảm."),
    "120": ("Canace", "Canace nhã nhặn, thông thái, lịch thiệp, câu từ mực thước.")
}

tech_patterns = [
    r"^SetPhoneMsgChoiceBegin$", r"^SetPhoneMsgChoiceJumpTo$",
    r"^SetPhoneMsgChoiceRollover$", r"^SetPhoneMsgChoiceEnd$",
    r"^SetPhoneMsg"
]

def is_tech(s):
    return any(re.search(p, s) for p in tech_patterns)

scenes_a_list = []
scenes_b_list = []

for sc_id, line_tuples in sorted(scene_map.items()):
    char_id = sc_id[2:5]
    char_name, voice_hint = char_meta.get(char_id, ("Trekker", "Standard Light Novel text messaging"))
    
    scene_obj = {
        "scene_id": sc_id,
        "character": char_name,
        "voice_hint": voice_hint,
        "line_count": len(line_tuples),
        "lines": []
    }
    
    for _, lid, en_text in line_tuples:
        tokens = []
        for m in re.findall(r"==[A-Z0-9_]+==|<[^>]+>|\{[0-9]+\}", en_text):
            if m not in tokens:
                tokens.append(m)
        line_obj = {
            "id": lid,
            "speaker": char_name if not is_tech(en_text) else "System",
            "en": en_text,
            "is_tech": is_tech(en_text),
            "tokens": tokens
        }
        scene_obj["lines"].append(line_obj)

    # Split into Partition A (103..112) and Partition B (113..120)
    if int(char_id) <= 112:
        scenes_a_list.append(scene_obj)
    else:
        scenes_b_list.append(scene_obj)

part_a_data = {
    "schema": "stella_sora.phone_messages_partition.v1",
    "partition_id": "PARTITION_PM_A",
    "run_id": run_id,
    "assigned_role": "TRANSLATOR_PHONE_A",
    "scope_description": "Core Companions Instant Messaging (Amber, Tilia, Kasimira, Firenze, Iris, Noya)",
    "total_scenes": len(scenes_a_list),
    "total_lines": sum(s["line_count"] for s in scenes_a_list),
    "scenes": scenes_a_list
}

part_b_data = {
    "schema": "stella_sora.phone_messages_partition.v1",
    "partition_id": "PARTITION_PM_B",
    "run_id": run_id,
    "assigned_role": "TRANSLATOR_PHONE_B",
    "scope_description": "Allies & City Companions Instant Messaging (Shimiao, Chaton, Firefly, Ridge, Jinglin, Coronis, Nanoha, Canace)",
    "total_scenes": len(scenes_b_list),
    "total_lines": sum(s["line_count"] for s in scenes_b_list),
    "scenes": scenes_b_list
}

part_a_path = os.path.join(subagent_base, "translator_phone_a", "PARTITION_PM_A_CANDIDATES.json")
with open(part_a_path, "w", encoding="utf-8") as f:
    json.dump(part_a_data, f, ensure_ascii=False, indent=2)

part_b_path = os.path.join(subagent_base, "translator_phone_b", "PARTITION_PM_B_CANDIDATES.json")
with open(part_b_path, "w", encoding="utf-8") as f:
    json.dump(part_b_data, f, ensure_ascii=False, indent=2)

print(f"Created PARTITION_PM_A: {len(scenes_a_list)} scenes, {part_a_data['total_lines']} lines (SHA256: {sha256_file(part_a_path)[:16]}...)")
print(f"Created PARTITION_PM_B: {len(scenes_b_list)} scenes, {part_b_data['total_lines']} lines (SHA256: {sha256_file(part_b_path)[:16]}...)")

# Build RUN.json
run_packet = {
    "schema": 1,
    "run_id": run_id,
    "campaign_name": "Stella Sora Phone Messages Light Novel Relocalization",
    "total_scenes": len(scene_map),
    "total_lines": len(all_pm_lines),
    "status": "in_progress",
    "tasks": [
        {
            "task_id": "translator_phone_a",
            "role": "TRANSLATOR_PHONE_A",
            "candidate_file": part_a_path,
            "scenes": len(scenes_a_list),
            "lines": part_a_data["total_lines"],
            "status": "ready"
        },
        {
            "task_id": "translator_phone_b",
            "role": "TRANSLATOR_PHONE_B",
            "candidate_file": part_b_path,
            "scenes": len(scenes_b_list),
            "lines": part_b_data["total_lines"],
            "status": "ready"
        },
        {
            "task_id": "qa_reviewer_phone",
            "role": "LOCALIZATION_QA_REVIEWER_PHONE",
            "status": "ready_standby"
        }
    ]
}

with open(os.path.join(run_dir, "RUN.json"), "w", encoding="utf-8") as f:
    json.dump(run_packet, f, ensure_ascii=False, indent=2)

print("RUN.json initialized for Phone Messages campaign.")
