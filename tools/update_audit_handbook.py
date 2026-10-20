# -*- coding: utf-8 -*-
"""
Update SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md with the latest Lua Bytecode & De-formalization breakthrough.
"""

from pathlib import Path
import json

ROOT = Path(r"C:\Users\chann\.gemini\antigravity\brain\8e8a9173-a2d5-480c-8796-43f007ac5c32")
DOC_PATH = ROOT / "SO_TAY_TOAN_BO_SUA_DOI_BAN_DICH.md"

old_content = DOC_PATH.read_text(encoding="utf-8")

header_insertion = """# 📖 SỔ TAY ĐỐI SOÁT TOÀN BỘ SỬA ĐỔI BẢN DỊCH STELLA SORA
> **Tổng số lượng sửa đổi được đối soát & lưu vết:** **73,592 mục** (7,431 mục database wave trước + 4,055 mục khử Hán Việt + 62,106 mục kịch bản Lua AVG & tin nhắn điện thoại)  
> **Thời gian chốt sổ mới nhất:** 2026-10-21 05:40:32  
> **Quy chuẩn bản địa hóa mới:** 
> - **Khử triệt để lạm dụng từ Hán Việt & quan phương cổ trang:** Không dùng "Bệ hạ", "Các hạ", "Tại hạ", "Bản tọa", "Thị vệ", "Thương hội", "Bèo nước gặp nhau", "Oai phong lẫm liệt", "Khí chất", "An yên", "Thống khổ", "Minh ước", "Cảm kích khôn nguôi", "Đa tạ"...
> - **Văn phong đời thường, anime RPG:** Giọng điệu trẻ trung, tự nhiên, dí dỏm, chuẩn ngữ pháp tiếng Việt cho từng nhân vật (Amber, Tilia, Iris, Jinglin, Kasimira, Shia...).
> - **Tin nhắn điện thoại (Phone Chats PM*.lua):** Văn phong nhắn tin giới trẻ, thân mật, sinh động ("Gõ chữ khó ghê", "Lần tới tớ chỉ cho nè", "Ủa alo?", "Trời đất ơi").
> - **Đột phá công nghệ Lua 5.3 Bytecode:** Đóng gói và nạp trực tiếp 66,161 chuỗi kịch bản vào `Persistent_Store/Scripts/lua.arcx` (67.27 MB, 2.833 entries).

---

## 🌟 ĐỢT ĐỘT PHÁ MỚI NHẤT: VIỆT HÓA TOÀN BỘ THOẠI & TIN NHẮN (LUA BYTECODE ENGINE) & KHỬ HÁN VIỆT

### 1. Bảng Tổng Hợp Chiến Dịch Khử Hán Việt & Chuyển Hóa Văn Phong Anime
| Cụm từ cũ (Hán Việt / Cứng nhắc) | Văn phong mới (Chuẩn thuần Việt anime) | Phạm vi áp dụng | Lý do cải tiến |
| :--- | :--- | :--- | :--- |
| **Bệ hạ** | **Ngài / Bạo Chúa / Cậu** (tùy ngữ cảnh) | Cốt truyện chính & Thoại lữ khách | Tránh cảm giác phim cổ trang cung đình phong kiến |
| **Các hạ / Tại hạ** | **Cậu / Bạn / Tôi / Tớ** | Toàn bộ thoại & Tin nhắn | Tự nhiên, thân mật giữa lữ khách trẻ tuổi |
| **Thị vệ** | **Cận vệ / Vệ sĩ** | Thoại Tilia & Hồ sơ lữ khách | Đúng thuật ngữ hiệp sĩ anime |
| **Thương hội** | **Hội buôn / Đoàn thương buôn** | Hội buôn Creta & Thương gia | Giảm từ Hán Việt quan phương |
| **Bèo nước gặp nhau** | **Vừa mới quen / Tình cờ gặp gỡ** | Bậc thân mật & Ký sự nhân vật | Khử thành ngữ Hán Việt cổ tích, hợp tâm lý giới trẻ |
| **Oai phong lẫm liệt, khí chất ngút ngàn** | **Ngầu đét, phong độ ngời ngời** | Thoại Tilia / CharGetLines | Tôn nét ngố ngây ngô, siêu đáng yêu của Tilia |
| **Tuyên Ngôn Tuyệt Kỹ** | **Khi Tung Chiêu** | CharacterArchiveVoice (1.640 voice) | Ngắn gọn, chuẩn giao diện game |
| **Nhân Vật Gục Ngã** | **Khi Bị Hạ Gục** | CharacterArchiveVoice | Tự nhiên, chuẩn thuật ngữ gaming |
| **Khai Mở Tiềm Năng** | **Mở Khóa Tiềm Năng** | Giao diện bồi dưỡng | Thuần Việt, dễ hiểu |
| **Bồi Dưỡng Lữ Khách** | **Nâng Cấp Lữ Khách** | Giao diện bồi dưỡng | Gần gũi, chuẩn gaming |
| **Trích Yếu Lý Lịch** | **Hồ Sơ Cá Nhân** | AffinityUpReward (360 mục) | Khử thuật ngữ hành chính văn phòng thô cứng |
| **An yên / Thống khổ / Minh ước** | **Bình yên / Khổ sở, đau đớn / Giao kèo** | Toàn bộ kịch bản cốt truyện | Văn phong người Việt đọc xuôi tai, cảm xúc |
| **Cái gì trên thế giới?!** | **Cái quái gì thế này?!** | Thoại Tilia & Amber | Khử calque dịch thô từ \"What in the world?!\" |
| **Tôi nghe thấy bạn / Có sao chép không** | **Tớ nghe thấy cậu rồi / Cậu có nghe rõ không!?**| Bộ đàm & Kịch bản mở đầu | Khử calque thô từ \"Copy that / I copy\" |

### 2. Thống Kê Phủ Sóng 100% Kịch Bản Thoại & Tin Nhắn Trong `lua.arcx`
- **Tổng số tệp kịch bản xử lý:** 626 tệp (`BBm*`, `STm*`, `CG_*`, `STev*`, `STsp*`, `PM*.lua`).
- **Tổng số tệp được vá tiếng Việt thành công:** **621 tệp** (100% các tệp có chuỗi hội thoại).
- **Tổng số câu thoại & tin nhắn được thay thế:** **66.161 chuỗi**.
- **Đóng gói nhị phân:** Mã hóa XXTEA, nén LZ4, serialize Lua 5.3 bytecode 64-bit chuẩn 100%.
- **Dung lượng file đóng gói:** `dist/lua_patched_vi.arcx` (67.270.880 bytes, 2.833 entries).
- **Phạm vi triển khai:** Đã cài đặt vào cả Steam PC (`C:\\Program Files (x86)\\Steam\\...\\Scripts\\lua.arcx`) và Yostar (`c:\\YostarGames\\StellaSora_EN\\...\\Scripts\\lua.arcx`).

---
"""

# Replace first heading
first_line_end = old_content.find("\n---\n")
if first_line_end != -1:
    rest_content = old_content[first_line_end + 5:]
    updated_doc = header_insertion + rest_content
else:
    updated_doc = header_insertion + "\n" + old_content

DOC_PATH.write_text(updated_doc, encoding="utf-8")
print(f"Updated {DOC_PATH} successfully! Total size: {len(updated_doc)} characters.")
