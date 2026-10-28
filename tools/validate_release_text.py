# -*- coding: utf-8 -*-
import re

title = "1.0.8"
body = """- Khắc phục triệt để lỗi xưng hô "anh/chị" hướng tới nhân vật chính, loại bỏ hoàn toàn tình trạng gọi nhầm khi chơi nhân vật nữ.
- Chuẩn hóa đồng bộ danh xưng và thuật ngữ trong toàn bộ cốt truyện, lời thoại hẹn hò, kỹ năng, đĩa nhạc và giao diện.
- Cập nhật Launcher PC (v1.0.8) và Android APK (v1.0.8) hỗ trợ tự động tải và cài đặt trực tiếp trong ứng dụng."""

title = title.strip()
body = body.strip()

if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", title):
    raise ValueError("Tiêu đề chỉ được chứa số phiên bản, ví dụ 0.1.2.")

word_count = len(body.split())
if word_count == 0:
    raise ValueError("Mô tả cần nêu nội dung cập nhật.")
if word_count > 100:
    raise ValueError(f"Mô tả có {word_count} từ, vượt giới hạn 100 từ.")

print(f"Title: {title}")
print(f"Word count: {word_count} (<= 100 PASS)")
print("Valid!")
