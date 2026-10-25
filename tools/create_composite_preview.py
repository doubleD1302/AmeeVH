from PIL import Image
from pathlib import Path

bg_path = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\Xuat_Anh_Su_Kien_DustDawn\Tranh_Nen_Goc_2048x1451_bg_dustdawn_main_1.png")
logo_path = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\Xuat_Anh_Su_Kien_DustDawn\Logo_Tieu_De_Tieng_Viet_zs_dustdawn_main_logo_lang.png")

bg = Image.open(bg_path).convert("RGBA")
logo = Image.open(logo_path).convert("RGBA")

# In the user's banner, the aspect ratio is roughly 16:9, cropped slightly from top and bottom
# Let's crop bg to 16:9 (2048 x 1152) centered vertically
target_h = int(bg.width * 9 / 16)
crop_y = (bg.height - target_h) // 2 + 50
bg_169 = bg.crop((0, crop_y, bg.width, crop_y + target_h))

# Scale logo to match placement (in user banner, logo is about 50-55% of width)
logo_w = int(bg_169.width * 0.52)
logo_h = int(logo.height * (logo_w / logo.width))
logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

# Position logo horizontally centered, near lower-center
pos_x = (bg_169.width - logo_w) // 2
pos_y = int(bg_169.height * 0.55)

composite = bg_169.copy()
composite.alpha_composite(logo_resized, (pos_x, pos_y))

out_composite = Path(r"C:\Users\chann\.gemini\antigravity\brain\fedb6985-4403-4c7b-b3c0-549d2f56084c\composite_dustdawn_vi_preview.png")
composite.save(out_composite)
print("Saved composite preview to:", out_composite)
