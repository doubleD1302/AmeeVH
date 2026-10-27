import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")

# 1. Update batch_10k_approved.json
p1 = ROOT / "work/batches/batch_10k_approved.json"
if p1.exists():
    d = json.loads(p1.read_text(encoding="utf-8"))
    d["STm03_00_b.35"] = "==PLAYER_NAME==, cậu không cần phải tự dằn vặt chuyện tụi này giao dịch linh hồn đâu."
    d["STm03_00_b.37"] = "Noya và Iris cũng nghĩ thế cả thôi. Cậu đã đứng ra che chắn cho tụi này, tụi này đâu thể để cậu một mình gánh chịu hiểm nguy được."
    d["STm03_00_b.38"] = "Cảm ơn cậu nhé, Amber."
    d["STm01_07.112"] = "Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của cậu, ==PLAYER_NAME== ơi!"
    p1.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Updated batch_10k_approved.json")

# 2. Update remaining_lua_avg_cache.json and dialogue_remaining_avg_approved.json
fix_map = {
    'The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It\'s called "Promotion."':
        'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên "Phong Cấp".',
    'The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It\'s called "Oracle."':
        'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên "Thần Dụ".',
}

for fname in ["remaining_lua_avg_cache.json", "dialogue_remaining_avg_approved.json"]:
    pf = ROOT / "work/batches" / fname
    if pf.exists():
        d = json.loads(pf.read_text(encoding="utf-8"))
        for k, v in fix_map.items():
            if k in d:
                d[k] = v
        pf.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Updated {fname}")

# 3. Update UNIFIED_ACT1_ACT2_PROPOSALS.jsonl
p_act = ROOT / "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl"
if p_act.exists():
    lines = p_act.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if not line.strip(): continue
        obj = json.loads(line)
        sid = obj.get("id")
        if sid == "STm03_00_b.35":
            obj["vi_editorial"] = "==PLAYER_NAME==, cậu không cần phải tự dằn vặt chuyện tụi này giao dịch linh hồn đâu."
        elif sid == "STm03_00_b.37":
            obj["vi_editorial"] = "Noya và Iris cũng nghĩ thế cả thôi. Cậu đã đứng ra che chắn cho tụi này, tụi này đâu thể để cậu một mình gánh chịu hiểm nguy được."
        elif sid == "STm03_00_b.38":
            obj["vi_editorial"] = "Cảm ơn cậu nhé, Amber."
        new_lines.append(json.dumps(obj, ensure_ascii=False))
    p_act.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("Updated UNIFIED_ACT1_ACT2_PROPOSALS.jsonl")

# 4. Update UNIFIED_CAMPAIGN_19_POLISHED.jsonl
p19 = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl"
if p19.exists():
    lines = p19.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if not line.strip(): continue
        obj = json.loads(line)
        gid = obj.get("global_id")
        if gid == 15582:
            obj["polished_vi"] = 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên "Thần Dụ".'
            obj["modified"] = True
        elif gid == 15583:
            obj["polished_vi"] = 'Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên "Phong Cấp".'
            obj["modified"] = True
        new_lines.append(json.dumps(obj, ensure_ascii=False))
    p19.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("Updated UNIFIED_CAMPAIGN_19_POLISHED.jsonl")

print("All source updates complete.")
