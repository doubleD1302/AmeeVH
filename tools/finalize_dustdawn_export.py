import shutil
from pathlib import Path

out_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\Xuat_Anh_Su_Kien_DustDawn")
out_dir.mkdir(parents=True, exist_ok=True)

src_bg = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\dustdawn_dump\ui_activity_20104__bg_dustdawn_main_1.png")
src_logo_vi = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\dustdawn_dump\ui_activity_20104.en__zs_dustdawn_main_logo_lang.png")

dst_bg = out_dir / "Tranh_Nen_Goc_2048x1451_bg_dustdawn_main_1.png"
dst_logo_vi = out_dir / "Logo_Tieu_De_Tieng_Viet_zs_dustdawn_main_logo_lang.png"

shutil.copy(src_bg, dst_bg)
shutil.copy(src_logo_vi, dst_logo_vi)

# Create an info file
info_txt = out_dir / "THONG_TIN_ASSET.md"
info_txt.write_text("""# THÔNG TIN TRÍCH XUẤT BANNER SỰ KIỆN DUSTDAWN

Ảnh bạn gửi là banner chính thức của sự kiện/chương truyện đặc biệt:
**Main Story Special Chapter: Wholeness at Reunion's Dawn** (Cập nhật ngày 19/10/2026).

Trong cấu trúc dữ liệu Unity của game Stella Sora, ảnh này không phải là một bức ảnh phẳng đơn lẻ mà được ghép từ 2 asset chính trong AssetBundle:

## 1. Tranh nền gốc chất lượng cao (Không có chữ)
* **File AssetBundle**: `ui_activity_20104.unity3d`
* **Vị trí file bundle trong game**:
  * `Persistent_Store\\AssetBundles\\ui_activity_20104.unity3d`
  * `StellaSora_Data\\StreamingAssets\\InstallResource\\ui_activity_20104.unity3d`
* **Tên Asset Texture2D**: `bg_dustdawn_main_1`
* **Độ phân giải**: **2048 x 1451** (chất lượng gốc siêu nét)
* **Đã trích xuất ra**: `Tranh_Nen_Goc_2048x1451_bg_dustdawn_main_1.png`

## 2. Logo chữ tiêu đề (Language Overlay)
* **File AssetBundle**: `ui_activity_20104.en.unity3d`
* **Tên Asset Texture2D / Sprite**: `zs_dustdawn_main_logo_lang`
* **Độ phân giải**: **730 x 363**
* **Nội dung gốc (EN)**:
  * Phía trên: *Main Story Special Chapter*
  * Tiêu đề: *Wholeness at Reunion's Dawn*
* **Bản dịch tiếng Việt trong dự án**:
  * Phía trên: *Sự Kiện Cập Nhật Truyện Chính*
  * Tiêu đề: *Bình Minh Đoàn Viên Trọn Vẹn*
* **Đã trích xuất ra**: `Logo_Tieu_De_Tieng_Viet_zs_dustdawn_main_logo_lang.png`
""", encoding="utf-8")

print("Files successfully exported to:", out_dir)
