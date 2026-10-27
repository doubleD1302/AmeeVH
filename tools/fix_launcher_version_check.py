from pathlib import Path

# 1. Update game_detection.py
gd_path = Path(r"StellaSora_VietHoa/launcher/core/game_detection.py")
gd_text = gd_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_gd = """def read_game_versions(root):
    \"\"\"Read actual version headers; never infer from a directory or bundle size.\"\"\"
    import json
    out={"game":"unknown","resource":"unknown"}
    root=Path(root)
    mf=root/"Persistent_Store"/"ss_win.mani"
    if mf.is_file():
        try:
            with mf.open(encoding="utf8",errors="replace") as f: header="".join(next(f,"") for _ in range(16))
            for part in header.replace(chr(10),'|').split('|'):
                fields=part.strip().split()
                if len(fields)>=2 and fields[0] in ('GAME_VER','RES_VER'):
                    out['game' if fields[0]=='GAME_VER' else 'resource']=fields[-1]
        except OSError:pass
    return out"""

new_gd = """def read_game_versions(root):
    \"\"\"Read actual version headers; never infer from a directory or bundle size.\"\"\"
    out = {"game": "unknown", "resource": "unknown"}
    root = Path(root)
    mf = root / "Persistent_Store" / "ss_win.mani"
    if mf.is_file():
        try:
            with mf.open(encoding="utf8", errors="replace") as f:
                header = "".join(next(f, "") for _ in range(32))
            for line in header.splitlines():
                line = line.strip().lstrip("$")
                m = re.match(r"^(GAME_VER|CLIENT_VER|RES_VER|RESOURCE_VER)[:=\\s]+([0-9A-Za-z_.-]+)", line)
                if m:
                    k, v = m.group(1), m.group(2)
                    if k in ("GAME_VER", "CLIENT_VER") and out["game"] == "unknown":
                        out["game"] = v
                    elif k in ("RES_VER", "RESOURCE_VER") and out["resource"] == "unknown":
                        out["resource"] = v
        except OSError:
            pass
    return out"""

if old_gd in gd_text:
    gd_text = gd_text.replace(old_gd, new_gd)
    gd_path.write_text(gd_text, encoding="utf-8")
    print("Updated launcher/core/game_detection.py")
else:
    print("Warning: old_gd not found in game_detection.py")

# 2. Update installer.py to use match_version
inst_path = Path(r"StellaSora_VietHoa/launcher/core/installer.py")
inst_text = inst_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_inst_check = "if observed['game']!=m['client_game_version'] or observed['resource']!=m['resource_version']:raise InstallerError(f\"Gói dành cho game {m['client_game_version']} / tài nguyên {m['resource_version']}; bản đã chọn là {observed['game']} / {observed['resource']}.\",'VERSION_MISMATCH')"

new_inst_check = """def _match_ver(exp, obs):
                if not exp or exp in ('*', 'all') or obs in ('*', 'all', 'unknown'): return True
                if obs == exp: return True
                for p in str(exp).replace(';', ',').replace('|', ',').split(','):
                    p = p.strip()
                    if p in ('*', obs): return True
                    if p.endswith('*') and obs.startswith(p[:-1]): return True
                return False
            if not _match_ver(m.get('client_game_version'), observed['game']) or not _match_ver(m.get('resource_version'), observed['resource']):raise InstallerError(f"Gói dành cho game {m['client_game_version']} / tài nguyên {m['resource_version']}; bản đã chọn là {observed['game']} / {observed['resource']}.",'VERSION_MISMATCH')"""

if old_inst_check in inst_text:
    inst_text = inst_text.replace(old_inst_check, new_inst_check)
    inst_path.write_text(inst_text, encoding="utf-8")
    print("Updated launcher/core/installer.py")
else:
    print("Warning: old_inst_check not found in installer.py")
