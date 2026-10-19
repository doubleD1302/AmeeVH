#!/usr/bin/env python3
"""Polisher for MailTemplate table (300 items).
Applies Master Glossary, fixes machine translation relics,
replaces clunky passive constructions with elegant anime RPG epistolary style,
and ensures 100% token preservation.
"""

import json
import re
from pathlib import Path
from token_validator import extract_tokens

def polish_mail_entries(items):
    """Takes list of MailTemplate items and returns dict {key: polished_vi}."""
    
    EVENT_TITLES = {
        "Daring Adventure! The Ghost Ship Haunts the Deep": "Mạo Hiểm Kỳ Thú! Truyền Thuyết Tàu Ma Vực Biển Sâu!",
        "Guild Sweet Guild": "Lữ Đoàn Của Chúng Ta",
        "Beyond the Dream": "Bến Bờ Mộng Cảnh",
        "Miracle of a Flicker": "Kỳ Tích Đốm Lửa Nhỏ",
        "Crackling Hint of Spring": "Pháo Hoa Rực Rỡ Tìm Sắc Xuân",
        "Winter Requiem and the Trigger of Dawn": "Bản Trấn Hồn Đêm Đông & Cò Súng Hừng Đông",
        "To My Dearest You": "Kính Gửi Người Ta Trân Quý",
        "Framing the Feelings Unseen": "Khung Ngắm Xuyên Thấu Tâm Can",
        "Heartbeat! Neo-Inspired Rhapsody": "Thình Thịch! Cuồng Tưởng Khúc Ánh Sáng Dịu Dàng",
        "A Sandstorm of Gunfire": "Mưa Đạn Phủ Cát Vàng",
    }

    EVENT_ITEMS = {
        "Squid Rice Crackers": "Bánh Gạo Mực",
        "Glass Marbles": "Viên Bi Thủy Tinh",
        "Healthy Rice Balls": "Cơm Nắm Dinh Dưỡng",
        "Forest Treasure Shovel": "Xẻng Thám Bảo Rừng Sâu",
        "Expense Receipts": "Chứng Từ Báo Chi",
        "Greenhouse Treasure Shovels": "Xẻng Thám Bảo Vườn Hoa",
        "Tasty Tanghulu": "Kẹo Hồ Lô Thơm Ngon",
        "Canned Rations": "Đồ Hộp Cấp Cứu",
        "Azure Feathers": "Lông Vũ Thanh Kiêu",
        "Bunny Stickers": "Miếng Dán Thỏ Con",
        "Spare Parts": "Linh Kiện Dư Thừa",
        "Dark Magic Bullets": "Ma Đạn Hắc Ám",
    }

    results = {}
    for it in items:
        k = it['key']
        en = it['en']
        cn = it.get('cn', '')
        vi = it.get('vi_current', it.get('vi', ''))

        if en == '!NONEED!':
            results[k] = '!NONEED!'
            continue

        # Check sender (.1)
        if k.endswith('.1'):
            if en == 'Trekker Association':
                results[k] = 'Hiệp Hội Địa Lý'
            elif en == 'Customer Service':
                results[k] = 'Dịch Vụ Khách Hàng'
            elif en == 'Operation Team' or en == 'Operations Team':
                results[k] = 'Đội Ngũ Vận Hành'
            elif en == 'Deepsea Finance':
                results[k] = 'Tài Chính Biển Sâu'
            else:
                results[k] = vi.replace('Hiệp hội Lữ khách', 'Hiệp Hội Địa Lý')
            continue

        # Check subject (.2)
        if k.endswith('.2'):
            polished_sub = vi
            polished_sub = polished_sub.replace('Lời nhắc hết hạn mã thông báo sự kiện', 'Nhắc Nhở Đạo Cụ Sự Kiện Sắp Hết Hạn')
            polished_sub = polished_sub.replace('Phân phối được phát hành lại – Mã thông báo đã hết hạn', 'Thư Bổ Sung - Đạo Cụ Quá Hạn Quy Đổi')
            polished_sub = polished_sub.replace('Giao hàng được phát hành lại - Phần thưởng nhiệm vụ', 'Thư Bổ Sung - Phần Thưởng Nhiệm Vụ Chưa Nhận')
            polished_sub = polished_sub.replace('người sống sót sau thảm họa', 'Phòng Tuyến Tai Họa')
            polished_sub = polished_sub.replace('Người sống sót sau thảm họa', 'Phòng Tuyến Tai Họa')
            polished_sub = polished_sub.replace('chưa được nhận', 'chưa nhận')
            polished_sub = polished_sub.replace('Boss Blitz', 'Liên Minh Thảo Phạt')
            results[k] = polished_sub
            continue

        # Check mail body (.3)
        polished_body = vi

        # Replace event names
        for en_ev, vi_ev in EVENT_TITLES.items():
            polished_body = re.sub(r'\[' + re.escape(en_ev) + r'\]', f'[{vi_ev}]', polished_body, flags=re.IGNORECASE)
        
        # Replace event names in case current translation has weird names
        polished_body = polished_body.replace('[lữ đoàn Sweet lữ đoàn]', '[Lữ Đoàn Của Chúng Ta]')
        polished_body = polished_body.replace('[Hội ngọt ngào]', '[Lữ Đoàn Của Chúng Ta]')
        polished_body = polished_body.replace('[Ngoài giấc mơ]', '[Bến Bờ Mộng Cảnh]')
        polished_body = polished_body.replace('[Phép lạ nhấp nháy]', '[Kỳ Tích Đốm Lửa Nhỏ]')
        polished_body = polished_body.replace('[Phép màu nhấp nháy]', '[Kỳ Tích Đốm Lửa Nhỏ]')
        polished_body = polished_body.replace('[Bão cát súng]', '[Mưa Đạn Phủ Cát Vàng]')
        polished_body = polished_body.replace('[Cơn bão cát súng]', '[Mưa Đạn Phủ Cát Vàng]')
        polished_body = polished_body.replace('[Đóng khung những cảm xúc không thể nhìn thấy]', '[Khung Ngắm Xuyên Thấu Tâm Can]')
        polished_body = polished_body.replace('[Gửi đến bạn thân yêu nhất của tôi]', '[Kính Gửi Người Ta Trân Quý]')
        polished_body = polished_body.replace('[Gửi người thân yêu nhất của anh]', '[Kính Gửi Người Ta Trân Quý]')
        polished_body = polished_body.replace('[Gửi tới bạn thân yêu nhất của tôi]', '[Kính Gửi Người Ta Trân Quý]')
        polished_body = polished_body.replace('[Winter Requiem và Trigger of Dawn]', '[Bản Trấn Hồn Đêm Đông & Cò Súng Hừng Đông]')
        polished_body = polished_body.replace('[Nhịp tim! Neo-Inspired Rhapsody]', '[Thình Thịch! Cuồng Tưởng Khúc Ánh Sáng Dịu Dàng]')
        polished_body = polished_body.replace('[Nhịp tim! Rhapsody lấy cảm hứng từ Neo]', '[Thình Thịch! Cuồng Tưởng Khúc Ánh Sáng Dịu Dàng]')

        # Replace item names
        polished_body = polished_body.replace('Bánh quy mực khó kiếm được của bạn', 'Số Bánh Gạo Mực bạn dày công thu thập')
        polished_body = polished_body.replace('Bánh gạo khô chưa sử dụng', 'Bánh Gạo Mực chưa sử dụng')
        polished_body = polished_body.replace('Những viên bi thủy tinh khó kiếm được của bạn', 'Số Viên Bi Thủy Tinh bạn dày công thu thập')
        polished_body = polished_body.replace('Viên bi Thủy tinh chưa sử dụng', 'Viên Bi Thủy Tinh chưa sử dụng')
        polished_body = polished_body.replace('Cơm nắm Healthy khó kiếm được của bạn', 'Số Cơm Nắm Dinh Dưỡng bạn dày công thu thập')
        polished_body = polished_body.replace('Tất cả Cơm nắm Khỏe mạnh và Xẻng kho báu rừng', 'Toàn bộ Cơm Nắm Dinh Dưỡng và Xẻng Thám Bảo Rừng Sâu')
        polished_body = polished_body.replace('Biên lai chi phí khó kiếm được của bạn', 'Số Chứng Từ Báo Chi bạn dày công thu thập')
        polished_body = polished_body.replace('Tất cả Biên nhận chi phí và Xẻng kho báu nhà kính', 'Toàn bộ Chứng Từ Báo Chi và Xẻng Thám Bảo Vườn Hoa')
        polished_body = polished_body.replace('Tasty Tanghulu khó kiếm được của bạn', 'Số Kẹo Hồ Lô Thơm Ngon bạn dày công thu thập')
        polished_body = polished_body.replace('Bất kỳ Tanghulu ngon nào chưa sử dụng', 'Kẹo Hồ Lô Thơm Ngon chưa sử dụng')
        polished_body = polished_body.replace('Khẩu phần đóng hộp khó kiếm được của bạn', 'Số Đồ Hộp Cấp Cứu bạn dày công thu thập')
        polished_body = polished_body.replace('Mọi Khẩu phần đóng hộp chưa sử dụng', 'Toàn bộ Đồ Hộp Cấp Cứu chưa sử dụng')
        polished_body = polished_body.replace('Azure Feathers khó kiếm được của bạn', 'Số Lông Vũ Thanh Kiêu bạn dày công thu thập')
        polished_body = polished_body.replace('Tất cả Azure Feather chưa sử dụng', 'Toàn bộ Lông Vũ Thanh Kiêu chưa sử dụng')
        polished_body = polished_body.replace('Nhãn dán Bunny khó kiếm được của bạn', 'Số Miếng Dán Thỏ Con bạn dày công thu thập')
        polished_body = polished_body.replace('Tất cả Nhãn dán Bunny chưa sử dụng', 'Toàn bộ Miếng Dán Thỏ Con chưa sử dụng')
        polished_body = polished_body.replace('Phụ tùng khó kiếm được của bạn', 'Số Linh Kiện Dư Thừa bạn dày công thu thập')
        polished_body = polished_body.replace('Mọi Phụ tùng thay thế chưa sử dụng', 'Toàn bộ Linh Kiện Dư Thừa chưa sử dụng')
        polished_body = polished_body.replace('Đạn ma thuật bóng tối khó kiếm được của bạn', 'Số Ma Đạn Hắc Ám bạn dày công thu thập')
        polished_body = polished_body.replace('Mọi Dark Magic Bullets chưa sử dụng', 'Toàn bộ Ma Đạn Hắc Ám chưa sử dụng')

        # Clean passive & mechanical phrasing
        polished_body = polished_body.replace('sẽ tự động được chuyển đổi thành Dorra và gửi đến kho lữ đoàn của bạn', 'đã được tự động quy đổi thành Dorra và gửi tới kho của Lữ Đoàn')
        polished_body = polished_body.replace('sẽ tự động được chuyển đổi thành Dorra và gửi đến kho', 'đã được tự động quy đổi thành Dorra và gửi tới kho')
        polished_body = polished_body.replace('đã được tự động chuyển đổi thành Dorra và gửi đến kho lữ đoàn của bạn', 'đã được tự động quy đổi thành Dorra và gửi tới kho của Lữ Đoàn')
        polished_body = polished_body.replace('đã được tự động chuyển đổi thành Dorra và gửi đến kho', 'đã được tự động quy đổi thành Dorra và gửi tới kho')
        polished_body = polished_body.replace('Vui lòng kiểm tra thư của bạn!', 'Xin vui lòng kiểm tra hòm thư!')
        polished_body = polished_body.replace('Vui lòng kiểm tra thư của bạn.', 'Xin vui lòng kiểm tra hòm thư.')
        polished_body = polished_body.replace('Hãy nhớ ghé thăm Cửa hàng sự kiện trước đó để đổi lấy phần thưởng!', 'Hãy nhớ ghé Cửa Hàng Sự Kiện trước khi kết thúc để đổi lấy phần thưởng giá trị nhé!')
        polished_body = polished_body.replace('Hãy nhớ nhận phần thưởng của bạn sau khi hoàn thành nhiệm vụ vào lần tới!', 'Lần tới sau khi hoàn thành nhiệm vụ, nhớ nhận thưởng kịp thời nhé!')
        polished_body = polished_body.replace('Lần sau đừng quên nhận phần thưởng đúng hạn nhé!', 'Lần tới sau khi hoàn thành nhiệm vụ, nhớ nhận thưởng đúng hạn nhé!')
        polished_body = polished_body.replace('văn phòng lữ đoàn của bạn', 'văn phòng Lữ Đoàn')
        polished_body = polished_body.replace('kho lữ đoàn của bạn', 'kho Lữ Đoàn')
        polished_body = polished_body.replace('Hiệp hội cực kỳ chu đáo đã đóng gói', 'Hiệp Hội đã chu đáo đóng gói')
        polished_body = polished_body.replace('đóng gói phần thưởng của bạn và chuyển chúng đến', 'đóng gói phần thưởng và chuyển tới')
        polished_body = polished_body.replace('đóng gói và gửi phần thưởng đến', 'đóng gói và gửi phần thưởng tới')
        polished_body = polished_body.replace('Thời hạn yêu cầu', 'Thời hạn nhận thưởng')
        polished_body = polished_body.replace('Thời hạn nhận quà đã hết', 'Thời hạn nhận thưởng đã kết thúc')
        polished_body = polished_body.replace('Xin chào, Tyrant nổi tiếng!', 'Kính chào Ma Vương tôn kính!')
        polished_body = polished_body.replace('Tyrant', 'Ma Vương')

        results[k] = polished_body

    return results

if __name__ == '__main__':
    root = Path(__file__).parent.parent
    with open(root / 'work' / 'polish' / 'audit_mail.json', 'r', encoding='utf-8') as f:
        items = json.load(f)

    res = polish_mail_entries(items)
    print(f"Polished {len(res)} MailTemplate entries.")

    mismatches = 0
    for it in items:
        k = it['key']
        en = it['en']
        vi = res[k]
        et = extract_tokens(en)
        vt = extract_tokens(vi)
        if et != vt:
            print(f"Token mismatch at {k}: EN={et} vs VI={vt}")
            mismatches += 1

    print(f"Token mismatches in MailTemplate: {mismatches}")
