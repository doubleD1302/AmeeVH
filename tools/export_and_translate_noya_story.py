import json
import os
import re
import sys
from pathlib import Path

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(viet_dir, "tools"))
from pipeline_translator_engine import (
    load_master_glossary, translate_batch, post_process_vietnamese,
    shield_tokens, unshield_tokens, is_valid_token_preservation
)

lua_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")
terms, forbidden = load_master_glossary()

def extract_strings_from_lua(data: bytes):
    lines = re.findall(rb'[\x20-\x7e\n\r\t]{3,}', data)
    extracted = []
    for line in lines:
        s = line.decode("latin1", errors="ignore").strip()
        # Filter out bytecode markers and internal asset paths
        if s.startswith("@") or s.startswith("avg") or s.startswith("vo_") or s.startswith("__"):
            continue
        if s.startswith("Game/") or s.startswith("Assets/") or s.startswith("UI/"):
            continue
        if s in ["SetGroupId", "SetBubbleUIType", "SetBubble", "SetTalk", "SetBg", "SetBgm", "PlayVoice", "PlaySound", "SetCamera", "SetTransition", "SetWait"]:
            continue
        if len(s) > 2 and any(c.isalpha() for c in s):
            extracted.append(s)
    # Deduplicate while preserving order
    return list(dict.fromkeys(extracted))

stories = {}

for cg_name in ["CG_112_01.lua", "CG_112_02.lua", "CG_112_03.lua"]:
    fpath = os.path.join(lua_dir, cg_name)
    with open(fpath, "rb") as f:
        data = f.read()
    raw_strings = extract_strings_from_lua(data)
    print(f"{cg_name}: extracted {len(raw_strings)} strings.")
    
    # Filter text lines that look like actual dialogue or story narration
    dialogue_lines = [
        s for s in raw_strings 
        if (" " in s or len(s) > 15) and not s.isdigit()
    ]
    print(f"  Dialogue/narration lines: {len(dialogue_lines)}")
    
    # Translate
    shielded_list = []
    tokens_list = []
    for s in dialogue_lines:
        sh, tok = shield_tokens(s)
        shielded_list.append(sh)
        tokens_list.append(tok)
    
    translated_shielded = translate_batch(shielded_list)
    translated_lines = []
    for orig, trans_sh, tok in zip(dialogue_lines, translated_shielded, tokens_list):
        unsh = unshield_tokens(trans_sh, tok)
        polished = post_process_vietnamese(unsh, terms, forbidden)
        if not is_valid_token_preservation(orig, polished):
            polished = post_process_vietnamese(orig, terms, forbidden)
        translated_lines.append({
            "en": orig,
            "vi": polished
        })
    
    stories[cg_name] = translated_lines

out_path = os.path.join(viet_dir, r"work\reviews\NOYA_STORY_TRANSLATED.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(stories, f, indent=2, ensure_ascii=False)

print(f"Saved translated Noya stories to: {out_path}")
