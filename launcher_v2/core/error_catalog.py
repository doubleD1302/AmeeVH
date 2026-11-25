"""Plain-language error catalog and exception diagnosis for Stella Sora Launcher v2.0.

Every failure the user can see is reduced to one stable ``E-...`` code with a short title,
a plain-language Vietnamese explanation, and concrete recovery steps.  All 36 shared
PC+Android codes and 28 Android-only codes from ``docs/ERROR_CODES.md`` are preserved
verbatim alongside the 33 existing PC-only codes and 7 new PC-only v2.0 codes (104 static
entries total, 76 PC codes).

This module is 100% pure Python (zero Qt / PySide6 imports).
"""
from __future__ import annotations

import errno
import http.client
import json
import os
import re
import socket
import ssl
import urllib.error
from dataclasses import dataclass, field
from typing import Optional

from .safety import InstallerError


@dataclass(frozen=True)
class ErrorInfo:
    code: str
    title: str
    summary: str
    steps: tuple = ()
    level: str = 'error'      # 'error' | 'warning' | 'info'
    network: bool = False     # a connectivity probe helps explain this failure
    platform: str = 'pc'      # 'pc' | 'android' | 'shared'

    @property
    def is_error(self) -> bool:
        return self.level == 'error'


ErrorSpec = ErrorInfo

_CATALOG: dict[str, ErrorInfo] = {}


def _add(code: str, title: str, summary: str, steps=(), level: str = 'error', network: bool = False, platform: str = 'pc') -> None:
    _CATALOG[code] = ErrorInfo(code, title, summary, tuple(steps), level, network, platform)


_SEND = 'Nếu vẫn lỗi, bấm "Sao chép mã lỗi" và gửi cho người làm bản dịch.'
_REPORT = 'Bấm "Sao chép mã lỗi" và gửi cho người làm bản dịch.'

# --------------------------------------------------------------------------- network (PC + shared)
_add('E-NET', 'Không kết nối được máy chủ',
     'Launcher không nói chuyện được với máy chủ. Mạng có thể đang yếu, bị chặn hoặc máy chủ đang bận.',
     ['Kiểm tra máy đã có Internet chưa (thử mở https://github.com trên trình duyệt).',
      'Tắt VPN/proxy nếu đang dùng, hoặc đổi mạng (Wi-Fi ↔ 4G) rồi thử lại.', _SEND],
     network=True, platform='shared')
_add('E-NET-OFFLINE', 'Máy chưa có đường ra Internet',
     'Windows báo không có đường tới mạng ngoài. Thường là Wi-Fi/cáp mạng đã ngắt hoặc chưa đăng nhập Wi-Fi công cộng.',
     ['Kiểm tra Wi-Fi hoặc dây mạng đã kết nối chưa.',
      'Nếu dùng Wi-Fi công cộng, mở trình duyệt để đăng nhập trang của mạng đó.',
      'Sau khi có mạng, bấm "Kiểm tra phiên bản Việt hoá".'],
     network=True, platform='shared')
_add('E-NET-DNS', 'Không tìm ra địa chỉ GitHub (lỗi DNS)',
     'Máy tính không tra được địa chỉ của GitHub. Thường do mạng vừa mất kết nối, DNS của nhà mạng bị lỗi hoặc GitHub bị chặn ở mạng của bạn.',
     ['Mở https://github.com trên trình duyệt. Nếu cũng không vào được thì lỗi nằm ở mạng của bạn, không phải ở launcher.',
      'Đổi DNS sang 1.1.1.1 và 8.8.8.8 (Cài đặt Windows → Mạng & Internet → mạng đang dùng → DNS), hoặc bật VPN/Cloudflare WARP.',
      'Mở PowerShell, gõ "ipconfig /flushdns" rồi thử lại.', _SEND],
     network=True, platform='shared')
_add('E-NET-TIMEOUT', 'GitHub phản hồi quá chậm',
     'Launcher đã gọi tới máy chủ nhưng chờ mãi không thấy trả lời (quá thời gian chờ). Mạng đang chập chờn hoặc bị nghẽn.',
     ['Chờ 1–2 phút rồi bấm "Kiểm tra phiên bản Việt hoá" lại.',
      'Thử mạng khác (ví dụ phát 4G từ điện thoại).',
      'Tắt VPN, proxy hoặc phần mềm tăng tốc mạng nếu có.', _SEND],
     network=True, platform='shared')
_add('E-NET-REFUSED', 'Máy chủ từ chối kết nối',
     'Kết nối tới máy chủ bị từ chối ngay. Thường do tường lửa, phần mềm diệt virus hoặc proxy đang chặn cổng 443 (HTTPS).',
     ['Tạm tắt VPN/proxy rồi thử lại.',
      'Kiểm tra tường lửa hoặc phần mềm diệt virus có chặn StellaSora_Launcher.exe không và cho phép nó truy cập mạng.', _SEND],
     network=True, platform='shared')
_add('E-NET-RESET', 'Kết nối bị ngắt giữa chừng',
     'Đang tải dở thì kết nối bị cắt. Mạng chập chờn hoặc phần mềm bảo mật đã ngắt kết nối.',
     ['Thử lại, launcher sẽ tải tiếp phần còn lại.',
      'Nếu hay bị ngắt, đổi mạng hoặc tạm tắt phần mềm quét web của diệt virus.', _SEND],
     network=True, platform='shared')
_add('E-NET-BLOCKED', 'Windows hoặc phần mềm bảo mật chặn launcher dùng mạng',
     'Hệ thống không cho launcher mở kết nối mạng (thường do tường lửa hoặc phần mềm diệt virus).',
     ['Mở Windows Security → Tường lửa → Cho phép ứng dụng qua tường lửa, tích chọn StellaSora_Launcher.exe.',
      'Nếu dùng phần mềm diệt virus riêng, thêm launcher vào danh sách tin cậy.', _SEND],
     network=True, platform='pc')
_add('E-NET-TLS-CERT', 'Chứng chỉ bảo mật không được tin cậy',
     'Kết nối HTTPS bị từ chối vì chứng chỉ của máy chủ không hợp lệ với máy bạn. Hay gặp khi ngày giờ máy sai, hoặc phần mềm diệt virus/proxy đang "quét HTTPS".',
     ['Kiểm tra ngày, giờ và múi giờ của Windows (bật "Đặt giờ tự động").',
      'Tạm tắt tính năng quét HTTPS/Web Shield của phần mềm diệt virus, hoặc tắt proxy/VPN.',
      'Chạy Windows Update để cập nhật chứng chỉ gốc, rồi thử lại.', _SEND],
     network=True, platform='shared')
_add('E-NET-TLS', 'Không thiết lập được kết nối an toàn (HTTPS)',
     'Quá trình bắt tay bảo mật với máy chủ thất bại. Thường do mạng can thiệp vào kết nối (proxy, diệt virus, mạng công ty) hoặc Windows quá cũ.',
     ['Tắt VPN/proxy rồi thử lại, hoặc đổi sang mạng khác.',
      'Cập nhật Windows và kiểm tra ngày giờ máy.', _SEND],
     network=True, platform='shared')
_add('E-NET-PROXY', 'Proxy từ chối hoặc chặn yêu cầu',
     'Launcher đi qua một proxy nhưng proxy này từ chối hoặc không cho truy cập GitHub.',
     ['Mở Cài đặt Windows → Mạng & Internet → Proxy và tắt proxy nếu bạn không chủ ý dùng.',
      'Nếu dùng proxy công ty/trường học, thử mạng khác (ví dụ 4G).', _SEND],
     network=True, platform='pc')
_add('E-HTTP-RATE', 'GitHub đang giới hạn lượt truy cập',
     'GitHub tạm chặn vì mạng của bạn gọi quá nhiều lần trong thời gian ngắn (hay gặp khi nhiều người dùng chung một địa chỉ mạng như 4G hoặc Wi-Fi chung).',
     ['Chờ 10–15 phút rồi thử lại.', 'Hoặc đổi sang mạng khác (Wi-Fi ↔ 4G).'],
     network=True, platform='shared')
_add('E-HTTP-404', 'Không tìm thấy tệp trên GitHub',
     'Bản phát hành hoặc tệp launcher cần không còn ở địa chỉ đó (đã bị xoá hoặc tên kho/nhánh bị sai).',
     ['Mở Cài đặt → kiểm tra Kho GitHub và Nhánh. Mặc định là doubleD1302/AmeeVH và main.',
      'Nếu bạn chưa sửa gì ở đó, đây là lỗi phía người phát hành. ' + _REPORT],
     network=True, platform='shared')
_add('E-HTTP-5XX', 'GitHub đang gặp sự cố',
     'Máy chủ GitHub trả về lỗi nội bộ (không phải lỗi của máy bạn).',
     ['Chờ vài phút rồi thử lại.', 'Xem tình trạng tại https://www.githubstatus.com.'],
     network=True, platform='shared')
_add('E-HTTP-4XX', 'GitHub từ chối yêu cầu',
     'Máy chủ trả về một mã lỗi từ chối (HTTP 4xx) cho yêu cầu của launcher.',
     ['Thử lại sau ít phút hoặc đổi mạng.', _SEND],
     network=True, platform='shared')

# --------------------------------------------------------------------------- sync / config / data
_add('E-SYNC-PENDING', 'Launcher đang đọc thông tin từ GitHub',
     'Launcher chưa đọc xong bản phát hành và bảng kê bản dịch nên chưa cho cài. Nút sẽ sáng khi đọc xong.',
     ['Chờ vài giây.', 'Nếu quá 30 giây nút vẫn xám, bấm "Kiểm tra phiên bản Việt hoá" để xem lý do cụ thể.'],
     level='info', platform='shared')
_add('E-CONFIG-CHANNEL', 'Nguồn GitHub trong Cài đặt chưa hợp lệ',
     'Tên kho hoặc tên nhánh GitHub trong Cài đặt có dạng không đúng nên launcher không biết tải bản dịch ở đâu.',
     ['Mở Cài đặt, đặt lại Kho = doubleD1302/AmeeVH và Nhánh = main rồi lưu.',
      'Kho phải có dạng tên-tài-khoản/tên-kho, không có dấu cách hay https://.'],
     platform='shared')
_add('E-CONFIG-SAVE', 'Không lưu được cấu hình launcher',
     'Launcher không ghi được tệp cấu hình vào thư mục dữ liệu của nó (AppData). Đường dẫn bạn chọn vẫn được giữ như cũ.',
     ['Kiểm tra ổ C: còn dung lượng trống.',
      'Tắt tạm phần mềm diệt virus/"Controlled folder access" của Windows Defender rồi thử lại.',
      'Chạy launcher bằng quyền Quản trị một lần.', _SEND],
     platform='pc')
_add('E-LOCAL-PAYLOAD', 'Gói bản dịch cục bộ không dùng được',
     'Trong Cài đặt đang có đường dẫn "Gói cục bộ", nên launcher bỏ qua GitHub và chỉ đọc bản dịch từ thư mục đó. Thư mục này không có tệp patch_manifest.json hợp lệ (hoặc tệp quá lớn/hỏng) nên không cài được.',
     ['Nếu bạn không chủ ý dùng gói cục bộ: mở Cài đặt, xoá trống ô "Gói cục bộ" rồi bấm Lưu. Launcher sẽ tự tải bản dịch từ GitHub.',
      'Nếu bạn đang dùng gói cục bộ: chọn đúng thư mục chứa patch_manifest.json cùng các tệp bản dịch đi kèm.', _SEND],
     platform='pc')
_add('E-RELEASE', 'Chưa có bản phát hành dùng được',
     'Kênh GitHub đang trỏ tới bản nháp/thử nghiệm hoặc chưa có bản phát hành chính thức nào.',
     ['Chờ người làm bản dịch công bố bản phát hành.', 'Kiểm tra Kho/Nhánh trong Cài đặt có đúng không.'],
     network=True, platform='pc')
_add('E-DATA-SCHEMA', 'Dữ liệu GitHub trả về sai định dạng',
     'Launcher đọc được tệp nhưng nội dung thiếu hoặc sai cấu trúc nên không dám dùng. Có thể tệp đang được cập nhật dở trên GitHub.',
     ['Chờ vài phút rồi bấm "Kiểm tra phiên bản Việt hoá" lại.', _SEND],
     platform='shared')
_add('E-DATA-JSON', 'Dữ liệu tải về không đọc được',
     'Máy chủ trả về nội dung không phải dữ liệu mong đợi. Hay gặp khi Wi-Fi công cộng bắt đăng nhập, hoặc proxy/diệt virus chèn trang cảnh báo.',
     ['Mở trình duyệt, vào https://github.com xem có hiện trang đăng nhập/cảnh báo không.',
      'Tắt proxy/VPN rồi thử lại.', _SEND],
     network=True, platform='shared')
_add('E-DATA-UNVERIFIED', 'Tệp phát hành chưa có mã xác minh',
     'Tệp trên GitHub không kèm mã SHA256 nên launcher từ chối dùng để đảm bảo an toàn.',
     ['Đây là lỗi phía người phát hành. ' + _REPORT],
     platform='shared')
_add('E-MANIFEST-MISSING', 'Bản phát hành chưa có bảng kê bản dịch',
     'Bản phát hành mới nhất trên GitHub chưa đính kèm tệp bảng kê (patch_manifest.json) nên launcher chưa biết cần cài những tệp nào.',
     ['Chờ người làm bản dịch đăng đủ tệp.', 'Nếu đã chờ lâu mà vẫn vậy: ' + _REPORT],
     platform='pc')
_add('E-MANIFEST-INVALID', 'Bảng kê bản dịch bị lỗi',
     'Tệp bảng kê thiếu thông tin hoặc có dữ liệu không hợp lệ nên launcher dừng lại để tránh cài sai.',
     ['Chờ bản phát hành được sửa rồi thử lại.', _SEND],
     platform='shared')
_add('E-MANIFEST-VERSION', 'Không so sánh được phiên bản bản dịch',
     'Số phiên bản trong bảng kê hoặc biên bản đã cài có dạng lạ nên launcher không biết bản nào mới hơn.',
     ['Bấm "Kiểm tra phiên bản Việt hoá" lại.', _SEND],
     platform='pc')
_add('E-MANIFEST-PLATFORM', 'Gói bản dịch không dành cho Windows',
     'Bản phát hành đang trỏ tới gói của nền tảng khác (ví dụ Android).',
     ['Đây là lỗi phía người phát hành. ' + _REPORT],
     platform='pc')
_add('E-SECURITY', 'Launcher từ chối vì không an toàn',
     'Gói bản dịch hoặc địa chỉ tải có đường dẫn/tệp nằm ngoài phạm vi cho phép nên launcher dừng lại để bảo vệ game của bạn. Game chưa bị thay đổi.',
     ['Đừng dùng gói này. ' + _REPORT],
     platform='shared')
_add('E-DOWNGRADE', 'Gói bản dịch cũ hơn bản đang cài',
     'Launcher không cho cài đè bản cũ lên bản mới hơn để tránh mất phần dịch đã cập nhật.',
     ['Bấm "Kiểm tra phiên bản Việt hoá" để lấy bản mới nhất.',
      'Nếu cố ý muốn quay lại bản cũ, hãy Khôi phục dữ liệu gốc trước rồi cài lại.'],
     platform='pc')

# --------------------------------------------------------------------------- download
_add('E-DL-VERIFY', 'Tệp tải về bị sai hoặc hỏng',
     'Tệp tải xong nhưng kích thước hoặc mã kiểm tra (SHA256) không khớp bảng kê. Có thể do đường truyền lỗi, hoặc bảng kê trỏ nhầm tệp.',
     ['Bấm cài lại, launcher sẽ tải lại tệp.',
      'Nếu lặp lại nhiều lần, đổi mạng hoặc tắt phần mềm quét web của diệt virus.', _SEND],
     network=True, platform='shared')
_add('E-DL-RANGE', 'Máy chủ trả dữ liệu tải tiếp không đúng',
     'Launcher cố tải tiếp phần dở dang nhưng máy chủ trả phần dữ liệu không khớp.',
     ['Bấm cài lại, launcher sẽ tải lại từ đầu.', _SEND],
     network=True, platform='shared')
_add('E-DL-TIMEOUT', 'Tải quá lâu so với thời hạn',
     'Tệp tải chậm hơn thời hạn cho phép. Phần đã tải hợp lệ vẫn được giữ lại.',
     ['Bấm cài lại để tải tiếp.', 'Nếu mạng yếu, đổi mạng rồi thử lại.'],
     network=True, platform='shared')
_add('E-DL-RESPONSE', 'Máy chủ trả về dữ liệu tải không hợp lệ',
     'Phản hồi của máy chủ khi tải tệp không đúng định dạng mong đợi.',
     ['Thử lại sau ít phút.', _SEND],
     network=True, platform='shared')
_add('E-DL-FAILED', 'Tải tệp không thành công',
     'Launcher đã thử tải nhiều lần nhưng không hoàn tất. Nguyên nhân thường là mạng chập chờn.',
     ['Kiểm tra mạng rồi bấm cài lại (phần đã tải được giữ lại).', _SEND],
     network=True, platform='pc')

# --------------------------------------------------------------------------- game folder / state
_add('E-NO-GAME-FOLDER', 'Chưa chọn thư mục game',
     'Launcher chưa biết game của bạn nằm ở đâu nên chưa thể cài, kiểm tra hay khôi phục.',
     ['Bấm biểu tượng thư mục cạnh nút Cài, chọn thư mục chứa tệp StellaSora.exe.',
      'Hoặc bấm biểu tượng kính lúp trên ô đường dẫn để launcher tự tìm.'],
     level='warning', platform='pc')
_add('E-NO-EXE', 'Thư mục này không có StellaSora.exe',
     'Launcher chỉ nhận thư mục nằm cùng chỗ với tệp StellaSora.exe. Đường dẫn cũ của bạn vẫn được giữ nguyên.',
     ['Steam: chuột phải game → Quản lý → Duyệt tệp cục bộ, rồi chọn đúng thư mục đó.',
      'Yostar: chọn thư mục cài game trong launcher Yostar (chứa StellaSora.exe).',
      'Đừng chọn thư mục cha hoặc thư mục con (ví dụ StellaSora_Data).'],
     level='warning', platform='pc')
_add('E-GAME-NOT-FOUND', 'Không tự tìm thấy game',
     'Launcher đã tìm trong thư viện Steam và các vị trí Yostar thường gặp nhưng không thấy Stella Sora.',
     ['Bấm biểu tượng thư mục và chọn thủ công thư mục có StellaSora.exe.',
      'Kiểm tra bạn đã cài game trên máy này chưa.'],
     level='warning', platform='pc')
_add('E-GAME-RUNNING', 'Game đang chạy',
     'Không thể thay đổi tệp khi game đang mở. Launcher dừng lại để không làm hỏng dữ liệu.',
     ['Thoát hẳn Stella Sora (kiểm tra cả Trình quản lý tác vụ: StellaSora.exe).', 'Sau đó thử lại.'],
     level='warning', platform='shared')
_add('E-BUSY', 'Launcher đang bận',
     'Một thao tác khác đang chạy nên launcher chưa nhận thêm yêu cầu.',
     ['Chờ thao tác hiện tại hoàn tất rồi thử lại.'],
     level='warning', platform='shared')
_add('E-NO-RECEIPT', 'Chưa cài Việt hoá bằng launcher này',
     'Kiểm tra tệp cần danh sách tệp đã cài (biên bản) do launcher tạo ra lúc cài. Thư mục game này chưa có biên bản đó nên chưa có gì để kiểm tra. Đây không phải lỗi hỏng game.',
     ['Bấm "Cài Việt hoá" để cài bản dịch.',
      'Nếu trước đây bạn cài bằng công cụ khác, hãy cài lại một lần bằng launcher này.',
      'Nếu bạn chắc đã cài bằng launcher này, kiểm tra đang chọn đúng thư mục game (không bị đổi tên/di chuyển), rồi gửi mã lỗi này.'],
     level='info', platform='shared')
_add('E-RECEIPT-MISMATCH', 'Biên bản cài đặt không khớp thư mục game',
     'Biên bản trong thư mục này được tạo cho một vị trí khác (game đã bị di chuyển/đổi tên, hoặc sao chép từ máy khác) hoặc có định dạng cũ.',
     ['Bấm "Cài lại Việt hoá" để launcher tạo biên bản mới đúng thư mục này.'],
     level='warning', platform='pc')
_add('E-FILE-MISMATCH', 'Tệp game không còn khớp bản Việt hoá đã cài',
     'Một số tệp đã bị thay đổi sau khi cài (game tự cập nhật, công cụ khác ghi đè, hoặc diệt virus sửa tệp).',
     ['Bấm "Cài lại Việt hoá" để áp dụng lại.',
      'Nếu game vừa cập nhật, bấm Khôi phục, mở game cho cập nhật xong rồi cài lại Việt hoá.'],
     level='warning', platform='shared')
_add('E-FILE-CHANGED', 'Tệp game bị thay đổi trong lúc launcher làm việc',
     'Có chương trình khác (Steam, launcher của Yostar, diệt virus) vừa sửa tệp game nên launcher dừng lại để không ghi đè sai. Game được giữ nguyên trạng thái trước đó.',
     ['Đợi Steam/launcher Yostar tải xong bản cập nhật (nếu có), thoát game rồi thử lại.',
      'Tạm tắt quét thời gian thực của diệt virus cho thư mục game.', _SEND],
     platform='shared')
_add('E-FILE-IN-USE', 'Tệp đang được chương trình khác sử dụng',
     'Một chương trình khác (game chưa tắt hẳn, diệt virus, Steam) đang giữ tệp nên launcher chưa ghi được. Launcher đã hoàn tác, game giữ nguyên trạng thái trước.',
     ['Thoát hẳn game và các chương trình tải/cập nhật game, đợi diệt virus quét xong.',
      'Khởi động lại máy nếu vẫn không được, rồi thử lại.'],
     platform='pc')
_add('E-FILE-DENIED', 'Windows không cho launcher ghi vào thư mục game',
     'Launcher không có quyền ghi vào thư mục game (thư mục chỉ-đọc, nằm trong Program Files, hoặc bị "Controlled folder access" chặn).',
     ['Bấm "Chạy quyền Quản trị" (nếu có) hoặc chuột phải launcher → Run as administrator.',
      'Bỏ dấu "Chỉ đọc" của thư mục game (chuột phải → Properties).',
      'Trong Windows Security → Ransomware protection, thêm launcher vào danh sách được phép.'],
     platform='pc')
_add('E-FILE-MISSING', 'Không tìm thấy một tệp cần thiết',
     'Launcher cần một tệp hoặc thư mục nhưng nó không còn tồn tại (bị xoá, hoặc game đang được cập nhật/di chuyển).',
     ['Kiểm tra thư mục game vẫn còn nguyên và đúng vị trí.', 'Bấm "Kiểm tra phiên bản Việt hoá" rồi thử lại.', _SEND],
     platform='pc')
_add('E-STORAGE', 'Ổ đĩa không đủ dung lượng',
     'Không còn đủ chỗ trống để tải gói, sao lưu và thay tệp một cách an toàn. Game chưa bị thay đổi.',
     ['Giải phóng dung lượng ở ổ chứa game và ổ C: (nơi launcher lưu bản sao lưu), mỗi ổ vài GB.',
      'Rồi bấm cài lại.'],
     platform='shared')
_add('E-BACKUP', 'Bản sao lưu bị thiếu hoặc hỏng',
     'Launcher cần bản sao lưu dữ liệu gốc để khôi phục nhưng nó không còn hoặc sai nội dung.',
     ['Dùng chức năng Khôi phục: launcher sẽ tự tải dữ liệu gốc mới nhất từ nhà phát hành (cần mạng).', _SEND],
     platform='shared')
_add('E-VERIFY-WRITE', 'Ghi xong nhưng đọc lại không khớp',
     'Sau khi ghi tệp, launcher đọc lại để kiểm tra nhưng nội dung khác dự kiến (có thể do diệt virus can thiệp hoặc ổ đĩa lỗi).',
     ['Tạm tắt diệt virus cho thư mục game rồi thử lại.',
      'Kiểm tra ổ đĩa còn dung lượng và không báo lỗi.', _SEND],
     platform='shared')
_add('E-ROOT-MISMATCH', 'Nhật ký thuộc về thư mục game khác',
     'Nhật ký thao tác dở dang không đúng với thư mục game đang chọn.',
     ['Chọn lại đúng thư mục game đã cài trước đó, hoặc mở Công cụ nâng cao để xử lý nhật ký.'],
     platform='pc')
_add('E-JOURNAL', 'Nhật ký thao tác bị hỏng',
     'Nhật ký ghi lại thao tác dở dang bị hỏng nên launcher không tự phục hồi. Launcher giữ nguyên nó để bạn gửi cho người hỗ trợ.',
     ['Bấm "Sao chép mã lỗi" và gửi kèm tệp nhật ký trong thư mục dữ liệu launcher.', 'Đừng xoá thư mục game.'],
     platform='shared')
_add('E-RECOVERY-REQUIRED', 'Có thao tác trước đó bị ngắt giữa chừng',
     'Lần cài/khôi phục trước chưa kết thúc (mất điện, tắt ngang…). Launcher phải phục hồi trước khi làm tiếp để game không bị hỏng.',
     ['Mở Công cụ nâng cao → "Phục hồi từ nhật ký" và chờ hoàn tất.', 'Sau đó cài lại như bình thường.'],
     platform='shared')
_add('E-INSTALL-ROLLED-BACK', 'Cài đặt không thành công, đã hoàn tác',
     'Quá trình cài gặp sự cố giữa chừng. Launcher đã tự trả game về trạng thái trước khi cài.',
     ['Thoát game và các chương trình tải game, rồi thử cài lại.', _SEND],
     platform='pc')

# --------------------------------------------------------------------------- self update
_add('E-UPDATE-TIMEOUT', 'Launcher cũ chưa đóng nên chưa cập nhật được',
     'Bản launcher cập nhật chờ launcher cũ đóng hẳn nhưng quá thời hạn. Bản cũ được giữ nguyên.',
     ['Đóng mọi cửa sổ launcher (kiểm tra Trình quản lý tác vụ) rồi bấm cập nhật lại.'],
     platform='pc')
_add('E-UPDATE-INVALID', 'Gói tự cập nhật không hợp lệ',
     'Tệp hoặc thông tin cập nhật launcher không đúng nên launcher dừng lại. Bản hiện tại vẫn chạy bình thường.',
     ['Tải bản launcher mới nhất thủ công từ trang phát hành.', _SEND],
     platform='pc')
_add('E-UPDATE-UNSUPPORTED', 'Chỉ tự cập nhật được bản launcher đã đóng gói',
     'Bạn đang chạy launcher từ mã nguồn nên chức năng tự cập nhật không dùng được.',
     ['Tải bản launcher (.exe) mới nhất từ trang phát hành.'],
     level='warning', platform='pc')
_add('E-UPDATE-RELAUNCH', 'Launcher mới không khởi động được',
     'Bản launcher vừa cập nhật không chạy được nên launcher đã tự quay lại bản cũ.',
     ['Tải bản launcher mới nhất thủ công và chạy lại.', _SEND],
     platform='pc')
_add('E-UPDATE-RECOVERY', 'Lần cập nhật launcher trước chưa hoàn tất',
     'Cập nhật launcher trước đó bị gián đoạn và cần phục hồi.',
     ['Chạy lại launcher; nếu vẫn lỗi hãy tải bản mới nhất thủ công.', _SEND],
     platform='pc')

# --------------------------------------------------------------------------- publisher (official) data
_add('E-OFFICIAL-NET', 'Không tải được dữ liệu gốc từ máy chủ nhà phát hành',
     'Launcher không kết nối được máy chủ tài nguyên chính thức của game (không phải GitHub). Mạng có thể chập chờn hoặc bị chặn.',
     ['Kiểm tra Internet rồi thử lại.', 'Tắt VPN/proxy hoặc đổi mạng nếu vẫn lỗi.', _SEND],
     network=True, platform='pc')
_add('E-OFFICIAL-INCONSISTENT', 'Máy chủ nhà phát hành đang cập nhật',
     'Thông tin tài nguyên chính thức đang thay đổi nên chưa đồng bộ. Đây là tình trạng tạm thời.',
     ['Chờ vài phút rồi thử lại.'],
     platform='pc')
_add('E-OFFICIAL-NOTFOUND', 'Nhà phát hành không còn tệp tài nguyên này',
     'Máy chủ chính thức không còn giữ bản tài nguyên launcher yêu cầu (game đã lên bản mới hơn).',
     ['Mở game cho nó tự cập nhật rồi thử lại.', _SEND],
     platform='pc')
_add('E-OFFICIAL-FORMAT', 'Launcher chưa hiểu dữ liệu của nhà phát hành',
     'Dữ liệu tài nguyên chính thức có cấu trúc launcher chưa đọc được (game có thể vừa đổi định dạng) hoặc bị hỏng.',
     ['Thử lại sau ít phút.', 'Nếu lặp lại, có thể cần cập nhật launcher. ' + _REPORT],
     platform='pc')
_add('E-OFFICIAL-CRYPTO', 'Windows thiếu thành phần giải mã',
     'Launcher cần bộ giải mã của Windows (BCrypt/AES) nhưng không dùng được trên máy này.',
     ['Cập nhật Windows lên bản mới nhất.', _SEND],
     platform='pc')
_add('E-OFFICIAL-REGION', 'Khu vực game chưa được hỗ trợ',
     'Bản game của bạn thuộc khu vực mà tính năng khôi phục chính thức chưa hỗ trợ.',
     [_REPORT],
     platform='pc')
_add('E-CANCELLED', 'Thao tác đã được huỷ',
     'Bạn (hoặc hệ thống) đã dừng thao tác. Game được giữ ở trạng thái an toàn.',
     ['Bấm lại nút tương ứng nếu muốn làm tiếp.'],
     level='info', platform='shared')

# --------------------------------------------------------------------------- misc (PC + shared)
_add('E-LAUNCH-FAILED', 'Không mở được game',
     'Launcher đã gửi lệnh mở game nhưng Windows hoặc Steam báo lỗi.',
     ['Mở game thủ công bằng Steam hoặc launcher của Yostar.',
      'Bản Steam: bảo đảm Steam đang chạy và đã đăng nhập.',
      'Kiểm tra phần mềm diệt virus có chặn StellaSora.exe không.', _SEND],
     platform='pc')
_add('E-SHORTCUT', 'Không tạo được lối tắt',
     'Launcher không tạo được lối tắt trên Màn hình. Tính năng này không ảnh hưởng tới việc cài bản dịch.',
     ['Thử chạy launcher bằng quyền Quản trị hoặc tạo lối tắt thủ công tới StellaSora.exe.'],
     level='warning', platform='pc')
_add('E-MEMORY', 'Máy không đủ bộ nhớ RAM',
     'Launcher hết bộ nhớ khi xử lý. Game chưa bị thay đổi.',
     ['Đóng bớt chương trình khác rồi thử lại.'],
     platform='pc')
_add('E-INTERNAL', 'Launcher gặp lỗi nội bộ',
     'Có lỗi ngoài dự kiến trong launcher. Game chưa bị thay đổi nếu thao tác chưa báo hoàn tất.',
     ['Đóng và mở lại launcher rồi thử lại.', _SEND],
     platform='shared')
_add('E-UNKNOWN', 'Lỗi chưa xác định',
     'Launcher chưa nhận ra loại lỗi này. Thông tin chi tiết được lưu trong mã lỗi để người hỗ trợ xem.',
     ['Thử lại một lần.', _SEND],
     platform='shared')

# --------------------------------------------------------------------------- Launcher v2.0 (PC-only)
_add('E-STARTUP-DLL', 'Không nạp được thư viện hệ thống / Qt khi khởi động',
     'Windows không tải được tệp thư viện giao diện (DLL của Qt/ICU hoặc gói hệ thống). Thường do thiếu tệp runtime Visual C++ / bản Windows cũ hoặc tệp hệ thống xung đột trong PATH.',
     ['Mở thư mục nhật ký để xem file startup_error.log và native_crash.log.',
      'Thử khởi động bằng chế độ đồ hoạ tương thích (--safe-graphics) hoặc tải lại bản EXE mới nhất.',
      'Cập nhật Windows và cài Microsoft Visual C++ Redistributable (x64), rồi thử lại.', _SEND],
     level='error', network=False, platform='pc')
_add('E-GPU-RENDER', 'Lỗi khởi tạo đồ họa phần cứng (đã bật chế độ tương thích)',
     'Lần mở trước bị thoát đột ngột khi khởi tạo GPU/OpenGL. Launcher đã tự chuyển sang chế độ vẽ phần mềm để hiển thị ổn định hơn.',
     ['Tiếp tục dùng ở chế độ đồ họa tương thích (hiệu năng ổn định trên card yếu/RDP).',
      'Cập nhật driver card đồ họa nếu muốn bật lại tăng tốc phần cứng trong Cài đặt.', _SEND],
     level='warning', network=False, platform='pc')
_add('E-BG-SYNC', 'Không đồng bộ được hình nền chính thức, đang dùng ảnh dự phòng',
     'Launcher không lấy được banner/hình nền mới từ máy chủ Yostar hoặc cache cục bộ nên đang hiển thị ảnh nền đi kèm.',
     ['Bấm "Kiểm tra kết nối & DNS" nếu muốn xem trạng thái mạng tới máy chủ Yostar.',
      'Hoặc tắt đồng bộ nền trong Cài đặt nếu bạn dùng mạng hạn chế.'],
     level='info', network=True, platform='pc')
_add('E-MIGRATION', 'Di trú dữ liệu từ phiên bản cũ gặp cảnh báo',
     'Quá trình chuyển cấu hình, sao lưu hoặc nhật ký từ phiên bản v1.3.4 có một vài mục cảnh báo. Dữ liệu gốc vẫn được giữ nguyên an toàn.',
     ['Kiểm tra lại đường dẫn game và kênh cập nhật trong Cài đặt.',
      'Nếu cấu hình cũ bị hỏng, bấm "Khôi phục cấu hình mặc định" (bản lỗi vẫn được sao lưu riêng).'],
     level='warning', network=False, platform='pc')
_add('E-NET-CAPTIVE', 'Mạng đang chặn hoặc chuyển hướng đăng nhập (Captive Portal)',
     'Máy chủ trả về một trang HTML đăng nhập/chuyển hướng mạng thay vì dữ liệu JSON hoặc tệp tải về.',
     ['Mở trình duyệt web và đăng nhập vào mạng Wi-Fi / cổng mạng đang dùng.',
      'Hoặc tắt bộ lọc web của router/nhà mạng, kiểm tra kết nối rồi thử lại.', _SEND],
     level='error', network=True, platform='pc')
_add('E-CFA-BLOCKED', 'Controlled Folder Access / Diệt virus chặn ghi tệp',
     'Thư mục có quyền NTFS bình thường nhưng Windows Defender (Controlled Folder Access) hoặc phần mềm diệt virus đang chặn launcher ghi tệp.',
     ['Mở Windows Security → Virus & threat protection → Ransomware protection → Allow an app through Controlled folder access, rồi thêm launcher.',
      'Hoặc thử chạy lại bằng quyền Quản trị và kiểm tra thư mục game.', _SEND],
     level='error', network=False, platform='pc')
_add('E-PARALLEL-DL', 'Tải song song gặp sự cố',
     'Nhiều luồng tải đồng thời bị gián đoạn do mạng hoặc lỗi ghi ổ đĩa. Các phần đã tải hợp lệ vẫn được giữ lại.',
     ['Bấm "Kiểm tra kết nối & DNS" để xác định đường truyền tới máy chủ.',
      'Kiểm tra dung lượng trống và quyền ghi thư mục game, rồi bấm thử lại.', _SEND],
     level='error', network=True, platform='pc')

# --------------------------------------------------------------------------- Android-only codes (28 entries, read-only parity with ERROR_CODES.md)
_add('E-DL-OVERSIZE', 'Tệp trên máy chủ lớn hơn kích thước công bố',
     'Dung lượng tải về vượt quá giới hạn công bố trong bảng kê nên ứng dụng dừng tải để đảm bảo an toàn.',
     ['Kiểm tra mạng (tránh proxy/cổng đăng nhập chèn dữ liệu) rồi thử lại.', _SEND],
     level='error', network=True, platform='android')
_add('E-DL-PARAM', 'Thông tin tải không hợp lệ',
     'Tham số tải về (URL hoặc kích thước tệp) không hợp lệ.',
     ['Cập nhật ứng dụng hoặc bảng kê mới nhất rồi thử lại.', _SEND],
     level='error', platform='android')
_add('E-NO-PACKAGE', 'Bản phát hành chưa có gói Android',
     'Bản phát hành trên GitHub chưa kèm gói bản dịch dành cho Android.',
     ['Chờ người làm bản dịch bổ sung gói Android.', _REPORT],
     level='error', platform='android')
_add('E-PKG-MISMATCH', 'Gói bản dịch không khớp phiên bản game trên máy',
     'Phiên bản game Stella Sora trên thiết bị Android không khớp với gói bản dịch hiện tại.',
     ['Cập nhật game lên phiên bản phù hợp rồi thử lại.', _SEND],
     level='error', platform='android')
_add('E-TIMEOUT', 'Thao tác quá thời hạn',
     'Thao tác trên thiết bị mất quá nhiều thời gian và bị huỷ.',
     ['Thử lại khi thiết bị rảnh hoặc kết nối ổn định hơn.', _SEND],
     level='error', platform='android')
_add('E-ADB', 'Lỗi Local ADB',
     'Kết nối Local ADB trên thiết bị Android gặp sự cố.',
     ['Kiểm tra Gỡ lỗi không dây (Wireless Debugging) và thử ghép đôi lại.', _SEND],
     level='error', platform='android')
_add('E-ADB-AUTH', 'Điện thoại chưa chấp nhận khoá Local ADB',
     'Thiết bị chưa cấp quyền cho khoá kết nối Local ADB.',
     ['Chấp nhận hộp thoại cho phép gỡ lỗi trên màn hình thiết bị.', _SEND],
     level='error', platform='android')
_add('E-ADB-INPUT', 'Thông tin kết nối Local ADB không hợp lệ',
     'Cổng hoặc mã ghép đôi Local ADB nhập vào không đúng định dạng.',
     ['Kiểm tra lại địa chỉ, cổng và mã 6 số trong Gỡ lỗi không dây.'],
     level='warning', platform='android')
_add('E-ADB-KEY', 'Khoá Local ADB gặp vấn đề',
     'Không thể tạo hoặc đọc khoá RSA dùng cho Local ADB.',
     ['Khởi động lại ứng dụng và ghép đôi lại.', _SEND],
     level='error', platform='android')
_add('E-ADB-NOT-CONNECTED', 'Chưa kết nối Local ADB',
     'Local ADB chưa kết nối tới thiết bị nên chưa thể truy cập thư mục dữ liệu game.',
     ['Bật Gỡ lỗi không dây và kết nối lại trong ứng dụng.'],
     level='warning', platform='android')
_add('E-ADB-PAIR', 'Ghép đôi chưa thành công',
     'Quá trình ghép đôi Local ADB thất bại hoặc hết hạn mã.',
     ['Mở lại màn hình ghép đôi mới trong Gỡ lỗi không dây và nhập mã kịp thời.', _SEND],
     level='error', platform='android')
_add('E-ADB-START', 'Không khởi động được Local ADB',
     'Không thể khởi chạy tiến trình Local ADB cục bộ.',
     ['Khởi động lại ứng dụng hoặc thiết bị rồi thử lại.', _SEND],
     level='error', platform='android')
_add('E-ADB-TIMEOUT', 'Local ADB không phản hồi',
     'Lệnh gửi qua Local ADB quá thời hạn chờ.',
     ['Kiểm tra kết nối Wi-Fi và bật lại Gỡ lỗi không dây.', _SEND],
     level='error', platform='android')
_add('E-DEVOPT', 'Chưa bật Tuỳ chọn nhà phát triển',
     'Thiết bị chưa kích hoạt Tuỳ chọn nhà phát triển (Developer Options).',
     ['Vào Cài đặt Android → Giới thiệu điện thoại → chạm Số bản dựng 7 lần để bật.'],
     level='warning', platform='android')
_add('E-BIND-MISMATCH', 'Nhật ký/bản sao lưu thuộc thiết bị hoặc thư mục khác',
     'Dữ liệu sao lưu hoặc nhật ký không khớp với thiết bị hoặc gói game hiện tại.',
     ['Kiểm tra đúng phiên bản game và thiết bị rồi thử lại.', _SEND],
     level='error', platform='android')
_add('E-GAME-ROOT-CHANGED', 'Thư mục dữ liệu game đã thay đổi',
     'Đường dẫn dữ liệu game trên Android đã thay đổi so với lúc bắt đầu thao tác.',
     ['Đóng game và thử lại thao tác từ đầu.', _SEND],
     level='error', platform='android')
_add('E-GAME-STATE', 'Không kiểm tra được trạng thái game',
     'Không đọc được trạng thái hiện tại của game qua hệ thống hoặc Local ADB.',
     ['Đảm bảo game đã cài đặt và Local ADB đang hoạt động.', _SEND],
     level='error', platform='android')
_add('E-GAME-VERSION', 'Chưa đọc được phiên bản game',
     'Không xác định được phiên bản Stella Sora trên thiết bị.',
     ['Mở game một lần để khởi tạo dữ liệu rồi kiểm tra lại.', _SEND],
     level='error', platform='android')
_add('E-NO-GAME', 'Chưa tìm thấy game Stella Sora',
     'Không tìm thấy gói Stella Sora cài đặt trên thiết bị Android.',
     ['Kiểm tra bạn đã cài đúng phiên bản game Stella Sora trên máy chưa.'],
     level='warning', platform='android')
_add('E-VER-CHANGED', 'Game đã cập nhật sau lần cài trước',
     'Phiên bản game đã thay đổi kể từ lần cài Việt hoá trước đó.',
     ['Kiểm tra bản dịch mới nhất và cài đặt lại.'],
     level='warning', platform='android')
_add('E-VERIFY', 'Không đối chiếu được tệp trên máy',
     'Không thể xác minh toàn vẹn các tệp game sau thao tác.',
     ['Đảm bảo Local ADB còn kết nối và thử kiểm tra lại.', _SEND],
     level='error', platform='android')
_add('E-NO-RECOVERY', 'Không có thao tác nào cần phục hồi',
     'Không phát hiện nhật ký thao tác dở dang nào cần khôi phục.',
     ['Bạn có thể tiếp tục sử dụng bình thường.'],
     level='info', platform='android')
_add('E-STORAGE-ACCESS', 'Ứng dụng chưa truy cập được vùng lưu trữ của nó',
     'Không có quyền đọc/ghi vùng lưu trữ nội bộ của ứng dụng.',
     ['Kiểm tra quyền lưu trữ của ứng dụng và dung lượng trống trên thiết bị.', _SEND],
     level='error', platform='android')
_add('E-APK-INVALID', 'Thông tin bản cập nhật ứng dụng không hợp lệ',
     'Metadata bản cập nhật APK thiếu hoặc sai định dạng.',
     ['Kiểm tra kênh cập nhật hoặc tải APK trực tiếp từ trang phát hành.', _SEND],
     level='error', platform='android')
_add('E-APK-NONE', 'Chưa có bản ứng dụng mới hơn',
     'Ứng dụng đang ở phiên bản mới nhất.',
     ['Không cần cập nhật thêm.'],
     level='info', platform='android')
_add('E-APK-SIGNATURE', 'Chữ ký APK không khớp',
     'Tệp APK tải về có chữ ký không khớp chữ ký phát hành chính thức.',
     ['Không cài APK này; hãy tải lại từ nguồn phát hành chính thức.', _SEND],
     level='error', platform='android')
_add('E-APK-VERIFY', 'APK tải về bị sai hoặc hỏng',
     'Mã kiểm tra SHA256 của tệp APK tải về không khớp.',
     ['Thử tải lại bản cập nhật APK.', _SEND],
     level='error', platform='android')
_add('E-UI-BLOCKED', 'Yêu cầu bị chặn',
     'Giao diện hệ thống đang chặn hộp thoại hoặc thao tác yêu cầu quyền.',
     ['Kiểm tra quyền hiển thị/cài đặt trên thiết bị rồi thử lại.', _SEND],
     level='error', platform='android')


# --------------------------------------------------------------------------- internal code -> catalog code
# Keys are the stable InstallerError.code values raised across the launcher core.
INTERNAL_MAP: dict[str, str] = {
    # network / release
    'ENDPOINT_INVALID': 'E-CONFIG-CHANNEL',
    'ENDPOINT_UNAVAILABLE': 'E-CONFIG-CHANNEL',
    'RELEASE_UNAVAILABLE': 'E-RELEASE',
    'RATE_LIMITED': 'E-HTTP-RATE',
    'SCHEMA_INVALID': 'E-DATA-SCHEMA',
    'METADATA_UNVERIFIED': 'E-DATA-UNVERIFIED',
    'RELEASE_ASSET_MISMATCH': 'E-DATA-SCHEMA',
    'MANIFEST_MISSING': 'E-MANIFEST-MISSING',
    'MANIFEST_INVALID': 'E-MANIFEST-INVALID',
    'EMPTY_MANIFEST': 'E-MANIFEST-INVALID',
    'VERSION_MISSING': 'E-MANIFEST-INVALID',
    'VERSION_INVALID': 'E-MANIFEST-VERSION',
    'PLATFORM_MISMATCH': 'E-MANIFEST-PLATFORM',
    'PATH_TRAVERSAL': 'E-SECURITY',
    'PATH_ESCAPE': 'E-SECURITY',
    'PATH_NOT_ALLOWED': 'E-SECURITY',
    'UNSAFE_PATH': 'E-SECURITY',
    'UNTRUSTED_URL': 'E-SECURITY',
    'ARCHIVE_INVALID': 'E-SECURITY',
    'DOWNGRADE_BLOCKED': 'E-DOWNGRADE',
    # download
    'HASH_MISMATCH': 'E-DL-VERIFY',
    'SIZE_MISMATCH': 'E-DL-VERIFY',
    'CORRUPT_PAYLOAD': 'E-DL-VERIFY',
    'DOWNLOAD_INCOMPLETE': 'E-DL-VERIFY',
    'DOWNLOAD_RANGE_INVALID': 'E-DL-RANGE',
    'DOWNLOAD_TIMEOUT': 'E-DL-TIMEOUT',
    'DOWNLOAD_INVALID': 'E-DL-RESPONSE',
    'DOWNLOAD_RESPONSE_INVALID': 'E-DL-RESPONSE',
    'DOWNLOAD_FAILED': 'E-DL-FAILED',
    'PAYLOAD_UNAVAILABLE': 'E-DL-FAILED',
    # game / install
    'INVALID_ROOT': 'E-NO-EXE',
    'GAME_RUNNING': 'E-GAME-RUNNING',
    'OPERATION_BUSY': 'E-BUSY',
    'RECOVERY_REQUIRED': 'E-RECOVERY-REQUIRED',
    'JOURNAL_CORRUPT': 'E-JOURNAL',
    'ROOT_MISMATCH': 'E-ROOT-MISMATCH',
    'BACKUP_INVALID': 'E-BACKUP',
    'BACKUP_CORRUPT': 'E-BACKUP',
    'BACKUP_MISSING': 'E-BACKUP',
    'PREIMAGE_CONFLICT': 'E-FILE-CHANGED',
    'SOURCE_CHANGED': 'E-FILE-CHANGED',
    'RESTORE_VERIFY_FAILED': 'E-VERIFY-WRITE',
    'READBACK_MISMATCH': 'E-VERIFY-WRITE',
    'READBACK_FAILED': 'E-VERIFY-WRITE',
    'STAGE_VERIFY_FAILED': 'E-VERIFY-WRITE',
    'TRANSACTION_FAILED': 'E-INSTALL-ROLLED-BACK',
    'NOT_VERIFIED': 'E-NO-RECEIPT',
    'FILE_MISMATCH': 'E-FILE-MISMATCH',
    'FILE_IN_USE': 'E-FILE-IN-USE',
    'FILE_ACCESS_DENIED': 'E-FILE-DENIED',
    'DISK_FULL': 'E-STORAGE',
    'NO_GAME_FOLDER': 'E-NO-GAME-FOLDER',
    'LAUNCH_FAILED': 'E-LAUNCH-FAILED',
    # self update
    'UPDATE_TIMEOUT': 'E-UPDATE-TIMEOUT',
    'UPDATE_INVALID': 'E-UPDATE-INVALID',
    'UPDATE_ERROR': 'E-UPDATE-INVALID',
    'UPDATE_UNSUPPORTED': 'E-UPDATE-UNSUPPORTED',
    'RELAUNCH_FAILED': 'E-UPDATE-RELAUNCH',
    'UPDATE_RECOVERY_REQUIRED': 'E-UPDATE-RECOVERY',
    # publisher data
    'NETWORK': 'E-OFFICIAL-NET',
    'METADATA_INCONSISTENT': 'E-OFFICIAL-INCONSISTENT',
    'NOT_FOUND': 'E-OFFICIAL-NOTFOUND',
    'METADATA_FORMAT': 'E-OFFICIAL-FORMAT',
    'MANIFEST_FORMAT': 'E-OFFICIAL-FORMAT',
    'METADATA_DECRYPT': 'E-OFFICIAL-FORMAT',
    'RESOLVE_FAILED': 'E-OFFICIAL-FORMAT',
    'PATCH_FAILED': 'E-OFFICIAL-FORMAT',
    'BSDIFF40': 'E-OFFICIAL-FORMAT',
    'BIN_DIFF_PATCH_INFO': 'E-OFFICIAL-FORMAT',
    'BIN_DIFF_PATCH_VER': 'E-OFFICIAL-FORMAT',
    'BIN_DIFF_PATCH_FILE': 'E-OFFICIAL-FORMAT',
    'CRYPTO_UNAVAILABLE': 'E-OFFICIAL-CRYPTO',
    'REGION_UNSUPPORTED': 'E-OFFICIAL-REGION',
    'CANCELLED': 'E-CANCELLED',
    # v2.0 additions
    'MIGRATION': 'E-MIGRATION',
    'NET_CAPTIVE': 'E-NET-CAPTIVE',
    'PARALLEL_DL': 'E-PARALLEL-DL',
    'SHORTCUT': 'E-SHORTCUT',
    'STARTUP_DLL': 'E-STARTUP-DLL',
    'GPU_RENDER': 'E-GPU-RENDER',
    'BG_SYNC': 'E-BG-SYNC',
    'CFA_BLOCKED': 'E-CFA-BLOCKED',
}

# These codes only wrap another failure; the real reason is deeper in the cause chain.
# PARALLEL_DL is intentionally NOT in _WRAPPER_CODES so pool-wide aborts diagnose as
# E-PARALLEL-DL while preserving the underlying cause in Diagnosis.chain.
_WRAPPER_CODES = frozenset({'TRANSACTION_FAILED', 'DOWNLOAD_FAILED', 'NETWORK'})

_HTTP_FAMILY = (
    (lambda c: c in (403, 429), 'E-HTTP-RATE'),
    (lambda c: c == 404, 'E-HTTP-404'),
    (lambda c: 500 <= c <= 599, 'E-HTTP-5XX'),
    (lambda c: 400 <= c <= 499, 'E-HTTP-4XX'),
)

_PUBLISHER = 'máy chủ nhà phát hành'


def _for_publisher(info: ErrorInfo) -> ErrorInfo:
    """Same network failure, but the host is the game publisher's server instead of GitHub."""
    if not info.network:
        return info
    steps = [s for s in info.steps if 'github.com' not in s.lower() and 'githubstatus' not in s.lower()]
    steps.insert(0, 'Kiểm tra Internet bằng cách mở một trang web bất kỳ trên trình duyệt.')
    return ErrorInfo(
        info.code,
        info.title.replace('GitHub', _PUBLISHER),
        info.summary.replace('GitHub', _PUBLISHER),
        tuple(s.replace('GitHub', _PUBLISHER) for s in steps),
        info.level,
        info.network,
        info.platform,
    )


def _safe_str(value, default: str = '') -> str:
    if value is None:
        return default
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return default


def _safe_bool(value, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def _safe_getattr(obj, name: str, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:  # noqa: BLE001
        return default


def _safe_opt_int(value) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if type(value) is int:
        return value
    if isinstance(value, int):
        try:
            v = int(value)
            return v if type(v) is int else None
        except Exception:  # noqa: BLE001
            return None
    return None


def lookup(code: Optional[str], subject: str = 'github') -> ErrorInfo:
    """Catalog entry for a (possibly specialised) code; never raises.

    ``subject='publisher'`` rewrites network wording for failures that talk to the game publisher's servers.
    """
    code = _safe_str(code, 'E-UNKNOWN') or 'E-UNKNOWN'
    info = _CATALOG.get(code)
    if info is None:
        m = re.fullmatch(r'E-HTTP-(\d{3})', code)
        if m:
            status = int(m.group(1))
            for pred, fam in _HTTP_FAMILY:
                if pred(status):
                    base = _CATALOG[fam]
                    info = ErrorInfo(
                        code,
                        base.title + f' (HTTP {status})',
                        base.summary,
                        base.steps,
                        base.level,
                        base.network,
                        base.platform,
                    )
                    break
    if info is None:
        info = _CATALOG['E-UNKNOWN']
    return _for_publisher(info) if subject == 'publisher' else info


def all_codes(platform: Optional[str] = None) -> list[str]:
    """Sorted catalog codes. Defaults to all 104 static codes (PC + Android)."""
    if platform is None:
        return sorted(_CATALOG)
    norm = _safe_str(platform).strip().lower()
    if norm == 'pc':
        return [c for c in sorted(_CATALOG) if _CATALOG[c].platform in ('pc', 'shared')]
    if norm == 'android':
        return [c for c in sorted(_CATALOG) if _CATALOG[c].platform in ('android', 'shared')]
    if norm == 'shared':
        return [c for c in sorted(_CATALOG) if _CATALOG[c].platform == 'shared']
    return [c for c in sorted(_CATALOG) if _CATALOG[c].platform == norm]


def pc_codes() -> list[str]:
    """Sorted list of the 76 PC-relevant static error codes."""
    return all_codes('pc')


# --------------------------------------------------------------------------- classification
def http_code(status) -> str:
    val = _safe_opt_int(status)
    if val is None and isinstance(status, str):
        try:
            val = int(_safe_str(status).strip())
        except (TypeError, ValueError):
            val = None
    if val is None:
        return 'E-NET'
    return f'E-HTTP-{val}'


def _is_dll_text(low: str) -> bool:
    if any(
        needle in low
        for needle in (
            'dll load failed',
            'the specified procedure could not be found',
            'the specified module could not be found',
            'is not a valid win32 application',
            'winerror 126',
            'winerror 127',
            'winerror 193',
            '[winerror 126]',
            '[winerror 127]',
            '[winerror 193]',
        )
    ):
        return True
    if 'could not find module' in low and (
        '.dll' in low or '.pyd' in low or 'dependencies' in low
    ):
        return True
    if any(tok in low for tok in ('pyside6', 'shiboken6', 'qtwidgets', 'qt6core', 'icuuc')) and any(
        err in low for err in ('import', 'dll', 'procedure', 'module', 'load failed', 'error')
    ):
        return True
    return False


def classify_text(text) -> Optional[str]:
    """Best-effort code for an error that survived only as a string; ``None`` if nothing matches."""
    t = _safe_str(text)
    if not t:
        return None
    low = t.lower()
    m = re.search(r'http error (\d{3})|\bhttp (\d{3})\b|mã (\d{3})\b', low)
    if m:
        return http_code(next(g for g in m.groups() if g))
    if _is_dll_text(low):
        return 'E-STARTUP-DLL'
    checks = (
        (('controlled folder access', 'ransomware protection', 'cfa_blocked'), 'E-CFA-BLOCKED'),
        (('captive portal', 'trang đăng nhập mạng', 'net_captive'), 'E-NET-CAPTIVE'),
        (('getaddrinfo failed', 'name or service not known', 'nodename nor servname', 'temporary failure in name resolution',
          '[errno 11001]', '[errno 11002]', '[errno 11004]', 'winerror 11001'), 'E-NET-DNS'),
        (('certificate_verify_failed', 'certificate verify failed', 'self signed certificate', 'unable to get local issuer'), 'E-NET-TLS-CERT'),
        (('tunnel connection failed', 'proxyerror', 'proxy authentication'), 'E-NET-PROXY'),
        ((r'\bssl\b', r'\btls\b', 'sslerror'), 'E-NET-TLS'),
        (('timed out', 'timeout', 'winerror 10060', '[errno 10060]', 'quá thời hạn'), 'E-NET-TIMEOUT'),
        (('connection refused', 'winerror 10061', '[errno 10061]', 'actively refused'), 'E-NET-REFUSED'),
        (('winerror 10013', '[errno 10013]', 'forbidden by its access permissions'), 'E-NET-BLOCKED'),
        (('network is unreachable', 'no route to host', 'winerror 10051', 'winerror 10065', '[errno 10051]', '[errno 10065]'), 'E-NET-OFFLINE'),
        (('forcibly closed', 'connection reset', 'connection aborted', 'remotedisconnected', 'incompleteread', 'winerror 10054', 'winerror 10053', 'broken pipe'), 'E-NET-RESET'),
        (('qsg_rhi', 'wglcreatecontext', 'graphics_boot_pending', 'lỗi khởi tạo đồ họa'), 'E-GPU-RENDER'),
        (('stellasora_launcher_candidate_r02', 'di trú dữ liệu'), 'E-MIGRATION'),
    )
    for needles, code in checks:
        for n in needles:
            if (n.startswith('\\b') and re.search(n, low)) or (not n.startswith('\\b') and n in low):
                return code
    return None


def _reason_exception(reason):
    return reason if isinstance(reason, BaseException) else None


def _probe_path_for_cfa(filename) -> bool:
    """Lazy lightweight check asking diagnostics if a denied path looks like Controlled Folder Access."""
    if os.name != 'nt':
        return False
    fname = _safe_str(filename)
    if not fname:
        return False
    try:
        from .diagnostics import probe_dir_writability

        from pathlib import Path
        p = Path(fname)
        target_dir = p if p.is_dir() else p.parent
        if not target_dir.is_dir():
            return False
        res = probe_dir_writability(target_dir)
        return bool(res.cfa_suspected or res.status == 'cfa_blocked')
    except Exception:  # noqa: BLE001
        return False


def _has_cfa_evidence(exc: BaseException, cfa_blocked: Optional[bool] = None) -> bool:
    if cfa_blocked is True:
        return True
    if cfa_blocked is False:
        return False
    if _safe_bool(_safe_getattr(exc, 'cfa_blocked', False)):
        return True
    fname = _safe_getattr(exc, 'filename', None)
    if fname is not None and _probe_path_for_cfa(fname):
        return True
    return False


def _is_dll_oserror(exc: OSError) -> bool:
    win = _safe_opt_int(_safe_getattr(exc, 'winerror', None))
    if win in (126, 127, 193):
        return True
    low = _safe_str(exc).lower()
    if isinstance(exc, FileNotFoundError) and 'could not find module' in low and (
        '.dll' in low or '.pyd' in low or 'dependencies' in low
    ):
        return True
    return _is_dll_text(low)


def classify_one(exc, *, cfa_blocked: Optional[bool] = None) -> Optional[str]:
    """Code for a single exception object (ignoring its causes) or ``None``."""
    if isinstance(exc, InstallerError):
        internal = _safe_str(_safe_getattr(exc, 'code', ''))
        if internal in _WRAPPER_CODES:
            return None
        exc_str = _safe_str(exc)
        if internal == 'NOT_VERIFIED' and ('không khớp' in exc_str or 'định dạng' in exc_str):
            return 'E-RECEIPT-MISMATCH'
        if internal == 'FILE_ACCESS_DENIED':
            if cfa_blocked is True or _safe_bool(_safe_getattr(exc, 'cfa_blocked', False)):
                return 'E-CFA-BLOCKED'
            if cfa_blocked is None:
                cause = _safe_getattr(exc, '__cause__', None)
                if cause is None and not _safe_bool(_safe_getattr(exc, '__suppress_context__', False)):
                    cause = _safe_getattr(exc, '__context__', None)
                if isinstance(cause, OSError):
                    win = _safe_opt_int(_safe_getattr(cause, 'winerror', None))
                    eno = _safe_opt_int(_safe_getattr(cause, 'errno', None))
                    if (isinstance(cause, PermissionError) or win == 5 or eno in (errno.EACCES, errno.EPERM)) and _has_cfa_evidence(cause, None):
                        return 'E-CFA-BLOCKED'
            return 'E-FILE-DENIED'
        mapped = INTERNAL_MAP.get(internal)
        if mapped:
            return mapped
        return None
    if isinstance(exc, ImportError):
        if _is_dll_text(_safe_str(exc).lower()):
            return 'E-STARTUP-DLL'
        return None
    win = _safe_opt_int(_safe_getattr(exc, 'winerror', None))
    if isinstance(exc, OSError) and win in (32, 33):     # unambiguous on Windows; errno 32 would otherwise look like EPIPE
        return 'E-FILE-IN-USE'
    if isinstance(exc, OSError) and _is_dll_oserror(exc):
        return 'E-STARTUP-DLL'
    if isinstance(exc, urllib.error.HTTPError):
        raw_code = _safe_getattr(exc, 'code', None)
        code_val = _safe_opt_int(raw_code)
        if code_val is None and isinstance(raw_code, str):
            try:
                code_val = int(_safe_str(raw_code).strip())
            except (TypeError, ValueError):
                code_val = None
        return 'E-NET-PROXY' if code_val == 407 else http_code(code_val)
    if isinstance(exc, urllib.error.URLError):
        inner = _reason_exception(_safe_getattr(exc, 'reason', None))
        if inner is not None:
            code = classify_one(inner, cfa_blocked=cfa_blocked)
            if code:
                return code
        return classify_text(_safe_str(_safe_getattr(exc, 'reason', None))) or 'E-NET'
    if isinstance(exc, ssl.SSLCertVerificationError):
        return 'E-NET-TLS-CERT'
    if isinstance(exc, ssl.SSLError):
        return 'E-NET-TLS-CERT' if 'CERTIFICATE' in _safe_str(exc).upper() else 'E-NET-TLS'
    if isinstance(exc, socket.gaierror):
        return 'E-NET-DNS'
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return 'E-NET-TIMEOUT'
    if isinstance(exc, ConnectionRefusedError):
        return 'E-NET-REFUSED'
    if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, http.client.IncompleteRead, http.client.RemoteDisconnected)):
        return 'E-NET-RESET'
    if isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError)):
        return 'E-DATA-JSON'
    if isinstance(exc, MemoryError):
        return 'E-MEMORY'
    if isinstance(exc, OSError):
        win = _safe_opt_int(_safe_getattr(exc, 'winerror', None))
        eno = _safe_opt_int(_safe_getattr(exc, 'errno', None))
        if win == 10013:
            return 'E-NET-BLOCKED'
        if win in (10051, 10050, 10065) or eno in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ENETDOWN):
            return 'E-NET-OFFLINE'
        if win == 10061:
            return 'E-NET-REFUSED'
        if win == 10060:
            return 'E-NET-TIMEOUT'
        if win in (10053, 10054):
            return 'E-NET-RESET'
        if win in (11001, 11002, 11004):
            return 'E-NET-DNS'
        if eno == errno.ENOSPC or win in (39, 112):
            return 'E-STORAGE'
        if win in (32, 33):
            return 'E-FILE-IN-USE'
        if isinstance(exc, PermissionError) or win == 5 or eno in (errno.EACCES, errno.EPERM):
            if _has_cfa_evidence(exc, cfa_blocked):
                return 'E-CFA-BLOCKED'
            return 'E-FILE-DENIED'
        if isinstance(exc, FileNotFoundError) or eno == errno.ENOENT:
            return 'E-FILE-MISSING'
        by_text = classify_text(_safe_str(exc))
        if by_text:
            return by_text
    return None


def exception_chain(exc, limit: int = 8) -> list[BaseException]:
    """Outermost-first list of the exception and its causes/contexts, without cycles."""
    out, seen = [], set()
    cur = exc
    while cur is not None and id(cur) not in seen and len(out) < limit:
        out.append(cur)
        seen.add(id(cur))
        nxt = _safe_getattr(cur, '__cause__', None)
        if nxt is None and not _safe_bool(_safe_getattr(cur, '__suppress_context__', False)):
            nxt = _safe_getattr(cur, '__context__', None)
        cur = nxt
    return out


def _trim(text, limit: int = 500) -> str:
    text = _safe_str(text).replace('\r', ' ').replace('\n', ' ').strip()
    return text if len(text) <= limit else text[:limit] + '…'


@dataclass
class Diagnosis:
    code: str
    info: ErrorInfo
    wrapper: str = ''                           # internal wrapper code such as TRANSACTION_FAILED / DOWNLOAD_FAILED
    subject: str = 'github'                     # 'github' | 'publisher'
    chain: list = field(default_factory=list)   # ["Type: message", ...] outermost first
    message: str = ''                           # outermost message, i.e. what used to be shown raw


def diagnose(exc, fallback: Optional[str] = None, subject: Optional[str] = None, *, cfa_blocked: Optional[bool] = None) -> Diagnosis:
    """Pick the single most useful catalog code for ``exc``.

    The real cause wins over wrappers: a TRANSACTION_FAILED raised ``from`` a locked-file OSError is reported as
    E-FILE-IN-USE, with the wrapper kept in ``Diagnosis.wrapper`` for the report.  ``fallback`` is a catalog code
    used only when nothing in the chain can be classified.
    """
    chain = exception_chain(exc) if isinstance(exc, BaseException) else []
    wrapper = ''
    chosen = None
    for item in chain:
        internal = _safe_str(_safe_getattr(item, 'code', '')) if isinstance(item, InstallerError) else ''
        if internal in _WRAPPER_CODES and not wrapper:
            wrapper = internal
        if chosen is None:
            chosen = classify_one(item, cfa_blocked=cfa_blocked)
    if chosen is None:
        for item in chain:               # nothing structural matched: try the text of the chain
            chosen = classify_text(_safe_str(item))
            if chosen:
                break
    if chosen is None and wrapper:
        chosen = INTERNAL_MAP.get(wrapper)
    if chosen is None:
        chosen = fallback
    if chosen is None:
        chosen = 'E-UNKNOWN' if (not chain or isinstance(chain[0], InstallerError)) else 'E-INTERNAL'
    if subject is None:
        subject = 'publisher' if any(type(i).__name__ == 'OfficialResourceError' for i in chain) else 'github'
    lines = [type(i).__name__ + ': ' + _trim(i) for i in chain]
    return Diagnosis(chosen, lookup(chosen, subject), wrapper, subject, lines, _trim(chain[0], 900) if chain else '')


def describe(exc) -> dict:
    """JSON-friendly summary of ``exc`` for storing in sync state (strings only)."""
    d = diagnose(exc)
    return {'code': d.code, 'chain': d.chain, 'message': d.message}
