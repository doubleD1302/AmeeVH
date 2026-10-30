from pathlib import Path
import json,re,hashlib
root=Path('StellaSora_VietHoa')
web=root/'web/story_translator';assets=web/'assets/tramvh-icons-r01'
report=root/'reports/tramvh_icons_20261031_r01';report.mkdir(parents=True,exist_ok=True)
backup=root/'work/tramvh_icons_20261031_r01_preintegration';backup.mkdir(parents=True,exist_ok=False)
paths=['index.html','manifest.json','js/controllers/AudioController.js','js/views/CardView.js','js/views/TableView.js','js/views/GlossaryView.js']
pre={}
for name in paths:
 p=web/name;pre[name]=hashlib.sha256(p.read_bytes()).hexdigest();dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
(report/'INPUT_HASHES.json').write_text(json.dumps(pre,indent=2),encoding='utf-8')

def icon(name):
 return f'<span class="tram-icon" aria-hidden="true"><img class="tram-icon-light" src="assets/tramvh-icons-r01/svg/light/{name}.svg" alt=""><img class="tram-icon-dark" src="assets/tramvh-icons-r01/svg/dark/{name}.svg" alt=""></span>'

p=web/'index.html';s=p.read_text(encoding='utf-8')
s=s.replace('href="web_assets/favicon.png"','href="assets/tramvh-icons-r01/brand/tramvh-app-light-32.png"',1)
s=s.replace('<link rel="manifest" href="manifest.json">','<link rel="apple-touch-icon" href="assets/tramvh-icons-r01/brand/tramvh-app-light-180.png">\n    <link rel="manifest" href="manifest.json?v=1.3.1">',1)
s=s.replace('<meta name="theme-color" content="#070c18">','<meta name="theme-color" content="#eaf3f8">',1)
s=s.replace('</head>','    <link rel="stylesheet" href="assets/tramvh-icons-r01/icons.css?v=1.3.1">\n</head>',1)
s=s.replace('<img class="brand-logo-img" src="web_assets/logo_stella_sora_clean.png" onerror="this.src=\'web_assets/favicon.png\'" alt="Stella Sora">','<span class="tram-brand-mark" aria-hidden="true"><img class="tram-icon-light" src="assets/tramvh-icons-r01/brand/tramvh-mark-light.svg" alt=""><img class="tram-icon-dark" src="assets/tramvh-icons-r01/brand/tramvh-mark-dark.svg" alt=""></span>',1)
for ident,name in [('bgmToggleBtn','music'),('bgmNextBtn','next')]:
 s,n=re.subn(r'(<button\b[^>]*\bid="'+ident+r'"[^>]*>).*?(</button>)',lambda m:m[1]+icon(name)+m[2],s,count=1,flags=re.S);assert n==1,ident
s,n=re.subn(r'(<button\b[^>]*\bid="themeToggleBtn"[^>]*>).*?(</button>)',lambda m:m[1]+'<span class="tram-theme-night">'+icon('moon')+'</span><span class="tram-theme-day">'+icon('sun')+'</span>'+m[2],s,count=1,flags=re.S);assert n==1
for handler,name in [('openLeaderboardModal()','trophy'),('openGlossaryModal()','glossary')]:
 s,n=re.subn(r'(<button\b[^>]*onclick="'+re.escape(handler)+r'"[^>]*>)<svg.*?</svg>(</button>)',lambda m:m[1]+icon(name)+m[2],s,count=1,flags=re.S);assert n==1,handler
s,n=re.subn(r'(<a\b[^>]*title="Mở Google Sheets"[^>]*>)<svg.*?</svg>(</a>)',lambda m:m[1]+icon('sheet')+m[2],s,count=1,flags=re.S);assert n==1
# Native select options remain plain text; drawings go in real HTML controls.
for a,b in [('🎮 Visual Novel',icon('visual-novel')+' Visual Novel'),('📋 Danh Sách',icon('list')+' Danh Sách'),('🔊 Lồng tiếng',icon('volume')+' Lồng tiếng'),('💬 LỜI THOẠI',icon('dialogue')+' LỜI THOẠI'),('💡 Bản dịch cũ:',icon('info')+' Bản dịch cũ:'),('⏮️ Câu trước',icon('previous')+' Câu trước'),('⏭️ Câu kế',icon('next')+' Câu kế'),('⭐ LƯU &amp;',icon('save-next')+' LƯU &amp;'),('⭐ LƯU & TIẾP',icon('save-next')+' LƯU & TIẾP'),('🏆 BẢNG PHONG THẦN',icon('trophy')+' BẢNG PHONG THẦN'),('📖 TỪ ĐIỂN',icon('glossary')+' TỪ ĐIỂN'),('💡 GỢI Ý',icon('glossary')+' GỢI Ý'),('🔍 Tra nhanh',icon('search')+' Tra nhanh')]:
 s=s.replace(a,b)
s=s.replace('<span>⭐</span>',icon('xp'),1)
s=s.replace('BẢN DỊCH TIẾNG VIỆT MỚI (⭐ SỬA Ở ĐÂY)',icon('quill')+' BẢN DỊCH TIẾNG VIỆT MỚI (SỬA Ở ĐÂY)')
s=s.replace('<span class="sync-icon">🔄</span>', '<span class="sync-icon">'+icon('sync')+'</span>')
s=s.replace('<span class="search-icon">🔍</span>','<span class="search-icon">'+icon('search')+'</span>')
s=s.replace('>✕</button>',' aria-label="Đóng">'+icon('close')+'</button>')
# Avoid duplicate aria labels on controls that already had them.
s=s.replace('aria-label="Đóng từ điển" aria-label="Đóng"','aria-label="Đóng từ điển"')
s=s.replace('onclick="clearGlossarySearch()" style="display:none;" aria-label="Đóng"','onclick="clearGlossarySearch()" style="display:none;" aria-label="Xóa tìm kiếm"')
s=s.replace('src="web_assets/favicon.png"','src="assets/tramvh-icons-r01/brand/tramvh-app-light-192.png"')
s=s.replace('    <!-- Models -->','    <script src="js/views/IconView.js?v=1.3.1"></script>\n    <!-- Models -->',1)
s=s.replace('?v=1.3.0','?v=1.3.1')
p.write_text(s,encoding='utf-8')

m=json.loads((web/'manifest.json').read_text(encoding='utf-8'))
m['icons']=[{'src':f'assets/tramvh-icons-r01/brand/tramvh-app-light-{size}.png','sizes':f'{size}x{size}','type':'image/png','purpose':purpose} for size,purpose in [(192,'any'),(512,'any'),(512,'maskable')]]
(web/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ids=[x['id'] for x in json.loads((assets/'manifest.json').read_text(encoding='utf-8'))['icons']]
helper='''/** TramVH original icon set. Only known asset IDs can enter markup. */
const TRAM_ICON_IDS = new Set(__IDS__);
function tramIcon(id) {
    const name = TRAM_ICON_IDS.has(id) ? id : "info";
    const base = "assets/tramvh-icons-r01/svg/";
    return `<span class="tram-icon" aria-hidden="true"><img class="tram-icon-light" src="${base}light/${name}.svg" alt=""><img class="tram-icon-dark" src="${base}dark/${name}.svg" alt=""></span>`;
}
'''.replace('__IDS__',json.dumps(ids))
(web/'js/views/IconView.js').write_text(helper,encoding='utf-8')
p=web/'js/controllers/AudioController.js';s=p.read_text(encoding='utf-8')
s,n=re.subn(r'btn.innerHTML = `<svg.*?</svg>`;', 'btn.innerHTML = tramIcon("pause");',s,count=1,flags=re.S);assert n==1
s,n=re.subn(r'btn.innerHTML = `<svg.*?</svg>`;', 'btn.innerHTML = tramIcon("music");',s,count=1,flags=re.S);assert n==1
s=s.replace('        if (isBgmPlaying) {','        btn.setAttribute("aria-label", btn.title);\n        btn.setAttribute("aria-pressed", String(isBgmPlaying));\n        if (isBgmPlaying) {',1)
p.write_text(s,encoding='utf-8')

p=web/'js/views/CardView.js';s=p.read_text(encoding='utf-8').replace('"web_assets/favicon.png"','"assets/tramvh-icons-r01/brand/tramvh-app-light-192.png"').replace('<span class="token-alert-icon">⚠️</span>','<span class="token-alert-icon">${tramIcon("warning")}</span>').replace('<span class="token-valid-icon">✅</span>','<span class="token-valid-icon">${tramIcon("approved")}</span>');p.write_text(s,encoding='utf-8')
p=web/'js/views/TableView.js';s=p.read_text(encoding='utf-8')
for a,b in [('⚠️ Thiếu','${tramIcon("warning")} Thiếu'),('💡 Gợi ý:','${tramIcon("glossary")} Gợi ý:'),('🗣️ ${item.speaker}','${tramIcon("dialogue")} ${item.speaker}'),('👤 Dịch giả:','${tramIcon("profile")} Dịch giả:'),('💾 Lưu câu này','${tramIcon("save")} Lưu câu này')]:s=s.replace(a,b)
s=s.replace("${m.is_critical ? '⚠️' : ''}","${m.is_critical ? tramIcon('warning') : ''}")
p.write_text(s,encoding='utf-8')
p=web/'js/views/GlossaryView.js';s=p.read_text(encoding='utf-8')
# Replace only HTML output, not plaintext labels, tooltips or search terms.
s=s.replace('>⚠️ LƯU Ý</span>','>${tramIcon("warning")} LƯU Ý</span>')
# Single-quoted template literal branch needs string concatenation.
s=s.replace("'<span class=\"chip-warn-badge\">${tramIcon(\"warning\")} LƯU Ý</span>'", "'<span class=\"chip-warn-badge\">' + tramIcon('warning') + ' LƯU Ý</span>'")
s=s.replace('>🔍 Không tìm', '>${tramIcon("search")} Không tìm').replace('>📋 Sao chép</button>','>${tramIcon("copy")} Sao chép</button>')
s=s.replace("${item.is_critical ? '⚠️' : 'ℹ️'}", "${tramIcon(item.is_critical ? 'warning' : 'info')}")
p.write_text(s,encoding='utf-8')
css='''/* TramVH r01: theme-aware vector icons, scoped to the icon elements. */
.tram-icon{width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;flex:none;vertical-align:middle;line-height:1}
.tram-icon img{width:100%;height:100%;object-fit:contain}
.tram-icon-light{display:inline-block}.tram-icon-dark{display:none}
html[data-theme="dark"] .tram-icon-light{display:none}html[data-theme="dark"] .tram-icon-dark{display:inline-block}
.tram-brand-mark{width:48px;height:40px;display:inline-flex;align-items:center;flex:none}
.tram-brand-mark img{width:100%;height:100%;object-fit:contain}
.tram-theme-night{display:inline-flex}.tram-theme-day{display:none}
html[data-theme="dark"] .tram-theme-night{display:none}html[data-theme="dark"] .tram-theme-day{display:inline-flex}
.btn-circle .tram-icon{width:23px;height:23px}.mode-tab-btn,.btn-direction,.btn-voice>span,.btn-save-glow>span{display:inline-flex;align-items:center;gap:7px;justify-content:center}
.mode-tab-btn .tram-icon,.btn-direction .tram-icon,.btn-voice .tram-icon{width:21px;height:21px}
.input-title .tram-icon,.speech-badge-title .tram-icon,.ref-quote-label .tram-icon,.suggestions-title .tram-icon{width:20px;height:20px;margin-right:3px}
.modal-panel-header h2 .tram-icon{width:26px;height:26px;margin-right:7px}
.table-row-speaker .tram-icon,.table-row-bottom .tram-icon,.table-glossary-label .tram-icon,.list-token-warning .tram-icon,.glossary-action-btn .tram-icon,.notes-icon .tram-icon,.chip-warn-badge .tram-icon{width:18px;height:18px}
.sync-icon,.search-icon{display:inline-flex;align-items:center;justify-content:center}
.sync-icon .tram-icon,.search-icon .tram-icon{width:20px;height:20px}
.btn-save-glow .tram-icon-light{display:none}.btn-save-glow .tram-icon-dark{display:inline-block}
html[data-theme="dark"] .btn-save-glow .tram-icon-light{display:none}
.tram-icon--sm{width:20px;height:20px}.tram-icon--lg{width:32px;height:32px}
.tram-icon-button{min-width:44px;min-height:44px;display:inline-flex;align-items:center;justify-content:center}
@media(max-width:700px){.tram-brand-mark{width:40px;height:34px}}
'''
(assets/'icons.css').write_text(css,encoding='utf-8')
readme=(assets/'README.md').read_text(encoding='utf-8').replace('Chỉ tạo bộ asset mới, chưa thay index.html, manifest.json hay đăng bản mới lên Workers.','Đã tích hợp vào index.html, manifest.json, các view biên dịch/từ điển và điều khiển nhạc. IconView.js cung cấp hàm tramIcon(id) cho HTML động. Việc đồng bộ GitHub và kiểm tra Workers được ghi ở báo cáo tích hợp riêng.').replace('Không có thao tác lưu Google Sheets hay deploy web trong đợt này.','Không gửi bản dịch thử lên Google Sheets. Trạng thái GitHub/Workers xem báo cáo tích hợp riêng.')
(assets/'README.md').write_text(readme,encoding='utf-8')
print('Integrated:',', '.join(paths),'+ js/views/IconView.js + icons.css')
