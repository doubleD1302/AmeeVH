import json, re

with open("StellaSora_VietHoa/work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/PARTITION_A_SOURCE.json", "r", encoding="utf-8") as f:
    pa = json.load(f)

for sc in sorted(list(set(x["scene_id"] for x in pa))):
    print("=" * 20, sc, "=" * 20)
    items = [x for x in pa if x["scene_id"] == sc]
    for x in items:
        # print all titles, summaries, or lines with common keywords
        line_num = int(x["id"].split(".")[1])
        if line_num <= 10 or any(k in x["current_vi"].lower() for k in ["hội", "người đi bộ", "hổ phách", "chết tiệt", "quái gì", "bạn biết đấy", "tiện lợi", "bỏ cuộc"]):
            print(f"[{x['id']}] EN: {x['en']}")
            print(f"    VI: {x['current_vi']}")
