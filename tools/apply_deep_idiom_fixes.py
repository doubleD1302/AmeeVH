# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")

STM02_04_PERFECT_DICT = {
    "Act Four": "Hồi Bốn",
    "Girl in Black": "Thiếu Nữ Áo Đen",
    "You take down the gangs and mercenaries, but prove no match for the knights. As you flee, the white-haired mage fires a spell, and you dive to shield Minova with your own body.": 
        "Các bạn đánh bại đám côn đồ và lính đánh thuê, nhưng lại thất thế trước lực lượng kỵ sĩ thiện chiến. Giữa lúc tháo chạy, nữ pháp sư tóc trắng tung đòn ma thuật hiểm hóc, và bạn đã liều mình lao tới lấy thân mình đỡ đòn che chắn cho Minova.",
    "Pluvia Month": "Tháng Pluvia",
    "Ash District in Emor": "Khu Tro Tàn ở Thành Phố Emor",
    "This way! That gate won't hold 'em long.": "Lối này! Cánh cổng đó không giữ chân chúng được lâu đâu.",
    "How many people did Feagin hire? The area is crawling with mercs and gangsters all lookin' to cash in on us.": 
        "Mụ Feagin đã thuê bao nhiêu người vậy chứ? Khắp khu vực này lúc nhúc toàn lính đánh thuê và côn đồ đang lăm le săn tiền thưởng của chúng ta.",
    "Checked my phone. Huge bounty. A million Dorra a head.": 
        "Tôi vừa kiểm tra điện thoại rồi. Tiền thưởng cao ngất ngưởng. Một triệu Dorra cho mỗi cái đầu.",
    "That much?==W== Why didn't she just use that money to pay us what she owed?": 
        "Nhiều đến thế sao?==W== Sao mụ ta không dùng số tiền đó để trả khoản nợ cho chúng ta luôn đi chứ?",
    "Paying us more would mean bowing down to us. She'd see it as losing.": 
        "Trả thêm tiền cho chúng ta đồng nghĩa với việc mụ ta phải cúi đầu nhận sai. Mụ ta sẽ coi đó là thất bại nhục nhã.",
    "Hiring mercs to hunt us down? That's protecting her pride. Something she has to do, in her mind.": 
        "Thuê lính đánh thuê truy sát chúng ta ư? Đó là cách mụ ta bảo vệ thể diện thối tha của mình. Một việc mà theo mụ ta là bắt buộc phải làm.",
    "What a messed-up way to think.": "Đúng là lối suy nghĩ méo mó bệnh hoạn.",
    "We can't just keep running.": "Chúng ta không thể cứ chạy trốn mãi thế này được.",
    "Too many enemies. If we just flee, the bounty will draw in even more hunters.": 
        "Kẻ thù quá đông. Nếu chỉ biết tháo chạy, món tiền thưởng khổng lồ đó sẽ càng thu hút thêm nhiều thợ săn kéo đến.",
    "So what's the plan?": "Vậy kế hoạch của cậu là gì?",
    "They aren't Creta soldiers, just mercs after cash. If the target fights back hard, they lose motivation fast.": 
        "Bọn chúng không phải binh lính Creta chính quy, chỉ là đám đánh thuê hám tiền thôi. Nếu mục tiêu chống trả quyết liệt, chúng sẽ nhanh chóng nhụt chí ngay.",
    "You're planning to use the Ashwind Clan's usual playbook?": 
        "Cậu định áp dụng bài bản tác chiến quen thuộc của Gia Tộc Tàn Phong sao?",
    "Heh, you catch on quick!": "Heh, nắm bắt nhanh đấy!",
    "We're not runnin', and we're not hidin'...": "Chúng ta sẽ không trốn chạy, cũng chẳng việc gì phải lén lút ẩn nấp...",
    "We're gonna wait right here and take 'em head-on!": "Chúng ta sẽ phục kích ngay tại đây và nghênh chiến trực diện với bọn chúng!",
    "Anxious Mercenary": "Lính Đánh Thuê Sốt Ruột",
    "C'mon, get the door open! They are gonna bolt!": "Nhanh lên, phá cửa ra mau! Bọn chúng sắp chuồn mất rồi!",
    "Broke Gangster": "Tên Côn Đồ Túng Tiền",
    "I was here first! Stay outta my way when we get inside.": "Tao tới đây trước! Lúc vào trong cấm đứa nào cản đường tao đấy!",
    "Ha? Like anyone cares! It's first come, first served. You snooze, you lose.": "Hả? Ai thèm quan tâm chứ! Đến trước thì ăn trước. Chậm chân thì nhịn xơi!",
    "Excited Gangster": "Tên Côn Đồ Hăng Máu",
    "It's open!": "Cửa mở rồi!",
    "Outta my way! I was first!": "Tránh đường mau! Tao tới đầu tiên!",
    "Hey, don't push! Floor's covered in ice!": "Này, đừng có xô đẩy! Mặt đường đóng băng trơn tuột rồi!",
    "<size=51>I said don't push!</size>": "<size=51>Tao đã bảo đừng có xô đẩy mà!</size>",
    "You think a little trick like this is gonna stop me?!": "Tụi mày tưởng chút mánh khóe vặt vãnh này ngăn nổi tao sao?!",
    "Ow! Hey, my weapon!": "Ái da! Này, vũ khí của tao đâu rồi?!",
    "Come on, Amber, time to roll! <size=60>♪</size>": "Đi nào, Amber, tới giờ xuất kích rồi! <size=60>♪</size>",
    "Right.": "Rõ.",
    "Amber's black armbands whip out into the crowd, snatching dropped weapons and launching them into the air.": 
        "Vạt băng đen trên tay áo Amber vung ra giữa đám đông, thoăn thoắt tước sạch vũ khí rơi rớt rồi hất tung chúng lên không trung.",
    "A gust of wind lifts Noya, letting her easily pluck the soaring weapons.": 
        "Một cơn gió nâng bổng Noya lên, giúp cô bé dễ dàng gom trọn số vũ khí đang bay lơ lửng.",
    "I'll be taking these! Thanks!": "Mấy thứ này tớ xin nhé! Cảm ơn nhiều nha!",
    "Don't sweat it! We still outnumber 'em! We can take 'em bare-handed!": 
        "Không phải xoắn! Quân ta vẫn đông hơn bọn chúng! Tay không cũng thừa sức đè bẹp tụi nó!",
    "Everybody charge! We'll split the prize!": "Tất cả xông lên! Bắt được thì chia đều tiền thưởng!",
    "Heh. You small fry think you can run your mouths here?": "Hừ. Lũ tép riu tụi mày dám to mồm ở đây à?",
    "Talk to my bat first.": "Bước qua cây gậy bóng chày của bà đây trước đã.",
    "Relieved Mercenary": "Lính Đánh Thuê Thở Phào",
    "I... I surrender!": "T-Tôi... tôi xin hàng!",
    "Subdued Gangster": "Tên Côn Đồ Bị Khuất Phục",
    "Our mistake! Please, let us go! We won't try anything again!": 
        "Tụi... tụi em biết sai rồi! Xin các đại tỷ tha mạng! Tụi em không dám giở trò gì nữa đâu mà!",
    "What, you wanna get acquainted with my bat too? Bunch of spineless cowards.": 
        "Sao, tụi mày cũng muốn làm quen với cây gậy của ta à? Đúng là một lũ hèn nhát không có xương sống.",
    "Observing Mercenary": "Lính Đánh Thuê Đứng Xem",
    "No, no! We were just ... just walking the dog!": "K-Không, không có đâu! Tụi tôi chỉ... chỉ đang dắt chó đi dạo thôi mà!",
    "Right, guys?!": "Đúng không mấy đứa?!",
    "Barking Mercenary": "Lính Đánh Thuê Sủa Tiếng Chó",
    " ==W==<size=55>Woof, woof!!</size>": " ==W==<size=55>Gâu, gâu!!</size>",
    "Hey, you're not even a real dog!": "Nè, ông có phải là chó thật đâu chứ hả!",
    "Cap! Neuvira and I made it!": "Đội trưởng! Tôi với Neuvira tới ứng cứu rồi đây!",
    "Huh? Where'd everybody go?": "Ủa? Mọi người chạy đâu hết rồi?",
    "It was all Minova's plan.==W== Hitting them hard really did the trick. All of them took off with their tails between their legs.": 
        "Tất cả đều nằm trong tính toán của Minova.==W== Giáng cho chúng một đòn chí mạng quả nhiên hiệu nghiệm. Đứa nào đứa nấy cúp đuôi chạy té khói cả rồi.",
    "I-I didn't really do much... This is just how the Ashwind Clan gets by.": 
        "T-Tôi cũng chẳng làm gì nhiều đâu... Đây chỉ là cách sinh tồn quen thuộc của Gia Tộc Tàn Phong thôi mà.",
    "What's that noise? An earthquake?": "Tiếng động gì thế này? Động đất à?",
    "Imperial Knights.": "Kỵ Sĩ Hoàng Gia.",
    "What now? Beat them up too?": "Giờ tính sao đây? Đập cho bọn họ một trận luôn à?",
    "No. Look at their formation—Feagin must have paid a fortune for them.": 
        "Không được. Nhìn đội hình của họ kìa—chắc chắn mụ Feagin đã phải vung ra một gia tài khổng lồ để thuê bọn họ đấy.",
    "Against well-paid Imperial Guards, there's only one thing to do.": 
        "Đối đầu với đám Cận Vệ Hoàng Gia được trả lương hậu hĩnh thế này, chỉ có duy nhất một kế sách thôi.",
    "Grab your skateboards!": "Lên ván trượt mau!",
    "Racing through the Ash District's narrow alleys, Minova leads the way, a teenage ==SEX9== with ==SEX14== at her side. Behind them, Vollara brings Noya, and Neuvira brings Iris.": 
        "Lao vun vút qua những con hẻm chật hẹp ở Khu Tro Tàn, Minova dẫn đầu đoàn xe, một ==SEX9== tuổi thiếu niên kề vai sát cánh cùng ==SEX14==. Phía sau họ, Vollara chở theo Noya, còn Neuvira kèm cặp Iris.",
    "The heavily armored Imperial Guards pursue at a relentless pace. From the rooftops, Amber's shots strike their silver plating, only to dissipate harmlessly.": 
        "Đoàn Cận Vệ Hoàng Gia giáp trụ nặng nề ráo riết đuổi bám phía sau không rời nửa bước. Từ trên các mái nhà, những phát bắn của Amber găm thẳng vào lớp giáp bạc của chúng nhưng chỉ vô hại bật ra.",
    "White-Haired Girl": "Cô Gái Tóc Trắng",
    "What quarry you dredge these from?": "Bà lôi đám này từ cái xó xỉnh nào ra thế?",
    "Durable, certainly. But they can't get those Trekkers with that speed.": 
        "Đúng là lì lợm thật đấy. Nhưng với cái tốc độ rùa bò đó thì sao đuổi kịp đám Trekker kia được.",
    "Hey, what can you do? The Imperial Guard always puts defense first. And that's what I'm paying for.": 
        "Ấy, biết sao được? Cận Vệ Hoàng Gia luôn đặt phòng ngự lên hàng đầu mà. Và đó chính là thứ mà ta đã vung tiền ra mua.",
    "Master, could you lend a hand again? What you did earlier was remarkable!": 
        "Đại Sư, cô có thể ra tay giúp một lần nữa không? Ma thuật hồi nãy của cô quả thực quá đỗi phi phàm!",
    "Poof! Just like that, their magic was gone. Oh, the looks on their faces were so satisfying.": 
        "Chỉ một cái búng tay là ma thuật của bọn chúng biến sạch. Ôi, nhìn vẻ mặt thất thần của chúng lúc đó thỏa mãn làm sao.",
    "I refuse. Participating in such a crude \"hunt\" is beneath me.": 
        "Tôi từ chối. Tham gia vào một cuộc 'săn đuổi' thô thiển hạ cấp thế này thật xúc phạm danh dự của tôi.",
    "No, no, you don't have to go that far! Just stop their magic like you did before. That's all the Imperial Guard needs to catch them.": 
        "Ấy, không, đâu cần cô phải nhọc công đến thế! Chỉ cần phong ấn ma thuật của chúng như lúc trước thôi. Ngần ấy là đủ để Cận Vệ Hoàng Gia tóm gọn bọn chúng rồi.",
    "If you don't, their fees will drain my savings, and I won't be able to get the materials you need for your research.": 
        "Nếu cô không chịu giúp, tiền thuê kỵ sĩ sẽ vét sạch tiền tiết kiệm của tôi mất, và tôi sẽ chẳng còn tiền mua tài liệu phục vụ nghiên cứu cho cô đâu.",
    "Very well. This is the last time.": "Được thôi. Đây là lần cuối cùng đấy.",
    "Let's be clear. I will help you capture them. But leave me alone after this.": 
        "Nói trước cho rõ: Tôi sẽ giúp bà bắt bọn chúng. Nhưng xong chuyện này thì để tôi yên.",
    "The raven perched on the girl's shoulder launches itself like an arrow, straight at Minova.": 
        "Con quạ đen đậu trên vai cô gái lao vút đi như mũi tên xé gió, nhắm thẳng về phía Minova.",
    "Commercial Street": "Phố Thương Mại",
    "Minova's skateboard carves a perfect arc across the cobblestones, dodging a knight's lunging spear before she ducks into a narrow alley.": 
        "Ván trượt của Minova vạch một đường cong hoàn mỹ trên mặt đường lát đá, lách qua ngọn giáo đang đâm tới của kỵ sĩ rồi lủi nhanh vào một con hẻm hẹp.",
    "==PLAYER_NAME==, hang on tight! Making a sharp turn!": "==PLAYER_NAME==, bám cho chắc! Tôi sẽ bẻ lái cua gắt đấy!",
    "Whoa, how is this thing so fast? It's just a skateboard!": "Oa, sao cái thứ này chạy nhanh thế được nhỉ? Rõ ràng nó chỉ là một chiếc ván trượt thôi mà!",
    "Feels like ... it's keeping pace with the Lucky Oasis.": "Cảm giác như... tốc độ của nó ngang ngửa với chiếc Lucky Oasis vậy.",
    "It's magic-powered. I'll teach you sometime, if you want. We could even race on the Waterway.": 
        "Nó vận hành bằng ma thuật đấy. Hôm nào rảnh tôi dạy bạn lái, nếu bạn muốn. Chúng mình thậm chí có thể đua xe trên Thủy Lộ nữa cơ.",
    "The Waterway ... huh.": "Thủy Lộ... sao.",
    "I glance up at the Waterway arching high above the city. A strangely familiar raven plummets towards Minova's back.": 
        "Tôi ngước nhìn lên cầu Thủy Lộ đang uốn lượn vắt ngang qua bầu trời thành phố. Một con quạ đen quen thuộc đến kỳ lạ đang lao thẳng xuống sau lưng Minova.",
    "Shield her": "Lấy thân che chắn",
    "Look out!": "Coi chừng!",
    "Acting purely on instinct, I throw myself behind Minova. The black raven slams silently into my chest.": 
        "Hành động hoàn toàn theo bản năng, tôi lao mình ra phía sau che chắn trọn vẹn cho Minova. Con quạ đen đâm sầm trong im lặng vào lồng ngực tôi.",
    "Knight Captain": "Đội Trưởng Kỵ Sĩ",
    "Now's our chance!": "Thời cơ tới rồi!",
    "Give me the spear.": "Giao ngọn giáo đây cho ta.",
    "A sudden, powerful gust of wind tore through the air. In that moment, as I accepted my fate and stood ready to meet my end, it felt as though soft petals brushed against my skin.": 
        "Một luồng gió dữ dội bất ngờ xé toạc không gian. Trong khoảnh khắc ấy, khi tôi đã buông xuôi chấp nhận số phận và sẵn sàng đón nhận cái chết, cảm giác như có những cánh hoa mềm mại vừa khẽ lướt qua làn da tôi.",
    "In the flash of a clash, before me were gleaming tips of several dead spears, sharp and silent...": 
        "Giữa khoảnh khắc giao tranh chớp nhoáng, trước mắt tôi là mũi nhọn sáng loáng của những ngọn giáo lạnh lùng đã gãy rạp...",
    "You're...": "Người là...",
    "My apologies for the delay, my ==SEX11==.": "Thứ lỗi vì tôi tới trễ, ==SEX11== của tôi."
}

GENERAL_IDIOM_OVERRIDES = {
    # Cap!
    "Cap! I know! The most important part is the truck, especially the axle, right?": 
        "Đội trưởng! Tôi biết mà! Bộ phận quan trọng nhất là chiếc xe tải, đặc biệt là phần trục xe đúng không?",
    "Cap! Neuvira and I made it!": 
        "Đội trưởng! Tôi với Neuvira tới ứng cứu rồi đây!",
    "Cap! Those White Cat punks haven't shot back in a while.": 
        "Đội trưởng! Lũ nhóc White Cat đó đã một lúc lâu không thấy bắn trả rồi.",
    "Wait up, Cap! You're going way too fast!": 
        "Đợi đã, Đội trưởng! Cậu đi nhanh quá đấy!",
    "Take care of yourself too, cap.": 
        "Cậu cũng nhớ tự chăm sóc bản thân nhé, Đội trưởng.",
    
    # Don't sweat it
    "Don't sweat it! You're right on time. Go wash up and let's eat!": 
        "Đừng bận tâm! Cậu tới đúng giờ mà. Đi rửa tay chân rồi vào ăn cơm thôi!",
    "Don't sweat it. Having you close actually makes me feel safer. Knowing I won't get ambushed by the Nocturn Eterna takes a load off. I'll sleep like a rock tonight.":
        "Đừng bận tâm. Có em ở bên thực sự khiến anh thấy an tâm hơn. Biết rằng mình sẽ không bị Đêm Trường Vĩnh Cửu phục kích giúp tôi trút được gánh nặng. Tối nay chắc chắn tôi sẽ ngủ say một giấc thật ngon.",
    "Don't sweat it. It's part of the job.": 
        "Đừng bận tâm. Đó là một phần của công việc mà.",
    "Don't sweat it. You're Mom's kids too, so we're family. And family helps each other.": 
        "Không có gì phải ngại đâu. Các cậu cũng là con của Mẹ, vậy chúng ta là một gia đình rồi. Đã là người một nhà thì phải giúp đỡ nhau chứ.",
    "Don't sweat the details. Come on, cheers!": 
        "Để ý mấy tiểu tiết đó làm gì. Nào, cạn ly!",
    "Eh, don't sweat it. It wouldn't be R&D without a few explosions, would it?": 
        "Hì, bận tâm làm gì. Nghiên cứu phát triển mà không nổ vài lần thì đâu còn là R&D nữa, đúng không nào?",
    "Hahaha! Is that all? Don't sweat it!": 
        "Hahaha! Chỉ có thế thôi á? Chuyện nhỏ, đừng để bụng!",
    "We're on vacation! Don't sweat the details. Let's go check out our rooms!==W== Ocean-view suite, here we come!": 
        "Chúng mình đang đi nghỉ dưỡng mà! Bận tâm mấy chuyện vụn vặt đó làm gì. Mau đi xem phòng thôi!==W== Phòng suite view biển ơi, tụi này tới đây!",

    # On the house
    "A gift? No need, really. It's on the house.": 
        "Quà tặng á? Không cần đâu, thật đấy. Bữa này quán bao nhé.",
    "Oh, Doctor Coronis! Please, take it! It's on the house!": 
        "Ôi, Bác sĩ Coronis! Xin người cứ nhận lấy đi ạ! Món này là quán tặng người đó!",

    # Piece of cake
    "Yep, piece of cake! Now watch!": 
        "Chuẩn rồi, dễ như trở bàn tay! Xem đây này!",

    # Spill the beans
    "My, oh my.==W== Was I that desperate to spill the beans?==W== Turns out I was the Boss's prey all along★": 
        "Chao ôi là trời.==W== Chẳng lẽ tôi lại nóng lòng khai sạch sành sanh thế cơ à?==W== Hóa ra từ đầu tới cuối tôi mới chính là con mồi của Boss★",

    # Ring a bell
    "Rings a bell... I've definitely heard it before somewhere.": 
        "Nghe quen tai thật đấy... Chắc chắn tôi đã từng nghe thấy ở đâu đó rồi.",

    # Outta my way
    "<size=50>Move! Move! Outta my way!": 
        "<size=50>Tránh ra! Tránh ra! Tránh đường mau!",

    # Bag this bounty
    "Look at you, getting all sympathetic!==W== Bag this bounty, and we can kick back for months.": 
        "Nhìn mày kìa, tự dưng lại mềm lòng thế!==W== Tóm gọn món tiền thưởng này là chúng ta có thể ung dung xả hơi cả mấy tháng trời rồi.",

    # On the same page
    "Looks like everyone's on the same page! So, leader of Post Haste, what's the call?": 
        "Có vẻ như mọi người đều đồng lòng rồi đấy! Vậy thì, người dẫn dắt Chuyển Phát Hỏa Tốc, quyết định thế nào đây?",
    
    # Hang in there
    "Hang in there! We can rest in Cangwu!": 
        "Cố lên nào! Tới Thương Ô là chúng ta có thể nghỉ ngơi rồi!",
    
    # Give me a break
    "Give me a break... Stop teasing me.": 
        "Tha cho tôi đi... Đừng trêu tôi nữa mà.",

    # Safe and sound
    "Ms. Montana! Post Haste delivery! Letters and medicine, safe and sound, meow!": 
        "Cô Montana ơi! Chuyển Phát Hỏa Tốc tới giao hàng đây! Thư từ và thuốc men đã tới nơi an toàn nguyên vẹn, meo meo!",
}

ALL_OVERRIDES = {**STM02_04_PERFECT_DICT, **GENERAL_IDIOM_OVERRIDES}

def apply_to_rem_cache():
    p_cache = ROOT / "work/batches/remaining_lua_avg_cache.json"
    cache = json.load(open(p_cache, encoding="utf-8"))
    updated = 0
    for en, vi in ALL_OVERRIDES.items():
        if en in cache:
            cache[en] = vi
            updated += 1
    with open(p_cache, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"Updated {updated} entries in remaining_lua_avg_cache.json")

def apply_to_campaign19_unified():
    p_c19 = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl"
    lines = [json.loads(x) for x in p_c19.read_text(encoding="utf-8").splitlines()]
    updated = 0
    for item in lines:
        en = item.get("en", "").strip()
        if en in ALL_OVERRIDES:
            item["polished_vi"] = ALL_OVERRIDES[en]
            item["modified"] = True
            updated += 1
    with open(p_c19, "w", encoding="utf-8") as f:
        for item in lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Updated {updated} entries in UNIFIED_CAMPAIGN_19_POLISHED.jsonl")

def apply_to_story_proposals():
    p_story = ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"
    lines = [json.loads(x) for x in p_story.read_text(encoding="utf-8").splitlines()]
    updated = 0
    for item in lines:
        en = item.get("en", "").strip()
        if en in ALL_OVERRIDES:
            item["vi"] = ALL_OVERRIDES[en]
            updated += 1
    with open(p_story, "w", encoding="utf-8") as f:
        for item in lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Updated {updated} entries in UNIFIED_STORY_PROPOSALS.jsonl")

if __name__ == "__main__":
    apply_to_rem_cache()
    apply_to_campaign19_unified()
    apply_to_story_proposals()
