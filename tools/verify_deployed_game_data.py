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
    "UIText.GachaCover3.1": "lượt chiêu mộ chắc chắn nhận Du Hành Giả Tiêu Điểm!",
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

    if not (found_disc and found_skill and found_uitext and found_gacha):
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
