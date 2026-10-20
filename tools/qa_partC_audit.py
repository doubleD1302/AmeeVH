import json
import re

orig_path = 'StellaSora_VietHoa/work/batches/batch_10k_partC_character_stories.json'
tr_path = 'StellaSora_VietHoa/work/batches/batch_10k_partC_translated.json'

orig = json.load(open(orig_path, encoding='utf-8'))
tr = json.load(open(tr_path, encoding='utf-8'))

engine_strings = {
    'SetChoiceBegin', 'SetChoiceJumpTo', 'SetChoiceRollover', 'SetMainRoleTalk', 'EV_SOLO_L__in',
    'carriage_inside', 'carriage_inside_dusk', 'carriage_inside_night', 'chitose_pavilion_daylight',
    'chitose_pavilion_rain', 'city_alley_daylight', 'city_alley_daylight_winter', 'city_alley_dusk',
    'city_alley_night', 'city_park_daylight', 'city_street_daylight', 'city_street_daylight_winter',
    'city_street_dusk', 'dessert_house_inside', 'element_temporary', 'emoji_cranky_c', 'emoji_flower_c',
    'emoji_heart_c', 'emoji_pride_c', 'ep_mainline_001', 'field_daylight', 'field_room_inside_daylight',
    'field_town_daylight', 'forest_daylight_2', 'forest_daylight_2_a', 'forest_room_daylight_b',
    'forest_winter', 'grocery_store', 'guard_outside_daylight', 'hospital_inside',
    'hotel_guest_room_night', 'posthouse_inside_dusk', 'traveller_camp_a_daylight',
    'traveller_camp_b_daylight', 'travellers_home_inside', 'uniseed_warehouse', 'ward_inside_night',
    'wild_tower_daylight', 'wild_tower_dusk', 'wog_academy_corridor', 'wog_academy_office'
}

translated_engine = []
for k, o in orig.items():
    if (o in engine_strings or o.startswith(('fx_', 'qstory_', 'story_'))) and o != tr[k]:
        translated_engine.append((k, o, tr[k]))

print(f"Engine strings translated accidentally: {len(translated_engine)}")
for k, o, t in translated_engine[:20]:
    print(f"  [{k}] orig='{o}' -> trans='{t}'")
