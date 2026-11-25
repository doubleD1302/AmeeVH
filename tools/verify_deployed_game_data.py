import json
import struct
import sys
import hashlib
from pathlib import Path

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "tools"))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY
from tools.test_lua_roundtrip import Lua53Chunk

EXPECTED_DISCS = {
    "DiscIP.211001.3": "Sớm Mai Trong Lành",
    "DiscIP.213013.3": "Thì Thầm Mùa Thu",
    "DiscIP.214058.3": "Hành Khúc Mùa Hè",
    "DiscIP.214066.3": "Khải Minh Dẫn Lối",
    "DiscIP.214067.3": "Rực Rỡ Vĩnh Hằng",
}

EXPECTED_SKILLS = {
    "Skill.101000103.1": "Shrew Toss",
    "Skill.101001502.1": "Bam Bam Bomb",
    "Skill.100011102.1": "Frozen Path",
    "Skill.14040000.1": "All-Out Bunny Barrage",
    "Skill.14740000.1": "Melodic Seraphim",
}


EXPECTED_MAINSKILL = {
    "MainSkill.405101.1": "Stellar Destination",
    "MainSkill.405101.2": "Tuần du giả Cân Bằng hệ Quang",
    "MainSkill.400301.2": "Tuần du giả Cân Bằng hệ Quang",
    "MainSkill.400801.2": "Tuần du giả Cân Bằng hệ Thủy",
    "MainSkill.405901.2": "Tinh Vọng",
}

EXPECTED_UITEXT = {
    "UIText.Achievement_Btn_ReceiveAll.1": "Nhận tất cả",
    "UIText.AVG_SkipTip.1": "Bỏ qua đoạn cốt truyện này?",
    "UIText.GachaHistory_Guarantee.1": "Chi Tiết Bảo Trợ (Pity)",
    "UIText.GachaHistory_History.1": "Lịch Sử Chiêu Mộ",
    "UIText.Recruit_history_empty.1": "Chưa có lịch sử chiêu mộ",
    "UIText.Plot_Index.1": "Hồi {0}",
    "UIText.Activity_Review.1": "Hồi Tưởng",
    "UIText.Nova_Story.1": "Thời Báo Nova",
    "UIText.GachaCover3.1": "lượt chiêu mộ chắc chắn nhận Tuần Du Giả Tiêu Điểm!",
    "UIText.Equipment_Btn_Upgrade.1": "Tôi Luyện",
    "UIText.Equipment_AttrTag_4.1": "Tiềm Năng Hỗ Trợ",
    "UIText.Equipment_Title_Info.1": "Thông Tin Huy Hiệu",
    "UIText.TowerDef_LevelPreTime.1": "Đợt tiếp theo bắt đầu sau <color=#08d3d4>{0}</color>",
    "UIText.Vampire_Bonus_Title.1": "Chuỗi {0} tiêu diệt <size=28>(Điểm x{1})</size>",
    "UIText.Diffculty_1.1": "Độ khó 1",
    "UIText.Diffculty_2.1": "Độ khó 2",
    "UIText.Diffculty_3.1": "Độ khó 3",
    "UIText.SkillInstance_PassConfition_1.1": "Thời gian vượt ải ≤ {0} s",
    "UIText.SkillInstance_PassConfition_2.1": "Vượt ải khi còn lại > {0} giây",
    "UIText.RegusBoss_Unlock.1": "Chưa mở khóa độ khó",
    "UIText.StarTower_Rank_Diff_Score.1": "Điểm độ khó",
}

EXPECTED_CHARGEM = {
    "CharGem.203.1": "Huy Hiệu Ánh Sao Khai Phá",
    "CharGem.201.1": "Huy Hiệu Gai Khai Phá",
    "CharGem.101.1": "Huy Hiệu Gai Tín Đồ",
}

EXPECTED_MANGA = {
    "MangaLoading.49.1": "Suýt Chút Nữa Thôi!",
    "MangaLoading.14.1": "Học Vấn Không Có Đường Tắt",
    "MangaLoading.28.1": "Mắt Mờ Như Đom Đóm",
    "MangaLoading.42.1": "Nhập Gia Tùy Tục",
}

EXPECTED_ITEMS = {
    "Item.103.1": "Amber",
    "Item.158.1": "Laru Dạ Thánh",
    "Item.162.1": "Noya - Khải Minh",
    "Item.111001.1": "Ma Vương Tập Sự",
    "Item.111009.1": "Bậc Thầy Ước Nguyện",
    "Item.11103.1": "Mảnh Ghép 1/365 Của Cậu",
    "Item.11205.1": "Phút Thảnh Thơi Bên Cậu",
    "Item.1030.2": "Dùng để kích hoạt Thiên phú Tuần Du Giả.",
    "Item.514908.1": "Đòn Đánh Hiểm Độc",
    "Item.513913.1": "Lướt Quét Thần Tốc",
    "Item.514906.1": "Tuyệt Không Khoan Nhượng",
}

EXPECTED_CHARGET = {
    "CharGetLines.10301.1": "Tớ là Amber.\nIris có viết cho tớ một bản tự giới thiệu đàng hoàng. Lát tớ nhắn qua cho cậu.",
    "CharGetLines.10701.1": "Tôi là Tilia, Hiệp sĩ Tập sự của Chính nghĩa!\nTừ nay về sau, tôi sẽ mang công lý đến cho mọi người!",
    "CharGetLines.11001.1": "Tôi là Firenze. Để tôi cho cậu thấy thực lực của mình.\nĐừng hòng làm tôi thất vọng đấy nhé.",
    "CharGetLines.16201.1": "Tôi là Alina, đội trưởng Thị Vệ Màn Đêm.",
}

EXPECTED_VOICE = {
    "vo_103_combat_chat_001": "2, 4, 6... Vẫn còn dư dả băng đạn dự phòng.",
    "vo_112_ui_affchat3_001": "Có cậu ngồi ghế phụ đi cùng thế này thì chuyến đi dài mấy cũng vui hết nấc luôn á! ♪",
    "vo_107_combat_chatLvUp_001": "Kẻ địch đang chiếm thế thượng phong, nhưng tôi quyết không lùi bước đâu!",
    "vo_103_combat_ultskill_001": "Năng lượng đã nạp đầy. Khai hỏa!",
    "vo_162_ui_gachaNew_001": "Tôi là Alina, đội trưởng Thị Vệ Màn Đêm.",
}


EXPECTED_SKIN_QUOTES = {
    "CharacterSkin.14403.2": "Đóa hoa triêu nhan cắm trong bình nước thanh khiết này—— sắc hoa tươi thắm cùng hương thơm thanh nhã ấy, liệu có thể lưu giữ được bao lâu đây?",
    "CharacterSkin.14903.2": "Vị chua đắng của cà phê, hương thơm ngát của đóa tường vi, em muốn chia sẻ trọn vẹn mọi trải nghiệm mới mẻ này cùng với cậu. Khi tuyết tan rồi, chúng mình cùng nhau hẹn hò một chuyến nhé?",
    "CharacterSkin.11104.2": "Cái đó... Em sẽ cố hết sức giữ thăng bằng cho chiếc phao bơi này, nhưng khi trèo lên Boss nhớ cẩn thận một chút nhé.\x0b——Đ-Đương nhiên rồi, nếu Boss lỡ sảy chân rơi xuống nước, em nhất định sẽ kéo Boss lại thật chặt!",
}

EXPECTED_GACHA_STORAGE = {
    "GachaStorage.CharacterCardPool.1": "Chiêu Mộ Tuần Du Giả Thường",
    "GachaStorage.CharacterUpCardPool.1": "Chiêu Mộ Tuần Du Giả Giới Hạn",
    "GachaStorage.DiscCardPool.1": "Chiêu Mộ Đĩa Nhạc Thường",
    "GachaStorage.DiscUpCardPool.1": "Chiêu Mộ Đĩa Nhạc Giới Hạn",
}

EXPECTED_FORCE = {
    "Force.18.1": "Thị Vệ Màn Đêm",
}

EXPECTED_CHARTAG = {
    "CharacterTag.318.1": "Thị Vệ Màn Đêm",
}

def get_hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_data_arcx(live_arcx: Path, expected_hash: str = None):
    print(f"\n=======================================================")
    print(f"VERIFYING DATA ARCHIVE: {live_arcx}")
    print(f"Size: {live_arcx.stat().st_size:,} bytes")
    
    current_hash = get_hash(live_arcx)
    print(f"SHA256: {current_hash}")
    if expected_hash and current_hash != expected_hash:
        raise AssertionError(f"Hash mismatch for {live_arcx}! Expected {expected_hash}, got {current_hash}")

    arc = ArcxArchive(live_arcx)
    raw = live_arcx.read_bytes()

    found_disc = False
    found_skill = False
    found_mainskill = False
    found_uitext = False
    found_gacha = False
    found_chargem = False
    found_item = False
    found_manga = False
    found_charget = False
    found_skin = False
    found_voice = False
    found_force = False
    found_chartag = False

    for e in arc.entries:
        # DiscIP (0x1f924138769d46ec)
        if e["hash"] == 0x1f924138769d46ec:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted DiscIP table.")
            for k, expected_val in EXPECTED_DISCS.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Disc regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: {actual_val} (MATCH)")
            found_disc = True

        # Skill (0x998f849a64309b25)
        if e["hash"] == 0x998f849a64309b25:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted Skill table.")
            for k, expected_val in EXPECTED_SKILLS.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Skill regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: {actual_val} (MATCH)")
            found_skill = True


        # MainSkill (0x57e760255c1d3b2d)
        if e["hash"] == 0x57e760255c1d3b2d:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted MainSkill table.")
            for k, expected_sub in EXPECTED_MAINSKILL.items():
                val = d.get(k, "")
                if expected_sub not in val:
                    raise AssertionError(f"MainSkill regression at {k}: expected substring '{expected_sub}', got '{val}'")
                if "phượt thủ" in val or "Auto Tấn Công" in val:
                    raise AssertionError(f"MainSkill regression at {k}: forbidden MT calque found in '{val}'")
                print(f"    - {k}: contains '{expected_sub}' (MATCH)")
            found_mainskill = True

        # UIText (0x87cc29ac0defc2d9)
        if e["hash"] == 0x87cc29ac0defc2d9:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted UIText table.")
            for k, expected_val in EXPECTED_UITEXT.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"UIText regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: {actual_val} (MATCH)")
            found_uitext = True

        # GachaStorage EN (0x4c3d6f59912566fc)
        if e["hash"] == 0x4c3d6f59912566fc:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted GachaStorage table.")
            for k, expected_val in EXPECTED_GACHA_STORAGE.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"GachaStorage regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: {actual_val} (MATCH)")
            found_gacha = True

        # Item (0xe60634348b826f41)
        if e["hash"] == 0xe60634348b826f41:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted Item table.")
            for k, expected_val in EXPECTED_ITEMS.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Item regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val}' (MATCH)")
            found_item = True

        # MangaLoading (0x5df8a2d9397ea4a6)
        if e["hash"] == 0x5df8a2d9397ea4a6:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted MangaLoading table.")
            for k, expected_val in EXPECTED_MANGA.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"MangaLoading regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val}' (MATCH)")
            found_manga = True

        # CharGem (0x627a5df613782a6e)
        if e["hash"] == 0x627a5df613782a6e:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted CharGem table.")
            for k, expected_val in EXPECTED_CHARGEM.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"CharGem regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: {actual_val} (MATCH)")
            found_chargem = True

        # CharGetLines (0x8dcf06b298f46b28)
        if e["hash"] == 0x8dcf06b298f46b28:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted CharGetLines table.")
            for k, substr in EXPECTED_CHARGET.items():
                actual_val = d.get(k, "")
                if substr not in actual_val:
                    raise AssertionError(f"CharGetLines regression at {k}: expected substring '{substr}', got '{actual_val}'")
                print(f"    - {k}: contains '{substr}' (MATCH)")
            found_charget = True

        # CharacterSkin (0xd79f78b562c5c75c)
        if e["hash"] == 0xd79f78b562c5c75c:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted CharacterSkin table.")
            for k, expected_val in EXPECTED_SKIN_QUOTES.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Skin quote regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val[:40]}...' (MATCH)")
            found_skin = True

        # Voice Subtitles (0x80911df3a563e0f3)
        if e["hash"] == 0x80911df3a563e0f3:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted Master Voice Subtitles table.")
            for k, expected_val in EXPECTED_VOICE.items():
                actual_val = d.get(k, {}).get("text", {}).get("female_jp", [""])[0]
                if actual_val != expected_val:
                    raise AssertionError(f"Voice regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val}' (MATCH)")
            found_voice = True

        # Force (0x3609bd7b72ac8e0d)
        if e["hash"] == 0x3609bd7b72ac8e0d:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted Force table.")
            for k, expected_val in EXPECTED_FORCE.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"Force regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val}' (MATCH)")
            found_force = True

        # CharacterTag (0xcecb63095d111150)
        if e["hash"] == 0xcecb63095d111150:
            data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
            d = json.loads(data.decode("utf-8"))
            print("  [PASS] Decrypted CharacterTag table.")
            for k, expected_val in EXPECTED_CHARTAG.items():
                actual_val = d.get(k)
                if actual_val != expected_val:
                    raise AssertionError(f"CharacterTag regression at {k}: expected '{expected_val}', got '{actual_val}'")
                print(f"    - {k}: '{actual_val}' (MATCH)")
            found_chartag = True

    if not (
        found_disc and found_skill and found_mainskill and found_uitext
        and found_gacha and found_chargem and found_item and found_manga
        and found_charget and found_skin and found_voice and found_force and found_chartag
    ):
        raise AssertionError("One or more essential tables were missing from data.arcx!")
    print(f"  --> ALL DATA CHECKS PASSED FOR {live_arcx.parent.parent.name}!")


def verify_lua_arcx(live_lua: Path, expected_hash: str):
    cur_hash = get_hash(live_lua)
    if cur_hash != expected_hash:
        raise AssertionError(f"Lua hash mismatch at {live_lua}! Expected {expected_hash}, got {cur_hash}")
    arc = ArcxArchive(live_lua)
    raw = live_lua.read_bytes()
    by_h = {e["hash"]: e for e in arc.entries}

    # Verify AvgUIText.lua (0x3e63762a97ac2700) K[99] split
    avg_e = by_h.get(0x3E63762A97AC2700)
    if not avg_e:
        raise AssertionError("AvgUIText.lua (0x3e63762a97ac2700) missing from lua.arcx")
    chunk = Lua53Chunk(xxtea_decrypt(arc.extract_entry(avg_e, raw), XXTEA_KEY))
    chunk.read_bytes(33)
    chunk.read_byte()
    proto = chunk.parse_proto()
    consts = proto["constants"]
    if len(consts) < 100:
        raise AssertionError(f"AvgUIText.lua missing K[99] split: len(constants)={len(consts)}")
    k75 = consts[75][1][1].decode("utf-8")
    k99 = consts[99][1][1].decode("utf-8")
    insts = list(struct.unpack(f"<{proto['sizecode']}I", proto["code"]))
    if k75 != "của cô ấy" or k99 != "cô ấy" or (insts[91] >> 14) != 75 or (insts[96] >> 14) != 99:
        raise AssertionError(f"AvgUIText.lua K[99] assertion failed: k75={k75!r}, k99={k99!r}")

    # Verify 0xcd02c7b6b576dcd8 trailing tab preserved
    tab_e = by_h.get(0xCD02C7B6B576DCD8)
    if not tab_e:
        raise AssertionError("0xcd02c7b6b576dcd8 missing from lua.arcx")
    tchunk = Lua53Chunk(xxtea_decrypt(arc.extract_entry(tab_e, raw), XXTEA_KEY))
    tchunk.read_bytes(33)
    tchunk.read_byte()
    tproto = tchunk.parse_proto()
    tstrs = [c[1][1].decode("utf-8", errors="replace") for c in tproto["constants"] if c[0] in (4, 20)]
    if not any(s.endswith("\t") for s in tstrs):
        raise AssertionError("Trailing tab constant missing in 0xcd02c7b6b576dcd8")

    print(f"  [PASS] Script archive verified: {live_lua} ({live_lua.stat().st_size:,} bytes, hash MATCH, AvgUIText K[99] & trailing tab OK)")

def main():
    dist_data = root / "dist" / "data_patched_vi.arcx"
    dist_lua = root / "dist" / "lua_patched_vi.arcx"

    if not dist_data.exists():
        print(f"ERROR: Golden data archive not found at {dist_data}")
        sys.exit(1)

    golden_data_hash = get_hash(dist_data)
    print(f"Golden data.arcx size: {dist_data.stat().st_size:,} | SHA: {golden_data_hash}")

    targets_data = [
        Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
    ]

    for td in targets_data:
        if td.parent.exists():
            verify_data_arcx(td, golden_data_hash)

    if dist_lua.exists():
        golden_lua_hash = get_hash(dist_lua)
        print(f"\nGolden lua.arcx size: {dist_lua.stat().st_size:,} | SHA: {golden_lua_hash}")
        targets_lua = [
            Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx"),
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Scripts\lua.arcx")
        ]
        for tl in targets_lua:
            if tl.parent.exists():
                verify_lua_arcx(tl, golden_lua_hash)

    print("\n=======================================================")
    print("ALL LIVE VERIFICATION & ANTI-REGRESSION CHECKS PASSED 100%!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
