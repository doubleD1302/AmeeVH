param(
    [Parameter(Mandatory=$true)][string]$ExportPath
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$projectRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$exportRoot=[System.IO.Path]::GetFullPath((Join-Path $projectRoot $ExportPath))
if(-not $exportRoot.StartsWith($projectRoot+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Output must stay under project root'}
$manifestPath=Join-Path $exportRoot 'MANIFEST.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -Depth 100
$imagesRoot=Join-Path $exportRoot '05_AnhCoChu_EN'
if(Test-Path -LiteralPath $imagesRoot){throw 'Image output already exists; choose a fresh export revision'}
$imageSource=Join-Path $projectRoot 'dist/StellaSora_Texture_AnhVeChu_EN.zip'
$imageHash=(Get-FileHash -LiteralPath $imageSource -Algorithm SHA256).Hash.ToLowerInvariant()
$archive=[System.IO.Compression.ZipFile]::OpenRead($imageSource)
$imageCount=0
try {
    foreach($entry in $archive.Entries){
        if(-not $entry.Name){continue}
        if([System.IO.Path]::IsPathRooted($entry.FullName)){throw 'Absolute archive member path rejected'}
        $target=[System.IO.Path]::GetFullPath((Join-Path $imagesRoot $entry.FullName))
        if(-not $target.StartsWith($imagesRoot+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Archive member escaped image directory'}
        $extension=[System.IO.Path]::GetExtension($target).ToLowerInvariant()
        if($extension -notin @('.png','.json','.csv','.html','.md')){throw ('Unexpected image package extension: '+$extension)}
        [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) | Out-Null
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target,$false)
        if($extension -eq '.png'){$imageCount++}
    }
} finally {$archive.Dispose()}
if($imageCount -ne 1326){throw ('Unexpected inherited PNG count: '+$imageCount)}
$docsRoot=Join-Path $exportRoot '00_ThongTinNguon'
[System.IO.Directory]::CreateDirectory($docsRoot) | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'work/subagents/language_export_20261031_r01/locale_inventory/SUPPLEMENT.json') -Destination (Join-Path $docsRoot 'KIEM_KE_DINH_DANG_NGUON.json')
$readmePath=Join-Path $exportRoot 'README.md'
$addition=@"

## Ảnh có chữ EN đi kèm

05_AnhCoChu_EN chứa $imageCount PNG cùng gallery DANH_SACH_ANH_VE_CHU.html và danh mục JSON/CSV. Bộ ảnh lấy nguyên từ gói đã xuất trước đó dist/StellaSora_Texture_AnhVeChu_EN.zip; SHA256: $imageHash. Đây là snapshot ảnh riêng, không phải kết quả quét lại toàn bộ Unity ở phiên này. Tên ảnh/nhóm giữ nguyên để đối chiếu. Phần ảnh không áp dụng cách chia chapter/nhân vật của thoại.

Báo cáo 00_ThongTinNguon/KIEM_KE_DINH_DANG_NGUON.json ghi kiểm kê cả bảng nhị phân/regex trong client EN. Chúng chủ yếu là cấu hình, khóa dịch, đường dẫn, nhãn nội bộ; không được gán thành văn bản tiếng Anh hay tự dịch để thêm vào corpus.
"@
[System.IO.File]::AppendAllText($readmePath,$addition,[System.Text.UTF8Encoding]::new($false))
$htmlPath=Join-Path $exportRoot 'MO_DAU.html'
$html=[System.IO.File]::ReadAllText($htmlPath)
$html=$html.Replace('</html>','<p><a href="05_AnhCoChu_EN/DANH_SACH_ANH_VE_CHU.html">Mở gallery 1.326 ảnh EN đã xuất trước đó</a></p></html>')
[System.IO.File]::WriteAllText($htmlPath,$html,[System.Text.UTF8Encoding]::new($false))
$manifest.counts | Add-Member -NotePropertyName inherited_en_png_images -NotePropertyValue $imageCount
$manifest.source_files+=@{path='dist/StellaSora_Texture_AnhVeChu_EN.zip';sha256=$imageHash;bytes=(Get-Item -LiteralPath $imageSource).Length;provenance='Previously exported EN texture snapshot; not a fresh Unity census'}
$manifest.tools+=@{path='tools/finalize_language_export_en_20261031.ps1';sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$oldKinds=@{}
foreach($fileRecord in $manifest.files){$oldKinds[$fileRecord.path]=$fileRecord.kind}
$records=@(Get-ChildItem -LiteralPath $exportRoot -Recurse -File | Where-Object {$_.FullName -ne $manifestPath} | Sort-Object FullName | ForEach-Object {
    $relative=[System.IO.Path]::GetRelativePath($exportRoot,$_.FullName).Replace('\','/')
    $kind=$oldKinds[$relative]
    if(-not $kind){$kind=if($relative.StartsWith('05_AnhCoChu_EN/')){'inherited_en_image_snapshot'}else{'source_documentation'}}
    @{path=$relative;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length;kind=$kind}
})
$manifest.files=$records
[System.IO.File]::WriteAllText($manifestPath,($manifest | ConvertTo-Json -Depth 100),[System.Text.UTF8Encoding]::new($false))
Write-Output ($manifest.counts | ConvertTo-Json -Compress)
Write-Output ('Manifest files: '+$records.Count)
