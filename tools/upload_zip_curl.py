import json
import subprocess
import urllib.request
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

def main():
    token = get_github_token()
    repo = "doubleD1302/AmeeVH"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "StellaSora-Uploader",
    }

    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/v0.9.5", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel = json.loads(resp.read().decode("utf-8"))

    upload_url_tmpl = rel["upload_url"].split("{")[0]
    zip_path = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\dist\StellaSora_Launcher_PC.zip")
    aname = zip_path.name

    # Check if asset exists and delete if so
    for a in rel.get("assets", []):
        if a["name"] == aname:
            aid = a["id"]
            del_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases/assets/{aid}",
                headers=headers,
                method="DELETE",
            )
            try:
                urllib.request.urlopen(del_req)
                print(f"Deleted old asset {aname}")
            except Exception as e:
                print(f"Delete err: {e}")

    upload_url = f"{upload_url_tmpl}?name={aname}"
    print(f"Uploading {aname} via curl to {upload_url}...")

    cmd = [
        "curl.exe",
        "-X", "POST",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/vnd.github.v3+json",
        "-H", "Content-Type: application/zip",
        "--data-binary", f"@{zip_path}",
        "--progress-bar",
        upload_url
    ]
    ret = subprocess.run(cmd, capture_output=True, text=True)
    if ret.returncode == 0:
        print("Upload SUCCESS!")
        try:
            res_obj = json.loads(ret.stdout)
            print("Download URL:", res_obj.get("browser_download_url"))
        except Exception:
            print("Response:", ret.stdout[:200])
    else:
        print("Upload FAILED:", ret.stderr)

if __name__ == "__main__":
    main()
