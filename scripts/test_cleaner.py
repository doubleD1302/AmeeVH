import json
import re

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/unique_binary_132.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

BINARY_OPCODE_REGEX = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u05ff]|Gѿ")

# Script tags to eliminate
STAGE_COMMANDS = [
    r"SetSceneHeading", r"SetHeartBeat", r"SetMainRoleTalk", r"SetTalk", r"SetStage",
    r"CtrlStage", r"PlayCharAnim", r"SetChoiceBegin", r"SetMajorChoice", r"SetFrontObj",
    r"SetFx", r"SetGoOn", r"AvgStageEffect_eyes", r"AvgChoice_item_\w+"
]

def clean_binary_string(text: str) -> str:
    if not text:
        return ""
    # 1. Remove Gѿ
    s = text.replace("Gѿ", "")
    
    # 2. Split or substitute binary tokens
    # Replace control sequences like \x04\x07se_123 or \x04\x10SetSceneHeading...
    # In many cases, \x04<len><token> is metadata.
    # Let's inspect what happens if we remove control bytes first
    
    # Remove binary opcodes regex matches
    # But wait, \x04\x11Mercenary Leader\x14] -> if we just strip binary chars,
    # "Mercenary Leader" might remain before "Nhìn mày kìa..."
    return s

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/binary_inspection_all.json', 'w', encoding='utf-8') as f:
    json.dump([{
        "id": it["id"],
        "en": it["en"],
        "vi": it["vi"],
        "files": it["files"]
    } for it in items], f, ensure_ascii=False, indent=2)

print("Exported binary_inspection_all.json")
