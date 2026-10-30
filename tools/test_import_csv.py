import csv
from pathlib import Path
import subprocess

p = Path("StellaSora_VietHoa/work/test_sample.csv")
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Màn (Phân đoạn)", "Mã câu (ID) [Khóa]", "Chủ thể / Người nói (Ai nói) 🗣️", "Lời thoại gốc (EN/JP) [Khóa]", "Bản dịch cũ (Tham khảo) [Khóa]", "BẢN DỊCH MỚI (⭐ SỬA Ở ĐÂY)", "Trạng thái", "Ghi chú & Thảo luận"])
    w.writerow(["🌟 MÀN TEST", "", "", "", "", "", "", ""])
    w.writerow(["STm03_00_a", "STm03_00_a.1", "Noya", "Hello world, test!", "Xin chào thế giới!", "Xin chào thế giới!", "Đã duyệt", ""])

res = subprocess.run(["gsheets", "mutate", "import-csv", "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM", str(p), "--sheet", "Chuong_3_MainStory"], capture_output=True, text=True, encoding="utf-8", shell=True)
print("stdout:", res.stdout)
print("stderr:", res.stderr)
