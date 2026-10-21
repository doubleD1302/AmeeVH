# -*- coding: utf-8 -*-
"""
Translate and patch all 6,658 character voice lines in VoiceTable (00552_0x80911df3a563e0f3.bin).
Also fixes Firstlight Noya -> Noya - Khải Minh across character tables.
Applies lively anime voice acting dialogue rules.
"""

import json
from pathlib import Path
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from pipeline_translator_engine import translate_batch
from deformalize_text import deformalize_text

CACHE_FILE = ROOT / "work" / "batches" / "voice_lines_cache.json"
VOICE_TABLE_FILE = ROOT / "work" / "research" / "data_200_decrypted" / "entries" / "00552_0x80911df3a563e0f3.bin"

def polish_voice_line(en: str, vi: str) -> str:
    # Common voice acting specific phrases
    custom_map = {
        "If you're planning to look around Filanis, I'd be happy to show you around. Just let me know.":
            "Nếu cậu muốn dạo quanh Filanis một vòng, tôi rất sẵn lòng dẫn đường cho cậu đấy. Cứ bảo tôi một tiếng nhé.",
        "All's good so far.": "Mọi chuyện đến giờ vẫn ổn áp nha.",
        "Okay. Good enough.": "Được rồi. Thế là đủ rồi nè.",
        "Let's move on.": "Bọn mình tiếp tục tiến lên thôi nào!",
        "The enemies are stronger. But I can take 'em.": "Kẻ địch mạnh hơn rồi đấy, nhưng tớ lo được tất!",
        "I'll scout ahead—Hm? You wanna tag along? Sure.": "Tớ đi trinh sát phía trước nhé—Hửm? Cậu muốn đi cùng hả? Được thôi!",
        "Leave the tough ones to me.": "Mấy tên khó nhằn cứ để tớ lo!",
        "I wonder if there is any cat food.": "Không biết ở đây có pate cho mèo không nhỉ.",
        "I'm down. Requesting retreat.": "Tớ kiệt sức rồi... Xin phép rút lui trước nha!",
        "Just need a little rest...": "Tớ chỉ cần nghỉ ngơi một xíu thôi...",
        "Talking to people is tough.": "Giao tiếp với mọi người khó thật đấy.",
        "This is easy to use.": "Món này dễ dùng ghê nè.",
        "Have I ... become stronger?": "Mình... đã mạnh hơn rồi sao?",
        "I feel powerful.": "Tớ cảm thấy tràn đầy sức mạnh!",
        "Boss, I wanna take a photo here.": "Sếp ơi, em muốn chụp một kiểu ảnh ở đây quá!",
        "There's so much cool stuff. Can I buy them all?": "Nhiều đồ hay ho ghê! Mình mua hết đống này được không ta?",
        "Now I can be of use to you.": "Giờ thì tớ đã có thể giúp ích được cho cậu rồi.",
        "Wanna hear the Meow Meow Song?": "Cậu có muốn nghe bài ca Meo Meo không nè?",
        "What a shame.": "Tiếc ghê á~",
        "Aww, what a shame...": "Ôi, tiếc thật đấy...",
        "That was a joke.": "Đùa chút thôi mà~",
        "Just a joke.": "Trêu cậu tí thôi mà~",
        "Is that so?": "Vậy sao?",
        "This is the way to reach me": "Có việc gì cứ nhắn cho tôi qua đây nhé.",
        "Hello": "Chào cậu nha",
        "At your service!": "Sẵn sàng nhận lệnh!",
        "Newbie squire Tilia, Defender of Justice!": "Cận vệ tập sự Tilia, Người Bảo Hộ Công Lý!"
    }
    if en in custom_map:
        return custom_map[en]

    polished = deformalize_text(vi)
    # Fix remaining calques in voice lines
    polished = polished.replace("Thật là xấu hổ", "Tiếc thật đấy")
    polished = polished.replace("Đó là một trò đùa", "Đùa thôi mà")
    polished = polished.replace("Có phải vậy không", "Vậy sao")
    polished = polished.replace("tiếp cận tôi", "liên lạc với tôi")
    polished = polished.replace("người liên hệ", "bạn bè")
    polished = polished.replace("Firstlight Noya", "Noya - Khải Minh")
    return polished

def main():
    print("=== TRANSLATING & PATCHING MASTER VOICE TABLE (00552) ===")
    
    # 1. Load Voice Table
    data = json.loads(VOICE_TABLE_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(data)} voice items from VoiceTable.")

    # 2. Collect unique strings
    unique_strings = set()
    for k, v in data.items():
        if isinstance(v, dict) and 'text' in v:
            for lang, t_list in v['text'].items():
                for t in t_list:
                    s = t.strip()
                    if s:
                        unique_strings.add(s)

    print(f"Total unique voice lines to localize: {len(unique_strings)}")

    # 3. Load or build translation cache
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.load(open(CACHE_FILE, encoding="utf-8"))
            print(f"Loaded {len(cache)} cached voice translations.")
        except Exception:
            pass

    to_translate = [s for s in sorted(unique_strings) if s not in cache]
    print(f"Remaining to translate: {len(to_translate)}")

    if to_translate:
        batch_size = 50
        batches = [to_translate[i : i + batch_size] for i in range(0, len(to_translate), batch_size)]
        print(f"Translating {len(to_translate)} strings in {len(batches)} batches...")

        def fetch(b):
            res = translate_batch(b)
            return list(zip(b, res))

        completed = 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_batch = {executor.submit(fetch, b): b for b in batches}
            for fut in as_completed(future_to_batch):
                try:
                    pairs = fut.result()
                    for en, vi in pairs:
                        cache[en] = polish_voice_line(en, vi)
                    completed += len(pairs)
                    if completed % 500 < batch_size or completed == len(to_translate):
                        elapsed = time.time() - t0
                        speed = completed / elapsed if elapsed > 0 else 0
                        print(f"Progress: {completed}/{len(to_translate)} ({completed/len(to_translate)*100:.1f}%) - {speed:.1f} strings/sec")
                        with open(CACHE_FILE, "w", encoding="utf-8") as f:
                            json.dump(cache, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"Batch error: {e}")

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print("Finished translating voice lines!")

    # 4. Patch Voice Table
    patched_count = 0
    for k, v in data.items():
        if isinstance(v, dict) and 'text' in v:
            for lang in ('female_jp', 'female_cn'):
                if lang in v['text']:
                    t_list = v['text'][lang]
                    new_list = []
                    for t in t_list:
                        s = t.strip()
                        if s in cache:
                            new_list.append(polish_voice_line(s, cache[s]))
                            patched_count += 1
                        else:
                            new_list.append(t)
                    v['text'][lang] = new_list

    VOICE_TABLE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully patched {patched_count} voice subtitle fields in VoiceTable!")

    # 5. Fix Firstlight Noya in character tables
    entries_dir = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
    for fn in ("00587_0xcb4918cdfc3acaf8.bin", "00588_0x836daae6b64cbbc8.bin", 
               "00591_0x40c643f18bf8d5ff.bin", "00843_0xfc1bc7670ae9c953.bin"):
        fp = entries_dir / fn
        if fp.exists():
            txt = fp.read_text(encoding="utf-8")
            if "Firstlight Noya" in txt:
                new_txt = txt.replace("Firstlight Noya", "Noya - Khải Minh")
                fp.write_text(new_txt, encoding="utf-8")
                print(f"Replaced 'Firstlight Noya' in {fn}")

    print("=== VOICE TABLE PATCHING COMPLETE ===")

if __name__ == "__main__":
    main()
