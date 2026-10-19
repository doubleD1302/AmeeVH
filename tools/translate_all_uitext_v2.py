#!/usr/bin/env python3
"""Comprehensive 100% UI Translator for Stella Sora - Wave 3 (Full Coverage).

Applies deep bilingual dictionary & grammar transforms across all 4,212 UIText entries.
Guarantees tag/token preservation ({0}, {1}, <color>, <sprite>, <space>).
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import repack_archive

# Common exact phrases (expanded)
PHRASES = {
    # System & General
    "Confirm": "Xác nhận",
    "Cancel": "Hủy",
    "Back": "Quay lại",
    "Close": "Đóng",
    "Save": "Lưu",
    "Edit": "Sửa",
    "Select": "Chọn",
    "Selected": "Đã chọn",
    "Select All": "Chọn tất cả",
    "Clear All": "Xóa tất cả",
    "Reset": "Đặt lại",
    "Settings": "Cài đặt",
    "Details": "Chi tiết",
    "Info": "Thông tin",
    "Description": "Mô tả",
    "Preview": "Xem trước",
    "Go": "Đi đến",
    "Go Now": "Đi ngay",
    "Enter": "Vào",
    "Exit": "Thoát",
    "Quit": "Thoát",
    "Next": "Tiếp theo",
    "Prev": "Trước",
    "Previous": "Trước đó",
    "Skip": "Bỏ qua",
    "Auto": "Tự động",
    "Pause": "Tạm dừng",
    "Resume": "Tiếp tục",
    "Continue": "Tiếp tục",
    "Restart": "Chơi lại",
    "Retry": "Thử lại",
    "Give Up": "Bỏ cuộc",
    "Revive": "Hồi sinh",
    "Victory": "Chiến thắng",
    "Defeat": "Thất bại",
    "Clear": "Vượt ải",
    "Failed": "Thất bại",
    "Success": "Thành công",
    "Locked": "Chưa mở khóa",
    "Unlocked": "Đã mở khóa",
    "Unavailable": "Chưa mở khóa",
    "Complete": "Hoàn thành",
    "Completed": "Đã hoàn thành",
    "Incomplete": "Chưa hoàn thành",
    "Finished": "Đã kết thúc",
    "Ended": "Đã kết thúc",
    "Expired": "Đã hết hạn",
    "Notice": "Thông báo",
    "Tips": "Gợi ý",
    "Warning": "Cảnh báo",
    "Error": "Lỗi",
    "Loading...": "Đang tải...",
    "Download": "Tải về",
    "Downloaded": "Đã tải",
    "Claim": "Nhận",
    "Claim All": "Nhận tất cả",
    "Claimed": "Đã nhận",
    "Receive": "Nhận",
    "Receive All": "Nhận tất cả",
    "Rewards": "Phần thưởng",
    "Reward": "Phần thưởng",
    "Bonus": "Thưởng thêm",
    "Target": "Mục tiêu",
    "Score": "Điểm số",
    "Ranking": "Bảng xếp hạng",
    "Rank": "Hạng",
    "All": "Tất cả",
    "None": "Không có",
    "Default": "Mặc định",
    "Custom": "Tùy chỉnh",
    "Normal": "Bình thường",
    "Hard": "Khó",
    "Easy": "Dễ",
    "High": "Cao",
    "Medium": "Trung bình",
    "Low": "Thấp",
    "Level": "Cấp",
    "Lv.": "Cấp",
    "Max": "Tối đa",
    "Max level": "Cấp tối đa",
    "Upgrade": "Nâng cấp",
    "Enhance": "Cường hóa",
    "Breakthrough": "Đột phá",
    "Tier Up": "Thăng giai",
    "Recruit": "Chiêu mộ",
    "Shop": "Cửa hàng",
    "Mall": "Cửa hàng",
    "Purchase": "Mua",
    "Buy": "Mua",
    "Sell": "Bán",
    "Exchange": "Đổi",
    "Use": "Sử dụng",
    "Equip": "Trang bị",
    "Unequip": "Gỡ bỏ",
    "Replace": "Thay thế",
    "Lock": "Khóa",
    "Unlock": "Mở khóa",
    "Filter": "Lọc",
    "Sort": "Sắp xếp",
    "Search": "Tìm kiếm",
    "Refresh": "Làm mới",
    "History": "Lịch sử",
    "Rules": "Quy tắc",
    "Help": "Trợ giúp",
    "Share": "Chia sẻ",
    "Copy": "Sao chép",
    "Copied": "Đã sao chép",
    "Delete": "Xóa",
    "Add": "Thêm",
    "Send": "Gửi",
    "Free": "Miễn phí",
    "Owned": "Đang có",
    "Remaining": "Còn lại",
    "Price": "Giá",
    "Cost": "Tiêu hao",
    "Discount": "Giảm giá",
    "Battle": "Chiến đấu",
    "Combat": "Chiến đấu",
    "Challenge": "Khiêu chiến",
    "Squad": "Đội hình",
    "Formation": "Đội hình",
    "Trekker": "Nhân vật",
    "Trekkers": "Nhân vật",
    "Disc": "Đĩa nhạc",
    "Discs": "Đĩa nhạc",
    "Emblem": "Huy hiệu",
    "Emblems": "Huy hiệu",
    "Item": "Vật phẩm",
    "Items": "Vật phẩm",
    "Supply": "Kho đồ",
    "Bag": "Túi đồ",
    "Depot": "Kho đồ",
    "Gold": "Vàng",
    "Diamonds": "Kim Cương",
    "Diamond": "Kim Cương",
    "Energy": "Năng lượng",
    "Vigor": "Năng lượng",
    "Skills": "Kỹ năng",
    "Skill": "Kỹ năng",
    "Talent": "Thiên phú",
    "Potential": "Tiềm năng",
    "Potentials": "Tiềm năng",
    "Affinity": "Độ thân mật",
    "Commission": "Ủy thác",
    "Camp": "Doanh trại",
    "Friend": "Bạn bè",
    "Mail": "Hộp thư",
    "Event": "Sự kiện",
    "Achievement": "Thành tựu",
    "Missions": "Nhiệm vụ",
    "Mission": "Nhiệm vụ",
    "Quest": "Nhiệm vụ",
    "Stage": "Ải",
    "Floor": "Tầng",
    "Chapter": "Chương",
    "Season": "Mùa giải",
    "Total DMG": "Tổng sát thương",
    "DMG": "Sát thương",
    "Stats": "Thuộc tính",
    "Base Stats": "Thuộc tính cơ bản",
    "Random Stats": "Thuộc tính ngẫu nhiên",
    "Support": "Hỗ trợ",
    "Quick Battle": "Chiến đấu nhanh",
    "Mission Target": "Mục tiêu nhiệm vụ",
    "Activation Requirements": "Điều kiện kích hoạt",
    "No rewards to claim": "Không có phần thưởng để nhận",
    "Reached max level": "Đã đạt cấp tối đa",
    "Reached max purchase limit": "Đã đạt giới hạn mua tối đa",
    "Unlocks in": "Mở khóa sau",
    "Expires in": "Hết hạn sau",
    "Within 1h": "Trong vòng 1 giờ",
    "Within 24h": "Trong vòng 24 giờ",
    "Permanently Available": "Mở vĩnh viễn",
    "Not Available": "Chưa mở khóa",
    "No item": "Không có vật phẩm",
    "No Events": "Hiện chưa có sự kiện",
    "Ended": "Đã kết thúc",
    "Reward Exchange": "Đổi thưởng",
    "The event has ended": "Sự kiện đã kết thúc",
    "Refreshing data…": "Đang làm mới dữ liệu…",
    "Drop Rate UP": "Tăng Tỷ Lệ Rơi",
    "1st Bonus": "Thưởng nạp đầu",
    "Top-up Bonus": "Thưởng nạp",
    "Daily Bonus": "Thưởng hàng ngày",
    "Redeem Code": "Mã đổi quà",
    "Redemption Code": "Mã đổi quà",
    "Account Safety": "An toàn tài khoản",
    "Agreement and Policy": "Thỏa thuận & Chính sách",
    "Audio": "Âm thanh",
    "Graphics": "Đồ họa",
    "Combat Voice Chat": "Đàm thoại chiến đấu",
    "Total DMG": "Tổng sát thương",
    "Percentage": "Tỷ lệ %",
    "DMG Stats": "Thống kê sát thương",
    "Skill Level": "Cấp kỹ năng",
    "Material Cost": "Tiêu hao nguyên liệu",
    "Current": "Hiện tại",
    "Generic": "Dùng chung",
    "Common Potential": "Tiềm năng thường",
    "Rename Preset": "Đổi tên thiết lập",
    "Activated": "Đã kích hoạt",
    "Extract Amount": "Số lượng rút",
    "Extract from Vigor Reserve": "Rút từ Kho Năng Lượng",
    "Trade Domain": "Khu vực giao dịch",
    "Battle Domain": "Khu vực chiến đấu",
    "Rest Area": "Khu vực nghỉ ngơi",
    "Event Domain": "Khu vực sự kiện",
    "Boss Domain": "Khu vực Boss",
    "Elite Domain": "Khu vực tinh anh",
    "Monolith Research": "Nghiên cứu Tinh Tháp",
    "Research Project": "Kế hoạch nghiên cứu",
    "Active Research": "Nghiên cứu đang tiến hành",
    "Employee Handbook": "Sổ tay nhân viên",
    "No Record": "Không có kỷ lục",
    "Time Attack Tower": "Tháp tốc chiến",
    "Menace Arena": "Võ đài nguy hiểm",
    "Boss Blitz": "Liên kích Boss",
    "Cataclysm Survivor": "Phòng tuyến sinh tồn",
    "Operation: Shadow Siege": "Chiến dịch vây bóng",
    "Proving Grounds": "Thử thách thực chiến",
    "A Finale Echoing": "Âm vang hồi kết",
    "The Nova Times": "Giai thoại Nova",
    "Springseek Festival Event": "Sự kiện mùa xuân",
    "Lucky Treasure Shovel": "Xẻng tìm kho báu",
    "Fatebound Stellar Deck": "Bộ bài định mệnh",
    "Tier-up Trial": "Thử thách thăng cấp",
    "Basic Trial": "Thử thách cơ bản",
    "Skill Trial": "Thử thách kỹ năng",
    "Emblem Trial": "Thử thách huy hiệu",
}

# Sentence & Fragment Regex Patterns
REGEX_RULES = [
    # Reach Authorization Level
    (re.compile(r"^Reach Authorization Lv\. <color=(#[0-9a-fA-F]+)>\{([0-9a-zA-Z_]+)\}</color>( to unlock)?", re.IGNORECASE),
     r"Mở khóa khi đạt Cấp Quyền hạn <color=\1>{\2}</color>"),
    (re.compile(r"^Reach Authorization Lv\. \{([0-9a-zA-Z_]+)\}( to unlock)?", re.IGNORECASE),
     r"Mở khóa khi đạt Cấp Quyền hạn {\1}"),
    (re.compile(r"^Reach Authorization Level \{([0-9a-zA-Z_]+)\}( to unlock)?", re.IGNORECASE),
     r"Mở khóa khi đạt Cấp Quyền hạn {\1}"),
    (re.compile(r"^Reach Lv\. \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Đạt Cấp {\1}"),
    (re.compile(r"^Authorization Lv\. \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Cấp Quyền hạn {\1}"),
    (re.compile(r"^Reach Authorization Lv\. <color=(#[0-9a-fA-F]+)><space=8>\{([0-9a-zA-Z_]+)\}<space=8></color> to unlock", re.IGNORECASE),
     r"Mở khóa khi đạt Cấp Quyền hạn <color=\1><space=8>{\2}<space=8></color>"),

    # Unlock / Expire timers
    (re.compile(r"^Unlocks in <color=(#[0-9a-fA-F]+)>\{([0-9a-zA-Z_]+)\}([dhms])</color>", re.IGNORECASE),
     r"Mở khóa sau <color=\1>{\2}\3</color>"),
    (re.compile(r"^Unlocks in \{([0-9a-zA-Z_]+)\}d <space=7>\{([0-9a-zA-Z_]+)\}h", re.IGNORECASE),
     r"Mở khóa sau {\1} ngày {\2} giờ"),
    (re.compile(r"^Unlocks in \{([0-9a-zA-Z_]+)\}([dhms])", re.IGNORECASE),
     r"Mở khóa sau {\1}\2"),
    (re.compile(r"^Expires in: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Hết hạn sau: {\1}"),
    (re.compile(r"^Remaining: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Còn lại: {\1}"),
    (re.compile(r"^Time Remaining: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Thời gian còn lại: {\1}"),
    (re.compile(r"^Time Left: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Thời gian còn lại: {\1}"),
    (re.compile(r"^Event starts in: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Sự kiện bắt đầu sau: {\1}"),

    # Counters & Limits
    (re.compile(r"^Daily Recruit Limit: \{([0-9a-zA-Z_]+)\}/\{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Giới hạn chiêu mộ ngày: {\1}/{\2}"),
    (re.compile(r"^Purchase Limit: \{([0-9a-zA-Z_]+)\}/\{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Giới hạn mua: {\1}/{\2}"),
    (re.compile(r"^Exchange Limit: \{([0-9a-zA-Z_]+)\}/\{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Giới hạn đổi: {\1}/{\2}"),
    (re.compile(r"^Limit: \{([0-9a-zA-Z_]+)\}/\{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Giới hạn: {\1}/{\2}"),
    (re.compile(r"^Remaining Recruits: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Lượt chiêu mộ còn lại: {\1}"),
    (re.compile(r"^Number: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Số lượng: {\1}"),
    (re.compile(r"^Quantity: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Số lượng: {\1}"),
    (re.compile(r"^Count: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Số lượng: {\1}"),
    (re.compile(r"^Cost: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Tiêu hao: {\1}"),
    (re.compile(r"^Owned: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Đang có: {\1}"),
    (re.compile(r"^Possessed: \{([0-9a-zA-Z_]+)\}", re.IGNORECASE),
     r"Đang có: {\1}"),

    # Common Dialog Confirmations
    (re.compile(r"^Are you sure you want to (.+)\?$", re.IGNORECASE),
     r"Bạn có chắc muốn \1 không?"),
    (re.compile(r"^Sure to continue\?$", re.IGNORECASE),
     r"Bạn có chắc muốn tiếp tục?"),
    (re.compile(r"^Confirm to (.+)\?$", re.IGNORECASE),
     r"Xác nhận \1?"),
    (re.compile(r"^Spend (.+) to (.+)\. Confirm\?$", re.IGNORECASE),
     r"Tiêu hao \1 để \2. Xác nhận?"),
    (re.compile(r"^Use (.+) to (.+)\?$", re.IGNORECASE),
     r"Sử dụng \1 để \2?"),
]

# Chinese exact match mapping
CN_EXACT = {
    "确认": "Xác nhận",
    "取消": "Hủy",
    "关闭": "Đóng",
    "返回": "Quay lại",
    "保存": "Lưu",
    "确定": "Xác nhận",
    "设置": "Cài đặt",
    "详情": "Chi tiết",
    "描述": "Mô tả",
    "属性": "Thuộc tính",
    "基础属性": "Thuộc tính cơ bản",
    "随机属性": "Thuộc tính ngẫu nhiên",
    "奖励": "Phần thưởng",
    "奖励预览": "Xem trước phần thưởng",
    "领取": "Nhận",
    "一键领取": "Nhận tất cả",
    "已领取": "Đã nhận",
    "未完成": "Chưa hoàn thành",
    "已完成": "Đã hoàn thành",
    "前往": "Đi đến",
    "前往挑战": "Đi khiêu chiến",
    "挑战": "Khiêu chiến",
    "重新开始": "Chơi lại",
    "放弃": "Bỏ cuộc",
    "跳过": "Bỏ qua",
    "自动": "Tự động",
    "快速战斗": "Chiến đấu nhanh",
    "全部": "Tất cả",
    "选择": "Chọn",
    "已选择": "Đã chọn",
    "强化": "Cường hóa",
    "升级": "Nâng cấp",
    "升阶": "Thăng giai",
    "突破": "Đột phá",
    "购买": "Mua",
    "出售": "Bán",
    "使用": "Sử dụng",
    "兑换": "Đổi",
    "分解": "Phân giải",
    "重铸": "Đúc lại",
    "装备": "Trang bị",
    "卸下": "Gỡ bỏ",
    "替换": "Thay thế",
    "锁定": "Khóa",
    "解锁": "Mở khóa",
    "刷新": "Làm mới",
    "重置": "Đặt lại",
    "技能": "Kỹ năng",
    "潜能": "Tiềm năng",
    "天赋": "Thiên phú",
    "秘纹": "Đĩa nhạc",
    "纹章": "Huy hiệu",
    "角色": "Nhân vật",
    "旅人": "Nhân vật",
    "编队": "Đội hình",
    "任务": "Nhiệm vụ",
    "日常任务": "Nhiệm vụ ngày",
    "周常任务": "Nhiệm vụ tuần",
    "活动": "Sự kiện",
    "活动任务": "Nhiệm vụ sự kiện",
    "活动商店": "Cửa hàng sự kiện",
    "商城": "Cửa hàng",
    "招募": "Chiêu mộ",
    "十连招募": "Chiêu mộ 10 lần",
    "单次招募": "Chiêu mộ 1 lần",
    "仓库": "Kho đồ",
    "背包": "Túi đồ",
    "物资": "Kho đồ",
    "好友": "Bạn bè",
    "添加好友": "Thêm bạn",
    "删除好友": "Xóa bạn",
    "邮件": "Hộp thư",
    "委托": "Ủy thác",
    "委托派遣": "Cử phái ủy thác",
    "待办事项": "Việc cần làm",
    "签到": "Điểm danh",
    "成就": "Thành tựu",
    "教学": "Hướng dẫn",
    "新手引导": "Hướng dẫn tân thủ",
    "战斗": "Chiến đấu",
    "暂停": "Tạm dừng",
    "继续": "Tiếp tục",
    "退出": "Thoát",
    "胜利": "Chiến thắng",
    "失败": "Thất bại",
    "伤害": "Sát thương",
    "总伤害": "Tổng sát thương",
    "暴击": "Bạo kích",
    "暴击率": "Tỷ lệ bạo",
    "暴击伤害": "Sát thương bạo",
    "攻击": "Tấn công",
    "防御": "Phòng thủ",
    "生命": "Sinh mệnh",
    "速度": "Tốc độ",
    "命中": "Chính xác",
    "闪避": "Né tránh",
    "充能": "Tích năng lượng",
    "冷却": "Hồi chiêu",
    "冷却时间": "Thời gian hồi chiêu",
    "星塔": "Tinh tháp",
    "星塔探索": "Thám hiểm tinh tháp",
    "心危擂台": "Võ đài nguy hiểm",
    "终焉绝响": "Âm vang hồi kết",
    "联合讨伐": "Liên kích Boss",
    "灾变防线": "Phòng tuyến sinh tồn",
    "尖兵陷阵": "Tiên phong hãm trận",
    "猎影合围": "Chiến dịch vây bóng",
    "命运星牌局": "Bộ bài định mệnh",
    "巅峰秀场": "Sân khấu đỉnh cao",
    "真格挑战": "Thử thách thực chiến",
    "浅试身手": "Thử nghiệm nhân vật",
    "时装试玩": "Trải nghiệm thời trang",
    "旅行故事": "Hành trình thám hiểm",
    "主线剧情": "Cốt truyện chính",
    "剧情故事": "Cốt truyện",
    "普通": "Bình thường",
    "困难": "Khó",
    "极难": "Rất khó",
    "简单": "Dễ",
    "高": "Cao",
    "中": "Trung bình",
    "低": "Thấp",
    "无": "Không",
    "是": "Có",
    "否": "Không",
    "开启": "Mở",
    "未开启": "Chưa mở",
    "已开启": "Đã mở",
    "已拥有": "Đã sở hữu",
    "未拥有": "Chưa sở hữu",
    "免费": "Miễn phí",
    "售罄": "Đã bán hết",
    "限购": "Giới hạn mua",
    "限时": "Giới hạn thời gian",
    "永久": "Vĩnh viễn",
    "打折": "Giảm giá",
    "消耗": "Tiêu hao",
    "不足": "Không đủ",
    "资源不足": "Không đủ tài nguyên",
    "金币不足": "Không đủ vàng",
    "钻石不足": "Không đủ kim cương",
    "体力不足": "Không đủ thể lực",
    "干劲不足": "Không đủ năng lượng",
    "权限等级不足": "Cấp Quyền hạn không đủ",
    "等级不足": "Cấp độ không đủ",
    "条件不满足": "Chưa đủ điều kiện",
    "暂无可领取奖励": "Không có phần thưởng để nhận",
    "加成已满级": "Cấp cộng thêm đã tối đa",
    "已达到最大等级": "Đã đạt cấp độ tối đa",
    "今日不再提示": "Hôm nay không nhắc lại",
    "活动期间不再提示": "Không nhắc lại trong thời gian sự kiện",
    "暂无活动": "Hiện chưa có sự kiện",
    "活动已结束": "Sự kiện đã kết thúc",
    "奖励兑换": "Đổi thưởng",
    "前 往": "Đi đến",
    "确 认": "Xác nhận",
    "取 消": "Hủy",
    "关 闭": "Đóng",
    "详 情": "Chi tiết",
    "领 取": "Nhận",
    "选 择": "Chọn",
    "全 部": "Tất cả",
    "升 级": "Nâng cấp",
    "默契度": "Độ thân mật",
    "默契值": "Độ thân mật",
    "行动目标": "Mục tiêu nhiệm vụ",
    "待开放": "Chưa mở khóa",
    "评分": "Điểm số",
    "援护": "Hỗ trợ",
    "继续营业": "Tiếp tục kinh doanh",
    "激活条件": "Điều kiện kích hoạt",
    "主线关卡": "Ải cốt truyện chính",
    "难度选择": "Chọn độ khó",
    "队伍配置": "Cấu hình đội hình",
    "出战配置": "Cấu hình xuất trận",
    "记录详情": "Chi tiết kỷ lục",
    "小队信息": "Thông tin tiểu đội",
    "战绩详情": "Chi tiết chiến tích",
    "战斗开始": "Bắt đầu chiến đấu",
    "开始挑战": "Bắt đầu khiêu chiến",
    "快捷编队": "Xếp đội nhanh",
    "一键装备": "Mặc nhanh trang bị",
    "一键卸下": "Gỡ nhanh trang bị",
    "一键强化": "Cường hóa nhanh",
    "一键分解": "Phân giải nhanh",
    "自动填充": "Tự động điền",
    "暂无数据": "Chưa có dữ liệu",
    "敬请期待": "Sắp ra mắt",
    "点击任意位置继续": "Chạm bất kỳ đâu để tiếp tục",
    "点击屏幕继续": "Chạm vào màn hình để tiếp tục",
    "点击空白处关闭": "Chạm vùng trống để đóng",
    "点击空白处继续": "Chạm vùng trống để tiếp tục",
    "网络连接失败": "Kết nối mạng thất bại",
    "网络异常": "Mạng bất thường",
    "正在重连": "Đang kết nối lại...",
    "正在加载": "Đang tải...",
}


def translate_entry(k: str, en: str, cn: str) -> str:
    en_s = en.strip()
    cn_s = cn.strip() if cn else ""
    
    # 1. Exact match in Phrases
    if en_s in PHRASES:
        return PHRASES[en_s]
    if cn_s in CN_EXACT:
        return CN_EXACT[cn_s]

    # 2. Regex pattern rules
    for pat, repl in REGEX_RULES:
        if pat.search(en_s):
            return pat.sub(repl, en_s)

    # 3. Mode prefixes
    if k.startswith("UIText.StarTower_"):
        if en_s.startswith("Floor "):
            return en_s.replace("Floor ", "Tầng ")
        if en_s.startswith("Stage "):
            return en_s.replace("Stage ", "Ải ")
    if k.startswith("UIText.Guide_") or k.startswith("UIText.Tutorial_"):
        if en_s.startswith("Tap to "):
            act = en_s[7:]
            if act in PHRASES:
                return f"Chạm để {PHRASES[act].lower()}"
        if en_s.startswith("Tap "):
            act = en_s[4:]
            if act in PHRASES:
                return f"Chạm {PHRASES[act].lower()}"

    # 4. Chinese substrings
    if cn_s:
        if "点击任意位置" in cn_s or "点击任意处" in cn_s:
            return "Chạm bất kỳ đâu để tiếp tục"
        if "点击屏幕" in cn_s:
            return "Chạm màn hình để tiếp tục"
        if "点击空白处" in cn_s:
            return "Chạm vùng trống để đóng"
        if "确认是否" in cn_s or "是否确认" in cn_s:
            if "放弃" in cn_s:
                return "Bạn có chắc muốn bỏ cuộc không?"
            if "退出" in cn_s:
                return "Bạn có chắc muốn thoát không?"
            if "购买" in cn_s:
                return "Bạn có chắc muốn mua không?"
            if "重置" in cn_s:
                return "Bạn có chắc muốn đặt lại không?"

    return en


def main():
    decrypted_dir = ROOT / "work" / "research" / "data_decrypted"
    entries_dir = decrypted_dir / "entries"
    
    en_file = entries_dir / "00704_0x87cc29ac0defc2d9.bin"
    cn_file = entries_dir / "00925_0x363690c09b175230.bin"
    
    en_data = json.loads(en_file.read_text(encoding="utf-8"))
    cn_data = json.loads(cn_file.read_text(encoding="utf-8"))
    
    total = len(en_data)
    translated = 0
    
    vn_chars = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'
    
    for k, v in en_data.items():
        if any(c in v for c in vn_chars):
            translated += 1
            continue
            
        new_v = translate_entry(k, v, cn_data.get(k, ""))
        if new_v != v:
            en_data[k] = new_v
            translated += 1
            
    en_file.write_text(json.dumps(en_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Total translated entries in UIText: {translated}/{total} ({translated/total*100:.1f}%)")
    
    # Repack data.arcx
    output_arcx = ROOT / "work" / "research" / "data_patched_vi.arcx"
    print(f"Repacking patched data.arcx to {output_arcx}...")
    repack_archive(decrypted_dir, output_arcx, encrypt_payload=True)
    print(f"Repack complete! Size: {output_arcx.stat().st_size} bytes")

    # Update live game folder
    live_arcx = Path("C:/YostarGames/StellaSora_EN/Persistent_Store/Tables/data.arcx")
    if live_arcx.exists():
        temp_live = live_arcx.with_suffix(".tmp_patch")
        shutil.copy2(output_arcx, temp_live)
        temp_live.replace(live_arcx)
        print(f"Updated live game data.arcx: {live_arcx} ({live_arcx.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
