#!/usr/bin/env python3
"""Comprehensive 100% UI Translator for Stella Sora - Complete Polish.

Translates remaining untranslated UIText strings via:
1. Multi-tier English and Chinese grammar templates
2. Game mode and event title translation
3. Tooltip and guidance phrase translation
4. Repacking data.arcx with full XXTEA encryption
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import repack_archive

# Pattern substitutions (English -> Vietnamese)
EN_PATTERNS = [
    # Time & Countdown
    (re.compile(r"^Available in (<color=[^>]+>)?\{([0-9a-zA-Z_]+)\}(</color>)?\s*([dhms]|min|d|h|m|s|sec|days?|hours?|mins?|secs?)?$", re.IGNORECASE),
     lambda m: f"Mở sau {m.group(1) or ''}{{{m.group(2)}}}{m.group(3) or ''} {m.group(4) or ''}".strip()),
    (re.compile(r"^Event starts in:?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Sự kiện bắt đầu sau: {\1}"),
    (re.compile(r"^Ends in:?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Kết thúc sau: {\1}"),
    (re.compile(r"^Expires in:?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Hết hạn sau: {\1}"),
    (re.compile(r"^Remaining time:?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Thời gian còn lại: {\1}"),
    (re.compile(r"^Cooldown:?\s*\{([0-9a-zA-Z_]+)\}s$", re.IGNORECASE),
     r"Hồi chiêu: {\1}s"),
    
    # Event & State Notifications
    (re.compile(r"^The (.+) event has ended$", re.IGNORECASE),
     r"Sự kiện \1 đã kết thúc"),
    (re.compile(r"^The (.+) has ended$", re.IGNORECASE),
     r"\1 đã kết thúc"),
    (re.compile(r"^The event has not started$", re.IGNORECASE),
     r"Sự kiện chưa bắt đầu"),
    (re.compile(r"^The (.+) event has not started$", re.IGNORECASE),
     r"Sự kiện \1 chưa bắt đầu"),
    (re.compile(r"^The (.+) is not available$", re.IGNORECASE),
     r"\1 hiện chưa mở"),
    (re.compile(r"^Not started$", re.IGNORECASE),
     r"Chưa bắt đầu"),
    (re.compile(r"^Not open$", re.IGNORECASE),
     r"Chưa mở"),
    (re.compile(r"^In progress$", re.IGNORECASE),
     r"Đang tiến hành"),
    
    # Selection & Prompts
    (re.compile(r"^Please select a (.+)$", re.IGNORECASE),
     r"Vui lòng chọn một \1"),
    (re.compile(r"^Please select (.+)$", re.IGNORECASE),
     r"Vui lòng chọn \1"),
    (re.compile(r"^Tap anywhere to (.+)$", re.IGNORECASE),
     r"Chạm bất kỳ đâu để \1"),
    (re.compile(r"^Tap screen to (.+)$", re.IGNORECASE),
     r"Chạm vào màn hình để \1"),
    (re.compile(r"^Tap to (.+)$", re.IGNORECASE),
     r"Chạm để \1"),
    (re.compile(r"^Click to (.+)$", re.IGNORECASE),
     r"Nhấp để \1"),
    (re.compile(r"^Select anywhere to (.+)$", re.IGNORECASE),
     r"Chạm bất kỳ đâu để \1"),
    
    # Requirements & Unlocks
    (re.compile(r"^Reach Authorization Lv\.?\s*(<[^>]+>)?\{([0-9a-zA-Z_]+)\}(<[^>]+>)?( to unlock)?$", re.IGNORECASE),
     lambda m: f"Mở khóa khi đạt Cấp Quyền hạn {m.group(1) or ''}{{{m.group(2)}}}{m.group(3) or ''}"),
    (re.compile(r"^Unlocks at Authorization Lv\.?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Mở khóa ở Cấp Quyền hạn {\1}"),
    (re.compile(r"^Unlocks at Lv\.?\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Mở khóa ở Cấp {\1}"),
    (re.compile(r"^Clear (.+) to unlock$", re.IGNORECASE),
     r"Vượt \1 để mở khóa"),
    (re.compile(r"^Complete (.+) to unlock$", re.IGNORECASE),
     r"Hoàn thành \1 để mở khóa"),
    
    # Upgrades & Stats
    (re.compile(r"^\+([0-9]+)%? (.+)$"),
     r"+\1% \2"),
    (re.compile(r"^Increases (.+) by \{([0-9a-zA-Z_]+)\}%?$", re.IGNORECASE),
     r"Tăng \1 thêm {\2}%"),
    (re.compile(r"^Reduces (.+) by \{([0-9a-zA-Z_]+)\}%?$", re.IGNORECASE),
     r"Giảm \1 đi {\2}%"),
    (re.compile(r"^Owned:\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Đang có: {\1}"),
    (re.compile(r"^Current:\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Hiện tại: {\1}"),
    (re.compile(r"^Next:\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Tiếp theo: {\1}"),
    (re.compile(r"^Cost:\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Tiêu hao: {\1}"),
    (re.compile(r"^Level:\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Cấp: {\1}"),
    (re.compile(r"^Lv\.\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Cấp {\1}"),
    (re.compile(r"^Floor\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Tầng {\1}"),
    (re.compile(r"^Stage\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Ải {\1}"),
    (re.compile(r"^Wave\s*\{([0-9a-zA-Z_]+)\}$", re.IGNORECASE),
     r"Đợt {\1}"),
]

# Chinese substring dictionary
CN_SUBSTRINGS = [
    ("点击任意位置继续", "Chạm bất kỳ đâu để tiếp tục"),
    ("点击屏幕继续", "Chạm vào màn hình để tiếp tục"),
    ("点击空白处关闭", "Chạm vùng trống để đóng"),
    ("点击空白处继续", "Chạm vùng trống để tiếp tục"),
    ("活动未开始", "Sự kiện chưa bắt đầu"),
    ("活动已结束", "Sự kiện đã kết thúc"),
    ("暂未开放", "Chưa mở khóa"),
    ("待开放", "Chưa mở khóa"),
    ("敬请期待", "Sắp ra mắt"),
    ("暂无数据", "Chưa có dữ liệu"),
    ("暂无记录", "Chưa có kỷ lục"),
    ("网络连接失败", "Kết nối mạng thất bại"),
    ("网络异常", "Mạng bất thường"),
    ("正在重连", "Đang kết nối lại..."),
    ("正在加载", "Đang tải..."),
    ("材料不足", "Nguyên liệu không đủ"),
    ("金币不足", "Vàng không đủ"),
    ("钻石不足", "Kim Cương không đủ"),
    ("体力不足", "Thể lực không đủ"),
    ("干劲不足", "Năng lượng không đủ"),
    ("背包已满", "Túi đồ đã đầy"),
    ("仓库已满", "Kho đồ đã đầy"),
    ("已达上限", "Đã đạt giới hạn"),
    ("权限等级不足", "Cấp Quyền hạn không đủ"),
    ("等级不足", "Cấp độ không đủ"),
    ("条件不满足", "Chưa đủ điều kiện"),
    ("暂无可领取奖励", "Không có phần thưởng để nhận"),
    ("一键领取", "Nhận tất cả"),
    ("一键装备", "Mặc nhanh"),
    ("一键卸下", "Gỡ nhanh"),
    ("一键强化", "Cường hóa nhanh"),
    ("一键分解", "Phân giải nhanh"),
    ("自动填充", "Tự động điền"),
    ("快速战斗", "Chiến đấu nhanh"),
    ("重新开始", "Chơi lại"),
    ("确定要放弃", "Bạn có chắc muốn bỏ cuộc không?"),
    ("确定要退出", "Bạn có chắc muốn thoát không?"),
    ("确定要购买", "Bạn có chắc muốn mua không?"),
    ("确定要重置", "Bạn có chắc muốn đặt lại không?"),
    ("确认放弃", "Xác nhận bỏ cuộc"),
    ("确认退出", "Xác nhận thoát"),
    ("确认购买", "Xác nhận mua"),
    ("确认重置", "Xác nhận đặt lại"),
    ("豪礼抛物线", "Vòng cung thịnh vượng"),
    ("甜心梦工坊", "Xưởng kẹo ngọt"),
    ("月华窃梦人", "Kẻ trộm trăng"),
    ("幸运寻宝铲", "Xẻng tìm kho báu"),
    ("心危擂台", "Võ đài nguy hiểm"),
    ("终焉绝响", "Âm vang hồi kết"),
    ("联合讨伐", "Liên kích Boss"),
    ("灾变防线", "Phòng tuyến sinh tồn"),
    ("尖兵陷阵", "Tiên phong hãm trận"),
    ("猎影合围", "Chiến dịch vây bóng"),
    ("命运星牌局", "Bộ bài định mệnh"),
    ("巅峰秀场", "Sân khấu đỉnh cao"),
    ("真格挑战", "Thử thách thực chiến"),
    ("浅试身手", "Thử nghiệm nhân vật"),
    ("时装试玩", "Trải nghiệm thời trang"),
    ("星塔探索", "Thám hiểm tinh tháp"),
    ("星塔研究", "Nghiên cứu tinh tháp"),
    ("宝藏图鉴", "Kho báu"),
    ("回收清单", "Danh sách thu hồi"),
]

# Additional specific phrases
MORE_PHRASES = {
    "Start Packing": "Bắt đầu đóng gói",
    "Start the Defense": "Bắt đầu phòng thủ",
    "Start Turn": "Bắt đầu lượt",
    "Start Run": "Bắt đầu lượt chạy",
    "Start Show": "Bắt đầu biểu diễn",
    "Start Invitation": "Bắt đầu lời mời",
    "Start Challenge": "Bắt đầu khiêu chiến",
    "Start Game": "Bắt đầu trò chơi",
    "Start Battle": "Bắt đầu chiến đấu",
    "Restart Battle": "Chiến đấu lại",
    "Restart this match?": "Bắt đầu lại trận đấu này?",
    "Tap here to start the game!": "Chạm vào đây để bắt đầu trò chơi!",
    "Tap the button above to start": "Chạm vào nút phía trên để bắt đầu",
    "Tap [Start Show] to go live!": "Chạm [Bắt đầu biểu diễn] để lên sàn!",
    "No download content selected": "Chưa chọn nội dung cần tải",
    "No downloadable content": "Không có nội dung để tải",
    "Preset selection canceled.": "Đã hủy lựa chọn thiết lập sẵn.",
    "Project: Start Up": "Dự án: Khởi nghiệp",
    "Startup Grant": "Quỹ khởi nghiệp",
    "Starter Grant": "Quỹ người mới",
    "Starting Chips +{num_0}": "Chip ban đầu +{num_0}",
    "Starting Plans": "Kế hoạch ban đầu",
    "Starting Plan": "Kế hoạch ban đầu",
    "Clear this stage?": "Vượt qua ải này?",
    "Confirm Result": "Xác nhận kết quả",
    "Confirm & Claim": "Xác nhận & Nhận",
    "Selection Confirmed": "Đã xác nhận chọn",
    "Not Started": "Chưa bắt đầu",
    "The event has not started": "Sự kiện chưa bắt đầu",
    "Event Details": "Chi tiết sự kiện",
    "Craft Materials": "Chế tạo vật liệu",
    "Close": "Đóng",
    "Details": "Chi tiết",
    "Notice": "Thông báo",
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
    "Restart": "Chơi lại",
    "Restart?": "Chơi lại?",
}


def translate_entry_full(k: str, en: str, cn: str) -> str:
    en_s = en.strip()
    cn_s = cn.strip() if cn else ""
    
    # 1. More phrases exact
    if en_s in MORE_PHRASES:
        return MORE_PHRASES[en_s]
        
    # 2. Chinese exact substring matches
    for cn_sub, vi_sub in CN_SUBSTRINGS:
        if cn_s == cn_sub:
            return vi_sub
            
    # 3. Pattern match
    for pat, repl in EN_PATTERNS:
        if pat.search(en_s):
            if callable(repl):
                return pat.sub(repl, en_s)
            return pat.sub(repl, en_s)
            
    # 4. Partial Chinese match for key dialogs
    if cn_s:
        for cn_sub, vi_sub in CN_SUBSTRINGS:
            if cn_sub in cn_s and len(cn_s) < len(cn_sub) + 10:
                # If tags exist, preserve them
                tags = re.findall(r'<[^>]+>|\{[^}]+\}', en_s)
                if not tags:
                    return vi_sub

    return en


def run_polish():
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
            
        new_v = translate_entry_full(k, v, cn_data.get(k, ""))
        if new_v != v:
            en_data[k] = new_v
            translated += 1
            
    en_file.write_text(json.dumps(en_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Total Vietnamese entries in UIText: {translated}/{total} ({translated/total*100:.1f}%)")
    
    # Repack
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
    run_polish()
