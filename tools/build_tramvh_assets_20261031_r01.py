from pathlib import Path
import json, hashlib, html
from datetime import datetime
ROOT = Path(r'C:/YostarGames/StellaSora_EN/StellaSora_VietHoa')
OUT = ROOT/'web/story_translator/assets/tramvh-icons-r01'
OUT.mkdir(parents=True, exist_ok=False)
# Custom paths on a 32-unit grid. All drawings are original vector geometry.
ICONS = [
('home','Trang chủ','Điều hướng','<path d="m5 14 11-9 11 9v12a1 1 0 0 1-1 1h-7v-9h-6v9H6a1 1 0 0 1-1-1Z"/>','<path d="m5 14 11-9 11 9-3 1-8-6-8 6Z"/>'),
('chapters','Chương truyện','Điều hướng','<path d="M8 5h16v22H8a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3Zm0 0v17m-3 2a3 3 0 0 1 3-2h16M13 10h6m-6 5h8"/>','<path d="M8 5h4v17H8Z"/>'),
('scenes','Cảnh truyện','Điều hướng','<rect x="5" y="7" width="22" height="20" rx="3"/><path d="M5 13h22M10 7l3 6m4-6 3 6M9 3h14"/>','<path d="M5 10a3 3 0 0 1 3-3h16a3 3 0 0 1 3 3v3H5Z"/>'),
('visual-novel','Visual Novel','Điều hướng','<rect x="4" y="6" width="24" height="19" rx="3"/><path d="m12 11 9 5-9 5ZM12 29h8"/>','<path d="m12 11 9 5-9 5Z"/>'),
('list','Danh sách','Điều hướng','<rect x="5" y="5" width="22" height="22" rx="3"/><path d="M13 11h9m-9 5h9m-9 5h6M9 11h.1M9 16h.1M9 21h.1"/>','<rect x="5" y="5" width="5" height="22" rx="2"/>'),
('previous','Câu trước','Điều hướng','<path d="M9 7v18m14-3-9-6 9-6Z"/>','<path d="m23 22-9-6 9-6Z"/>'),
('next','Câu kế','Điều hướng','<path d="M23 7v18M9 10l9 6-9 6Z"/>','<path d="m9 10 9 6-9 6Z"/>'),
('menu','Mở menu','Điều hướng','<path d="M6 9h20M6 16h14M6 23h20"/>','<circle cx="25" cy="16" r="2"/>'),
('dialogue','Lời thoại','Biên dịch','<path d="M8 5h16a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H13l-7 5v-6a4 4 0 0 1-2-3V9a4 4 0 0 1 4-4Z"/><path d="M10 12h12m-12 5h8"/>','<path d="M13 23 6 28v-6Z"/>'),
('translate','Việt hóa','Biên dịch','<path d="M4 7h13M10 4v3m4 0c-1 7-4 10-10 13m2-9c2 4 5 7 9 9m2 7 6-15 6 15m-10-5h8"/>','<path d="m23 12 6 15h-4l-2-6-2 6h-4Z"/>'),
('edit','Biên tập','Biên dịch','<path d="m20 6 6 6M7 21l-2 7 7-2L27 11a2 2 0 0 0 0-3l-3-3a2 2 0 0 0-3 0Zm0 0 5 5M17 28h11"/>','<path d="m20 6 6 6-4 4-6-6Z"/>'),
('quill','Bút dịch','Biên dịch','<path d="M7 26C7 13 16 5 28 4c-1 12-9 21-22 21m4-4L23 9M17 15v-5m0 5h5M5 29l5-8"/>','<path d="M7 26C7 13 16 5 28 4L10 22Z"/>'),
('save','Lưu bản dịch','Biên dịch','<path d="M6 4h17l5 5v17a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm4 0v9h12V4M9 28V18h14v10M18 7v3"/>','<path d="M10 4h12v9H10Z"/>'),
('save-next','Lưu và tiếp tục','Biên dịch','<path d="M13 28H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h17l5 5v5M10 4v9h12V4M9 28V18h8m2 5h10m-4-4 4 4-4 4"/>','<path d="M10 4h12v9H10Z"/>'),
('glossary','Từ điển thuật ngữ','Biên dịch','<path d="M16 8C12 5 8 5 3 6v19c5-1 9-1 13 2 4-3 8-3 13-2V6c-5-1-9-1-13 2Zm0 0v19M7 11l5 1m-5 4 5 1m8-5 5-1m-5 6 5-1"/>','<path d="M16 8c4-3 8-3 13-2v19c-5-1-9-1-13 2Z"/>'),
('tokens','Token hệ thống','Biên dịch','<path d="M11 5H8a2 2 0 0 0-2 2v5a4 4 0 0 1-3 4 4 4 0 0 1 3 4v5a2 2 0 0 0 2 2h3m10-22h3a2 2 0 0 1 2 2v5a4 4 0 0 0 3 4 4 4 0 0 0-3 4v5a2 2 0 0 1-2 2h-3m-4-16-3 10"/>','<path d="m16 10 3 6-3 6-3-6Z"/>'),
('copy','Sao chép','Biên dịch','<rect x="10" y="10" width="17" height="18" rx="3"/><path d="M21 10V7a3 3 0 0 0-3-3H7a3 3 0 0 0-3 3v11a3 3 0 0 0 3 3h3m5-5h7m-7 5h7"/>','<rect x="10" y="10" width="17" height="6" rx="2"/>'),
('undo','Hoàn tác','Biên dịch','<path d="M11 7 4 14l7 7m-7-7h14a9 9 0 0 1 0 18" transform="translate(0 -3)"/>','<circle cx="22" cy="24" r="3"/>'),
('search','Tìm kiếm','Công cụ','<circle cx="14" cy="14" r="9"/><path d="m21 21 7 7M10 14a4 4 0 0 1 4-4"/>','<circle cx="14" cy="14" r="9"/>'),
('filter','Lọc câu thoại','Công cụ','<path d="M5 5h22L19 16v9l-6 3V16Z"/>','<path d="M5 5h22l-4 6H9Z"/>'),
('sync','Đồng bộ','Công cụ','<path d="M27 12a12 12 0 0 0-20-5L4 10m0-6v6h6M5 20a12 12 0 0 0 20 5l3-3m0 6v-6h-6"/>','<circle cx="16" cy="16" r="4"/>'),
('upload','Tải lên','Công cụ','<path d="M9 25H7a5 5 0 0 1-1-10 10 10 0 0 1 19-3 7 7 0 0 1 0 14h-2m-7 2V16m-5 5 5-5 5 5"/>','<path d="M6 15a10 10 0 0 1 19-3 7 7 0 0 1 3 2H11Z"/>'),
('download','Tải xuống','Công cụ','<path d="M16 4v17m-6-6 6 6 6-6M5 22v4a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2v-4"/>','<path d="M5 24h22v2a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2Z"/>'),
('sheet','Bảng dữ liệu','Công cụ','<path d="M7 4h13l6 6v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm13 0v6h6M10 15h12v8H10Zm0 4h12m-6-4v8"/>','<path d="M20 4v6h6Z"/>'),
('external-link','Mở liên kết','Công cụ','<path d="M18 5h9v9m0-9L14 18m-1-11H7a3 3 0 0 0-3 3v15a3 3 0 0 0 3 3h15a3 3 0 0 0 3-3v-6"/>','<path d="m18 5 9 9V5Z"/>'),
('settings','Cài đặt','Công cụ','<path d="M5 8h22M5 16h22M5 24h22"/><circle cx="12" cy="8" r="3"/><circle cx="22" cy="16" r="3"/><circle cx="10" cy="24" r="3"/>','<circle cx="12" cy="8" r="3"/><circle cx="22" cy="16" r="3"/><circle cx="10" cy="24" r="3"/>'),
('close','Đóng','Công cụ','<path d="m9 9 14 14M23 9 9 23"/>',''),
('help','Trợ giúp','Công cụ','<circle cx="16" cy="16" r="12"/><path d="M12 12a4 4 0 1 1 6 3.5c-2 1-2 2-2 3.5m0 4h.01"/>','<circle cx="16" cy="16" r="12"/>'),
('approved','Đã duyệt','Trạng thái','<path d="m16 3 4 3 5 1 1 5 3 4-3 4-1 5-5 1-4 3-4-3-5-1-1-5-3-4 3-4 1-5 5-1Z"/><path d="m10 16 4 4 8-8"/>','<path d="m16 3 4 3 5 1 1 5 3 4-3 4-1 5-5 1-4 3-4-3-5-1-1-5-3-4 3-4 1-5 5-1Z"/>'),
('translated','Đã dịch','Trạng thái','<path d="M18 4H7a2 2 0 0 0-2 2v20a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V13M11 10h5m-5 6h5m-5 6h10m-1-16 3 3 6-6"/>','<path d="M5 23h22v3a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2Z"/>'),
('pending','Chờ xử lý','Trạng thái','<path d="M8 4h16M8 28h16M10 4v5l12 14v5M22 4v5L10 23v5M12 10h8m-8 13h8"/>','<path d="M12 23h8l2 3v2H10v-2Z"/>'),
('warning','Cần kiểm tra','Trạng thái','<path d="m14 5-11 20a2 2 0 0 0 2 3h22a2 2 0 0 0 2-3L18 5a2 2 0 0 0-4 0ZM16 12v7m0 4h.01"/>','<path d="m14 5-11 20a2 2 0 0 0 2 3h22a2 2 0 0 0 2-3L18 5a2 2 0 0 0-4 0Z"/>'),
('error','Có lỗi','Trạng thái','<circle cx="16" cy="16" r="12"/><path d="m12 12 8 8m0-8-8 8"/>','<circle cx="16" cy="16" r="12"/>'),
('info','Thông tin','Trạng thái','<circle cx="16" cy="16" r="12"/><path d="M16 15v8m0-14h.01"/>','<circle cx="16" cy="16" r="12"/>'),
('check','Hoàn thành','Trạng thái','<path d="m6 16 7 7L27 9"/>',''),
('profile','Hồ sơ dịch giả','Cộng đồng','<circle cx="16" cy="10" r="6"/><path d="M5 28v-2a11 11 0 0 1 22 0v2Z"/>','<circle cx="16" cy="10" r="6"/>'),
('community','Cộng đồng','Cộng đồng','<circle cx="12" cy="10" r="5"/><path d="M3 27v-3a9 9 0 0 1 18 0v3ZM22 5a5 5 0 0 1 0 10m2 4a8 8 0 0 1 5 8"/>','<circle cx="12" cy="10" r="5"/>'),
('trophy','Bảng xếp hạng','Cộng đồng','<path d="M9 4h14v8a7 7 0 0 1-14 0ZM9 7H4v3a6 6 0 0 0 7 6m12-9h5v3a6 6 0 0 1-7 6m-5 3v6m-6 3h12m-10-3h8"/>','<path d="M9 4h14v8a7 7 0 0 1-14 0Z"/>'),
('medal','Huy hiệu','Cộng đồng','<circle cx="16" cy="21" r="8"/><path d="m10 15-5-11h8l3 9m6 2 5-11h-8l-3 9m0 4 1.3 2.6 2.9.4-2.1 2 .5 2.9-2.6-1.3-2.6 1.3.5-2.9-2.1-2 2.9-.4Z"/>','<circle cx="16" cy="21" r="8"/>'),
('star','Ngôi sao','Cộng đồng','<path d="m16 3 4 8 9 1.5-6.5 6.2L24 28l-8-4.5L8 28l1.5-9.3L3 12.5l9-1.5Z"/>','<path d="m16 3 4 8 9 1.5-6.5 6.2L24 28l-8-4.5L8 28l1.5-9.3L3 12.5l9-1.5Z"/>'),
('xp','Kinh nghiệm','Cộng đồng','<path d="m18 3-13 16h10l-1 10 13-16H17Z"/>','<path d="m18 3-13 16h10l-1 10 13-16H17Z"/>'),
('sun','Chế độ sáng','Âm thanh & giao diện','<circle cx="16" cy="16" r="6"/><path d="M16 3v3m0 20v3M3 16h3m20 0h3M7 7l2 2m14 14 2 2M25 7l-2 2M9 23l-2 2"/>','<circle cx="16" cy="16" r="6"/>'),
('moon','Chế độ tối','Âm thanh & giao diện','<path d="M28 18A12 12 0 0 1 14 4a12 12 0 1 0 14 14Z"/><path d="m24 3 1 3 3 1-3 1-1 3-1-3-3-1 3-1Z"/>','<path d="M28 18A12 12 0 0 1 14 4a12 12 0 1 0 14 14Z"/>'),
('music','Nhạc nền','Âm thanh & giao diện','<path d="M12 24V8l15-4v16M12 12l15-4"/><ellipse cx="8" cy="25" rx="4" ry="3"/><ellipse cx="23" cy="21" rx="4" ry="3"/>','<path d="m12 8 15-4v4l-15 4Z"/><ellipse cx="8" cy="25" rx="4" ry="3"/>'),
('music-off','Tắt nhạc nền','Âm thanh & giao diện','<path d="M12 24V12m0-4 15-4v16m-11-9 11-3M4 4l24 24"/><ellipse cx="8" cy="25" rx="4" ry="3"/><path d="M27 21a4 3 0 0 1-8 0"/>','<path d="m12 8 15-4v4l-11 3Z"/>'),
('volume','Lồng tiếng','Âm thanh & giao diện','<path d="M5 12h6l7-7v22l-7-7H5Zm17 0a7 7 0 0 1 0 8m3-13a13 13 0 0 1 0 18"/>','<path d="m11 12 7-7v22l-7-7Z"/>'),
('volume-off','Tắt lồng tiếng','Âm thanh & giao diện','<path d="M5 12h6l7-7v22l-7-7H5Zm18 1 6 6m0-6-6 6"/>','<path d="m11 12 7-7v22l-7-7Z"/>'),
('play','Phát','Âm thanh & giao diện','<circle cx="16" cy="16" r="12"/><path d="m13 10 9 6-9 6Z"/>','<path d="m13 10 9 6-9 6Z"/>'),
('pause','Tạm dừng','Âm thanh & giao diện','<circle cx="16" cy="16" r="12"/><path d="M12 11v10m8-10v10"/>','<circle cx="16" cy="16" r="12"/>'),
]
PALETTES={'light':{'ink':'#28687b','accent':'#bf8b3b'},'dark':{'ink':'#b9e4ed','accent':'#efc47f'},'mono':{'ink':'currentColor','accent':'currentColor'}}
COLORS={'approved':('#287e6b','#287e6b'),'translated':('#287e6b','#287e6b'),'warning':('#95651e','#b17a28'),'error':('#a64657','#a64657')}

def svg(body,under='',variant='light',name='',viewbox='0 0 32 32',width=32):
 p=PALETTES[variant]; ink=p['ink']; accent=p['accent']
 if name=='upload':
  body='<g transform="translate(1 1) scale(.92)">'+body+'</g>'
  under='<g transform="translate(1 1) scale(.92)">'+under+'</g>'
 if variant=='light' and name in COLORS: ink,accent=COLORS[name]
 if variant=='dark' and name in COLORS: ink,accent={'approved':('#91d8bd','#91d8bd'),'translated':('#91d8bd','#91d8bd'),'warning':('#efc47f','#efc47f'),'error':('#f3a8b5','#f3a8b5')}[name]
 style=f'--tram-ink:{ink};--tram-accent:{accent};'
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{width}" viewBox="{viewbox}" fill="none" style="{style}"><g fill="var(--tram-accent)" opacity=".18">{under}</g><g stroke="var(--tram-ink)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
items=[]
for variant in PALETTES:
 d=OUT/'svg'/variant;d.mkdir(parents=True)
 for key,label,category,body,under in ICONS:
  file=d/f'{key}.svg';file.write_text(svg(body,under,variant,key),encoding='utf-8')
  if variant=='light':items.append({'id':key,'label':label,'category':category,'viewBox':'0 0 32 32','recommended_size':[20,24,32],'files':{v:f'svg/{v}/{key}.svg' for v in PALETTES}})
 # Sprite follows currentColor in mono and retains scoped palette in colored modes.
 symbols=[]
 for key,label,cat,body,under in ICONS:
  s=svg(body,under,variant,key)
  content=s[s.index('>')+1:s.rfind('</svg>')]
  style=s.split('style="')[1].split('"')[0]
  symbols.append(f'<symbol id="tram-{key}" viewBox="0 0 32 32" style="{style}">{content}</symbol>')
 (OUT/f'sprite-{variant}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg">'+''.join(symbols)+'</svg>',encoding='utf-8')

# Identity: open book, writing feather, and north star. No game logo or game art reused.
MARK='''<path d="M32 42C24 37 16 37 6 40V18c10-3 18-3 26 2 8-5 16-5 26-2v22c-10-3-18-3-26 2Zm0-22v22M12 25c5-1 9-1 13 1m-13 6c5-1 9-1 13 1"/>
<path d="M30 36C34 22 42 12 53 8c-2 15-9 24-23 28Zm0 0 16-18m-7 9 7-1m-7 1 1-7M27 44l4-10"/>
<path d="m20 3 1.8 5.2L27 10l-5.2 1.8L20 17l-1.8-5.2L13 10l5.2-1.8Z"/>'''
MARK_UNDER='<path d="M32 20c8-5 16-5 26-2v22c-10-3-18-3-26 2Z"/><path d="M30 36C34 22 42 12 53 8c-2 15-9 24-23 28Z"/>'
brand=OUT/'brand';brand.mkdir()
for v in PALETTES:
 s=svg(MARK,MARK_UNDER,v,viewbox='0 0 64 52',width=64).replace('height="64"','height="52"').replace('stroke-width="1.7"','stroke-width="2"')
 (brand/f'tramvh-mark-{v}.svg').write_text(s,encoding='utf-8')
 # App icon with ample safe zone and a solid background for favicons/PWA.
 p=PALETTES[v]; bg='#eef7f8' if v=='light' else '#192d3d'
 if v=='mono':continue
 inner=s[s.index('>')+1:s.rfind('</svg>')]
 app=f'<svg fill="none" xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" style="--tram-ink:{p["ink"]};--tram-accent:{p["accent"]}"><rect width="512" height="512" rx="112" fill="{bg}"/><circle cx="256" cy="256" r="197" fill="none" stroke="{p["accent"]}" stroke-opacity=".25" stroke-width="2"/><g transform="translate(64 100) scale(6)">{inner}</g></svg>'
 (brand/f'tramvh-app-{v}.svg').write_text(app,encoding='utf-8')

BADGES=[('translator','Dịch giả','quill'),('storyteller','Người kể chuyện','dialogue'),('reviewer','Người duyệt','approved'),('terminologist','Người giữ thuật ngữ','glossary'),('contributor','Người đóng góp','community'),('honor','Vinh danh','star')]
bd=OUT/'badges';bd.mkdir()
for key,label,icon in BADGES:
 source=next(x for x in ICONS if x[0]==icon)
 for v in ['light','dark']:
  p=PALETTES[v]; bg='#f0f7f8' if v=='light' else '#213b4c'
  content=svg(source[3],source[4],v,icon); inner=content[content.index('>')+1:content.rfind('</svg>')]
  s=f'<svg fill="none" xmlns="http://www.w3.org/2000/svg" width="96" height="104" viewBox="0 0 96 104" style="--tram-ink:{p["ink"]};--tram-accent:{p["accent"]}"><path d="m27 66-6 32 27-12 27 12-6-32" fill="{p["accent"]}" fill-opacity=".22" stroke="{p["accent"]}" stroke-width="2"/><circle cx="48" cy="44" r="38" fill="{bg}" stroke="{p["accent"]}" stroke-width="2"/><circle cx="48" cy="44" r="31" fill="none" stroke="{p["ink"]}" stroke-opacity=".2"/><g transform="translate(24 20) scale(1.5)">{inner}</g></svg>'
  (bd/f'{key}-{v}.svg').write_text(s,encoding='utf-8')

css='''/* TramVH Icons r01 — opt-in; no global selectors. */
.tram-icon{width:1.5rem;height:1.5rem;display:inline-block;flex-shrink:0;vertical-align:-.22em;color:inherit}
.tram-icon--sm{width:1.25rem;height:1.25rem}.tram-icon--lg{width:2rem;height:2rem}
.tram-icon-light{display:inline-block}.tram-icon-dark{display:none}
html[data-theme="dark"] .tram-icon-light{display:none}html[data-theme="dark"] .tram-icon-dark{display:inline-block}
.tram-icon-button{min-width:44px;min-height:44px;display:inline-flex;align-items:center;justify-content:center}
'''
(OUT/'icons.css').write_text(css,encoding='utf-8')
manifest={'name':'TramVH — Soft Sky Icons','revision':'r01','date_local':'2026-10-31','source_web':'https://tramvh.doubled1302.workers.dev/','authoring':'Original SVG geometry; no image-generation model used','icon_count':len(ICONS),'variants':list(PALETTES),'palette':PALETTES,'icons':items,'badges':[{'id':x,'label':y} for x,y,z in BADGES],'brand':'brand/','integration':'asset_package_only; existing index, manifest and live web are unchanged'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

# Standalone offline catalog; the light/dark buttons affect only this preview.
sections=''
for category in dict.fromkeys(x[2] for x in ICONS):
 cards=''
 for key,label,cat,body,under in ICONS:
  if cat!=category:continue
  cards+=f'<button class="tile" data-search="{key} {label.lower()}" data-id="{key}" title="Sao chép tên asset {key}"><span class="sample"><img class="light" src="svg/light/{key}.svg" alt=""><img class="dark" src="svg/dark/{key}.svg" alt=""></span><span class="tile-label">{label}</span><code>{key}</code></button>'
 sections+=f'<section class="icon-section"><div class="section-heading"><h2>{category}</h2><span>{sum(1 for x in ICONS if x[2]==category):02} biểu tượng</span></div><div class="grid">{cards}</div></section>'
badges=''.join(f'<div class="badge"><img class="light" src="badges/{k}-light.svg" alt=""><img class="dark" src="badges/{k}-dark.svg" alt=""><span>{l}</span></div>' for k,l,i in BADGES)
preview='''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TramVH — Bộ biểu tượng r01</title><style>
:root{color-scheme:light;--bg:#f4f8f9;--paper:#fff;--ink:#29495a;--muted:#66828e;--line:#dce9ed;--soft:#ecf5f6;--accent:#267f9d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 'Segoe UI',sans-serif}button,input{font:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #69aebd;outline-offset:3px}.shell{max-width:1240px;margin:auto;padding:0 40px 56px}.top{height:82px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.wordmark{display:flex;align-items:center;gap:12px;font-size:21px;font-weight:750;letter-spacing:-.5px}.wordmark img{width:42px}.edition{font-size:11px;font-weight:650;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}.theme-button{border:1px solid var(--line);background:var(--paper);color:var(--ink);min-height:44px;padding:0 17px;border-radius:24px;display:flex;align-items:center;gap:10px}.theme-button img{width:20px}.hero{display:grid;grid-template-columns:1fr 330px;gap:44px;align-items:center;padding:50px 0 44px}.eyebrow{color:#8c6d36;font-size:11px;font-weight:750;letter-spacing:2px;text-transform:uppercase}h1{font-size:46px;line-height:1.12;letter-spacing:-1.8px;margin:16px 0 20px;max-width:650px}.intro{max-width:590px;color:var(--muted);line-height:1.8}.pills{display:flex;gap:8px;margin-top:24px;flex-wrap:wrap}.pill{padding:7px 12px;border-radius:7px;border:1px solid var(--line);font-size:12px;background:var(--paper)}.brand-panel{height:252px;background:#192d3d;border-radius:32px;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:0 20px 36px #284f6312}.brand-panel:before,.brand-panel:after{content:'';position:absolute;border:1px solid #efc47f2b;border-radius:50%;width:230px;height:230px}.brand-panel:after{width:300px;height:300px}.brand-panel img{width:180px;z-index:1}.brand-caption{position:absolute;bottom:24px;color:#adcbd0;letter-spacing:3px;font-size:10px}.toolbar{position:sticky;top:0;z-index:2;display:flex;gap:18px;align-items:center;justify-content:space-between;padding:18px 0;background:var(--bg);border-block:1px solid var(--line)}.search{display:flex;align-items:center;gap:10px;width:360px;border:1px solid var(--line);padding:0 14px;background:var(--paper);border-radius:12px}.search img{width:20px}.search input{width:100%;height:44px;background:none;border:none;color:var(--ink);outline:none}.size-control{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px}.size-control button{width:42px;height:36px;border:1px solid var(--line);border-radius:8px;background:var(--paper);color:var(--ink)}.size-control button[aria-pressed=true]{background:var(--ink);color:var(--paper)}.section-heading{display:flex;align-items:baseline;justify-content:space-between;margin:32px 0 16px}.section-heading h2{font-size:17px;margin:0;letter-spacing:-.3px}.section-heading>span{font-size:11px;text-transform:uppercase;letter-spacing:1.3px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(8,1fr);gap:10px}.tile{min-width:0;background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:20px 5px 13px;color:var(--ink);display:flex;flex-direction:column;align-items:center;gap:7px;transition:background .15s,transform .15s}.tile:hover{transform:translateY(-3px);background:var(--soft)}.sample{height:44px;display:flex;align-items:center;justify-content:center;margin-bottom:8px}.sample img{width:var(--icon-size,32px);height:var(--icon-size,32px)}.tile-label{font-size:11px;font-weight:600;text-align:center}.tile code{font-size:10px;color:var(--muted)}.badges{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:25px 15px;background:var(--paper);border:1px solid var(--line);border-radius:20px}.badge{display:flex;flex-direction:column;align-items:center;gap:13px;font-size:11px;color:var(--muted);text-align:center}.badge img{width:76px;height:83px}.integration{margin-top:35px;padding:26px;border:1px solid var(--line);border-radius:18px;background:var(--paper);display:flex;justify-content:space-between;gap:20px}.integration h2{font-size:17px;margin:0 0 8px}.integration p{font-size:13px;color:var(--muted);margin:0}.integration a{color:var(--accent);text-decoration:none;font-size:13px;white-space:nowrap;align-self:center}footer{display:flex;justify-content:space-between;margin-top:30px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:11px}.dark{display:none}html[data-theme=dark]{color-scheme:dark;--bg:#111f2c;--paper:#192e3d;--ink:#dbeff2;--muted:#9cbac5;--line:#304b5a;--soft:#223e4d;--accent:#9bd7e2}html[data-theme=dark] .light{display:none}html[data-theme=dark] .dark{display:block}[hidden]{display:none!important}.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);border:1px solid var(--line);background:var(--ink);color:var(--paper);padding:12px 20px;border-radius:12px;z-index:5;box-shadow:0 4px 20px #0002}
@media(max-width:900px){.grid{grid-template-columns:repeat(4,1fr)}.hero{grid-template-columns:1fr 240px;gap:25px}h1{font-size:38px}.brand-panel{height:230px}.brand-panel img{width:150px}}
@media(max-width:600px){.shell{padding:0 18px 30px}.top{height:72px}.edition{display:none}.hero{grid-template-columns:1fr;gap:24px;padding:30px 0}.brand-panel{height:185px}.brand-panel img{width:130px}.brand-caption{bottom:16px}h1{font-size:35px;letter-spacing:-1.1px}.intro{font-size:14px}.toolbar{flex-wrap:wrap;gap:12px}.search{width:100%}.size-control{justify-content:flex-end;width:100%}.grid{grid-template-columns:repeat(3,1fr);gap:8px}.tile{padding-top:17px}.badges{grid-template-columns:repeat(3,1fr);gap:25px 6px}.section-heading>span{font-size:9px}.integration{flex-direction:column}.integration a{align-self:flex-start}footer{gap:10px;font-size:10px}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><div class="shell"><header class="top"><div class="wordmark"><img class="light" src="brand/tramvh-mark-light.svg" alt=""><img class="dark" src="brand/tramvh-mark-dark.svg" alt="">TramVH <span class="edition">/ Asset collection 01</span></div><button id="theme" class="theme-button" aria-pressed="false"><img class="light" src="svg/light/moon.svg" alt=""><img class="dark" src="svg/dark/sun.svg" alt=""><span>Chế độ tối</span></button></header><div class="hero"><div><span class="eyebrow">Thiết kế riêng cho trạm Việt hóa</span><h1>Mỗi biểu tượng,<br>một nét đồng điệu.</h1><p class="intro">Một bộ nét mềm, rõ nghĩa và vừa vặn với không gian dịch truyện. Xanh trời cho thao tác, vàng ấm cho điểm nhấn — đồng bộ từ laptop đến điện thoại.</p><div class="pills"><span class="pill">__COUNT__ icon gốc</span><span class="pill">SVG + PNG trong suốt</span><span class="pill">Sáng · Tối · Đơn sắc</span></div></div><div class="brand-panel"><img src="brand/tramvh-mark-dark.svg" alt="Biểu tượng sách mở, ngòi bút và sao dẫn đường"><span class="brand-caption">TRAMVH · THE STORY STATION</span></div></div><div class="toolbar"><label class="search"><img class="light" src="svg/light/search.svg" alt=""><img class="dark" src="svg/dark/search.svg" alt=""><input id="search" type="search" aria-label="Tìm biểu tượng" placeholder="Tìm biểu tượng hoặc chức năng…"></label><div class="size-control"><span>Xem ở</span><button data-size="20" aria-pressed="false">20</button><button data-size="24" aria-pressed="false">24</button><button data-size="32" aria-pressed="true">32</button><span>px</span></div></div>__SECTIONS__<section><div class="section-heading"><h2>Huy hiệu cộng đồng</h2><span>06 biểu tượng lớn</span></div><div class="badges">__BADGES__</div></section><aside class="integration"><div><h2>Sẵn sàng đưa vào giao diện</h2><p>SVG riêng lẻ, sprite SVG, PNG 64/128 px và icon ứng dụng. Bấm một icon để sao chép tên asset.</p></div><a href="README.md">Xem hướng dẫn sử dụng ↗</a></aside><footer><span>TramVH · Soft Sky Icons / r01</span><span>Bản xem thử cục bộ · 31.10.2026</span></footer></div><div id="toast" class="toast" hidden role="status"></div><script>
const root=document.documentElement;document.querySelector('#theme').onclick=e=>{const dark=root.dataset.theme!=='dark';root.dataset.theme=dark?'dark':'light';document.querySelector('#theme').setAttribute('aria-pressed',String(dark));document.querySelector('#theme span').textContent=dark?'Chế độ sáng':'Chế độ tối';};const normalize=s=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');document.querySelector('#search').oninput=e=>{const q=normalize(e.target.value);document.querySelectorAll('.tile').forEach(t=>t.hidden=!normalize(t.dataset.search).includes(q));document.querySelectorAll('.icon-section').forEach(s=>s.hidden=![...s.querySelectorAll('.tile')].some(t=>!t.hidden));};document.querySelectorAll('[data-size]').forEach(b=>b.onclick=()=>{root.style.setProperty('--icon-size',b.dataset.size+'px');document.querySelectorAll('[data-size]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));});let timer;document.querySelectorAll('.tile').forEach(t=>t.onclick=async()=>{let msg;try{await navigator.clipboard.writeText(t.dataset.id);msg='Đã sao chép: '+t.dataset.id;}catch{msg='Tên asset: '+t.dataset.id;}const toast=document.querySelector('#toast');toast.textContent=msg;toast.hidden=false;clearTimeout(timer);timer=setTimeout(()=>toast.hidden=true,2000);});
</script></body></html>'''
(OUT/'preview.html').write_text(preview.replace('__COUNT__',str(len(ICONS))).replace('__SECTIONS__',sections).replace('__BADGES__',badges),encoding='utf-8')
(OUT/'README.md').write_text('''# TramVH — Soft Sky Icons r01

Bộ asset mới dành cho web https://tramvh.doubled1302.workers.dev/, đối chiếu mã web cục bộ `web/story_translator/` ngày 31/10/2026. Hình SVG được vẽ riêng bằng mã vector, không sao chép artwork hay logo của game. Không sử dụng mô hình tạo ảnh.

## Thành phần

- 49 icon UI, mỗi icon có 3 phiên bản: `svg/light`, `svg/dark`, `svg/mono` (xem số chuẩn trong manifest.json).
- 3 sprite SVG tương ứng. ID có dạng `tram-save`, `tram-glossary`.
- PNG light/dark ở 64 và 128 px; nền trong suốt.
- 6 huy hiệu cộng đồng, mỗi huy hiệu có bản sáng/tối. Đây là asset tùy chọn; chưa gán vào cấp độ hay thành tích thật.
- Biểu tượng TramVH: sách mở + bút dịch + sao dẫn đường; 3 bản SVG nền trong suốt.
- Icon ứng dụng có nền đặc, favicon 16/32/48 và icon PWA 192/512; có vùng đệm cho safe zone maskable.
- `icons.css` là CSS chỉ có class được đặt tiền tố; `manifest.json` liệt kê asset.
- Mở `preview.html` để tìm kiếm, xem sáng/tối, đổi kích thước và xem huy hiệu. Không cần mạng.

## Dùng với cấu trúc web hiện tại

Bộ này đang ở `assets/tramvh-icons-r01/`. Chỉ tạo bộ asset mới, chưa thay index.html, manifest.json hay đăng bản mới lên Workers.

Cách đơn giản, dùng ảnh SVG màu theo theme (không cần JavaScript):

```html
<link rel="stylesheet" href="assets/tramvh-icons-r01/icons.css">
<button type="button" aria-label="Lưu bản dịch">
  <img class="tram-icon tram-icon-light" src="assets/tramvh-icons-r01/svg/light/save.svg" alt="">
  <img class="tram-icon tram-icon-dark" src="assets/tramvh-icons-r01/svg/dark/save.svg" alt="">
</button>
```

CSS dùng đúng thuộc tính theme hiện có: `html[data-theme="dark"]`. Giữ hàm và ID của nút đang dùng; chỉ đổi phần hình bên trong. Nhãn aria-label cần nằm trên nút; icon trang trí có alt rỗng.

Dùng sprite đơn sắc để thừa hưởng màu chữ hiện tại:

```html
<button type="button" aria-label="Mở từ điển thuật ngữ">
  <svg class="tram-icon" aria-hidden="true">
    <use href="assets/tramvh-icons-r01/sprite-mono.svg#tram-glossary"></use>
  </svg>
</button>
```

Sprite ngoài cần chạy trên HTTP cùng origin; khi mở file trực tiếp, dùng SVG qua img như preview. `currentColor` chỉ thừa hưởng từ trang khi SVG inline hoặc qua use; img của bản mono mặc định màu đen, không tự đổi theo màu CSS cha.

Kích thước khuyên dùng: 20 hoặc 24 px trong nút, 32 px trong thẻ, huy hiệu 64–96 px. Giữ vùng chạm nút tối thiểu 44×44 px. Status đã duyệt/chờ/lỗi luôn đi kèm chữ, không truyền đạt chỉ bằng màu. Icon save-next dùng hình lưu + mũi tên; icon next/previous có vạch chặn để phân biệt với play.

## Gợi ý thay thế đúng chức năng

| Thành phần hiện tại | Asset |
|---|---|
| bgmToggleBtn | music / music-off |
| themeToggleBtn | moon / sun |
| openLeaderboardModal | trophy |
| openGlossaryModal | glossary |
| Mở Google Sheets | sheet hoặc external-link |
| tabGameMode / tabListMode | visual-novel / list |
| voiceJpBtn / voiceCnBtn | volume (giữ nhãn JP/CN) |
| navigateLine(-1 / 1) | previous / next |
| saveCurrentLine | save-next |
| Đồng bộ từ điển | sync |
| Kiểm token | tokens + approved/warning |

Không chèn hình vào option của select native; dùng nhãn chữ cho bộ lọc hoặc tạo custom select có hỗ trợ bàn phím trong một thay đổi riêng.

## Phạm vi kiểm chứng

Kết quả tự kiểm và hash được ghi ở QA.json/SHA256SUMS.txt sau khi xuất PNG. Xem ảnh preview-desktop.png, preview-dark.png và preview-mobile.png. Kiểm thử ở viewport di động bằng Chrome máy tính không thay thế kiểm trên điện thoại thật. Không có thao tác lưu Google Sheets hay deploy web trong đợt này.
''',encoding='utf-8')
print(json.dumps({'out':str(OUT),'icon_count':len(ICONS),'svg_files':len(list(OUT.rglob('*.svg')))},ensure_ascii=False))
