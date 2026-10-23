import sys
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
code = p.read_text(encoding="utf-8")

# Fix the broken multiline string literals
broken_lines = [
    'self.log_ui(f"\n[1/3] Bắt đầu tải Bảng dữ liệu {tag} ({arcx_mb:.1f} MB)...")',
    'self.log_ui(f"\n[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")',
    'self.log_ui(f"\n[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")',
    'self.log_ui(f"\n==================================================")',
    'messagebox.showinfo("Thành Công", f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB gồm 3 phần) trực tiếp vào game thành công!\n\nBạn có thể khởi động game để trải nghiệm ngay.")'
]

# Let's replace the broken sections cleanly
target_bad = '''            # --- BƯỚC 1: TẢI VÀ ÁP DỤNG TABLES/DATA.ARCX ---
            self.log_ui(f"
[1/3] Bắt đầu tải Bảng dữ liệu {tag} ({arcx_mb:.1f} MB)...")'''

replacement_good = '''            # --- BƯỚC 1: TẢI VÀ ÁP DỤNG TABLES/DATA.ARCX ---
            self.log_ui("")
            self.log_ui(f"[1/3] Bắt đầu tải Bảng dữ liệu {tag} ({arcx_mb:.1f} MB)...")'''

code = code.replace(target_bad, replacement_good)

target_bad2 = '''            # --- BƯỚC 2: TẢI VÀ ÁP DỤNG SCRIPTS/LUA.ARCX ---
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                self.log_ui(f"
[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")'''

replacement_good2 = '''            # --- BƯỚC 2: TẢI VÀ ÁP DỤNG SCRIPTS/LUA.ARCX ---
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                self.log_ui("")
                self.log_ui(f"[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")'''

code = code.replace(target_bad2, replacement_good2)

target_bad3 = '''            # --- BƯỚC 3: TẢI VÀ ÁP DỤNG ASSETBUNDLES (ẢNH CHỮ) ---
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                self.log_ui(f"
[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")'''

replacement_good3 = '''            # --- BƯỚC 3: TẢI VÀ ÁP DỤNG ASSETBUNDLES (ẢNH CHỮ) ---
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                self.log_ui("")
                self.log_ui(f"[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")'''

code = code.replace(target_bad3, replacement_good3)

target_bad4 = '''            self.log_ui(f"
==================================================")
            self.log_ui(f"🎉 CHÚC MỪNG! ĐÃ CẬP NHẬT TRỌN VẸN {total_mb:.1f} MB VÀO GAME!")
            self.log_ui(f"   Game đã sẵn sàng với 100% tiếng Việt cho Bảng dữ liệu, Thoại nhân vật và Ảnh chữ!")
            self.log_ui(f"==================================================")
            messagebox.showinfo("Thành Công", f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB gồm 3 phần) trực tiếp vào game thành công!

Bạn có thể khởi động game để trải nghiệm ngay.")'''

replacement_good4 = '''            self.log_ui("")
            self.log_ui("==================================================")
            self.log_ui(f"🎉 CHÚC MỪNG! ĐÃ CẬP NHẬT TRỌN VẸN {total_mb:.1f} MB VÀO GAME!")
            self.log_ui("   Game đã sẵn sàng với 100% tiếng Việt cho Bảng dữ liệu, Thoại nhân vật và Ảnh chữ!")
            self.log_ui("==================================================")
            msg_ok = f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB gồm 3 phần) trực tiếp vào game thành công!\\n\\nBạn có thể khởi động game để trải nghiệm ngay."
            messagebox.showinfo("Thành Công", msg_ok)'''

code = code.replace(target_bad4, replacement_good4)

p.write_text(code, encoding="utf-8")
print("Fixed string literals in launcher_pc.py")
