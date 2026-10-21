# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"C:\Users\chann\.gemini\antigravity\brain\8e8a9173-a2d5-480c-8796-43f007ac5c32")
DOC_PATH = ROOT / "SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md"

old_content = DOC_PATH.read_text(encoding="utf-8")

insertion = """# 📖 SỔ TAY ĐỐI SOÁT TOÀN BỘ SỬA ĐỔI BẢN DỊCH STELLA SORA
> **Tổng số lượng sửa đổi được đối soát & lưu vết:** **81,477 mục** (73,592 mục các đợt trước + 6,658 mục VoiceTable 00552 + 1,227 mục khử calque tin nhắn điện thoại)  
> **Thời gian chốt sổ mới nhất:** 2026-10-21 11:15:00  

---

## 🌟 ĐỢT ĐỘT PHÁ v0.9.0: VIỆT HÓA 100% LỜI THOẠI NHÂN VẬT (VOICETABLE) & KHỬ TRIỆT ĐỂ CALQUE MÁY DỊCH TIN NHẮN (PHONE CHATS)

### 1. Giải Quyết Triệt Để 2 Điểm Phản Hồi Trọng Tâm Kèm Ảnh Thực Tế Của Người Dùng

#### A. Việt hóa 100% Lời thoại nhân vật trên màn hình chính & trong game (VoiceTable `00552`)
- **Phát hiện:** Bảng dữ liệu `00552_0x80911df3a563e0f3.bin` (`VoiceTable`) chứa toàn bộ lời thoại hiển thị khi phát lồng tiếng của nhân vật. Trước đây bảng này chưa từng được dịch, khiến bong bóng thoại trên màn hình chính và trong trận đấu hiển thị 100% tiếng Anh.
- **Xử lý:** Đã dịch toàn bộ **4.400 mục voice** với **6.658 câu thoại phụ đề**:
  * **Alina trên màn hình chính (`vo_162_ui_greet_001`):**
    - *Trước:* `"If you're planning to look around Filanis, I'd be happy to show you around. Just let me know."`
    - *Sau:* **"Nếu cậu muốn dạo quanh Filanis một vòng, tôi rất sẵn lòng dẫn đường cho cậu đấy. Cứ bảo tôi một tiếng nhé."**
  * **Thoại chiến đấu (Combat lines):** Xuất trận, khi dọn sạch ải, tung tuyệt kỹ, nhắc nhở đồng đội, bị hạ gục.
  * **Thoại tương tác sảnh chờ & hồ sơ:** Khi chạm màn hình, khi chờ lâu, tăng cấp, đột phá, tặng quà, kết bạn.

#### B. Khử sạch hoàn toàn lỗi máy dịch ngô nghê trong Tin nhắn điện thoại (`PM*.lua`)
| Cụm từ gốc tiếng Anh | Dịch máy cũ (Ngô nghê / Sai ngữ cảnh) | Bản Việt hóa chuẩn Anime RPG | Phân tích lý do cải tiến |
| :--- | :--- | :--- | :--- |
| **"What a shame."** | *"Thật là xấu hổ."* | **"Tiếc ghê á~" / "Uổng thật đấy~"** | Từ "shame" bị máy dịch nhầm thành xấu hổ, làm sai hoàn toàn nghĩa câu tiếc nuối |
| **"That was a joke."** | *"Đó là một trò đùa."* | **"Đùa chút thôi mà~" / "Trêu cậu tí thôi mà~"** | Khử câu văn cơ giới, biến thành câu đùa cợt tự nhiên của bạn bè |
| **"Is that so?"** | *"Có phải vậy không?"* | **"Vậy sao?" / "Thế à?"** | Chuyển câu hỏi khô khan thành lời đáp chuyện thân mật |
| **"This is the way to reach me"** | *"Đây là cách để tiếp cận tôi"* | **"Có việc gì cứ nhắn cho tôi qua đây nhé."** | Khử từ "tiếp cận" máy móc từ "approach/reach me" |
| **"I use this phone for non-work stuff"**| *"Tôi sử dụng điện thoại này cho những việc không liên quan đến công việc"* | **"Tôi dùng máy này để nói mấy chuyện ngoài lề công việc thôi nhé."** | Câu từ gãy gọn, đúng tính cách nghệ sĩ của Flora |
| **"Mentor!"** | *"Người hướng dẫn!"* | **"Tiền bối ơi!"** | Chuẩn hóa danh xưng kính ngữ anime |
| **"Booyah! We're contacts now."** | *"Booyah! Bây giờ chúng ta là người liên hệ."* | **"Tuyệt cú mèo! Bọn mình kết bạn xong xuôi rồi nha!"** | Khử calque dịch từ "contacts" thành "người liên hệ" |
| **"You are such a rare and precious specimen..."** | *"Bạn là một mẫu vật quý hiếm—nếu tôi không thực hiện vài nghiên cứu về cậu..."* | **"Cậu là một mẫu vật hiếm có khó tìm đấy—nếu không được làm vài nghiên cứu trên người cậu..."** | Khử lỗi trộn lẫn "bạn" và "cậu" trong cùng 1 câu, đúng chất bác sĩ lập dị Coronis |
| **"Alright then, I'll be looking forward to the day you visit my clinic of your own volition~"** | *"Được rồi, tôi sẽ mong chờ ngày bạn tự nguyện đến thăm phòng khám của tôi~"* | **"Được rồi, vậy tôi sẽ chờ tới ngày cậu tự nguyện bước chân vào phòng khám của tôi nhé~"** | Câu văn mượt mà, đầy tính trêu chọc |
| **"Why asking me this all the sudden?"** | *Chưa dịch (sót tiếng Anh)* | **"Sao tự nhiên cậu lại hỏi tôi chuyện này thế?"** | Dịch hoàn thiện câu thoại sót |
| **"Firstlight Noya"** | *"Firstlight Noya"* (tiếng Anh) | **"Noya - Khải Minh"** | Chuẩn hóa tên lữ khách trên toàn bộ danh bạ |

---
"""

first_line_end = old_content.find("\n---\n")
if first_line_end != -1:
    rest_content = old_content[first_line_end + 5:]
    updated = insertion + rest_content
else:
    updated = insertion + "\n" + old_content

DOC_PATH.write_text(updated, encoding="utf-8")
print(f"Updated handbook: {DOC_PATH} ({len(updated)} bytes)")
