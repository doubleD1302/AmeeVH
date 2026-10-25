#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

# Curated list of skills that are awkward, clunky, literal, or Han-Viet calques:
SKILL_POLISH_PROPOSALS = {
    # Key: (EN, CN, Current_VI, Proposed_VI, Reason)
    "Skill.101000103.1": ("Shrew Toss", "", "Ném Chuột Chuột", "Ném Chuột Chù", "Sửa lỗi lặp từ ngớ ngẩn 'Chuột Chuột'"),
    "Skill.101000303.1": ("Shrew Pact", "", "Minh Ước Chuột Chuột", "Khế Ước Chuột Chù", "Sửa lỗi lặp từ ngớ ngẩn 'Chuột Chuột'"),
    "Skill.101001502.1": ("Bam Bam Bomb", "", "Bom Bồm Bộp", "Bom Bùm Bụp", "Từ tượng thanh 'Bùm Bụp' tự nhiên, vui nhộn hơn 'Bồm Bộp'"),
    "Skill.101001503.1": ("Bam Bam Cure", "", "Trị Liệu Bồm Bộp", "Trị Liệu Bùm Bụp", "Từ tượng thanh chuẩn xác hơn"),
    "Skill.100011102.1": ("Frozen Path", "", "Đạo Tiêu Sương Giá", "Hàn Băng Lộ / Đường Băng Sương Giá", "Đạo Tiêu là mốc tiêu đường, tối nghĩa"),
    "Skill.100011103.1": ("Glacial Eruption", "", "Kiên Băng Dũng Trận", "Băng Trụ Dâng Trào / Cực Băng Bùng Nổ", "Kiên Băng Dũng Trận là Hán Việt thô"),
    "Skill.100011503.1": ("Starflare Pursuit", "", "Diệu Tinh Truy Lạp", "Truy Kích Tinh Diệu / Sao Băng Truy Kích", "Truy Lạp là Hán Việt thô"),
    "Skill.100012003.1": ("Dustwind Star", "", "Trần Phong Chi Tinh", "Ngôi Sao Cát Bụi / Tinh Cầu Gió Cát", "Bỏ chữ 'Chi Tinh' Hán Việt sượng"),
    "Skill.100013303.1": ("Bouquet Blast", "", "Lạc Anh Tân Phấn", "Mưa Hoa Nở Rộ / Vũ Điệu Muôn Hoa", "Lạc Anh Tân Phấn quá tối nghĩa"),
    "Skill.100013403.1": ("Eruption Punch", "", "Tật Bộ Xung Quyền", "Quyền Năng Bộc Phát / Hỏa Bộc Xung Quyền", "Khớp với Eruption"),
    "Skill.100014303.1": ("Rolling Bungee", "", "Cối Xay Gió Nhào Lộn", "Bungee Nhào Lộn", "Gọn gàng, đúng kỹ năng búp bê Bungee"),
    "Skill.100014402.1": ("Water Surge", "", "Thoáng Thác Đổ", "Thác Nước Trào Dâng / Thủy Triều Dâng Trào", "'Thoáng thác đổ' nghe rất kỳ quặc"),
    "Skill.100014903.1": ("Thorned Inferno", "", "Địa Ngục Gai Góc", "Hỏa Ngục Gai Nhọn / Gai Nhọn Hỏa Ngục", "'Gai góc' dùng cho tính cách, không dùng cho vũ khí"),
    "Skill.100015503.1": ("Surfing Rondo", "", "Bích Ba Luân Tấu", "Khúc Luân Tấu Lướt Sóng", "Tự nhiên, dễ hiểu"),
    "Skill.101001701.1": ("Feline Gift", "", "Món Quà Của Mèo", "Mèo Con Trao Quà / Miêu Ban Ân Huệ", "Bỏ chữ 'của' rườm rà"),
    "Skill.109000101.1": ("Feline Healing", "", "Trị Liệu Của Mèo", "Mèo Con Trị Liệu", "Bỏ chữ 'của' rườm rà"),
    "Skill.109000102.1": ("Feline Protection", "", "Bảo Hộ Của Mèo", "Mèo Con Che Chở / Miêu Giáp Bảo Hộ", "Bỏ chữ 'của' rườm rà"),
    "Skill.13720000.1": ("Eleanor's Dodge", "", "Né Tránh Của Eleanor", "Eleanor Né Tránh", "Gọn gàng chuẩn anime skill"),
    "Skill.13770000.1": ("Eleanor's Dash", "", "Lướt Nhanh Của Eleanor", "Eleanor Lướt Nhanh", "Gọn gàng chuẩn anime skill"),
    "Skill.14040000.1": ("All-Out Bunny Barrage", "", "Áp Chế Toàn Diện Của Thỏ", "Bão Đạn Thỏ Con Toàn Lực", "Bỏ cấu trúc dịch thô 'Áp chế toàn diện của thỏ'"),
    "Skill.14731003.1": ("Death Scene", "", "Cảnh Tử Vong", "Hồi Kết Sinh Mệnh / Khúc Tử Điệu", "'Cảnh tử vong' nghe như báo cáo pháp y"),
    "Skill.14740000.1": ("Melodic Seraphim", "", "Thiên Thần Sa Ngã Nhịp Điệu", "Giai Điệu Seraphim / Thiên Thần Giai Điệu", "Xóa chữ 'Sa Ngã' bịa đặt vô căn cứ"),
    "Skill.15710001.1": ("Special Hunt Auto Attack", "", "Săn Bắn Đặc Biệt Đánh Thường", "Đòn Đánh Thường: Săn Bắn Đặc Biệt", "Rõ ràng, mạch lạc"),
    "Skill.5014102.1": ("Tower Forge: Roam", "", "Lò Tháp - Đi Dạo", "Lò Tháp: Tuần Tra", "Sửa 'Đi dạo' máy dịch ngớ ngẩn"),
    "MainSkill.300101.1": ("Zesty Curiosity", "柠柚好奇", "Hương Chanh Tò Mò", "Hiếu Kỳ Tươi Vui", "Sửa 'Hương Chanh Tò Mò' dịch máy chữ zesty"),
    "MainSkill.402901.1": ("The Cat's Treasure", "猫之珍藏", "Kho Báu Của Mèo", "Kho Báu Mèo Cưng", "Bỏ chữ 'của' rườm rà"),
    "MainSkill.403601.1": ("The Lost Pilgrim", "迷途的朝圣者", "Kẻ Hành Hương Lạc Lối", "Kẻ Hành Hương Lạc Bước", "Chất thơ hơn"),
    "MainSkill.405901.1": ("Fly, O Caged Bird", "飞吧，笼中鸟", "Bay Đi, Chú Chim Trong Lồng", "Bay Đi, Chim Trong Lồng", "Gọn gàng, hào sảng"),
    "SecondarySkill.3014101.1": ("Engine Lubrication", "引擎润滑", "Bôi Trơn Động Cơ", "Động Cơ Trơn Tru / Tiếp Dầu Động Cơ", "Tránh từ 'bôi trơn' thô thiển"),
    "SecondarySkill.3018101.1": ("Chilling Coolness", "透心凉意", "Thấu Tâm Lạnh Giá", "Làn Hơi Băng Giá / Lạnh Thấu Tâm Can", "Tự nhiên hơn"),
    "SecondarySkill.3020101.1": ("Startling Moment", "惊吓时刻", "Khoảnh Khắc Giật Mình", "Khoảnh Khắc Bất Ngờ / Kinh Hãi Tức Thì", "'Khoảnh Khắc Giật Mình' nghe như hài kịch"),
    "SecondarySkill.4004101.1": ("Graceful Essence", "淑慧本色", "Thục Huệ Bản Sắc", "Nết Na Thục Nữ / Bản Sắc Dịu Dàng", "'Thục Huệ Bản Sắc' là Hán Việt vô nghĩa"),
    "SecondarySkill.4005201.1": ("Bygone Echoes", "彷若昨日", "Dường Như Hôm Qua", "Ngỡ Như Hôm Qua / Ký Ức Hôm Qua", "Tự nhiên, gợi cảm xúc"),
    "SecondarySkill.4015101.1": ("Dreamflow Breeze", "流淌于梦的清风", "Gió Nhẹ Chảy Trong Mộng", "Gió Thoảng Miền Mộng Ảo", "Gió thổi chứ không 'chảy'"),
    "SecondarySkill.4036201.1": ("Prison of Passion", "私情满溢的禁锢", "Giam Hãm Trong Men Tình", "Xiềng Xích Tình Si / Ngục Tù Men Tình", "Mạnh mẽ, chuẩn anime"),
    "SecondarySkill.4040101.1": ("Passion of the Captain", "名为团长的热情", "Nhiệt Huyết Của Đoàn Trưởng", "Nhiệt Huyết Đoàn Trưởng", "Bỏ chữ 'của'"),
    "SecondarySkill.4044201.1": ("Blossom's Requiring", "春华亦需滋养", "Hoa Nở Cũng Cần Dưỡng Nuôi", "Hoa Nở Cần Nắng Dưỡng", "Chất thơ, tự nhiên")
}

print(f"Total curated polished skills: {len(SKILL_POLISH_PROPOSALS)}")
for k, v in SKILL_POLISH_PROPOSALS.items():
    print(f"[{k}] {v[0]} -> {v[3]} ({v[4]})")
