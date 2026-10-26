# -*- coding: utf-8 -*-
import json
import unicodedata
import re

OUTPUT_FILE = r'C:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/BATCH_FIX_04_STORY_SHORT_LINES.json'

with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

assert data['batch_id'] == 'BATCH_FIX_04_STORY_SHORT_LINES'
assert data['translator'] == 'TRANSLATOR_VI_STORY'
assert data['total_items'] == 306
entries = data['entries']
assert len(entries) == 306

print('1. Header and counts: PASS')

# Check required fields
for idx, e in enumerate(entries):
    for field in ['id', 'scene_id', 'entry_hash', 'source_en', 'text_vi', 'notes']:
        assert field in e, f'Missing field {field} in entry {idx}'
        assert e[field] is not None, f'None field {field} in entry {idx}'

print('2. Required fields: PASS')

# Check idioms
idioms_checked = 0
for e in entries:
    sc = e['scene_id']
    loc = e['id']
    vi = e['text_vi']
    en = e['source_en']
    if sc == 'STev_04_06' and 'My bad' in en:
        assert 'Sơ suất quá' in vi or 'Lỗi của' in vi
        assert 'Cái xấu của tôi' not in vi
        idioms_checked += 1
    if sc == 'CG_158_02' and 'grasping at straws' in en:
        assert 'bấu víu' in vi and 'hy vọng mong manh' in vi
        assert 'nắm ống hút' not in vi
        idioms_checked += 1
    if sc == 'STev_08_06' and 'Read the room' in en:
        assert 'nhìn tình huống' in vi or 'nhìn sắc mặt' in vi
        assert 'đọc phòng' not in vi.lower()
        idioms_checked += 1
    if sc == 'STsp_17_03' and 'back to square one' in en:
        assert 'trở về vạch xuất phát' in vi
        assert 'hình vuông' not in vi
        idioms_checked += 1
    if sc == 'CG_117_02' and 'draws her in the first round' in en:
        assert 'bốc thăm trúng cô ấy ở vòng đầu' in vi
        assert 'hòa cô ấy' not in vi
        idioms_checked += 1
    if sc == 'CG_disc4029' and 'perfect view' in en:
        assert 'góc ngắm' in vi.lower() and 'đỉnh' in vi.lower()
        assert 'cái nhìn hoàn hảo' not in vi
        idioms_checked += 1

assert idioms_checked == 6, f'Expected 6 idioms checked, got {idioms_checked}'
print('3. 6 Key Idioms: PASS')

# Check STm08_11
stm08_11_checked = 0
for e in entries:
    if e['scene_id'] == 'STm08_11':
        loc = e['id']
        vi = e['text_vi']
        if loc == 'root:k272':
            assert 'cận vệ' in vi and 'Nữ Hoàng' in vi and ('phản bội' in vi or 'sát hại' in vi)
            assert 'biểu diễn' not in vi
            stm08_11_checked += 1
        elif loc == 'root:k273':
            assert 'Cận Vệ Hoàng Gia' in vi and 'Đoàn Bạch Miêu' in vi and 'Huyễn Cảnh' in vi
            assert 'tiền trên trời' not in vi
            stm08_11_checked += 1
        elif loc == 'root:k274':
            assert 'Huyễn Cảnh' in vi and 'chiến loạn' in vi and 'tàn tích' in vi
            assert 'sát khí' not in vi
            stm08_11_checked += 1

assert stm08_11_checked == 3, f'Expected 3 STm08_11 checked, got {stm08_11_checked}'
print('4. STm08_11 Lore restoration: PASS')

# Check 58 calque sentences: none should have 'Đó là lý do tại sao'
calque_count = 0
for e in entries:
    vi = e['text_vi']
    if 'đó là lý do tại sao' in vi.lower() or 'đó là lí do tại sao' in vi.lower():
        calque_count += 1
assert calque_count == 0, f'Found {calque_count} remaining calques!'
print('5. 58 Calque phrases eliminated: PASS')

# Check token balance
tag_re = re.compile(r'<[^>]+>|\{[^{}]+\}|%\d*\$?[sdf]|==[A-Z0-9_]+==|\\n')
for idx, e in enumerate(entries):
    en_toks = sorted(tag_re.findall(e['source_en']))
    vi_toks = sorted(tag_re.findall(e['text_vi']))
    assert en_toks == vi_toks, f'Token mismatch at entry {idx}: EN={en_toks} vs VI={vi_toks}'

print('6. 100% Token preservation: PASS')

# Check Unicode NFC
for idx, e in enumerate(entries):
    assert unicodedata.normalize('NFC', e['text_vi']) == e['text_vi'], f'Non-NFC at entry {idx}'

print('7. 100% Unicode NFC: PASS')
print('=== ALL 7 QUALITY AND TECHNICAL GATES PASSED PERFECTLY! ===')
