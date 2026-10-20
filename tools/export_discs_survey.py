import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries_vi = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
entries_en = ROOT / "work" / "research" / "data_200_pristine_en" / "entries"

item_zh = json.loads((entries_vi / "00900_0xdb546f14f2f79a11.bin").read_text(encoding="utf-8"))
item_vi = json.loads((entries_vi / "00653_0xe60634348b826f41.bin").read_text(encoding="utf-8"))
item_en = json.loads((entries_en / "00653_0xe60634348b826f41.bin").read_text(encoding="utf-8"))

disc_zh = json.loads((entries_vi / "00867_0x5d07838c4787cc54.bin").read_text(encoding="utf-8"))
disc_vi = json.loads((entries_vi / "00620_0x1f924138769d46ec.bin").read_text(encoding="utf-8"))
disc_en = json.loads((entries_en / "00620_0x1f924138769d46ec.bin").read_text(encoding="utf-8"))

disc_ids = sorted(list(set(k.split(".")[1] for k in disc_zh)))

records = []
for did in disc_ids:
    records.append({
        "id": did,
        "tier": did[:3],
        "zh_name": disc_zh.get(f"DiscIP.{did}.3", ""),
        "en_name": disc_en.get(f"DiscIP.{did}.3", ""),
        "cur_discip_name": disc_vi.get(f"DiscIP.{did}.3", ""),
        "cur_item_name": item_vi.get(f"Item.{did}.1", ""),
        "zh_desc": item_zh.get(f"Item.{did}.3", ""),
        "en_desc": item_en.get(f"Item.{did}.3", ""),
        "cur_desc": item_vi.get(f"Item.{did}.3", "")
    })

out_p = ROOT / "work" / "batches" / "all_104_discs_survey.json"
out_p.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(records)} discs to {out_p.name}!")

# Sample check from each tier
for tier in ["211", "212", "213", "214"]:
    tier_recs = [r for r in records if r["tier"] == tier]
    print(f"\n=== TIER {tier} (Total: {len(tier_recs)}) ===")
    for r in tier_recs[:3]:
        print(f"{r['id']} | ZH: {r['zh_name']:12} | EN: {r['en_name']:22} | DiscIP: {r['cur_discip_name']:20} | Item: {r['cur_item_name']}")
