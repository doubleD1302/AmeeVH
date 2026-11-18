"""Build-only entry with an explicit Windows DLL search environment."""
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json, os, re, subprocess, sys
from pathlib import Path


def build_candidate(revision: str = 'r10'):
    if not re.fullmatch(r'r\d{2,3}[A-Za-z0-9_-]*', revision):
        raise SystemExit(f'Invalid revision tag: {revision!r}')
    src = Path(__file__).resolve().parent
    root = src.parent
    venv_py = root / '.venv' / 'Scripts' / 'python.exe'
    if venv_py.is_file() and Path(sys.executable).resolve() != venv_py.resolve() and not os.environ.get('STELLA_BUILD_REEXEC'):
        try:
            for pkg in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'PyInstaller', 'pefile'):
                importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            env_re = dict(os.environ)
            env_re['STELLA_BUILD_REEXEC'] = '1'
            r = subprocess.run([str(venv_py), str(Path(__file__).resolve()), '--revision', revision], cwd=root, env=env_re)
            raise SystemExit(r.returncode)
    out = root / f'dist/launcher_ui_candidate_{revision}'
    work = root / f'work/build_launcher_ui_{revision}'
    report = root / f'reports/launcher_ui_candidate_{revision}/implementer'
    cache = root / f'work/launcher_qt_build_{revision}/pyinstaller-cache'
    for p in (out, work, report, cache):
        p.mkdir(parents=True, exist_ok=True)
    if (out / 'StellaSora_Launcher.exe').exists():
        raise SystemExit('Refuse existing candidate. Choose a new revision; never overwrite a delivered EXE.')
    if any(work.iterdir()):
        raise SystemExit('Fresh build directory required; choose a new work revision.')
    versions = {
        n: importlib.metadata.version(n)
        for n in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'PyInstaller', 'pefile')
    }
    if len({versions[n] for n in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6')}) != 1:
        raise SystemExit('PySide6/Shiboken versions are not coherent; build refused.')
    qt = Path(importlib.metadata.distribution('PySide6_Essentials').locate_file('PySide6')).resolve()
    windows = Path(os.environ.get('SystemRoot', 'C:/Windows')).resolve()
    path_allowlist = [
        windows / 'System32',
        windows,
        Path(sys.executable).resolve().parent,
        Path(sys.base_prefix).resolve(),
        Path(sys.base_prefix).resolve() / 'DLLs',
        qt,
    ]
    env = dict(os.environ)
    removed = []
    for key in (
        'PYTHONPATH',
        'PYTHONHOME',
        'QT_PLUGIN_PATH',
        'QT_QPA_PLATFORM_PLUGIN_PATH',
        'QML2_IMPORT_PATH',
        'QML_IMPORT_PATH',
        'QT_DEBUG_PLUGINS',
        'CONDA_PREFIX',
        'CONDA_DEFAULT_ENV',
        'CONDA_DLL_SEARCH_MODIFICATION_ENABLE',
    ):
        if key in env:
            removed.append(key)
            env.pop(key)
    env.update({
        'PATH': os.pathsep.join(str(p) for p in path_allowlist if p.is_dir()),
        'PYTHONNOUSERSITE': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYINSTALLER_CONFIG_DIR': str(cache),
        'STELLA_PACKAGING_REPORT_DIR': str(report),
    })
    environment = {
        'revision': revision,
        'path_allowlist': env['PATH'].split(os.pathsep),
        'removed_variable_names': removed,
        'python': sys.executable,
        'base_python': sys.base_prefix,
        'qt_wheel_dir': str(qt),
        'versions': versions,
        'shared_venv_modified': False,
        'application_executed': False,
    }
    (report / 'BUILD_ENVIRONMENT.json').write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding='utf8')
    command = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--noconfirm',
        '--distpath',
        str(out),
        '--workpath',
        str(work),
        str(src / 'StellaSora_Launcher.spec'),
    ]
    with (report / 'build.log').open('w', encoding='utf8') as log:
        r = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    if r.returncode:
        raise SystemExit(r.returncode)
    exe = out / 'StellaSora_Launcher.exe'
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    (out / 'SHA256SUMS.txt').write_text(digest + ' *StellaSora_Launcher.exe\n', encoding='utf8')
    receipt = {
        'revision': revision,
        'command': command,
        'working_directory': str(root),
        'exit_code': r.returncode,
        'exe': str(exe),
        'bytes': exe.stat().st_size,
        'sha256': digest,
        'dependencies': versions,
        'validation': 'not_run_user_requested',
        'exe_launched': False,
        'environment': 'BUILD_ENVIRONMENT.json',
        'dependency_provenance': 'DEPENDENCY_PROVENANCE.json',
    }
    (report / 'BUILD_RECEIPT.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return receipt


def main():
    parser = argparse.ArgumentParser(description='Build Stella Sora Launcher candidate EXE')
    parser.add_argument('--revision', default='r10', help='Candidate revision tag (default: r10)')
    args = parser.parse_args()
    build_candidate(args.revision)


if __name__ == '__main__':
    main()
