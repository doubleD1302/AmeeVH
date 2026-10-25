"""Build only. Never launches the output or runs tests."""
import hashlib,json,subprocess,sys,importlib.metadata
from pathlib import Path

def build_candidate():
    src=Path(__file__).resolve().parent;root=src.parent;out=root/'dist/launcher_ui_candidate_r02';work=root/'work/build_launcher_ui_r02'
    out.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    if (out/'StellaSora_Launcher.exe').exists():raise SystemExit('Refuse to overwrite existing candidate; use a new build revision.')
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(out),'--workpath',str(work),str(src/'StellaSora_Launcher.spec')]
    report=root/'reports/launcher_ui_candidate_r02/implementer';report.mkdir(parents=True,exist_ok=True)
    with (report/'build.log').open('w',encoding='utf8') as log:
        r=subprocess.run(command,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise SystemExit(r.returncode)
    exe=out/'StellaSora_Launcher.exe';digest=hashlib.sha256(exe.read_bytes()).hexdigest();(out/'SHA256SUMS.txt').write_text(digest+' *StellaSora_Launcher.exe\n',encoding='utf8')
    receipt={'command':command,'working_directory':str(root),'exit_code':r.returncode,'exe':str(exe),'bytes':exe.stat().st_size,'sha256':digest,'dependencies':{n:importlib.metadata.version(n) for n in ('PySide6','PyInstaller','Pillow')},'validation':'untested_user_requested','exe_launched':False}
    (report/'BUILD_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(receipt,ensure_ascii=False,indent=2))
if __name__=='__main__':build_candidate()
