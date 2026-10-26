import re
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\tools\build_lua_arcx_v097.py")
content = p.read_text(encoding="utf-8")

addition = """
    # 3.3 Load Batch 4 (306 short lines & story QA) and Batch 6 story polish lines
    b4_path = ROOT / "work" / "batches" / "BATCH_FIX_04_STORY_SHORT_LINES.json"
    if b4_path.exists():
        b4_data = json.loads(b4_path.read_text(encoding="utf-8"))
        b4_count = 0
        for it in b4_data.get("entries", []):
            sc = it.get("scene_id")
            en = it.get("source_en")
            vi = it.get("text_vi")
            if en and vi:
                en_str = en.strip()
                vi_str = vi.strip()
                if sc:
                    sdict = scene_dicts.setdefault(sc, {})
                    sdict[en_str] = vi_str
                    c_en = clean_str(en_str)
                    if c_en:
                        sdict[c_en] = vi_str
                master_dict[en_str] = vi_str
                c_en = clean_str(en_str)
                if c_en:
                    master_dict[c_en] = vi_str
                b4_count += 1
        print(f"  Applied {b4_count} overrides from Batch 4.")

    # Batch 6 story polish
    b6_path = ROOT / "work" / "batches" / "BATCH_FIX_06_POLISH_CANDIDATES.json"
    if b6_path.exists():
        b6_data = json.loads(b6_path.read_text(encoding="utf-8"))
        b6_count = 0
        b6_story_map = {
            "root:k192": ("Uh-huh, I get it! So basically, you just need to crossbreed the high-yield varieties, right?", "Ừm ừm, tôi hiểu rồi! Vậy cơ bản là chúng ta chỉ cần lai tạo các giống cao sản với nhau đúng không?"),
            "root:k282": ("What are you talking about? When have I ever failed to deliver on a promise to you?", "Cậu đang nói cái gì thế? Tôi đã bao giờ nuốt lời hứa với cậu chưa?"),
            "root:k200": ("Don't you worry, Master, leave it to me! I'm an expert at making wishes!", "Đừng lo lắng, Master, hãy để việc đó cho tôi! Tôi là chuyên gia ban điều ước!")
        }
        for it in b6_data.get("entries", []):
            kid = it.get("id")
            if kid in b6_story_map:
                en_str, vi_str = b6_story_map[kid]
                master_dict[en_str] = vi_str
                c_en = clean_str(en_str)
                if c_en:
                    master_dict[c_en] = vi_str
                b6_count += 1
        print(f"  Applied {b6_count} story overrides from Batch 6.")
"""

target = '    # 4. Patch all 626 Lua AVG files'
if target in content and 'BATCH_FIX_04_STORY_SHORT_LINES' not in content:
    new_content = content.replace(target, addition + "\n" + target)
    p.write_text(new_content, encoding="utf-8")
    print("Successfully updated build_lua_arcx_v097.py with Batch 4 and Batch 6!")
else:
    print("Already updated or target not found.")
