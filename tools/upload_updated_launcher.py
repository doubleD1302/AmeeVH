import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

def get_github_token() -> str:
    p = subprocess.Popen(
        ["git", "credential", "fill"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, _ = p.communicate(input="protocol=https\nhost=github.com\n\n")
    for line in out.splitlines():
        if line.startswith("password="):
            return line[9:]
    return ""

def repack_launcher_zip():
    dist = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist")
    zip_path = dist / "StellaSora_Launcher_PC.zip"
    temp_zip = dist / "StellaSora_Launcher_PC_new.zip"
    new_exe = dist / "StellaSora_Launcher.exe"

    print("Repacking StellaSora_Launcher_PC.zip with new launcher exe...")
    with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "StellaSora_Launcher.exe":
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.write(new_exe, "StellaSora_Launcher.exe")

    temp_zip.replace(zip_path)
    print(f"Repacked {zip_path.name}: {zip_path.stat().st_size / (1024*1024):.2f} MB")

def upload_asset(rel, file_path: Path, ctype: str, headers: dict, repo: str):
    upload_url_tmpl = rel["upload_url"].split("{")[0]
    existing_assets = {a["name"]: a["id"] for a in rel.get("assets", [])}
    aname = file_path.name

    if aname in existing_assets:
        aid = existing_assets[aname]
        del_req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/releases/assets/{aid}",
            headers=headers,
            method="DELETE",
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"Deleted old asset {aname} (id: {aid})")
        except Exception as e:
            print(f"Could not delete old asset {aname}: {e}")

    file_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"Uploading {aname} ({file_mb:.2f} MB)...")
    upload_url = f"{upload_url_tmpl}?name={aname}"
    data = file_path.read_bytes()
    up_req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            **headers,
            "Content-Type": ctype,
            "Content-Length": str(len(data)),
        },
        method="POST",
    )
    with urllib.request.urlopen(up_req) as resp:
        up_res = json.loads(resp.read().decode("utf-8"))
        print(f"Successfully uploaded {aname}: {up_res.get('browser_download_url')}")

def main():
    repack_launcher_zip()

    token = get_github_token()
    if not token:
        print("ERROR: Could not retrieve GitHub token")
        return

    repo = "doubleD1302/AmeeVH"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "StellaSora-Uploader",
    }

    # Fetch release v0.9.5
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/v0.9.5", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel = json.loads(resp.read().decode("utf-8"))

    print(f"Found release: {rel.get('tag_name')} (ID: {rel.get('id')})")

    dist = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist")
    upload_asset(rel, dist / "StellaSora_Launcher.exe", "application/vnd.microsoft.portable-executable", headers, repo)
    upload_asset(rel, dist / "StellaSora_Launcher_PC.zip", "application/zip", headers, repo)
    print("ALL DONE!")

if __name__ == "__main__":
    main()
