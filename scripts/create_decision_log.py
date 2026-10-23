import json
import os
import datetime

out_dir = "StellaSora_VietHoa/work/editorial/lightnovel_editorial_20261024_r02"
os.makedirs(out_dir, exist_ok=True)
decision_log_path = os.path.join(out_dir, "EDITORIAL_DECISION_LOG.jsonl")

decisions = [
    {
        "decision_id": "ED_DEC_001",
        "timestamp": "2026-10-24T00:20:00+07:00",
        "domain": "story_partitioning",
        "topic": "Độc lập phân vùng 4 subagent dịch song song",
        "rationale": "Chia 5.558 dòng thành 4 phân vùng độc lập 100% ID (A1: 1758 dòng, A2: 1503 dòng, B1: 1008 dòng, B2: 1289 dòng) để tối đa hóa tốc độ và chuyên môn hóa giọng kể từng nhân vật.",
        "status": "APPROVED"
    },
    {
        "decision_id": "ED_DEC_002",
        "timestamp": "2026-10-24T00:30:00+07:00",
        "domain": "character_voice",
        "topic": "Xưng hô Amber - Iris - Player",
        "rationale": "Amber và Iris xưng 'cậu - tớ', phản ánh đúng tình bạn đồng trang lứa từ viện mồ côi. Gọi Player là 'anh / cậu / Đội trưởng' tùy phân cảnh, không rải đại từ nũng nịu vô căn cứ.",
        "status": "APPROVED"
    },
    {
        "decision_id": "ED_DEC_003",
        "timestamp": "2026-10-24T00:40:00+07:00",
        "domain": "character_voice",
        "topic": "Khẩu khí Tilia & Treant Cự Tháp",
        "rationale": "Tilia giữ tác phong kỵ sĩ tập sự nghiêm cẩn, thanh cao, khao khát công lý. Treant và Ý Chí Cổ Xưa dùng giọng trầm mặc, uy nghiêm, giữ đúng ngôi vị ngàn năm.",
        "status": "APPROVED"
    },
    {
        "decision_id": "ED_DEC_004",
        "timestamp": "2026-10-24T01:00:00+07:00",
        "domain": "qa_gate_a",
        "topic": "Thẩm định độc lập Cốt truyện chính (QA Reviewer A)",
        "rationale": "QA Reviewer A duyệt 100% Hồi 1 (mẫu vàng), đồng thời phát hiện 106 lỗi trượt chỉ mục kỹ thuật ở Hồi 2, yêu cầu tác giả Translator 2 sửa đổi R02.",
        "status": "RESOLVED_IN_R02"
    },
    {
        "decision_id": "ED_DEC_005",
        "timestamp": "2026-10-24T01:15:00+07:00",
        "domain": "style_slang_purge",
        "topic": "Loại bỏ triệt để từ lóng mạng và tiếng bồi",
        "rationale": "Sửa toàn bộ các từ lóng 'quẩy' (STm02_04.34), 'bựa đời' (CG_150_02.13), 'bay màu', 'cà khịa' sang từ vựng văn học Light Novel bền vững với thời gian.",
        "status": "APPROVED"
    },
    {
        "decision_id": "ED_DEC_006",
        "timestamp": "2026-10-24T01:25:00+07:00",
        "domain": "qa_gate_b",
        "topic": "Thẩm định độc lập Hẹn hò & Ký sự CG (QA Reviewer B)",
        "rationale": "QA Reviewer B duyệt 100% 100 cảnh Hẹn hò/Tháp Sao; phát hiện 4 cảnh CG có tình tiết phóng tác (Minova) và vỡ nhịp hài (Laru), yêu cầu tác giả sửa đổi R02.",
        "status": "RESOLVED_IN_R02"
    },
    {
        "decision_id": "ED_DEC_007",
        "timestamp": "2026-10-24T01:40:00+07:00",
        "domain": "technical_tokens",
        "topic": "Bảo toàn 100% mã lệnh Unity AVG và Token động",
        "rationale": "Toàn bộ ==PLAYER_NAME==, ==SEX...==, <size>, <color>, {0}, {1}, ep_..., fx_..., city_alley_... được kiểm định đạt 100% số lượng và vị trí hiển thị.",
        "status": "APPROVED"
    }
]

with open(decision_log_path, "w", encoding="utf-8") as f:
    for d in decisions:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

print(f"Created {decision_log_path} with {len(decisions)} decision records.")
