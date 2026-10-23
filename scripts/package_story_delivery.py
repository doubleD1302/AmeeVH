import zipfile
import os
import hashlib

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

zip_out = "StellaSora_VietHoa/dist/StellaSora_Story_LightNovel_VI_20261024_r02.zip"

files_to_pack = [
    ("UNIFIED_STORY_PROPOSALS.jsonl", "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"),
    ("STORY_COVERAGE.json", "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02/STORY_COVERAGE.json"),
    ("EDITORIAL_DECISION_LOG.jsonl", "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02/EDITORIAL_DECISION_LOG.jsonl"),
    ("CHECKPOINT_STORY.json", "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02/CHECKPOINT_STORY.json"),
    ("RUN.json", "StellaSora_VietHoa/work/runs/lightnovel_editorial_20261024_r02/RUN.json"),
    ("STORY_LIGHTNOVEL_VI_DELIVERY_20261024_r02.md", "StellaSora_VietHoa/reports/STORY_LIGHTNOVEL_VI_DELIVERY_20261024_r02.md")
]

with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as z:
    for arcname, fpath in files_to_pack:
        if os.path.exists(fpath):
            z.write(fpath, arcname=arcname)
            print(f"Added {arcname} ({os.path.getsize(fpath)} bytes)")
        else:
            print(f"WARNING: Missing {fpath}")

z_hash = sha256_file(zip_out)
z_size = os.path.getsize(zip_out)
print(f"\nCreated deliverable zip: {zip_out}")
print(f"Size: {z_size} bytes")
print(f"SHA256: {z_hash}")
