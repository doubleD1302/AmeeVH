import os
import struct
import json

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")
output_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json")

def extract_clean_lua53_strings(filepath):
    """
    Directly extracts constant strings from Lua 5.3 bytecode.
    Eliminates internal debug chunk paths and skips the Lua length byte cleanly.
    """
    with open(filepath, "rb") as f:
        data = f.read()
    strings = []
    i = 0
    L = len(data)
    while i < L:
        tag = data[i]
        if tag in (0x04, 0x14):
            if i + 1 < L:
                size_byte = data[i+1]
                if size_byte < 0xFF:
                    str_len = size_byte - 1
                    header_len = 2
                else:
                    if i + 10 <= L:
                        str_len = struct.unpack("<Q", data[i+2:i+10])[0] - 1
                        header_len = 10
                    else:
                        i += 1
                        continue
                if 0 < str_len <= 10000 and i + header_len + str_len <= L:
                    s_bytes = data[i+header_len : i+header_len+str_len]
                    try:
                        s = s_bytes.decode("utf-8")
                        # Filter out Lua identifiers, engine methods, file paths
                        if not (s.startswith("@") or s.startswith("avg") or s.startswith("vo_") or s.startswith("__")
                                or s.startswith("Game/") or s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Prefab")
                                or s.startswith("ttc_") or s.startswith("AvgStageEffect") or s.startswith("music_") or s.startswith("sound_")
                                or s in ["SetGroupId", "SetBubbleUIType", "SetBubble", "SetTalk", "SetBg", "SetBgm", "PlayVoice", "PlaySound", "SetCamera", "SetTransition", "SetWait", "True", "False"]):
                            if any(c.isalpha() for c in s) and (" " in s or len(s) > 12):
                                strings.append(s)
                    except:
                        pass
                    i += header_len + str_len
                    continue
        i += 1
    return list(dict.fromkeys(strings))

def get_priority_weight(filename):
    if filename.startswith("BBm"): return 1
    if filename.startswith("STm01_"): return 2
    if filename.startswith("STm02_"): return 3
    if filename.startswith("STm03_"): return 4
    if filename.startswith("CG_112_"): return 5 # Noya Firstlight / Story
    if any(filename.startswith(f"CG_{cid}_") for cid in ["103", "107", "111", "115", "118", "120", "127", "134", "144"]): return 6
    if filename.startswith("PM112"): return 7 # Noya Phone Chats
    if filename.startswith("PM"): return 8
    if filename.startswith("STm04_"): return 9
    if filename.startswith("CG_"): return 10
    if filename.startswith("STsp_"): return 11
    return 20

def main():
    all_files = sorted(os.listdir(lua_config_dir))
    ranked_files = sorted(all_files, key=lambda f: (get_priority_weight(f), f))

    batch = {}
    files_used = []
    
    for f in ranked_files:
        if not f.endswith(".lua"):
            continue
        fpath = os.path.join(lua_config_dir, f)
        slist = extract_clean_lua53_strings(fpath)
        if not slist:
            continue
        
        base = f[:-4]
        file_items = []
        for idx, s in enumerate(slist):
            file_items.append((f"{base}.{idx+1}", s))
        
        if len(batch) + len(file_items) <= 10000:
            for k, s in file_items:
                batch[k] = s
            files_used.append((f, len(file_items)))
        else:
            needed = 10000 - len(batch)
            if needed > 0:
                for k, s in file_items[:needed]:
                    batch[k] = s
                files_used.append((f, needed))
            break

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(batch, fp, ensure_ascii=False, indent=2)

    print(f"Extracted exactly {len(batch)} clean strings from {len(files_used)} Lua files.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
