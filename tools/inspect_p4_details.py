import json
import os

batches_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches"

def inspect_table_fields(pillar_file, table_names):
    p = os.path.join(batches_dir, pillar_file)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n==================== {pillar_file} ====================")
    for tbl in table_names:
        if tbl not in data:
            print(f"Table {tbl} not found!")
            continue
        entries = data[tbl].get("entries", {})
        print(f"\n--- {tbl} (Total {len(entries)} entries) ---")
        groups = {}
        for k, v in entries.items():
            parts = k.split(".")
            row_id = parts[1] if len(parts) > 1 else parts[0]
            field_id = parts[2] if len(parts) > 2 else "1"
            if row_id not in groups:
                groups[row_id] = {}
            groups[row_id][field_id] = v
        for row_id in list(groups.keys())[:5]:
            print(f"  Row {row_id}:")
            for fid, val in sorted(groups[row_id].items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]):
                val_snippet = val.replace("\n", "\\n")
                if len(val_snippet) > 80:
                    val_snippet = val_snippet[:80] + "..."
                print(f"    .{fid} = {val_snippet}")

inspect_table_fields("pillar4_system_gacha_shops.json", [
    "DiscIP", "Gacha", "GachaType", "Honor", "Title", "Force", 
    "ContentWord", "Character", "MallShop", "MallRecommendGroup", 
    "DictionaryTopBarEntry", "DictionaryEntry", "DictionaryTab", "AgentTab"
])
