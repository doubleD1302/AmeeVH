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

polished = {}
stats = {
    "engine_restored": 0,
    "untranslated_fixed": 0,
    "hoa_hong_fixed": 0,
    "hairpin_fixed": 0,
    "duplicated_fixed": 0,
    "noya_voice_polished": 0,
    "chitose_swordsmanship_polished": 0,
    "iris_shopping_polished": 0,
    "ruby_verified": 0,
    "total_reviewed": len(orig)
}

# Explicit line corrections for perfection
manual_fixes = {
    # Untranslated & partial English fixes
    "CG_112_01.34": "==W==<size=50>Bay ra khỏi ghế ngồi á?!</size>",
    "CG_112_01.35": "… Khoan đã, sao Loxy lại phát ra tiếng kêu đó thế?",
    "CG_112_01.39": "Không không không, sắp đâm rồi!==W== Không cua kịp đâu! Chúng ta chắc chắn sẽ lao xuống vực mất!",
    "CG_112_01.54": '"Tốt nhất hãy từ chối thẳng thừng nếu còn quý mạng sống."',
    "CG_112_01.56": "Lẽ ra mình nên nghe lời cô, ==W==Iris ơi...",
    "CG_112_01.60": "Haha, ==W==ngài thấy sao hả? ==W==Trình lái xe của em đỉnh chưa từng thấy đúng không...",
    "CG_112_02.4": "Phong cách lái xe của Noya khiến bạn không khỏi thắt thỏm lo âu. Quả nhiên, một tai nạn đã xảy ra, chỉ là không theo cách mà bạn lường trước.",
    "CG_112_02.12": "Nên em đã giảm tốc về lại tốc độ bình thường...",
    "CG_112_02.36": "Đầu chiếc xe đó có một vết lõm nhỏ. Chính là chiếc xe vừa đâm trúng chúng ta đấy.",
    "CG_112_02.40": "… Noya?",
    "CG_112_02.42": "Cận Vệ Đế Quốc sẽ không tới kịp đâu. Em và Loxy sẽ đích thân đuổi theo hắn.",
    "CG_112_02.62": "Tưởng đâm trúng Loxy rồi mà dễ dàng chuồn thoát thế à?",
    "CG_112_02.63": "Bản lĩnh của chú em rùa bò chỉ có thế thôi à?==W== Sao không tấp xe vào lề rồi chịu thua đi cho xong?",
    "CG_112_02.64": "Hừ! Khúc cua tới liệu mà hít khói xe của ta đi!==W==",
    "CG_112_02.67": "Ồ, hắn đâm sầm vào rồi. +Chà... Nghe tiếng va chạm đau điếng người luôn đấy...",
    "CG_112_02.68": "Tôi sẽ liên lạc với Cận Vệ Đế Quốc, Noya, em hãy kiểm tra xem tài xế có sao không.",
    "CG_112_02.69": "Ối?!==W== Hắn—hắn tự bò ra khỏi xe được kìa?!",
    "CG_112_02.72": "Này cô em tóc vàng, cô là đứa lái cái đống sắt vụn này đấy à?",
    "CG_112_02.73": "Không phải sắt vụn! Và đúng thế, tôi là tài xế đây.",
    "CG_112_02.78": "Rõ rồi! ==W==Ngài cứ nấp trong xe nhé! Em không muốn ngài bị thương đâu.",

    "CG_103_02.95": "Có kẻ ngáng đường kìa, tôi hạ gục hắn được chứ?",
    "CG_103_03.7": "Cảm ơn bạn đã góp phần giữ gìn an toàn cho khu phố!",
    "CG_103_03.9": "Cảm ơn các bạn đã xuất hiện kịp thời! Thật yên tâm khi thấy các hiệp sĩ ở đây!",
    "CG_103_03.11": "À phải rồi, Amber vẫn đang đợi mình...",
    "CG_103_03.16": "Mèo con không sao đâu, chỉ hơi đói một chút thôi.",
    "CG_103_03.17": "Tôi đã mua chút đồ ăn mang tới cho nó.",
    "CG_103_03.23": "Mình không nỡ phá vỡ khoảnh khắc êm đềm hoàn hảo thế này...",
    "CG_103_03.32": "Cậu có thể hiểu được cảm xúc của loài mèo ư?",

    "CG_111_03.63": "==W==Sáng nay tôi vừa cằn nhằn No<r=Seina></r>ya ==W==vì ăn trên giường,==W== mà giờ tôi cũng đang làm y như vậy...==W== Boss,==W== xin ngài hãy giữ bí mật này giúp tôi nhé!",
    "CG_134_01.33": "Suỵt, nhỏ tiếng thôi. Người đó trông giống như... ==W==Hội Trưởng của Hiệp Hội Boss. Nghe nói chỉ bằng một đòn ma pháp, ==SEX== đã quét sạch một Stellaroid to lớn ngang ngửa cả nhà máy Nông Nghiệp Liên Hợp.",

    # Hairpins / Drift / Noya Story polish
    "CG_112_01.1": "Bầu trời trong xanh và gió nhẹ thoảng qua.==W== Cuối tuần này không có ủy thác nào cần làm, ánh nắng ấm áp ru bạn vào giấc ngủ dễ chịu.",
    "CG_112_01.15": "Nếu Noya rủ ngài đi dạo trên chiếc Loxy...==W== Tốt nhất hãy từ chối thẳng thừng nếu ngài còn quý mạng sống của mình.",
    "CG_112_01.17": "Vâng. Mặc dù cô ấy đã hứa sẽ không bao giờ lái xe liều lĩnh nữa...==W== Dẫu sao thì cẩn tắc vô áy náy vẫn hơn.",
    "CG_112_01.27": "Vì em vừa thay thế bộ phận giảm xóc cho em ấy mà.==W== Phải lên xe ngồi thử thì ngài mới cảm nhận được độ êm ái chứ.",
    "CG_112_01.28": "Sao nào, ==PLAYER_NAME==? Ngài có muốn... đi dạo một vòng cùng Loxy không?",
    "CG_112_01.29": "Ngài có muốn...==W== Lượn một vòng...==W== Cùng Loxy không nào? Boss thân yêu của em~~",
    "CG_112_01.51": "Sau nhiều năm khổ luyện, vị nhân vật chính ấy có thể ôm cua gắt ở tốc độ cao mà không làm sánh một giọt nước nào.==W== Đến lúc đó, người cha mới chính thức công nhận anh ấy là một tài xế giao đậu hũ đích thực.",
    "CG_112_01.52": "Vì vậy em bắt đầu học theo. Mỗi lần đưa Loxy ra ngoài chạy thử, em luôn đặt một cốc nước bên cạnh. Đó là lời nhắc nhở nhỏ để em lái xe an toàn.",
    "CG_112_01.55": "Hóa ra đây chính là ý nghĩa của câu nói==W== \"tò mò hại thân.\"",
    "CG_112_01.57": "Boss! Phía trước chính là 5 khúc cua tay áo liên hoàn trứ danh đấy.==W== Đã đến lúc cho ngài chiêm ngưỡng bản lĩnh thực sự của em và Loxy rồi!",
    "CG_112_01.59": "… Sau 5 khúc cua tay áo, phía trước có một địa điểm...==W== Ngắm cảnh tuyệt đẹp luôn...",
    "CG_112_01.64": "se_095 *Mau tỉnh lại đi mà, ==PLAYER_NAME==?",

    "CG_112_02.16": "Đã đi dạo thì làm gì có \"đích đến\" chứ.==W== Cứ để con đường dẫn lối chúng ta đi bất cứ đâu. Mọi khung cảnh dọc đường đều vô cùng tuyệt đẹp.",
    "CG_112_02.17": "Nhất là những lúc thế này, khi được ở bên ngài.==W== Ngay cả con đường em đã lái qua cả nghìn lần cũng bỗng thấy... thật khác lạ.",
    "CG_112_02.20": "Thình thịch... thình thịch...==W== Tiếng tim em đập rộn ràng, ngỡ như sắp nhảy ra khỏi lồng ngực vậy...",
    "CG_112_02.34": "Con rùa nhà ta bò còn nhanh hơn! Thế mà cũng đòi lái xe à?==W==",
    "CG_112_02.41": "Tên khốn đó... Dám làm Loxy bị thương và khiến ngài gặp nguy hiểm thế này...",

    "CG_112_03.11": "Sư phụ, ==W==<size=50>Sư phụ!!</size>==W== Xin hãy nhận tôi làm đệ tử!!",
    "CG_112_03.14": "Cú drift phanh dừng xe vừa rồi của sư phụ... Đỉnh của chóp luôn!",
    "CG_112_03.15": "Tôi thật ngu ngốc khi dám chạy đua với người.==W== Chỉ có bậc thầy thực thụ như sư phụ mới sở hữu phong thái điềm tĩnh,==W== nhẹ nhàng đến thế!",
    "CG_112_03.16": "Ahaha... Anh bảo cú drift dừng xe đó á? Bộ nó khó đến vậy sao?",
    "CG_112_03.17": "Tất nhiên rồi!! Rất ít người có thể làm được như thế. Sư phụ, người luyện thế nào vậy??",
    "CG_112_03.18": "Em chỉ coi Loxy như người bạn đồng hành tâm đầu ý hợp thôi.==W== Nhờ đó, em ấy giống như một phần cơ thể của em và những thao tác ấy cứ tự nhiên xuất ra thôi.",
    "CG_112_03.20": "Đây chính là cảnh giới của một bậc thầy thực thụ sao? Thật không thể tin nổi...",
    "CG_112_03.21": "Xin người! Hãy thu nhận tôi làm đệ tử!!",
    "CG_112_03.24": "Tất nhiên rồi! Tất nhiên rồi! Tôi suýt chút nữa đâm vào bạn đồng hành của sư phụ!==W== Tôi vô cùng xin lỗi!!",
    "CG_112_03.40": "Đừng bận tâm về tôi... Cậu không sợ bị thương sao, No<r=Seina></r>ya?",
    "CG_112_03.60": "Vậy ngoắc tay hứa rồi nhé. Cấm nuốt lời đấy!",
    "CG_112_03.62": "Nhưng đừng lo! ==W==Từ giờ em sẽ biết chăm sóc bản thân tốt hơn ==W==để có thể bảo vệ ngài vào những thời khắc quan trọng nhất!",
    "CG_112_03.68": "Nhưng ngài biết đấy, có một điều mà hiệp sĩ Cận Vệ Đế Quốc nói rất đúng.==W== Luôn phải lái xe ở tốc độ an toàn, bất kể kỹ năng giỏi đến đâu.",
    "CG_112_03.75": "Lần tới khi chúng ta đi dạo và em lại muốn \"hết tốc lực\", tôi sẽ bật cuốn băng này lên cho em nghe.",

    # Chitose Swordsmanship polish
    "CG_144_01.15": "Cậu muốn tôi luyện tập cùng để đạt được cảnh giới \"Nhân Kiếm Hợp Nhất\" này sao?",
    "CG_144_01.19": "Tôi mong ước được trải nghiệm cảnh giới Hợp Nhất ấy cùng người—ngay lúc này, nếu có thể! Tôi mong nắm bắt được chân ý thực sự của kiếm đạo càng sớm càng tốt.",
    "CG_144_01.21": "Chẳng lẽ... trong mắt người, tôi vẫn chưa đủ chín muồi để lãnh hội cảnh giới Hợp Nhất sao?",
    "CG_144_01.24": 'Dù sao đi nữa—tôi nghĩ mọi chuyện sẽ ổn thôi! Chitose, tôi biết cậu nhất định sẽ lĩnh hội được "Nhân Kiếm Hợp Nhất" mà.',
    "CG_144_01.26": "Tất nhiên rồi. Sau cùng thì, tôi—khụ...==W== Tôi đang nói với tư cách là người đã nắm vững cảnh giới Hợp Nhất đấy nhé!",
    "CG_144_01.32": 'Tuyệt lắm. Dù tôi có cố giấu thì người cũng sẽ nhìn thấu ngay thôi, ==SEX11== của tôi, bởi người đã nắm vững "Nhân Kiếm Hợp Nhất" rồi mà.',
    "CG_144_01.34": 'Như người đã biết, tôi là một "thanh kiếm chưa tra vỏ". Vì thế tôi luôn lo lắng mình có thể vô tình làm tổn thương người qua đường.',
    "CG_144_01.36": "Vậy là cậu vẫn gặp khó khăn trong việc điều khiển ma kiếm bên trong cơ thể sao?",
    "CG_144_01.38": "Tôi không còn cách nào khác ngoài việc tự bẻ gãy kiếm của mình để tạ tội!",
    "CG_144_01.41": "Phù... Nghe Chitose nói về chuyện \"tự bẻ gãy kiếm\" nghe đáng sợ thật đấy. Đó không phải chuyện để đùa đâu...",
    "CG_144_01.47": "Không đâu, ==SEX11== của tôi, đây cũng là một phần tu luyện để đạt tới cảnh giới Nhân Kiếm Hợp Nhất. Tôi hoàn toàn thấu hiểu...!",
    "CG_144_01.55": "Tôi là thanh kiếm của người, ==SEX11== của tôi; và thanh kiếm thì đương nhiên phải luôn cận kề bên cạnh ==SEX11== của nó.",
    "CG_144_01.56": 'Đó là lý do tại sao tôi muốn người hãy "tra kiếm vào bao"...!',
    "CG_144_01.60": "Có phải tôi đã không thấu hiểu được ý đồ của người, ==SEX11== của tôi...? Nói gì đến việc đạt tới cảnh giới Nhân Kiếm Hợp Nhất. Có phải tôi đã thất bại rồi không...?",
    "CG_144_03.37": "Vậy thì tôi, Chitose—thanh kiếm của người,==W== sẽ dốc lòng nỗ lực gấp bội...==W== để làm chủ cảnh giới Nhân Kiếm Hợp Nhất,==W== và trở thành một thần kiếm tuyệt luân xứng đáng phục vụ người!",
    "CG_144_03.38": "Về phần mình, tôi cũng sẽ cố gắng hết sức để trở thành một kiếm chủ xứng đáng với thanh kiếm ấy.",
    "CG_144_03.42": "Chừng nào==W== sinh mệnh này còn tiếp diễn,==W== tôi nguyện mãi là thanh kiếm của người.==W== Tôi xin lập lời thề danh dự này trước người.",
    "CG_144_03.45": "Bằng sự điềm tĩnh tuyệt đối, Chitose vung kiếm chớp nhoáng—lưỡi kiếm vẽ nên một đường cung tuyệt mỹ giữa không trung. Trước khi tôi kịp nhận ra điều gì, cô ấy đã tra kiếm vào bao.",
    "CG_144_03.47": "Cô ấy có thể chẻ đôi cự thạch chỉ bằng một nhát kiếm... và dùng kiếm phong để thổi bay hơi ẩm... Kiếm thuật của Chitose thực sự quá đỗi phi phàm...",
    "CG_144_03.49": "Cảm ơn cậu nhé. Cứu nguy kịp thời thật đấy. Hừm... Tôi tuy không có kiếm thuật thần sầu như cậu, nhưng ít ra cũng có thể giúp cậu sấy khô mái tóc này!",
    "CG_144_03.51": "Chẳng phiền toái chút nào đâu. Chăm sóc thanh kiếm là bổn phận của một kiếm chủ mà.",
    "CG_144_03.69": 'Chuyện đó tạm gác lại đã... Chitose, cậu cứ như thế này thực sự ổn chứ? Ngay cả một "thanh kiếm" cũng không nên bắt mình làm việc quá sức...',
    "CG_144_03.71": 'Tôi không hề gượng ép bản thân đâu... Một thanh kiếm chỉ tìm thấy ý nghĩa khi luôn kề cận bên kiếm chủ của mình.',
    "CG_144_03.72": "Bổn phận của thanh kiếm là bảo vệ kiếm chủ—vì vậy ngay cả khi say ngủ, kiếm cũng phải luôn ở trong tầm tay.",
    "CG_144_03.74": 'Chẳng hạn như ba thanh kiếm này—==W==chúng chính là "cha", "mẹ" và "sư phụ" của tôi...',
    "CG_144_03.76": "Chính vì thế... Với tư cách là kiếm chủ của tôi, tôi hy vọng người sẽ luôn cho phép tôi ở bên cạnh phụng sự người.",
    "CG_144_03.85": "Chính xác. Như tôi đã thưa trước đó, thanh kiếm phải luôn ở bên cạnh kiếm chủ của mình mọi lúc mọi nơi—dù thức hay ngủ.",
    "CG_144_03.89": "Tại sao người lại chối từ? Chẳng lẽ rốt cuộc tôi không xứng đáng làm thanh kiếm của người sao...?",
    "CG_144_03.90": "Đã đến nước này rồi sao. Tôi đành phải tự bẻ gãy thanh kiếm này để tạ tội với người!",
    "CG_144_03.94": 'Thiếu nữ tự nhận mình là "thanh kiếm" và người đang rèn luyện để trở thành "kiếm chủ" của cô... Hành trình hướng tới cảnh giới Nhân Kiếm Hợp Nhất đích thực của họ chỉ vừa mới bắt đầu.',

    # Iris shopping polish
    "CG_111_01.60": "Nếu không đủ tiền mua đồ ăn, chúng ta sẽ không có sức làm ủy thác. Không có trang bị phù hợp, chúng ta sẽ không thể lên tầng cao nhất tìm Hộp Nguyện Ước. Không kiếm ra tiền thì không có ăn, không có ăn thì không kiếm ra tiền...",
    "CG_111_02.50": "Nhìn đằng kia kìa. Quay vòng quay giảm giá==W== và chém giá xuống sập sàn luôn... Đúng theo nghĩa đen đấy...",
    "CG_111_02.57": "Vậy là tỷ lệ giảm của mỗi lượt chém giá sẽ được quyết định bởi vòng quay sao."
}

# Regex replacements for common patterns
hoa_hong_replacements = [
    (r'\bkhoản hoa hồng\b', 'nhiệm vụ ủy thác'),
    (r'\bphí hoa hồng\b', 'thù lao ủy thác'),
    (r'\bhoa hồng\b', 'ủy thác'),
    (r'\bHoa hồng\b', 'Ủy thác')
]

for k, o in orig.items():
    # 1. Exact engine strings restore
    if o in engine_strings or o.startswith(('fx_', 'qstory_', 'story_')):
        polished[k] = o
        if o != tr[k]:
            stats["engine_restored"] += 1
        continue

    # 2. Manual fixes take precedence
    if k in manual_fixes:
        polished[k] = manual_fixes[k]
        stats["untranslated_fixed"] += 1
        continue

    v = tr[k]

    # 3. Hoa hong replacement if commission in orig
    if 'commission' in o.lower() and 'hoa hồng' in v.lower():
        for pat, rep in hoa_hong_replacements:
            v = re.sub(pat, rep, v)
        stats["hoa_hong_fixed"] += 1

    # 4. Remove duplicate terms like "Thành Phố Thành Phố"
    if 'Thành Phố Thành Phố' in v:
        v = v.replace('Thành Phố Thành Phố', 'Thành Phố')
        stats["duplicated_fixed"] += 1

    # 5. Common calques clean
    v = re.sub(r'\bbạn tình\b', 'đồng đội', v)
    v = re.sub(r'\bbản dựng\b', 'lối chơi', v)
    v = re.sub(r'\bkẻ thù\b', 'kẻ địch', v)
    v = re.sub(r'\bsiêu giáp\b', 'Bá Thể', v)
    v = re.sub(r'\bchiếc hộp ước nguyện\b', 'Hộp Nguyện Ước', v)
    v = re.sub(r'\bChiếc hộp ước nguyện\b', 'Hộp Nguyện Ước', v)
    v = re.sub(r'\bSơ Quang\b', 'Khải Minh', v)
    v = re.sub(r'\bFirstlight Noya\b', 'Noya - Khải Minh', v)

    # 6. Spacing around punctuation and tags
    v = re.sub(r'==\s*([A-Z0-9_]+)\s*==', r'==\1==', v)
    v = re.sub(r'\s+([,.:;?!])', r'\1', v)

    polished[k] = v

# Save polished output
with open(tr_path, 'w', encoding='utf-8') as f:
    json.dump(polished, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("Part C Localization QA Polish Completed Successfully!")
print(f"Total items in Part C: {len(polished)}")
for k, val in stats.items():
    print(f"  {k}: {val}")
print("=" * 60)
