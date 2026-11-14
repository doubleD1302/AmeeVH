# Upload (replace) patch assets on an existing GitHub release.
# The token is read ONLY from the GH_TOKEN environment variable. Never hard-code it or commit it.
#   $env:GH_TOKEN = "<fine-grained token: AmeeVH, Contents = Read and write>"
#   powershell -File tools\upload_release_assets.ps1 -Tag v1.3.0
# Upload every file the manifest needs in ONE run (the launcher rejects size/SHA256 mismatches).
param(
  [string]$Repo = "doubleD1302/AmeeVH",
  [string]$Tag = "v1.3.0",
  [string]$Dist = (Join-Path (Split-Path $PSScriptRoot -Parent) "dist"),
  [string[]]$Files = @("data_patched_vi.arcx","lua_patched_vi.arcx","patch_manifest.json","android_patch_manifest.json","SHA256SUMS.txt")
)
$ErrorActionPreference = "Stop"
$localToken = Join-Path (Split-Path $PSScriptRoot -Parent) ".secrets\github_token.txt"  # git-ignored, local only
if (-not $env:GH_TOKEN -and (Test-Path $localToken)) { $env:GH_TOKEN = (Get-Content $localToken -Raw).Trim() }
if (-not $env:GH_TOKEN) { throw "No token: set GH_TOKEN or put it in .secrets\github_token.txt. Ask the user; do not search other stored credentials." }
$h = @{ Authorization = "Bearer $env:GH_TOKEN"; "User-Agent" = "vh"; Accept = "application/vnd.github+json" }
$rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/tags/$Tag" -Headers $h
foreach ($n in $Files) {
  $f = Join-Path $Dist $n
  if (-not (Test-Path $f)) { throw "Missing $f" }
  $old = $rel.assets | Where-Object name -eq $n
  if ($old) { Invoke-RestMethod -Method Delete "https://api.github.com/repos/$Repo/releases/assets/$($old.id)" -Headers $h }
  Invoke-RestMethod -Method Post "https://uploads.github.com/repos/$Repo/releases/$($rel.id)/assets?name=$n" -Headers $h -InFile $f -ContentType "application/octet-stream" | Out-Null
  "uploaded $n"
}
"Now verify: sizes and sha256 of the release assets must equal dist\patch_manifest.json."
