import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

# Load manifest if available
manifest_path = ROOT / "work" / "research" / "data_200_manifest.json"
manifest = {}
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

print(f"Manifest has {len(manifest)} entries")

# Check Batch 1
b1 = json.loads((ROOT / "work/batches/BATCH_FIX_01_MECHANISMS_TOKENS.json").read_text(encoding="utf-8"))
# Check Batch 3
b3 = json.loads((ROOT / "work/batches/BATCH_FIX_03_DATA_UNTRANSLATED.json").read_text(encoding="utf-8"))
# Check Batch 6
b6 = json.loads((ROOT / "work/batches/BATCH_FIX_06_POLISH_CANDIDATES.json").read_text(encoding="utf-8"))

# Check all IDs in b1, b3, b6
data_entries = []
for it in b1["entries"]:
    data_entries.append(("b1", it["id"], it["text_vi"]))

for it in b3["entries"]:
    data_entries.append(("b3", it["id"], it["text_vi"]))

for it in b6["entries"]:
    if not it["id"].startswith("root:k"):
        data_entries.append(("b6", it["id"], it["text_vi"]))

print(f"Total data entries to map: {len(data_entries)}")

# Search which .bin file contains which ID
# We know 00552_0x80911df3a563e0f3.bin is the embedded voice table
bin_files = list(ENTRIES_DIR.glob("*.bin"))
print(f"Found {len(bin_files)} bin files in data entries")

# Let's map prefix -> bin file
# We can load bin files and index keys
prefix_to_bins = {}
key_to_bin = {}

# First, check Voice lines for embedded
voice_bin = ENTRIES_DIR / "00552_0x80911df3a563e0f3.bin"
voice_keys = set()
if voice_bin.exists():
    v_data = json.loads(voice_bin.read_text(encoding="utf-8"))
    voice_keys = set(v_data.keys())

# Map keys
missing = []
for batch_tag, kid, text in data_entries:
    if kid in voice_keys:
        key_to_bin[kid] = voice_bin.name
        continue
    # Check other bins
    found = False
    prefix = kid.split(".")[0]
    # Check if we already know the bin for this prefix
    if prefix in prefix_to_bins:
        bfile = prefix_to_bins[prefix]
        bdata = json.loads((ENTRIES_DIR / bfile).read_text(encoding="utf-8"))
        if kid in bdata:
            key_to_bin[kid] = bfile
            found = True
    if not found:
        # scan bins
        for bf in bin_files:
            # Quick check: does the file name match manifest?
            # Or read json
            try:
                bdata = json.loads(bf.read_text(encoding="utf-8"))
                if isinstance(bdata, dict) and kid in bdata:
                    key_to_bin[kid] = bf.name
                    prefix_to_bins[prefix] = bf.name
                    found = True
                    break
            except Exception:
                pass
    if not found:
        missing.append((batch_tag, kid))

print(f"Mapped {len(key_to_bin)} / {len(data_entries)} keys successfully!")
if missing:
    print(f"MISSING ({len(missing)} keys):")
    for btag, kid in missing[:10]:
        print(f"  [{btag}] {kid}")
