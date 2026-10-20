import re
from pathlib import Path

launcher_path = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
text = launcher_path.read_text(encoding="utf-8")

# 1. Update imports
old_imp = "from tkinter import messagebox, ttk"
new_imp = "from tkinter import filedialog, messagebox, ttk"
assert old_imp in text, "old_imp not found"
text = text.replace(old_imp, new_imp, 1)

# 2. Update DEFAULT_CONFIG
old_cfg = '''DEFAULT_CONFIG = {
    "version": "0.7.0",
    "app_name": "Stella Sora Việt Hóa - Multiplatform Launcher",'''
new_cfg = '''DEFAULT_CONFIG = {
    "version": "0.8.0",
    "app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher",'''
assert old_cfg in text, "old_cfg not found"
text = text.replace(old_cfg, new_cfg, 1)

# 3. Add save_config, get_steam_libraries, find_potential_game_paths after load_config
target_after_load_config = '''    return DEFAULT_CONFIG.copy()'''
replacement_load_config = '''    return DEFAULT_CONFIG.copy()


def save_config(new_config: dict):
    """Saves updated launcher configuration."""
    global CONFIG_FILE
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(new_config, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        DiagnosticCollector.log(f"Lỗi lưu cấu hình: {e}")


def get_steam_libraries() -> list[Path]:
    """Detects all Steam library directories from Registry and libraryfolders.vdf."""
    libraries = []
    default_steams = [
        Path(r"C:\\Program Files (x86)\\Steam"),
        Path(r"C:\\Program Files\\Steam"),
    ]
    try:
        import winreg
        for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root_key, r"Software\\Valve\\Steam") as key:
                    val, _ = winreg.QueryValueEx(key, "SteamPath")
                    if val:
                        p = Path(val)
                        if p.exists() and p not in default_steams:
                            default_steams.insert(0, p)
            except Exception:
                pass
    except Exception:
        pass

    for steam_root in default_steams:
        if not steam_root.exists():
            continue
        if steam_root not in libraries:
            libraries.append(steam_root)
        vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'"path"\\s+"([^"]+)"', content):
                    raw_p = m.group(1).replace("\\\\\\\\", "\\\\")
                    lib_p = Path(raw_p)
                    if lib_p.exists() and lib_p not in libraries:
                        libraries.append(lib_p)
            except Exception:
                pass
    return libraries


def find_potential_game_paths() -> list[dict]:
    """Returns detected Stella Sora game installations (Steam, Yostar, Config)."""
    found = []
    seen = set()

    def add_candidate(path: Path, source_label: str):
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        res_str = str(resolved).lower()
        if res_str in seen:
            return
        seen.add(res_str)

        has_exe = (resolved / "StellaSora.exe").exists()
        has_store = (resolved / "Persistent_Store").exists()
        has_data = (resolved / "StellaSora_Data").exists()
        is_valid = has_exe or has_store or has_data

        edition = "Bản Tùy Chọn"
        if "steamapps" in res_str or "steam" in res_str:
            edition = "Bản Steam PC"
        elif "yostargames" in res_str or "stellasora_en" in res_str:
            edition = "Bản Yostar PC"

        found.append({
            "path": resolved,
            "label": f"{source_label} ({edition})",
            "edition": edition,
            "exists": resolved.exists(),
            "is_valid_game": is_valid
        })

    # 1. Configured default path
    cfg = load_config()
    cfg_p = Path(cfg.get("default_game_path", r"C:\\YostarGames\\StellaSora_EN"))
    add_candidate(cfg_p, "Thư Mục Đang Chọn")

    # 2. Standalone paths
    add_candidate(Path(r"C:\\YostarGames\\StellaSora_EN"), "Yostar Standalone [C:]")
    add_candidate(Path(r"D:\\YostarGames\\StellaSora_EN"), "Yostar Standalone [D:]")
    add_candidate(Path(r"F:\\YostarGames\\StellaSora_EN"), "Yostar Standalone [F:]")

    # 3. Steam paths
    for lib in get_steam_libraries():
        steam_game = lib / "steamapps" / "common" / "Stella Sora"
        add_candidate(steam_game, f"Steam Library [{lib.drive}]")

    return found'''
assert target_after_load_config in text, "target_after_load_config not found"
text = text.replace(target_after_load_config, replacement_load_config, 1)

# 4. Replace detect_game_info with enhanced version
old_detect = '''def detect_game_info(game_path: Path) -> dict:
    info = {
        "exists": game_path.exists(),
        "client_ver": "Unknown",
        "game_ver": "Unknown",
        "res_ver": "Unknown",
        "is_running": False,
        "installed_patch": False,
        "backup_count": 0,
    }
    if not game_path.exists():
        return info

    # Check running process
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq StellaSora.exe" /NH', shell=True).decode()
        info["is_running"] = "StellaSora.exe" in out
    except Exception:
        info["is_running"] = False

    # Check client version
    launcher_cfg = game_path / "game-launcher-config.json"
    if launcher_cfg.exists():
        try:
            d = json.loads(launcher_cfg.read_text(encoding="utf-8"))
            info["client_ver"] = d.get("version", "Unknown")
        except Exception:
            pass

    # Check manifest version
    mani = game_path / "Persistent_Store" / "ss_win.mani"
    if mani.exists():
        try:
            lines = mani.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[:10]:
                if "GAME_VER" in line:
                    parts = line.split("|")
                    for p in parts:
                        if p.startswith("GAME_VER"):
                            info["game_ver"] = p.split()[-1]
                        elif p.startswith("RES_VER"):
                            info["res_ver"] = p.split()[-1]
        except Exception:
            pass

    # Check installed patch marker
    patch_marker = game_path / "Persistent_Store" / "viethoa_installed.json"
    info["installed_patch"] = patch_marker.exists()

    # Count backups
    if BACKUP_DIR.exists():
        info["backup_count"] = len([d for d in BACKUP_DIR.iterdir() if d.is_dir()])

    return info'''

new_detect = '''def detect_game_info(game_path: Path) -> dict:
    info = {
        "exists": game_path.exists(),
        "client_ver": "Unknown",
        "game_ver": "Unknown",
        "res_ver": "Unknown",
        "is_running": False,
        "installed_patch": False,
        "backup_count": 0,
        "edition": "Không xác định",
        "is_steam": False,
        "has_game_data": False,
    }
    if not game_path.exists():
        return info

    path_lower = str(game_path).lower()
    if "steamapps" in path_lower or "steam" in path_lower:
        info["edition"] = "Bản Steam PC"
        info["is_steam"] = True
    elif "yostargames" in path_lower or "stellasora_en" in path_lower:
        info["edition"] = "Bản Yostar Standalone"
        info["is_steam"] = False
    else:
        info["edition"] = "Bản PC Tùy Chọn"
        info["is_steam"] = False

    has_exe = (game_path / "StellaSora.exe").exists()
    has_store = (game_path / "Persistent_Store").exists()
    info["has_game_data"] = has_exe or has_store

    # Check running process
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq StellaSora.exe" /NH', shell=True).decode()
        info["is_running"] = "StellaSora.exe" in out
    except Exception:
        info["is_running"] = False

    # Check client version from Yostar config if available
    launcher_cfg = game_path / "game-launcher-config.json"
    if launcher_cfg.exists():
        try:
            d = json.loads(launcher_cfg.read_text(encoding="utf-8"))
            info["client_ver"] = d.get("version", "Unknown")
        except Exception:
            pass

    # Fallback 1: Read prefs.dat (present in all PC builds including Steam)
    prefs_file = game_path / "prefs.dat"
    if prefs_file.exists():
        try:
            lines = prefs_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                if line.startswith("LOCAL_CLIENT_VERSION:"):
                    if info["client_ver"] == "Unknown":
                        info["client_ver"] = line.split(":", 1)[1].strip()
                elif line.startswith("LOCAL_GAME_VERSION:"):
                    if info["game_ver"] == "Unknown":
                        info["game_ver"] = line.split(":", 1)[1].strip()
                elif line.startswith("LOCAL_CLIENT_RESOURCE_VERSION:"):
                    if info["res_ver"] == "Unknown":
                        info["res_ver"] = line.split(":", 1)[1].strip()
        except Exception:
            pass

    # Fallback 2: Check manifest version
    mani = game_path / "Persistent_Store" / "ss_win.mani"
    if mani.exists():
        try:
            lines = mani.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[:15]:
                if "GAME_VER" in line:
                    parts = line.split("|")
                    for p in parts:
                        if p.startswith("GAME_VER"):
                            info["game_ver"] = p.split()[-1]
                        elif p.startswith("RES_VER"):
                            info["res_ver"] = p.split()[-1]
        except Exception:
            pass

    # Check installed patch marker
    patch_marker = game_path / "Persistent_Store" / "viethoa_installed.json"
    info["installed_patch"] = patch_marker.exists()

    # Count backups
    if BACKUP_DIR.exists():
        info["backup_count"] = len([d for d in BACKUP_DIR.iterdir() if d.is_dir()])

    return info


def launch_game(game_path: Path) -> tuple[bool, str]:
    """Launches Stella Sora via Steam protocol or direct executable."""
    info = detect_game_info(game_path)
    exe_file = game_path / "StellaSora.exe"

    if info["is_steam"]:
        try:
            webbrowser.open("steam://rungameid/4813850")
            DiagnosticCollector.log("Đã phát lệnh khởi động qua giao thức Steam (AppID 4813850)")
            return True, "Đang khởi động trò chơi qua Steam Client..."
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khởi động qua Steam: {e}")

    if exe_file.exists():
        try:
            subprocess.Popen([str(exe_file)], cwd=str(game_path))
            DiagnosticCollector.log(f"Đã khởi động trực tiếp file thực thi: {exe_file}")
            return True, "Đã khởi động Stella Sora thành công!"
        except Exception as e:
            return False, f"Không thể khởi động game: {e}"
    else:
        return False, f"Không tìm thấy file StellaSora.exe tại: {game_path}"'''

assert old_detect in text, "old_detect not found"
text = text.replace(old_detect, new_detect, 1)

# 5. Update DiagnosticCollector.generate_report
old_diag_report = '''        report = [
            "### 🛠️ Báo Cáo Chẩn Đoán Lỗi Việt Hóa Stella Sora",
            f"- **Thời gian**: `{timestamp}`",
            f"- **Hệ điều hành**: `{platform.system()} {platform.release()} ({platform.version()})`",
            f"- **Kiến trúc**: `{platform.machine()}`",
            f"- **Python**: `{platform.python_version()}`",
            "",
            "#### 📁 Thông Tin Bản Cài Game",
            f"- **Đường dẫn**: `{game_path}`",'''

new_diag_report = '''        report = [
            "### 🛠️ Báo Cáo Chẩn Đoán Lỗi Việt Hóa Stella Sora",
            f"- **Thời gian**: `{timestamp}`",
            f"- **Hệ điều hành**: `{platform.system()} {platform.release()} ({platform.version()})`",
            f"- **Kiến trúc**: `{platform.machine()}`",
            f"- **Python**: `{platform.python_version()}`",
            "",
            "#### 📁 Thông Tin Bản Cài Game",
            f"- **Đường dẫn**: `{game_path}`",
            f"- **Phiên bản cài đặt**: `{info.get('edition', 'Không xác định')}`",'''

assert old_diag_report in text, "old_diag_report not found"
text = text.replace(old_diag_report, new_diag_report, 1)

# 6. Update LocalizationEngine.install_pc validation
old_install_pc_check = '''            info = detect_game_info(game_path)
            if not info["exists"]:
                raise FileNotFoundError(f"Không tìm thấy thư mục game tại: {game_path}")
            if info["is_running"]:
                raise RuntimeError("Game StellaSora.exe đang chạy! Vui lòng đóng game trước khi cài đặt.")'''

new_install_pc_check = '''            info = detect_game_info(game_path)
            if not info["exists"]:
                raise FileNotFoundError(f"Không tìm thấy thư mục game tại: {game_path}")
            if not info["has_game_data"]:
                raise FileNotFoundError(f"Thư mục đã chọn chưa có tệp trò chơi ({game_path}).\\nNếu bạn tải từ Steam, vui lòng đảm bảo game đã được tải hoàn tất qua Steam.")
            if info["is_running"]:
                raise RuntimeError("Game StellaSora.exe đang chạy! Vui lòng đóng game trước khi cài đặt.")'''

assert old_install_pc_check in text, "old_install_pc_check not found"
text = text.replace(old_install_pc_check, new_install_pc_check, 1)

# 7. Update LauncherGUI title & geometry
old_gui_init = '''        self.root.title("Stella Sora - Trình Cài Đặt Việt Hóa Đa Nền Tảng (1-Chạm)")
        self.root.geometry("820x620")'''
new_gui_init = '''        self.root.title("Stella Sora - Trình Cài Đặt Việt Hóa Đa Nền Tảng & Steam (v0.8.0)")
        self.root.geometry("840x640")'''
assert old_gui_init in text, "old_gui_init not found"
text = text.replace(old_gui_init, new_gui_init, 1)

# 8. Update build_pc_tab and refresh_status
old_build_pc = '''    def build_pc_tab(self):
        # Card 1: Game Status
        card_info = tk.Frame(self.tab_pc, bg="#24273a", bd=1, relief="solid")
        card_info.pack(fill="x", padx=12, pady=10)

        tk.Label(card_info, text="Trạng Thái Trò Chơi", font=("Segoe UI", 11, "bold"), fg="#cdd6f4", bg="#24273a").grid(row=0, column=0, sticky="w", padx=12, pady=8)

        self.lbl_path = tk.Label(card_info, text=f"Thư mục: {self.game_path}", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_path.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=2)

        self.lbl_game_ver = tk.Label(card_info, text="Phiên bản: Đang kiểm tra...", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_game_ver.grid(row=2, column=0, sticky="w", padx=12, pady=2)

        self.lbl_patch_status = tk.Label(card_info, text="Trạng thái Việt Hóa: Chưa xác định", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#24273a")
        self.lbl_patch_status.grid(row=3, column=0, sticky="w", padx=12, pady=6)

        # Buttons Row
        btn_frame = tk.Frame(self.tab_pc, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=12, pady=6)

        self.btn_install = tk.Button(btn_frame, text="⚡ CÀI ĐẶT VIỆT HÓA (NỘI BỘ)", font=("Segoe UI", 10, "bold"),
                                     bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
                                     padx=12, pady=8, bd=0, cursor="hand2", command=self.on_install_pc)
        self.btn_install.pack(side="left", padx=(0, 8))

        self.btn_online_sync = tk.Button(btn_frame, text="🌐 CẬP NHẬT TỪ GITHUB (TRỰC TIẾP)", font=("Segoe UI", 10, "bold"),
                                         bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
                                         padx=12, pady=8, bd=0, cursor="hand2", command=self.on_sync_game_patch_from_github)
        self.btn_online_sync.pack(side="left", padx=(0, 8))

        self.btn_rollback = tk.Button(btn_frame, text="🔄 Khôi Phục Gốc", font=("Segoe UI", 10, "bold"),
                                      bg="#eba0ac", fg="#11111b", activebackground="#f38ba8",
                                      padx=10, pady=8, bd=0, cursor="hand2", command=self.on_rollback_pc)
        self.btn_rollback.pack(side="left", padx=8)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 Làm Mới", font=("Segoe UI", 10),
                                     bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                     padx=10, pady=8, bd=0, cursor="hand2", command=self.refresh_status)
        self.btn_refresh.pack(side="right")'''

new_build_pc = '''    def build_pc_tab(self):
        # Card 1: Game Status & Path Selector
        card_info = tk.Frame(self.tab_pc, bg="#24273a", bd=1, relief="solid")
        card_info.pack(fill="x", padx=12, pady=10)

        # Top row: Title & Edition Badge
        top_frame = tk.Frame(card_info, bg="#24273a")
        top_frame.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(top_frame, text="Trạng Thái & Thư Mục Trò Chơi", font=("Segoe UI", 11, "bold"), fg="#cdd6f4", bg="#24273a").pack(side="left")

        self.lbl_edition_badge = tk.Label(top_frame, text="[Đang nhận diện...]", font=("Segoe UI", 9, "bold"), fg="#89b4fa", bg="#313244", padx=8, pady=2)
        self.lbl_edition_badge.pack(side="right")

        # Path entry row with Browse and Scan buttons
        path_box = tk.Frame(card_info, bg="#24273a")
        path_box.pack(fill="x", padx=12, pady=4)

        tk.Label(path_box, text="Thư mục:", font=("Segoe UI", 9, "bold"), fg="#bac2de", bg="#24273a").pack(side="left")

        self.ent_path = tk.Entry(path_box, font=("Consolas", 9), bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4", bd=1, relief="solid")
        self.ent_path.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.ent_path.insert(0, str(self.game_path))
        self.ent_path.bind("<Return>", lambda e: self.on_path_entered())

        btn_browse = tk.Button(path_box, text="📁 Chọn Thư Mục...", font=("Segoe UI", 9, "bold"),
                               bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
                               bd=0, padx=8, pady=3, cursor="hand2", command=self.on_browse_game_path)
        btn_browse.pack(side="left", padx=(0, 6))

        btn_scan_steam = tk.Button(path_box, text="🔍 Quét Steam/PC", font=("Segoe UI", 9),
                                   bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                   bd=0, padx=8, pady=3, cursor="hand2", command=self.on_quick_scan_paths)
        btn_scan_steam.pack(side="left")

        # Status & Version Information
        status_box = tk.Frame(card_info, bg="#24273a")
        status_box.pack(fill="x", padx=12, pady=(4, 8))

        self.lbl_game_ver = tk.Label(status_box, text="Phiên bản: Đang kiểm tra...", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_game_ver.pack(anchor="w", pady=1)

        self.lbl_patch_status = tk.Label(status_box, text="Trạng thái Việt Hóa: Chưa xác định", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#24273a")
        self.lbl_patch_status.pack(anchor="w", pady=2)

        # Buttons Row
        btn_frame = tk.Frame(self.tab_pc, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=12, pady=6)

        self.btn_install = tk.Button(btn_frame, text="⚡ CÀI ĐẶT VIỆT HÓA (1-CHẠM)", font=("Segoe UI", 10, "bold"),
                                     bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
                                     padx=12, pady=8, bd=0, cursor="hand2", command=self.on_install_pc)
        self.btn_install.pack(side="left", padx=(0, 6))

        self.btn_launch_game = tk.Button(btn_frame, text="🚀 KHỞI ĐỘNG GAME", font=("Segoe UI", 10, "bold"),
                                         bg="#fab387", fg="#11111b", activebackground="#f9e2af",
                                         padx=12, pady=8, bd=0, cursor="hand2", command=self.on_launch_game)
        self.btn_launch_game.pack(side="left", padx=(0, 6))

        self.btn_online_sync = tk.Button(btn_frame, text="🌐 CẬP NHẬT TỪ GITHUB", font=("Segoe UI", 9, "bold"),
                                         bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
                                         padx=10, pady=8, bd=0, cursor="hand2", command=self.on_sync_game_patch_from_github)
        self.btn_online_sync.pack(side="left", padx=(0, 6))

        self.btn_rollback = tk.Button(btn_frame, text="🔄 Khôi Phục Gốc", font=("Segoe UI", 9, "bold"),
                                      bg="#eba0ac", fg="#11111b", activebackground="#f38ba8",
                                      padx=10, pady=8, bd=0, cursor="hand2", command=self.on_rollback_pc)
        self.btn_rollback.pack(side="left", padx=(0, 6))

        self.btn_steam_help = tk.Button(btn_frame, text="🎮 Hướng Dẫn Steam", font=("Segoe UI", 9),
                                        bg="#cba6f7", fg="#11111b", activebackground="#b4befe",
                                        padx=10, pady=8, bd=0, cursor="hand2", command=self.on_show_steam_guide)
        self.btn_steam_help.pack(side="left")

        self.btn_refresh = tk.Button(btn_frame, text="🔄 Làm Mới", font=("Segoe UI", 9),
                                     bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                     padx=10, pady=8, bd=0, cursor="hand2", command=self.refresh_status)
        self.btn_refresh.pack(side="right")'''

assert old_build_pc in text, "old_build_pc not found"
text = text.replace(old_build_pc, new_build_pc, 1)

# 9. Replace refresh_status with enhanced version and helper methods
old_refresh = '''    def refresh_status(self):
        info = detect_game_info(self.game_path)
        if not info["exists"]:
            self.lbl_patch_status.config(text="⚠️ Không tìm thấy game!", fg="#f38ba8")
            self.btn_install.config(state="disabled")
            return

        self.lbl_game_ver.config(text=f"Client: {info['client_ver']} | Game: {info['game_ver']} | Res: {info['res_ver']}")
        if info["installed_patch"]:
            self.lbl_patch_status.config(text="✓ ĐÃ CÀI ĐẶT BẢN VIỆT HÓA (Active)", fg="#a6e3a1")
        else:
            self.lbl_patch_status.config(text="Chưa cài đặt bản Việt Hóa", fg="#f9e2af")
        self.btn_install.config(state="normal")

        # Update diag preview
        report = DiagnosticCollector.generate_report(self.game_path)
        self.txt_diag_preview.delete("1.0", "end")
        self.txt_diag_preview.insert("1.0", report)'''

new_refresh = '''    def on_browse_game_path(self):
        new_dir = filedialog.askdirectory(
            title="Chọn Thư Mục Cài Đặt Trò Chơi Stella Sora (Steam hoặc Yostar)",
            initialdir=str(self.game_path) if self.game_path.exists() else "C:\\\\"
        )
        if new_dir:
            self.set_game_path(Path(new_dir))

    def on_path_entered(self):
        entered = self.ent_path.get().strip()
        if entered:
            self.set_game_path(Path(entered))

    def set_game_path(self, path: Path):
        self.game_path = path
        self.config["default_game_path"] = str(path)
        save_config(self.config)
        self.ent_path.delete(0, "end")
        self.ent_path.insert(0, str(path))
        self.log_ui(f"Đã chuyển sang thư mục game: {path}")
        self.refresh_status()

    def on_quick_scan_paths(self):
        candidates = find_potential_game_paths()
        existing = [c for c in candidates if c["exists"]]

        if not existing:
            messagebox.showinfo("Quét Thư Mục", "Không phát hiện thêm thư mục Stella Sora nào khác trên máy.")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("🔍 Chọn Bản Cài Đặt Stella Sora")
        dlg.geometry("640x360")
        dlg.configure(bg="#1e1e2e")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Các thư mục Stella Sora được phát hiện trên máy tính:", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e").pack(anchor="w", padx=14, pady=(12, 6))

        frame_list = tk.Frame(dlg, bg="#24273a", bd=1, relief="solid")
        frame_list.pack(fill="both", expand=True, padx=14, pady=6)

        for c in candidates:
            row = tk.Frame(frame_list, bg="#24273a")
            row.pack(fill="x", padx=10, pady=4)
            badge_color = "#a6e3a1" if c["is_valid_game"] else "#f9e2af"
            status_text = "✓ Sẵn sàng" if c["is_valid_game"] else ("Thư mục trống" if c["exists"] else "Chưa cài đặt")

            lbl_name = tk.Label(row, text=f"[{c['edition']}] {c['label']}", font=("Segoe UI", 9, "bold"), fg="#cdd6f4", bg="#24273a")
            lbl_name.pack(side="left")

            lbl_sub = tk.Label(row, text=f" — {status_text}", font=("Segoe UI", 8), fg=badge_color, bg="#24273a")
            lbl_sub.pack(side="left")

            def make_chooser(p):
                return lambda: (self.set_game_path(p), dlg.destroy())

            if c["exists"]:
                btn_select = tk.Button(row, text="Chọn Thư Mục Này", font=("Segoe UI", 8, "bold"),
                                       bg="#89b4fa", fg="#11111b", bd=0, padx=8, pady=2, cursor="hand2",
                                       command=make_chooser(c["path"]))
                btn_select.pack(side="right")

        tk.Button(dlg, text="Đóng", font=("Segoe UI", 9), bg="#45475a", fg="#cdd6f4", bd=0, padx=14, pady=4, cursor="hand2", command=dlg.destroy).pack(pady=10)

    def on_launch_game(self):
        info = detect_game_info(self.game_path)
        if not info["exists"]:
            messagebox.showwarning("Cảnh Báo", "Thư mục trò chơi chưa tồn tại!")
            return
        ok, msg = launch_game(self.game_path)
        if ok:
            self.log_ui(f"🚀 {msg}")
        else:
            self.log_ui(f"❌ {msg}")
            messagebox.showerror("Khởi Động Lỗi", msg)

    def on_show_steam_guide(self):
        msg = (
            "HƯỚNG DẪN CHƠI STELLA SORA TRÊN STEAM\\n"
            "====================================\\n\\n"
            "1. Nếu bạn tải game từ Steam (AppID 4813850):\\n"
            "   - Trong Launcher, bấm '📁 Chọn Thư Mục...' hoặc '🔍 Quét Steam/PC'.\\n"
            "   - Chọn thư mục: .../steamapps/common/Stella Sora\\n"
            "   - Bấm '⚡ CÀI ĐẶT VIỆT HÓA (1-CHẠM)'.\\n"
            "   - Bấm '🚀 KHỞI ĐỘNG GAME' hoặc mở trực tiếp từ Steam!\\n\\n"
            "2. Chơi bản Yostar qua Steam (Non-Steam Game - Khuyên Dùng):\\n"
            "   - Mở Steam -> Menu 'Games' -> 'Add a Non-Steam Game to My Library...'\\n"
            "   - Bấm 'Browse...' -> Chọn file:\\n"
            "     C:\\\\YostarGames\\\\StellaSora_EN\\\\StellaSora.exe\\n"
            "   - Bấm 'Add Selected Programs'.\\n"
            "   - Bạn sẽ có toàn bộ tính năng cao cấp của Steam: Steam Overlay (Shift+Tab), xem FPS, chụp ảnh màn hình F12 và kết nối mọi tay cầm (Xbox, PlayStation, Switch)!"
        )
        messagebox.showinfo("🎮 Hướng Dẫn Chơi Trên Steam", msg)

    def refresh_status(self):
        info = detect_game_info(self.game_path)

        # Update edition badge
        edition = info.get("edition", "Không xác định")
        if info.get("is_steam"):
            self.lbl_edition_badge.config(text=f"🎮 {edition}", bg="#1e66f5", fg="#ffffff")
            self.btn_launch_game.config(text="🚀 CHẠY QUA STEAM")
        elif "Yostar" in edition:
            self.lbl_edition_badge.config(text=f"🏢 {edition}", bg="#cba6f7", fg="#11111b")
            self.btn_launch_game.config(text="🚀 KHỞI ĐỘNG GAME")
        else:
            self.lbl_edition_badge.config(text=f"📁 {edition}", bg="#45475a", fg="#cdd6f4")
            self.btn_launch_game.config(text="🚀 KHỞI ĐỘNG GAME")

        if not info["exists"]:
            self.lbl_patch_status.config(text="⚠️ Thư mục chưa tồn tại trên máy!", fg="#f38ba8")
            self.lbl_game_ver.config(text="Phiên bản: Không tìm thấy tệp trò chơi")
            self.btn_install.config(state="disabled")
            self.btn_launch_game.config(state="disabled")
            return

        if not info["has_game_data"]:
            self.lbl_patch_status.config(text="⚠️ Thư mục trống hoặc game chưa tải xong!", fg="#fab387")
            self.lbl_game_ver.config(text="Vui lòng tải game từ Steam/Yostar trước khi cài Việt Hóa")
            self.btn_install.config(state="disabled")
            self.btn_launch_game.config(state="disabled")
            return

        self.btn_launch_game.config(state="normal")
        self.lbl_game_ver.config(text=f"Client: {info['client_ver']} | Game: {info['game_ver']} | Res: {info['res_ver']}")

        if info["installed_patch"]:
            self.lbl_patch_status.config(text="✓ ĐÃ CÀI ĐẶT BẢN VIỆT HÓA (Active - Sẵn sàng chơi)", fg="#a6e3a1")
        else:
            self.lbl_patch_status.config(text="Chưa cài đặt bản Việt Hóa (Sẵn sàng cài 1-chạm)", fg="#f9e2af")
        self.btn_install.config(state="normal")

        # Update diag preview
        report = DiagnosticCollector.generate_report(self.game_path)
        self.txt_diag_preview.delete("1.0", "end")
        self.txt_diag_preview.insert("1.0", report)'''

assert old_refresh in text, "old_refresh not found"
text = text.replace(old_refresh, new_refresh, 1)

# 10. Update cli_main
old_cli = '''    parser = argparse.ArgumentParser(description="Stella Sora Việt Hóa CLI & Launcher")
    parser.add_argument("--install", action="store_true", help="Cài đặt Việt Hóa 1-chạm")'''

new_cli = '''    parser = argparse.ArgumentParser(description="Stella Sora Việt Hóa CLI & Launcher")
    parser.add_argument("--game-path", type=str, default="", help="Đường dẫn thư mục game tùy chọn")
    parser.add_argument("--install", action="store_true", help="Cài đặt Việt Hóa 1-chạm")'''

assert old_cli in text, "old_cli not found"
text = text.replace(old_cli, new_cli, 1)

old_cli_path = '''    cfg = load_config()
    game_path = Path(cfg.get("default_game_path", "C:\\\\YostarGames\\\\StellaSora_EN"))'''

new_cli_path = '''    cfg = load_config()
    game_path = Path(args.game_path) if args.game_path else Path(cfg.get("default_game_path", "C:\\\\YostarGames\\\\StellaSora_EN"))'''

assert old_cli_path in text, "old_cli_path not found"
text = text.replace(old_cli_path, new_cli_path, 1)

launcher_path.write_text(text, encoding="utf-8")
print("Successfully upgraded launcher_pc.py to v0.8.0!")
