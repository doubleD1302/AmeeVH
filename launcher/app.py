"""Launcher candidate bootstrap. Default startup never applies patches automatically."""
from __future__ import annotations
import argparse,logging,os,sys,traceback
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description='Stella Sora Việt Hóa launcher candidate r09')
    parser.add_argument('--app-data-dir',type=Path,help='Explicit writable config/log/backup/cache directory')
    parser.add_argument('--resource-dir',type=Path,help='Explicit development resource override')
    parser.add_argument('--apply-update',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.apply_update:
        from launcher.core.self_update import apply_job
        apply_job(args.apply_update);return 0
    from PySide6.QtWidgets import QApplication
    from launcher.core.config import PathManager,ConfigManager
    from launcher.ui.assets import AssetManager
    from launcher.ui.theme import Theme
    from launcher.ui.typography import register_fonts,font
    from launcher.ui.main_window import MainWindow
    app=QApplication(sys.argv);app.setApplicationName('StellaSora Launcher');app.setOrganizationName('StellaSora VietHoa')
    pm=PathManager(args.resource_dir,args.app_data_dir)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s [%(levelname)s] %(name)s %(message)s',handlers=[logging.FileHandler(pm.logs_dir/'launcher.log',encoding='utf8')])
    register_fonts(pm.resource_dir);app.setFont(font(15));AssetManager.initialize(pm.resource_dir);app.setStyleSheet(Theme.get_application_stylesheet());app.setWindowIcon(AssetManager.get().get_app_icon())
    win=MainWindow(pm,ConfigManager(pm));win.show();return app.exec()

def entry():
    try:return main()
    except Exception:
        error=traceback.format_exc()
        fallback=Path(os.environ.get('LOCALAPPDATA') or Path.home())/'StellaSora_Launcher_Candidate_r02'
        try:
            fallback.mkdir(parents=True,exist_ok=True);(fallback/'startup_error.log').write_text(error,encoding='utf8')
        except OSError:pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'Launcher không mở được. Chi tiết tại:\n'+str(fallback/'startup_error.log'),'Stella Sora Việt Hóa',0x10)
        except Exception:pass
        return 1
if __name__=='__main__':sys.exit(entry())
