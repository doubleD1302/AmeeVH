#!/usr/bin/env python3
"""Fill initial translations for SRT001_JPVA, SRT002_CNVA, SRT003_CH04ED, SRT004_CH06ED."""
import json
from pathlib import Path
import unicodedata

PROJECT = Path(__file__).resolve().parents[1]
TRANSLATOR = "Antigravity_Translator"

TRANSLATIONS_SRT001 = {
    "1": ("Người Nova thường nói: \"Đừng dại bước vào vùng hoang dã.\"", "Dịch theo đề xuất glossary: Novians -> người Nova"),
    "2": ("Vì thế, phần lớn mọi người bám víu lấy cuộc sống bình yên nơi các Thành phố.", "Bảo toàn đối lập giữa Cities và the wild"),
    "3": ("Thế nhưng Lữ khách lại nói: \"Đừng vội hài lòng với cuộc sống chốn Thành thị.\"", "Dịch theo đề xuất glossary: Trekkers -> Lữ khách"),
    "4": ("Bỏ lại những bức tường thành sau lưng,", "Giữ nhịp câu đối ngẫu ngữ cảnh"),
    "5": ("chinh phục các Cự tháp,", "Dịch theo đề xuất glossary: Monoliths -> Cự tháp"),
    "6": ("thu thập các Cổ vật,", "Artifacts -> Cổ vật"),
    "7": ("và mang nền văn minh về cho các Thành phố,", "Giữ liên từ và danh từ Cities"),
    "8": ("những Lữ khách vẫn bị dân thường xem như những kẻ ngoại tộc.", "Outcasts -> kẻ ngoại tộc / người ngoài lề"),
    "9": ("Thế nhưng, với họ, chẳng có điều gì quan trọng hơn thế.", "Giữ sắc thái chuyển ý However"),
    "10": ("Trở thành Lữ khách là được tự do và không bị ai ràng buộc.", "To be a Trekker is to be free..."),
    "11": ("Khi các Thành phố phát triển nhanh chóng, lịch sử đã bị bóp méo và xuyên tạc một cách có chủ đích—", "Bảo toàn gạch ngang dài —"),
    "12": ("Và giờ đây, tên của Lữ khách đầu tiên đã trôi vào quên lãng.", "Lost in time -> trôi vào quên lãng"),
    "13": ("Dẫu vậy, khi ngai vàng định mệnh được tìm thấy—", "Yet, when the fated throne is discovered—"),
    "14": ("Một cơn lốc đổi thay sẽ cuốn phăng tất cả—", "A whirlwind of change will sweep over everyone—")
}

TRANSLATIONS_SRT002 = {
    "1": ("Người Nova thường nói: \"Đừng dại bước vào vùng hoang dã.\"", "Khớp bản JPVA, đồng bộ thuật ngữ"),
    "2": ("Vì thế, phần lớn mọi người bám víu lấy cuộc sống bình yên nơi các Thành phố.", "Khớp bản JPVA"),
    "3": ("Thế nhưng Lữ khách lại nói: \"Đừng vội hài lòng với cuộc sống chốn Thành thị.\"", "Bỏ chuỗi rác dffd ở cuối câu nguồn EN sau khi đối chiếu bản JPVA"),
    "4": ("Bỏ lại những bức tường thành sau lưng,", "Khớp bản JPVA"),
    "5": ("chinh phục các Cự tháp,", "Khớp bản JPVA"),
    "6": ("thu thập các Cổ vật,", "Khớp bản JPVA"),
    "7": ("và mang nền văn minh về cho các Thành phố,", "Khớp bản JPVA"),
    "8": ("những Lữ khách vẫn bị dân thường xem như những kẻ ngoại tộc.", "Khớp bản JPVA"),
    "9": ("Thế nhưng, với họ, chẳng có điều gì quan trọng hơn thế.", "Khớp bản JPVA"),
    "10": ("Trở thành Lữ khách là được tự do và không bị ai ràng buộc.", "Khớp bản JPVA"),
    "11": ("Khi các Thành phố phát triển nhanh chóng, lịch sử đã bị bóp méo và xuyên tạc một cách có chủ đích—", "Khớp bản JPVA, giữ dash —"),
    "12": ("Và giờ đây, tên của Lữ khách đầu tiên đã trôi vào quên lãng.", "Khớp bản JPVA"),
    "13": ("Dẫu vậy, khi ngai vàng định mệnh được tìm thấy—", "Khớp bản JPVA, giữ dash —"),
    "14": ("Một cơn lốc đổi thay sẽ cuốn phăng tất cả—", "Khớp bản JPVA, giữ dash —")
}

TRANSLATIONS_SRT003 = {
    "1": ("Chiếc gương cầm tay bị lãng quên nơi góc khuất lặng im", "Ca từ kết thúc Chapter 4, giữ hình ảnh thơ mộng"),
    "2": ("Những thước phim xem đi xem lại chỉ để giết thời gian", "One too many times -> xem đi xem lại"),
    "3": ("Khẽ đung đưa theo từng con sóng êm đềm trên mặt biển tĩnh lặng", "Swaying gently with the calm waves"),
    "4": ("Trôi dạt qua từng ngày, cho đến khi cả bầu trời cũng dần ảm đạm", "Dim and dull -> ảm đạm"),
    "5": ("Tôi muốn thay đổi tương lai ngột ngạt này, dù chỉ một chút thôi", "Stifling future -> tương lai ngột ngạt"),
    "6": ("Cất bước đi đầu tiên với tâm thế hoàn toàn mới", "Brand-new spirit -> tâm thế hoàn toàn mới"),
    "7": ("Trái tim tôi khao khát một thế giới tràn đầy sức sống", "Vivid world -> thế giới tràn đầy sức sống"),
    "8": ("Nơi những khuôn nhạc phác họa nên khúc ca của riêng mình tôi", "Musical staffs -> khuôn nhạc"),
    "9": ("Giọt nước mắt dâng trào nơi khóe mi không phải vì nỗi buồn", "Tears welling up in my eyes"),
    "10": ("Mà bắt nguồn từ ánh lấp lánh rạng ngời của những vì sao trên cao", "Dazzling shine of those stars above")
}

TRANSLATIONS_SRT004 = {
    "1": ("Hồi tưởng lại quá khứ xa xăm nay đã phai mờ", "Ca từ kết thúc Chapter 6, giọng hoài niệm"),
    "2": ("Ký ức tăm tối tan biến khi được đầu ngón tay khẽ chạm", "Gently brushed by fingertips"),
    "3": ("Từng giọt lệ lặng lẽ lăn dài vào màn đêm", "Silent tears slip into the night"),
    "4": ("dấu hiệu duy nhất", "the only sign"),
    "5": ("dẫn lối con đường phía trước", "guiding the road ahead"),
    "6": ("Vẽ nên một vòng cung rạng ngời ánh sáng", "Tracing an arc of radiance"),
    "7": ("Cảm xúc bất diệt giữa đôi ta một lần nữa giao hòa", "Our undying feelings overlap once more"),
    "8": ("Quyện chặt vào nhau", "Intertwining together"),
    "9": ("Dù có lạc lối trước bình minh, ta vẫn sẽ bao lần nắm chặt tay nhau", "Join hands again and again"),
    "10": ("Hai vì sao tách biệt, lung linh và say đắm—", "Bảo toàn gạch ngang —"),
    "11": ("Dõi theo dấu vết này", "Following this trail"),
    "12": ("Tôi sẽ mãi bước đi cho đến khi tới bên người", "I'll keep walking until I reach you"),
    "13": ("Cho tới khi được kề vai sát cánh cùng người", "Until I stand beside you")
}


def fill_proposal(batch_file: Path, trans_map: dict):
    data = json.loads(batch_file.read_text(encoding="utf-8"))
    data["translator"] = TRANSLATOR
    for entry in data["entries"]:
        cue = entry["source"]["locator"]["cue"]
        if cue in trans_map:
            text_vi, notes = trans_map[cue]
            entry["text_vi"] = unicodedata.normalize("NFC", text_vi)
            entry["notes"] = notes
    batch_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {batch_file.name} with {len(data['entries'])} entries.")


def main():
    batches = PROJECT / "work" / "batches"
    fill_proposal(batches / "SRT001_JPVA.json", TRANSLATIONS_SRT001)
    fill_proposal(batches / "SRT002_CNVA.json", TRANSLATIONS_SRT002)
    fill_proposal(batches / "SRT003_CH04ED.json", TRANSLATIONS_SRT003)
    fill_proposal(batches / "SRT004_CH06ED.json", TRANSLATIONS_SRT004)


if __name__ == "__main__":
    main()
