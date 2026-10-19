#!/usr/bin/env python3
"""Fine-tune the 6 entries with precise poetic Vietnamese and exact vertical tabs."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VI_PATH = ROOT / "work" / "research" / "data_decrypted" / "entries" / "00577_0xe60634348b826f41.bin"

with open(VI_PATH, "r", encoding="utf-8") as f:
    vi = json.load(f)

vi["Item.223024.3"] = (
    '"Này, khách quen! Rất vui được gặp lại! Vẫn như cũ chứ?"\x0b'
    '"Hả? Chỗ ngồi này chỉ dành cho trẻ em thôi sao?"\x0b'
    '"Ơ kìa, quy tắc đặt ra là để phá vỡ mà, phải không? Đằng nào cũng có ai nhìn đâu!"\x0b'
    '"Thả hồn thư giãn chính là thiên đường của người lớn!"\x0b\x0b'
    "Kỳ nghỉ dưỡng hoàn hảo chính là đây!\x0b"
    "Tựa lưng vào quầy thu ngân, cô nàng thưởng thức giấc mơ ngọt ngào xen lẫn chút vị chua thanh mát."
)

vi["Item.223025.3"] = (
    "Hỡi chú thỏ nhỏ,\x0b"
    "nhắm mắt lại và chìm vào giấc mộng say,\x0b"
    "ta sẽ ru ngươi trong vòng tay của màn đêm dịu êm;\x0b\x0b"
    "Hỡi chú thỏ nhỏ,\x0b"
    "hãy gối đầu và mơ những giấc mơ thật ngọt ngào,\x0b"
    "ta hứa sẽ dành cho ngươi món quà ngọt ngào nhất trần đời."
)

vi["Item.223026.3"] = (
    '"La-la-la—chào mừng Chủ nhân đã về nhà! ♥"\x0b'
    '"Dù là nỗi mỏi mệt trong lòng hay những xui xẻo đeo bám bên người,"\x0b'
    '"em sẽ đích thân giúp ngài quét sạch đống rác rưởi phiền toái đó đi!"\x0b'
    '"Hãy để em biến năng lượng tràn trề thành phép thuật nhiệm màu cho ngài nhé! ♥"\x0b'
    '"Nàng hầu gái đáng yêu nhất thiên đường, Beatrixa, hân hạnh được phục vụ ngài! ♥"\x0b\x0b'
    "Với chất giọng trong trẻo ngân vang cùng cử chỉ đáng yêu khôn xiết,\x0b"
    "cô ấy luôn dốc hết tâm sức mỗi ngày\x0b"
    "để trao gửi sự chữa lành và niềm hy vọng tới người hâm mộ khắp Lục địa Nova."
)

vi["Item.224019.3"] = (
    "Kasimira, cậu đã chuẩn bị sẵn sàng chưa?\x0b"
    "Đây là hiệp thứ 37 và cũng là trận so tài cuối cùng của chúng ta hôm nay.\x0b\x0b"
    "Tiếc thật đấy, chỉ thiếu đúng một phát bắn nữa thôi.\x0b"
    "Nếu phát bắn ấy chuẩn xác thì cậu đã đánh bại được tớ rồi.\x0b"
    "Chaton này, tay cậu đã hơi run vào khoảnh khắc quyết định đấy nhé.\x0b\x0b"
    "Chỉ cần nghĩ tới viễn cảnh vượt qua cậu là tim tớ đã đập rộn ràng rồi!\x0b"
    "Nào, làm lại một trận nữa đi!\x0b\x0b"
    "Cất súng đi đã, chúng ta còn ủy thác tiếp theo phải chuẩn bị đấy.\x0b\x0b"
    "—Xem ra lời khiêu chiến của Chaton vẫn chưa kết thúc đâu."
)

vi["Item.224022.3"] = (
    "Kìa, có bóng đen đang lờ mờ hiện ra trong màn đêm.\x0b"
    "Hãy lắng nghe thật kỹ, có nghe thấy tiếng bước chân ấy đang vang vọng không?\x0b"
    "Lạ thật, một cơn ớn lạnh đột nhiên chạy dọc sống lưng.\x0b\x0b"
    "Chiếc máy chiếu chập chờn, cuộn phim không tên và những hình ảnh kỳ quái liên tục nhấp nháy...\x0b"
    "Doanh trại của Lữ khách lúc nửa đêm, một vị khách không mời và cuộc viếng thăm bất ngờ.\x0b"
    '"Meow—"\x0b'
    "Sự tĩnh lặng bao trùm mọi ngóc ngách. Bạn vội đóng cửa lại, nhưng thứ ấy dường như đã lọt vào bên trong."
)

vi["Item.33011.3"] = (
    "Một Cổ vật kỳ diệu có thể bốc cháy chỉ bằng một cái búng tay. "
    "Đây là công cụ vô cùng tiện dụng cho các Lữ khách trên hành trình khám phá Vùng hoang dã.\x0b"
    "Nghiêm cấm sử dụng trong rừng rậm!\x0b"
)

with open(VI_PATH, "w", encoding="utf-8") as f:
    json.dump(vi, f, ensure_ascii=False, indent=2)

print("Updated 6 entries with precise poetic translation and paragraph breaks!")
