import json
import sys
import hashlib
from pathlib import Path

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(root))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY

EXPECTED_DISCS = {
    "DiscIP.211001.3": "Sớm Mai Trong Lành",
    "DiscIP.213013.3": "Thì Thầm Mùa Thu",
    "DiscIP.214058.3": "Hành Khúc Mùa Hè",
    "DiscIP.214066.3": "Khải Minh Dẫn Lối",
    "DiscIP.214067.3": "Rực Rỡ Vĩnh Hằng",
}

EXPECTED_SKILLS = {
    "Skill.101000103.1": "Ném Chuột Chù",
    "Skill.101001502.1": "Bom Bùm Bụp",
    "Skill.100011102.1": "Hàn Băng Lộ",
    "Skill.14040000.1": "Bão Đạn Thỏ Con",
    "Skill.14740000.1": "Giai Điệu Seraphim",
}

EXPECTED_UITEXT = {
    "UIText.Achievement_Btn_ReceiveAll.1": "Nhận tất cả",
    "UIText.AVG_SkipTip.1": "Bỏ qua đoạn cốt truyện này?",
    "UIText.GachaHistory_Guarantee.1": "Chi Tiết Bảo Trợ (Pity)",
    "UIText.GachaHistory_History.1": "Lịch Sử Chiêu Mộ",
    "UIText.Recruit_history_empty.1": "Chưa có lịch sử chiêu mộ",
    "UIText.Plot_Index.1": "Hồi {0}",
    "UIText.Activity_Review.1": "Hồi Tưởng Sự Kiện",
    "UIText.Nova_Story.1": "Thời Báo Nova",
    "UIText.GachaCover3.1": "lượt chiêu mộ chắc chắn nhận Du Hành Giả Tiêu Điểm!",
    "UIText.Equipment_Btn_Upgrade.1": "Tôi Luyện",
    "UIText.Equipment_AttrTag_4.1": "Tiềm Năng Hỗ Trợ",
    "UIText.Equipment_Title_Info.1": "Thông Tin Huy Hiệu",
    "UIText.TowerDef_LevelPreTime.1": "Đợt tiếp theo bắt đầu sau <color=#08d3d4>{0}</color>",
    "UIText.Vampire_Bonus_Title.1": "{0} Chuỗi tiêu diệt <size=28>(Điểm x {1})</size>",
}

EXPECTED_CHARGEM = {
    "CharGem.203.1": "Huy Hiệu Ánh Sao Pathfinder",
    "CharGem.201.1": "Huy Hiệu Gai Pathfinder",
    "CharGem.101.1": "Huy Hiệu Gai Tín Đồ",
}

EXPECTED_MANGA = {
    "MangaLoading.49.1": "Suýt Chút Nữa Thôi!",
    "MangaLoading.14.1": "Học Vấn Không Có Đường Tắt",
    "MangaLoading.28.1": "Mắt Mờ Như Đom Đóm",
    "MangaLoading.42.1": "Nhập Gia Tùy Tục",
}

EXPECTED_ITEMS = {
    "Item.111001.1": "Ma Vương Tập Sự",
    "Item.111009.1": "Bậc Thầy Ước Nguyện",
    "Item.11103.1": "Mảnh Ghép 1/365 Của Anh",
    "Item.11205.1": "Phút Thảnh Thơi Bên Cậu",
    "Item.1030.2": "Dùng để kích hoạt Thiên phú Du Hành Giả.",
    "Item.514908.1": "Đòn Đánh Hiểm Độc",
    "Item.513913.1": "Lướt Quét Thần Tốc",
    "Item.514906.1": "Tuyệt Không Khoan Nhượng",
}

EXPECTED_CHARGET = {
    "CharGetLines.10301.1": "Em là Amber",
    "CharGetLines.10701.1": "Kỵ sĩ Tập sự",
    "CharGetLines.11001.1": "đồng minh đắc lực của cậu",
}

EXPECTED_VOICE = {
    "vo_103_combat_chat_001": "2, 4, 6... Vẫn còn dư dả băng đạn dự phòng.",
    "vo_112_ui_affchat3_001": "Có cậu ngồi ghế phụ đi cùng thế này thì chuyến đi dài mấy cũng vui hết nấc luôn á! ♪",
    "vo_107_combat_chatLvUp_001": "Kẻ địch đang chiếm thế thượng phong, nhưng em quyết không lùi bước đâu!",
    "vo_103_combat_ultskill_001": "Năng lượng đã nạp đầy. Khai hỏa!",
}

EXPECTED_GACHA_STORAGE = {
    "GachaStorage.CharacterCardPool.1": "Chiêu Mộ Du Hành Thường",
    "GachaStorage.CharacterUpCardPool.1": "Chiêu Mộ Du Hành Giới Hạn",
    "GachaStorage.DiscCardPool.1": "Khắc Ấn Thường",
    "GachaStorage.DiscUpCardPool.1": "Khắc Ấn Giới Hạn",
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
    found_uitext = False
    found_gacha = False
    found_chargem = False
    found_item = False
    found_manga = False

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

        # GachaStorage (0x07f8babd51f803d6)
        if e["hash"] == 0x07f8babd51f803d6:
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

    if not (found_disc and found_skill and found_uitext and found_gacha and found_chargem and found_item and found_manga):
        raise AssertionError("One or more essential tables were missing from data.arcx!")
    print(f"  --> ALL DATA CHECKS PASSED FOR {live_arcx.parent.parent.name}!")

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
                cur_hash = get_hash(tl)
                if cur_hash != golden_lua_hash:
                    raise AssertionError(f"Lua hash mismatch at {tl}! Expected {golden_lua_hash}, got {cur_hash}")
                print(f"  [PASS] Script archive verified: {tl} ({tl.stat().st_size:,} bytes, hash MATCH)")

    print("\n=======================================================")
    print("ALL LIVE VERIFICATION & ANTI-REGRESSION CHECKS PASSED 100%!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
