# -*- coding: utf-8 -*-
"""
High-priority Story Terminology and Pronoun Consistency Overrides for Stella Sora.
Addresses:
1. Scene STm03_00_b:
   - Amber pronoun and address: change 'anh' -> 'cậu' to preserve unisex player identity.
   - Consistent term: 'giao dịch linh hồn' instead of 'đánh đổi linh hồn'.
   - Promotion: 'Phong Cấp' instead of 'Khuyến mãi'.
   - The Well of Worlds: 'Giếng Vạn Giới' instead of 'Giếng nước của Thế giới'.
   - Seal of Grace: 'Ấn Ký Ân Tứ' instead of 'Dấu ấn Ân điển'.
   - Oracle: 'Thần Dụ' instead of 'Oracle'.
2. General Story Terminology across all scenes:
   - 'The Well of Worlds' -> 'Giếng Vạn Giới'
   - 'God of Grace' -> 'Thần Ân Tứ'
   - 'Eye of Grace' -> 'Đôi Mắt Ân Tứ' / 'Tổ Chức Đôi Mắt Ân Tứ'
   - 'Seal of Grace' -> 'Ấn Ký Ân Tứ'
   - 'Creta Trading' -> 'Thương Hội Creta'
   - 'Promotion' -> 'Phong Cấp'
   - 'Oracle' -> 'Thần Dụ'
   - 'Soul Stones' -> 'Hồn Thạch'
   - 'Wishing Box' -> 'Hộp Ước Nguyện'
"""

STM03_00_B_PERFECT_DICT = {
    "==PLAYER_NAME==, don't stress over our soul trades.":
        "==PLAYER_NAME==, cậu không cần phải tự dằn vặt chuyện tụi này giao dịch linh hồn đâu.",
    "It was our choice. We're a Guild, and Guilds gotta stick together.":
        "Đó là lựa chọn của chính tụi này mà. Chúng ta là một Công hội, và người trong Công hội thì phải cùng chung hoạn nạn chứ.",
    "Noya and Iris feel the same way. You stood up for us, and we couldn't let you face the risks alone.":
        "Noya và Iris cũng nghĩ thế cả thôi. Cậu đã đứng ra che chắn cho tụi này, tụi này đâu thể để cậu một mình gánh chịu hiểm nguy được.",
    "Thanks, Amber.":
        "Cảm ơn cậu nhé, Amber.",
    "The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It's called \"Promotion.\"":
        "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên \"Phong Cấp\".",
    "The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It's called \"Oracle.\"":
        "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên \"Thần Dụ\".",
}

GENERAL_TERMINOLOGY_OVERRIDES = {
    "The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It's called \"Promotion.\"":
        "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên \"Phong Cấp\".",
    "The Well of Worlds Tyrant Development System has identified the power within this Seal of Grace. It's called \"Oracle.\"":
        "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới đã nhận diện sức mạnh bên trong Ấn Ký Ân Tứ này. Nó mang tên \"Thần Dụ\".",
    "Ahem. Pardon my manners. I'm Edda, a researcher with the Eye of Grace.":
        "Ừm. Xin thứ lỗi cho sự thất lễ của tôi. Tôi là Edda, một nhà nghiên cứu trực thuộc Tổ Chức Đôi Mắt Ân Tứ.",
    "Alright, I'm making my wish now!==W== O mighty God of Grace, please hear our prayer—":
        "Được rồi, giờ tôi sẽ thực hiện điều ước!==W== Hỡi Thần Ân Tứ tối cao, xin hãy lắng nghe lời cầu nguyện của chúng con—",
    "But the God of Grace looked right past me.":
        "Thế nhưng Thần Ân Tứ lại chẳng đoái hoài gì đến tôi.",
    "For us to meet again like this... Could it be the work of the God of Grace?":
        "Để chúng ta có thể hội ngộ thế này... Phải chăng chính là sự an bài của Thần Ân Tứ?",
    "Great ==SEX12==, do you think the God of Grace is actually real?":
        "Thưa ==SEX12== vĩ đại, ngài có nghĩ Thần Ân Tứ thực sự tồn tại không?",
    "Have you heard of the Eye of Grace, Tyrant?":
        "Ngài đã từng nghe qua về Tổ Chức Đôi Mắt Ân Tứ chưa, hỡi Bạo Chúa?",
    "Hehe. I forgot to mention... The Tyrant in the <i>Book of Grace Prophecies</i> is someone who does the good deeds no one else will.":
        "Hihi. Suýt nữa thì quên nói... Bạo Chúa được nhắc đến trong <i>Sách Tiên Tri Ân Tứ</i> là người sẵn sàng làm những việc nghĩa hiệp mà không ai dám làm.",
    "Heh... You're right.==W====RT==Fate can be so cruel. If this isn't some sick joke by the God of Grace, what else could it be?":
        "Heh... Cậu nói phải.==W====RT==Số phận trớ trêu thật đấy. Nếu đây không phải là trò đùa quái ác của Thần Ân Tứ thì còn là gì được nữa chứ?",
    "I-It's a disaster!==W== I'm a witch who feasts on the truth, yet I'm missing scoop after scoop.==W== Bwaahh... The God of Grace hates me...":
        "T-Thảm họa rồi!==W== Tôi là phù thủy săn tìm sự thật, thế mà hết lần này đến lần khác để hụt mất tin sốt dẻo.==W== Oa oa... Chắc Thần Ân Tứ ghét bỏ tôi rồi...",
    "I... I just happened to overhear those bigwigs talking about it...==W== That the Boss possesses a priceless Seal of Grace.":
        "Tôi... tôi chỉ vô tình nghe lỏm được mấy tay đầu sỏ bàn tán thôi...==W== Rằng Sếp đang nắm giữ một Ấn Ký Ân Tứ vô giá.",
    "Man, the God of Grace must be furious today. Picked a hell of a day to come down here... Talk about rotten luck.":
        "Trời ạ, hôm nay Thần Ân Tứ chắc hẳn đang nổi trận lôi đình rồi. Chọn đúng cái ngày xúi quẩy này để xuống đây... Đúng là đen như mực.",
    "Manual says we just channel magic—y'know, the Grace in our Soul Stones—to our fingertips and aim. It'll work out somehow!":
        "Sách hướng dẫn bảo chỉ cần dẫn truyền ma lực—cậu biết đấy, dòng Ân Tứ trong Hồn Thạch—ra đầu ngón tay rồi nhắm chuẩn là được. Thể nào cũng ổn thỏa thôi!",
    "No, I've never heard of the God of Grace having any other name.==W== I suppose it's just a unique belief of the North. People here revere more primal, natural entities.":
        "Không, tôi chưa từng nghe nói Thần Ân Tứ có danh xưng nào khác cả.==W== Tôi đoán đó chỉ là tín ngưỡng đặc thù của phương Bắc thôi. Cư dân ở đây sùng bái các thực thể tự nhiên nguyên sơ hơn.",
    "O God of Grace, please let us find a Wishing Box bigger than my hand.":
        "Hỡi Thần Ân Tứ, xin hãy cho chúng con tìm được một Chiếc Hộp Ước Nguyện to hơn bàn tay này.",
    "O mighty God of Grace, please hear my prayer...==W== Please grant me a picture book==W== that Noya, Amber, and Iris will all love.":
        "Hỡi Thần Ân Tứ tối cao, xin hãy lắng nghe lời khẩn cầu của con...==W== Xin ban cho con một cuốn truyện tranh==W== mà cả Noya, Amber lẫn Iris đều say mê yêu thích.",
    "Oh! You must mean those Trekkers! They just got back to Emor recently. Right now, they're helping the Ashwind Clan fight back against Creta Trading.":
        "Ồ! Chắc hẳn cậu đang nói đến những Lữ Khách kia rồi! Họ vừa mới trở lại Emor cách đây không lâu. Hiện họ đang hỗ trợ Thị Tộc Gió Tro chống lại Thương Hội Creta.",
    "Oh, Shia...==W== Thank you!!==W== O mighty God of Grace, please hear our prayer—":
        "Ôi, Shia...==W== Cảm ơn cậu!!==W== Hỡi Thần Ân Tứ tối cao, xin hãy lắng nghe lời cầu nguyện của chúng con—",
    "Our meeting must be guided by the God of Grace... Heh heh, let me show you how it works!":
        "Cuộc hội ngộ của chúng ta ắt hẳn là do Thần Ân Tứ dẫn lối rồi... Hehe, để tôi chỉ cho cậu xem nó vận hành thế nào nhé!",
    "She asked me once==W== if the Gods had forsaken her. I could only tell her the God of Grace abandons no one.":
        "Cô ấy từng hỏi tôi một lần==W== liệu các vị thần đã ruồng bỏ cô ấy chưa. Tôi chỉ có thể đáp rằng Thần Ân Tứ không bao giờ bỏ rơi bất kỳ ai.",
    "Some claim the God of Grace hears us, others think our harvested memories react with the Monolith...==W== There are endless theories.":
        "Có người bảo Thần Ân Tứ lắng nghe chúng ta, kẻ khác lại nghĩ ký ức hiến tế phản ứng với Cự Tháp...==W== Giả thuyết thì vô thiên lủng.",
    "That night, Gerie sees me safely back to the Lucky Oasis, as serene and gentle as a true devotee of the God of Grace.":
        "Đêm đó, Gerie hộ tống tôi an toàn trở về Lucky Oasis, dáng vẻ điềm đạm và dịu dàng hệt như một tín đồ thuần thành của Thần Ân Tứ.",
    "The Creta Trading's building is huge, and we're going in blind.":
        "Tòa nhà của Thương Hội Creta đồ sộ vô cùng, trong khi chúng ta lại mù tịt về tình hình bên trong.",
    "The Eye of Grace... Canace mentioned them. They're the intellectual elite, the absolute peak of academia and research on this continent.":
        "Đôi Mắt Ân Tứ... Canace từng nhắc tới họ rồi. Họ là giới tinh hoa tri thức, đỉnh cao tuyệt đối của học thuật và nghiên cứu trên lục địa này.",
    "The God of Grace hasn't looked upon me for a long time.":
        "Thần Ân Tứ đã từ lâu lắm rồi không đoái hoài nhìn đến tôi.",
    "The box you're touching has Water of Grace in it, straight from the God of Grace.":
        "Chiếc hộp cậu đang chạm vào chứa Nước Ân Tứ bên trong, được ban phát trực tiếp từ Thần Ân Tứ.",
    "They wouldn't dare. Aside from the Wishing Box, everything in this Monolith is property of the God of Grace.":
        "Họ không dám đâu. Ngoại trừ Chiếc Hộp Ước Nguyện ra, mọi thứ trong Cự Tháp này đều là tài sản của Thần Ân Tứ.",
    "They know they need to eat. But their idealized God of Grace is their only hope.==W== This pointless competition of devotion has trapped them all, and nobody wants to be the first to quit.":
        "Họ biết mình cần phải ăn chứ. Nhưng hình tượng Thần Ân Tứ lý tưởng hóa lại là niềm hy vọng duy nhất của họ.==W== Cuộc tranh đua sùng kính vô nghĩa này đã bẫy tất cả bọn họ lại, và chẳng ai muốn là kẻ đầu tiên bỏ cuộc cả.",
    "This company, \"Creta Trading.\"":
        "Công ty này, \"Thương Hội Creta\".",
    "This forest ...==W== graveyard... Right, isn't there a Sanctuary of Grace nearby?":
        "Khu rừng này...==W== nghĩa địa... Phải rồi, gần đây chẳng phải có một Thánh Địa Ân Tứ sao?",
    "We aren't meant to fully comprehend the ultimate Grace.":
        "Chúng ta vốn dĩ đâu thể lĩnh hội được trọn vẹn Ân Tứ tối thượng.",
    "Well, companies are blessed by the God of Grace, after all.":
        "Chà, suy cho cùng thì các công ty đều nhận được sự bảo hộ từ Thần Ân Tứ mà.",
    "Wha...? What?!! The Water of Grace ... it didn't crystallize!!!":
        "Cái...? Cái gì cơ?!! Nước Ân Tứ... không hề kết tinh chút nào!!!",
    "Yeah. Everyone's Soul Stones are completely drained of Grace. Which means...==W== Loxy won't start!!":
        "Ừ. Hồn Thạch của mọi người đều đã cạn kiệt hoàn toàn Ân Tứ rồi. Đồng nghĩa với việc...==W== xe Loxy không nổ máy được!!",
    "I wish I had a phone with a big screen like yours, ==PLAYER_NAME==!":
        "Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của cậu, ==PLAYER_NAME== ơi!",
}
