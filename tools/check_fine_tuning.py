import json
import re

from test_build_part_b import proposals

english_words = [
    r'\b(the|and|you|is|are|was|were|have|has|had|with|for|about|from|into|this|that|these|those)\b',
    r'\b(what|why|how|when|where|who)\b',
    r'\b(miss|mister|lady|lord)\b'
]

potential_calques = [
    (r'\bở trong tay tốt\b', 'in good hands -> được chăm sóc cẩn thận / yên tâm'),
    (r'\blàm thế nào mà\b', 'how come / how did -> sao / làm sao / sao có thể'),
    (r'\bngười đàn ông\b', 'the man -> người đó / ông ấy'),
    (r'\bdưới radar\b', 'under the radar -> không bị chú ý / lọt lưới'),
    (r'\bkết luận trước\b', 'jump to conclusions -> vội vàng kết luận'),
    (r'\bvào cuối ngày\b', 'at the end of the day -> rốt cuộc / suy cho cùng'),
    (r'\bđóng gói kho báu\b', 'bag the treasure -> thu gom kho báu / ẵm trọn kho báu'),
    (r'\bđậu bên ngoài\b', 'parked outside (locomotive) -> đỗ bên ngoài'),
    (r'\bbạn đặt cược\b', 'you bet -> chắc chắn rồi / khỏi phải nói'),
]

hits = []
for p in proposals:
    iid = p['id']
    vi = p['vi_editorial']
    en = p['en']
    
    if iid in ['STsp_17_01.54', 'STsp_17_03.52', 'STsp_18_01.17', 'STev_01_04.119', 'STev_01_07.102', 'STev_01_09.35', 'STev_01_09.63']:
        continue
        
    for pat, desc in potential_calques:
        if re.search(pat, vi, re.I):
            hits.append((iid, desc, vi))
            
    # Check suspicious English
    # Exclude known English names/terms: Horizon, Philae, Emor, Sailstead, Laru, Bloc, Albedo, Grace Imperium, Teresa, Donna, Freesia, Loxy, Post Haste, Nova, Amber, Iris, Darcia, Karin, Shia, Marlene, Gobble, Dorra, Monolith, Artifact, Calor
    filtered_vi = re.sub(r'\b(Horizon|Philae|Emor|Sailstead|Laru|Bloc|Albedo|Grace Imperium|Teresa|Donna|Freesia|Loxy|Post Haste|Nova|Amber|Iris|Darcia|Karin|Shia|Marlene|Gobble|Dorra|Monolith|Artifact|Calor|Boss|Plan B|Wally)\b', '', vi, flags=re.I)
    for ew in english_words:
        m = re.findall(ew, filtered_vi, re.I)
        if m:
            hits.append((iid, f"Suspicious English: {m}", vi))

print(f"Total hits: {len(hits)}")
for h in hits[:25]:
    print(f"[{h[0]}] {h[1]}")
    print(f"      Text: {h[2]}\n")
