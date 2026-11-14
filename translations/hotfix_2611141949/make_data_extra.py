"""Build data_extra.jsonl: hand translations for strings the 2.1.0 delivery left in English.
Resolves each key to the entry hash whose official value still starts with the expected English text."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY

V = "\x0b"
T = []  # (key, expected English prefix, Vietnamese)
def t(key, en, vi): T.append((key, en, vi))

t("Achievement.663.1", "Longing Across Time", "Nỗi Nhớ Vượt Thời Gian")
for n, q in ((1, 200), (2, 300), (3, 400)):
    t(f"ActivityDoubleQuest.11200{n}.1", "Consume a total of", f"Tiêu thụ tổng cộng {q} Thể Lực")
for k in ("ActivityGoods.101903.1", "Honor.116018.1", "Item.116018.1"):
    t(k, "Brushstrokes of the Unknown", "Nét Bút Vô Danh")
for k, vi in (("1301", "Đỉnh Cao Chưa Khai Phá"), ("1302", "Lặn Sâu"), ("1303", "Bước Đầu Tiên")):
    t(f"BdConvertContent.{k}.1", {"1301": "Uncharted Heights", "1302": "Deep Dive", "1303": "First Steps"}[k], vi)
for i, pts in enumerate((200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400), start=1):
    t(f"BdConvertRewardGroup.13{i:02d}.1", "Total Clearance Points reach",
      f"Tổng Điểm Chiến Tích đạt {pts:,}".replace(",", ",") + " trong Đại Thu Thập Hồ Sơ Chiến Tích")
t("ActivityDouble.103012.1", V + "Event Period",
  f"{V}【Thời Gian Sự Kiện】{V}13:00, 09/11/2026 – 12:59:59, 12/11/2026{V}{V}【Điều Kiện Tham Gia】{V}Cấp Quyền Hạn ≥ 3{V}{V}"
  f"【Chi Tiết Sự Kiện】{V}Ủy thác khẩn cấp đã mở! Hoàn thành một số loại màn thử thách nhất định để nhận gấp đôi phần thưởng!")
t("BdConvertControl.500013.1", V + "Event Period",
  f"{V}【Thời Gian Sự Kiện】{V}21:00, 09/11/2026 – 20:00, 16/11/2026{V}{V}【Điều Kiện Tham Gia】{V}Cấp Quyền Hạn ≥ 10{V}{V}"
  f"【Chi Tiết Sự Kiện】{V}1. Hiệp hội Tuần du giả đang thu thập Hồ Sơ Chiến Tích vượt Tháp sao thành công để đổi lấy Điểm Chiến Tích.{V}"
  f"2. Tích lũy Điểm Chiến Tích để nhận vô vàn phần thưởng hấp dẫn!")
t("MailTemplate.4020.1", "Trekker Association", "Hiệp hội Tuần du giả")
t("MailTemplate.4020.2", "Reissue Parcel", "Gửi Bù Nhanh: Phần Thưởng Sự Kiện")
t("MailTemplate.4020.3", "The claim deadline",
  "Sự kiện [Một Năm Tinh Đồ · Tri Ân Đặc Biệt] đã kết thúc, thời hạn nhận thưởng cũng đã qua rồi!\n\n"
  "Tuy nhiên, Hiệp hội đã chu đáo đóng gói phần thưởng và gửi đến văn phòng của bạn. Hãy kiểm tra thư nhé.\n\n"
  "Lần sau nhớ nhận thưởng đúng hạn nhé!")
t("Item.71027.1", "Prefix Title: Time", "Tiền tố danh hiệu: Thời Gian")
t("Item.71027.2", "Used to unlock the title: Time", "Dùng để mở khóa danh hiệu: Thời Gian")
t("Item.71027.3", "A small card inscribed", "Tấm thẻ nhỏ khắc những dòng chữ phép thuật.")
t("Item.72027.1", "Suffix Title: Traveler", "Hậu tố danh hiệu: Lữ Khách")
t("Item.72027.2", "Used to unlock the title: Traveler", "Dùng để mở khóa danh hiệu: Lữ Khách")
t("Item.72027.3", "A small card inscribed", "Tấm thẻ nhỏ khắc những dòng chữ phép thuật.")
t("Title.58.1", "Traveler", "Lữ Khách")
t("Title.59.1", "Open-sea", "Biển Khơi")
t("ThrowGiftItem.106.1", "Airdrop Sherlock", "Sherlock Thả Dù")
t("UIText.MainView_MainStoryPreview.1", "Available Now", "Đã mở")
# titles whose descriptions were already translated in 2.1.0
t("Item.111012.1", "Longing Across Time", "Nỗi Nhớ Vượt Thời Gian")
t("Honor.111012.1", "Longing Across Time", "Nỗi Nhớ Vượt Thời Gian")
t("Item.112161.1", "The Navigator", "Người Dẫn Đường")
t("Honor.112161.1", "The Navigator", "Người Dẫn Đường")
for i, s in zip((71, 72, 73), ("Kỳ Tài", "Bậc Thầy", "Tinh Anh")):
    for k in ("Item", "Honor"):
        t(f"{k}.1170{i}.1", "", f"{s} Tàn Cuộc Mùa 8")
for i, s in zip((41, 42, 43), ("Kỳ Tài", "Bậc Thầy", "Tinh Anh")):
    for k in ("Item", "Honor"):
        t(f"{k}.1181{i}.1", "", f"{s} Săn Bắt Mùa 15")
for n in range(18, 31):
    t(f"Item.1150{n}.1", "", f"Quán Quân Sinh Tồn Mùa {n}")
t("vo_114_combat_perk_001", "Dun-dun-dun", "Tèn tén ten! ♪ Tada!")

def main(official):
    arc = ArcxArchive(official); raw = official.read_bytes()
    index = {}
    for e in arc.entries:
        try:
            j = json.loads(xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY).decode("utf-8"))
        except Exception:
            continue
        if isinstance(j, dict):
            for k, v in j.items():
                index.setdefault(k, []).append((e["hash_hex"], v))
    out, miss = [], []
    for key, en, vi in T:
        hit = False
        for h, v in index.get(key, []):
            if isinstance(v, dict):  # voice subtitle table: /key/text/female_jp/0
                cur = (v.get("text", {}).get("female_jp") or [""])[0]
                if cur.startswith(en):
                    out.append({"id": f"2.1.0:data:{h}:/{key}/text/female_jp/0", "text_vi": vi, "status": "Bản nháp"}); hit = True
            elif isinstance(v, str) and v.startswith(en):
                out.append({"id": f"2.1.0:data:{h}:/{key}", "text_vi": vi, "status": "Bản nháp"}); hit = True
        if not hit:
            miss.append(key)
    dest = Path(__file__).with_name("data_extra.jsonl")
    dest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print("rows", len(out), "unresolved", miss)

if __name__ == "__main__":
    main(Path(sys.argv[1]))
