# -*- coding: utf-8 -*-
"""
Flawless localization for AvgUIText.lua (Pronouns/Gender/UI), STm02_09.lua, and recurring titles.
Resolves all 3 reported translation defects and eliminates machine translation across Act 2.
"""

from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto
from arcx_adapter import xxtea_decrypt, xxtea_encrypt, XXTEA_KEY

AVGUITEXT_TRANSLATIONS = {
    # UI elements
    "Cancel": "Hủy",
    "Confirm": "Xác nhận",
    "Option %d": "Lựa chọn %d",
    "Leads to Bad Ending": "Dẫn đến Kết cục Xấu (Bad Ending)",
    "Selected": "Đã chọn",
    "This branch corresponds to...": "Nhánh này tương ứng với...",
    "A new choice has appeared.": "Một lựa chọn mới đã xuất hiện.",
    "The Final Path": "Con đường Cuối cùng",
    "If we had more information...": "Nếu chúng ta có thêm thông tin...",
    "The Unknown Path": "Con đường Chưa biết",
    "%s has selected": "%s đã chọn",
    "%s thinks...": "%s đang suy nghĩ...",
    "Records": "Lịch sử",
    "Last Selection": "Lựa chọn trước",
    "Hide": "Ẩn",
    "Skip": "Bỏ qua",
    "Skipping an ending will return you to the previous choice. Continue?": "Bỏ qua kết thúc sẽ quay lại lựa chọn trước đó. Tiếp tục?",
    "Do you want to skip the story?": "Bạn có muốn bỏ qua đoạn cốt truyện này không?",
    
    # Pronoun & Gender tags (Resolves "của lady", "của lord", etc.)
    "sisters": "chị em",
    "brothers": "anh em",
    "lady": "tiểu thư",
    "lord": "thiếu gia",
    "Lady": "Tiểu thư",
    "Lord": "Thiếu gia",
    "gentleman": "quý ngài",
    "white hair": "tóc trắng",
    "black hair": "tóc đen",
    "woman": "nữ",
    "man": "nam",
    "witch": "phù thủy",
    "wizard": "pháp sư",
    "Miss": "Cô",
    "Mister": "Cậu",
    "skirt": "váy",
    "pant": "quần",
    "maid": "hầu gái",
    "butler": "quản gia",
    "She": "Cô ấy",
    "He": "Cậu ấy",
    "shirt": "áo sơ mi",
    "undershirt": "áo ba lỗ",
    "Her": "Của cô ấy",
    "His": "Của cậu ấy",
    "her": "cô ấy",
    "his": "cậu ấy",
    "him": "cậu ấy",
    "hers": "của cô ấy",
    "Ms.": "Cô",
    "Mr.": "Anh",
    "herself": "bản thân cô ấy",
    "himself": "bản thân cậu ấy",
    "girl": "cô gái",
    "boy": "chàng trai",
    "she": "cô ấy",
    "he": "cậu ấy"
}

STM02_09_PERFECT_DICT = {
    "Act Nine": "Hồi 9",
    "A One Hour War": "Cuộc Chiến Một Giờ",
    'You are the CEO of the Boss Accord Staffing Co. The moment your company is activated, news of it flashes across the world. You immediately declare a "company war" on Creta Trading.':
        'Ngài là Giám đốc điều hành của Công ty Phái cử Boss Accord. Ngay khi Công ty được tái kích hoạt, tin tức lập tức chấn động toàn thế giới. Ngài lập tức tuyên chiến "Chiến tranh Công ty" với Thương đoàn Creta.',
    "Pluvia Month": "Tháng Pluvia",
    "Scarlet Sights Street": "Phố Cảnh Đỏ Rực",
    "Blonde Bassist": "Tay Bass Tóc Vàng",
    "Waaah!": "Oái!",
    "Hurried Witch": "Phù Thủy Vội Vã",
    "Sorry! Didn't mean to spook you.": "Xin lỗi nhé! Tôi không cố ý làm bạn giật mình đâu.",
    "I'd love to properly apologize,==W== but something huge just went down in Emor. I gotta fly over there now. ":
        "Tôi rất muốn xin lỗi bạn cho đàng hoàng,==W== cơ mà ở Emor vừa xảy ra chuyện long trời lở đất rồi! Tôi phải bay qua đó gấp đây.",
    "So we're cool, right? ★": "Vậy coi như chúng mình huề nha? ★",
    "I owe ya one! I'll definitely catch your next show, promise.":
        "Tôi nợ bạn một lần đó! Lần tới nhất định tôi sẽ đến xem buổi biểu diễn của bạn, hứa danh dự luôn!",
    "Competent Association Trekker": "Lữ Khách Hiệp Hội Tháo Vát",
    "Look! There's some huge company news!": "Nhìn kìa! Có tin chấn động liên quan đến giới Công ty đấy!",
    "Dashing Association Captain": "Đội Trưởng Hiệp Hội Phong Độ",
    "News? Just focus on work, Willow. Companies aren't what they used to be. No headline is going to get us a sponsor now.":
        "Tin tức gì chứ? Tập trung làm việc đi, Willow. Giới Công ty thời nay chẳng còn như xưa nữa đâu. Chẳng có dòng tít giật gân nào đem về nhà tài trợ cho chúng ta lúc này đâu.",
    "Sluggish Xuan Shi": "Huyền Sĩ Uể Oải",
    "What brings you here?": "Ủa, gió nào đưa cô tới đây thế?",
    "Diligent Secretary": "Thư Ký Mẫn Cán",
    # IMAGE 1 FIX: Short, natural, eliminate clipping/overflow ("mức độ...")
    "I should be asking you that. This is my office, not your personal crash pad!==W== Still, your timing's perfect. Urgent company intel. Get this to your master, top priority.":
        "Câu đó tôi phải hỏi anh mới đúng chứ! Đây là bàn làm việc của tôi, đâu phải chỗ để anh lăn ra ngủ!==W== Cơ mà anh tới vừa khéo lắm. Có tin mật khẩn cấp về Công ty đây. Đưa ngay cho chủ nhân của anh đi, hỏa tốc đấy!",
    "Ugh, I was having such a great nap. Fine, on my way.":
        "Ugh, đang chợp mắt ngon lành... Thôi được rồi, tôi đi ngay đây.",
    "Proactive Employee": "Nhân Viên Năng Nổ",
    "An old company just came off ice. Weird name... Boss Accord Staffing Co.?":
        "Một Công ty cổ xưa vừa mới rã đông kìa. Tên lạ hoắc... Công ty Phái cử Boss Accord?",
    "Scheming Manager": "Quản Lý Mưu Mô",
    'Heehee, how delightful! It seems we have a new "piggy bank." Hehehe...<size=60>♪</size>':
        'Hi hi, thú vị thật đấy! Xem ra chúng ta sắp có thêm một "con heo đất" mới rồi. Hê hê hê...<size=60>♪</size>',
    "Get me everything on this company. Freshly reactivated... They'll definitely need our financial support.":
        "Mau tìm cho tôi toàn bộ hồ sơ về Công ty này. Vừa mới tái kích hoạt... nhất định bọn họ sẽ rất cần nguồn lực tài chính từ phía chúng ta.",
    "Yes, ma'am.": "Rõ, thưa bà.",
    "Gentle Maid": "Hầu Gái Dịu Dàng",
    "Understood, Lord Tanikaze.": "Thuộc hạ đã rõ, thưa ngài Tanikaze.",
    "We're ready to supply housekeeping staff to the newly reactivated company.":
        "Chúng tôi đã sẵn sàng cung ứng nhân sự gia vụ cho Công ty vừa mới tái kích hoạt.",
    "Haughty Executive": "Quan Chức Kiêu Kỳ",
    "A company just reactivated is declaring war on Creta Trading?==W== Interesting...":
        "Một Công ty vừa tái kích hoạt đã dám ngang nhiên tuyên chiến với Thương đoàn Creta sao?==W== Thú vị đấy...",
    "Composed Assistant": "Trợ Lý Điềm Tĩnh",
    "This marks the first company war in a century. Shall we dispatch observers?":
        "Đây là cuộc Chiến tranh Công ty đầu tiên sau cả một thế kỷ qua. Chúng ta có nên cử quan sát viên tới không ạ?",
    "There's no time, nor can we afford such distractions. Our own research is at a critical juncture.":
        "Không có thời gian đâu, và chúng ta cũng chẳng rảnh để phân tâm vào mấy chuyện bao đồng đó. Đề tài nghiên cứu của chúng ta đang bước vào giai đoạn then chốt.",
    "Once our plan succeeds, United Harvest will be untouchable.":
        "Một khi kế hoạch thành công, Tập đoàn Đại Phong Thu sẽ là bất khả xâm phạm.",
    "Shadow of the West": "Bóng Đêm Phương Tây",
    "Ahahaha, fantastic! Newly reactivated and already starting a war... Guess the legends weren't wrong.":
        "A ha ha ha, tuyệt vời làm sao! Vừa mới tái xuất đã châm ngòi chiến tranh ngay... Xem ra những lời đồn truyền thuyết quả không sai chút nào.",
    "Voice from the North": "Tiếng Nói Phương Bắc",
    "Please, God of Grace, don't let the world descend into chaos. Please, keep the people safe...":
        "Cầu xin Thần Ban Ân, xin đừng để thế gian này rơi vào cảnh hỗn loạn lầm than. Cầu xin Người che chở cho muôn dân...",
    "Blade of the East": "Lưỡi Kiếm Phương Đông",
    "What good are prayers? Let's use our heads. Isn't the Tetrad Aspects here precisely to handle situations like this?":
        "Cầu nguyện thì tích sự gì? Động não chút đi. Chẳng phải Tứ Diện Vị diện chúng ta lập ra chính là để giải quyết những chuyện thế này sao?",
    "The South should have some input... Tch. Absent again. How irresponsible. Utterly irresponsible.":
        "Phương Nam cũng nên lên tiếng chứ... Chậc. Lại vắng mặt à? Thật là vô trách nhiệm. Vô trách nhiệm hết chỗ nói.",
    "My apologies. Lady Angie had urgent matters to attend to. You were all notified in advance.":
        "Vô cùng thứ lỗi. Tiểu thư Angie có việc đột xuất cần đích thân xử lý. Chuyện này đã thông báo trước với chư vị rồi mà.",
    "I know. Never mind that. Albedo. Was it your new intern who handled the reactivation?":
        "Tôi biết rồi. Bỏ chuyện đó qua một bên đi. Albedo, có phải chính thực tập sinh mới của cô là người thực hiện việc tái kích hoạt không?",
    "You're not ... pulling something again, are you?":
        "Cô... lại đang giở trò mờ ám gì nữa đúng không?",
    "It is all according to the God of Grace's will. That is all I'm permitted to say.":
        "Tất cả đều tuân theo ý chỉ của Thần Ban Ân. Đó là tất cả những gì tôi được phép tiết lộ.",
    "Rest assured, everyone. I will see to the Boss Accord personally.":
        "Mọi người cứ yên tâm. Tôi sẽ đích thân giám sát bên Hội Boss Accord.",
    "Standard Bearer": "Kỵ Sĩ Mang Cờ",
    # IMAGE 2 FIX: Precise grammar ("target" = con mồi / đối tượng bị săn lùng)
    "Wait, what? The Creta Trading's target reactivated a whole company?":
        "Khoan đã, cái gì cơ? Con mồi mà Thương đoàn Creta đang truy bắt vừa tái kích hoạt cả một Công ty ư?!",
    "Young Squire": "Hầu Tận Trẻ Tuổi",
    "Yes, sir. And that company has declared a war against Creta Trading...":
        "Vâng thưa ngài. Và Công ty đó vừa chính thức tuyên chiến với Thương đoàn Creta...",
    "What are we standing around for? Pull our units back now!":
        "Còn đứng đực mặt ra đó làm gì nữa? Lập tức thu quân về ngay!",
    "The Imperial Guard does not get involved in company wars.":
        "Cận Vệ Hoàng Gia tuyệt đối không được phép can dự vào các cuộc Chiến tranh Công ty.",
    "Ash District in Emor": "Khu Phố Tro Tàn ở Emor",
    "Alright, savages! You're surrounded. Give it up!":
        "Được rồi, lũ mọi rợ kia! Tụi mày đã bị bao vây. Khôn hồn thì buông vũ khí hàng đi!",
    "I had to hock the HQ hall and my Seal of Grace just to corner you rats!":
        "Bà đây đã phải đem thế chấp cả sảnh trụ sở lẫn Ấn Tín Ban Ân chỉ để dồn lũ chuột cống tụi mày vào đường cùng đấy!",
    "Every one of you is gonna work for me for free for the next fifty years!":
        "Từng đứa tụi mày sẽ phải còng lưng làm không công cho bà suốt năm mươi năm tới!",
    "Uh oh... This is really not good.": "Nguy rồi... Tình hình này gay go thật đấy.",
    "They're all over the roofs.": "Bọn chúng mai phục kín cả trên mái nhà rồi.",
    "Wonder if ==PLAYER_NAME== managed to pull it off on their end.":
        "Không biết phía ==PLAYER_NAME== đã xoay xở xong xuôi chưa nữa.",
    "Even if ==PLAYER_NAME== couldn't handle it, cap sure can.":
        "Kể cả ==PLAYER_NAME== không lo nổi thì đội trưởng chắc chắn sẽ giải quyết êm xuôi thôi.",
    "So, now what? We've bought enough time. Should we just surrender for now?":
        "Vậy giờ tính sao đây? Chúng ta đã câu đủ thời gian rồi. Có nên tạm thời giả vờ đầu hàng trước không?",
    # IMAGE 3 FIX: Noble samurai tone, using ==SEX11== which is now translated to "tiểu thư"/"thiếu gia"
    "No.==W== As my ==SEX11=='s blade, I fight until I break or receive orders.":
        "Không.==W== Là thanh bảo kiếm của ==SEX11==, tôi sẽ chiến đấu cho đến khi gãy nát hoặc khi nhận được quân lệnh.",
    "Knight Captain": "Kỵ Sĩ Đoàn Trưởng",
    "All units, advance.": "Toàn quân, tiến lên.",
    "W-Wait, captain! Actually...": "Khoan... Khoan đã Đoàn trưởng! Thật ra thì...",
    "(mumbling)": "(thì thầm)",
    "Hmm...": "Hừm...",
    "We're pulling out!": "Rút quân!",
    "Hey! Where do you think you're going?! Our deal was to catch them!":
        "Này! Các người định đi đâu thế hả?! Thỏa thuận của chúng ta là bắt sống tụi nó cơ mà!",
    "This is a serious breach of contract! I'll sue you for it!":
        "Đây là hành vi vi phạm hợp đồng nghiêm trọng! Bà đây sẽ kiện các người ra tòa!",
    "Apologies, Chief Feagin. A company has declared war against yours.":
        "Vô cùng thứ lỗi, Hội trưởng Feagin. Một Công ty khác vừa chính thức tuyên chiến với công ty của bà.",
    "The Imperial Guard swore off company wars a century ago. We ask for your understanding.":
        "Cận Vệ Hoàng Gia đã tuyên thệ không can dự vào các cuộc Chiến tranh Công ty từ một thế kỷ trước. Rất mong bà thông cảm cho chúng tôi.",
    "We sincerely regret breaking our deal. The Imperial Guard Security Solutions Company will compensate you for any penalties incurred.":
        "Chúng tôi thành thật lấy làm tiếc vì phải hủy bỏ thỏa thuận. Công ty Giải pháp An ninh Cận Vệ Hoàng Gia sẽ bồi thường toàn bộ tiền phạt vi phạm cho bà.",
    "Dammit! Who is pulling this crap now?":
        "Khốn kiếp! Đứa nào dám chọc gậy bánh xe vào lúc này hả?!",
    "That would be us. The Boss Accord Staffing Co.":
        "Là chúng tôi đây. Công ty Phái cử Boss Accord.",
    "Ha...? What kind of sick joke is this? There's no way you savages could own a Seal of Grace...":
        "Hả...? Trò đùa quái đản gì thế này? Lũ mọi rợ tụi mày làm sao có cửa sở hữu được Ấn Tín Ban Ân chứ...",
    "Confused Gangster": "Tên Côn Đồ Ngơ Ngác",
    'What\'s a "company war"?': "'Chiến tranh Công ty' là cái giống gì thế đại ca?",
    "Timid Gangster": "Tên Côn Đồ Nhát Gan",
    "Dunno, but the Guard's leaving. Maybe we should bail too?":
        "Ai mà biết, cơ mà bên Hiệp sĩ rút quân rồi kìa. Hay tụi mình cũng chuồn lẹ đi đại ca?",
    "Cheapskate Mercenary": "Lính Đánh Thuê Hám Tiền",
    "No way! Those Trekkers are spent! With the knights gone, that bounty's all ours, yeah?":
        "Chuồn cái đầu mày! Đám Lữ Khách kia kiệt sức cả rồi! Lũ hiệp sĩ rút đi thì tiền thưởng thuộc hết về bọn mình còn gì, đúng không?!",
    "Knowledgeable Mercenary": "Lính Đánh Thuê Thạo Đời",
    "Don't be stupid. A company war is a fight to the death between two companies. It only ends when one side surrenders and meets all the other's demands.":
        "Bớt ngu lại đi. Chiến tranh Công ty là trận chiến sinh tử một mất một còn giữa hai Công ty. Nó chỉ kết thúc khi một bên chịu đầu hàng vô điều kiện và đáp ứng mọi yêu sách của đối phương.",
    "Anyone involved in a company war loses all legal protection.":
        "Bất cứ ai dính líu vào Chiến tranh Công ty đều bị tước bỏ mọi quyền bảo hộ pháp lý đấy.",
    "Wait ... you mean ... we could actually get killed?":
        "Khoan... Ý anh là... tụi mình có thể bị giết thật á?!",
    "That's right. And for the record, nobody gets punished for killing someone in a fight like this. Anything goes.":
        "Chuẩn rồi đấy. Nói cho mà biết, giết người trong trận chiến kiểu này chẳng ai bị khép tội đâu. Thích làm gì thì làm.",
    "Yikes! Then what are we waiting for?! Let's bounce!":
        "Ái chà! Vậy còn đứng chờ chết ở đây làm gì nữa?! Chuồn thôi bà con ơi!",
    "Don't go! I'll pay you triple! No, five times the rate!":
        "Đứng lại! Đừng có đi! Bà sẽ trả gấp ba! Không, gấp năm lần thù lao luôn!",
    "What good's money if you're dead?!":
        "Chết rồi thì ôm tiền xuống mồ mà xài à?!",
    "They're all gone.": "Bọn chúng chạy sạch cả rồi.",
    "I thought Creta Trading would have at least some loyal employees.":
        "Tôi cứ ngỡ Thương đoàn Creta chí ít cũng phải có vài nhân viên trung thành chứ.",
    "This is what happens when you only hire sellswords.":
        "Cái giá của việc chỉ biết dùng tiền thuê lính đánh thuê đấy.",
    "I may be a blade, but to strike down a defenseless foe is beneath me.":
        "Dù tôi là một lưỡi kiếm, nhưng việc hạ sát kẻ không còn khả năng tự vệ chẳng xứng với đạo của tôi.",
    "D-Damn you. How dare you all just stand there and gloat...!":
        "L-Lũ khốn tụi mày... Dám đứng đó mà châm chọc bà đây à...!",
    "Surrender, Feagin. Disband your corrupt Creta Trading, explain what happened at the orphanage, and apologize to everyone you've deceived.":
        "Đầu hàng đi, Feagin. Giải tán cái Thương đoàn Creta thối nát của bà, khai rõ những gì đã diễn ra ở trại trẻ mồ côi, và công khai tạ lỗi với tất cả những người từng bị bà lừa gạt.",
    "Those are our terms.": "Đó là điều kiện tối hậu của chúng tôi.",
    "Apologize? Are you kidding me? Who'd agree to that?!==W== The Creta Trading, the orphanage ... fine, whatever. But an apology? That's never gonna happen.":
        "Xin lỗi á? Tụi mày đang đùa đấy à? Ai đời lại đi đồng ý cái thứ nhảm nhí đó chứ?!==W== Chuyện Thương đoàn Creta, chuyện trại trẻ mồ côi... được thôi, sao cũng được. Nhưng bảo bà đây phải cúi đầu xin lỗi ư? Đời nào có chuyện đó đâu!",
    "... It's their own fault==W== for being so stupid!==W== When I was the one getting scammed, those jerks just laughed in my face. Nobody ever said sorry to me.":
        "... Tất cả là do bọn chúng tự chuốc lấy==W== vì quá ngu ngốc mà thôi!==W== Hồi bà đây bị lừa gạt, lũ khốn đó chỉ biết cười cợt vào mặt tao. Có đứa nào từng mở mồm nói lời xin lỗi với tao chưa?!",
    "I don't know what you've been through, but that's no excuse to hurt other people.":
        "Tôi không rõ bà từng nếm trải những gì, nhưng đó không phải là cái cớ để bà làm tổn thương người khác.",
    "Then what do you want from me?! It's not fair! Why am I always the one getting screwed over?!":
        "Vậy tụi mày còn muốn bà phải làm sao nữa hả?! Thật bất công! Tại sao lúc nào người chịu thiệt cũng là tao chứ?!",
    "Some, having been wronged before, choose to protect others from suffering the same fate instead.":
        "Có những người sau khi nếm trải đau thương, họ chọn cách bảo bọc người khác để không ai phải chịu chung số phận ấy nữa.",
    "You're just looking for excuses to make yourself feel better about the terrible things you've done.":
        "Bà chỉ đang cố tìm cớ để lấp liếm lương tâm trước những tội ác tày trời mà mình đã gây ra thôi.",
    "That magic again! Watch out!": "Lại là loại ma thuật đó! Cẩn thận!",
    "White-Haired Girl": "Cô Gái Tóc Trắng",
    "Well, well. I didn't expect we'd be running into each other again so soon, my dear new executive.":
        "Chà chà. Không ngờ chúng ta lại tương phùng sớm đến thế này đấy, ngài Tân Giám đốc thân mến.",
    "Or perhaps I should call you Boss now?":
        "Hay là giờ tôi nên gọi ngài là Sếp Boss đây nhỉ?",
    "I don't know why you're helping her,==W== but are you going to keep enabling this?":
        "Tôi không hiểu tại sao cô lại giúp bà ta,==W== nhưng cô định tiếp tay cho việc này đến bao giờ nữa?",
    "What can I say? I owe a debt.": "Biết sao được chứ? Tôi mắc nợ người ta mà.",
    "Let's head to the Monolith, Chief Feagin.": "Chúng ta hãy tới Cự Thạch thôi, Hội trưởng Feagin.",
    "I'll show you the value of your investment in me.":
        "Tôi sẽ cho bà thấy khoản đầu tư vào tôi đáng giá đến mức nào.",
    "Emor Monolith #7": "Cự Thạch Emor Số 7",
    "45th Floor": "Tầng 45",
    "Master... This is that new tech you mentioned?":
        "Đại sư... Đây chính là công nghệ mới mà ngài từng nhắc tới sao?",
    "Yup, take a look.": "Phải rồi, nhìn xem này.",
    "I've connected one hundred wishing boxes with magic. We can call forth an Artifact of any size.":
        "Ta đã dùng ma thuật liên kết một trăm Hộp Nguyện Ước lại với nhau. Giờ chúng ta có thể hiệu triệu Thần Khí với bất kỳ kích thước nào.",
    "Put simply, any part that exceeds a single box's limit is broken down into a hundred components. We just draw them out and reassemble them.":
        "Nói một cách đơn giản, bất cứ phần nào vượt quá giới hạn chứa của một chiếc hộp sẽ được phân tách thành một trăm cấu kiện. Chúng ta chỉ việc triệu hồi rồi lắp ráp chúng lại.",
    "This is astonishing!": "Thật là kinh ngạc quá đỗi!",
    "I had a promise to keep. When I first came to Emor, you were the only one who believed in my magic enough to invest in it.":
        "Ta phải giữ đúng lời hứa chứ. Khi ta mới chân ướt chân ráo tới Emor, chỉ có mỗi bà là đủ tin tưởng vào ma thuật của ta để rót vốn đầu tư.",
    "Hah! I always trust my eye for talent!":
        "Hahaha! Con mắt nhìn người của bà đây chưa bao giờ sai lầm mà!",
    "Master, conjure an Artifact for me! Something powerful enough to win this war!":
        "Đại sư, mau hiệu triệu cho tôi một Thần Khí đi! Một thứ đủ sức mạnh hủy diệt để đè bẹp cuộc chiến này!",
    "You're now the Deputy Executive... No, you're the Co-Executive of Creta Trading!":
        "Ngài giờ sẽ là Phó Giám đốc... Không, ngài là Đồng Giám đốc của Thương đoàn Creta luôn!",
    "I'm afraid ... that is not possible.":
        "E rằng... điều đó là không thể rồi.",
    "You see, this particular magic alters the fundamental rules of wishing.":
        "Bà thấy đấy, loại ma thuật đặc thù này đã làm thay đổi quy tắc căn bản của sự nguyện ước.",
    "To put it bluntly, these boxes don't require human memories. They run on ... boiling, seething hatred.":
        "Nói toạc móng heo ra, những chiếc hộp này chẳng cần tới ký ức con người đâu. Chúng vận hành dựa trên... lòng thù hận sôi sục và cuồng nộ.",
    "The greater the hatred channeled, the larger the Artifact that can be manifested. But I have no one to hate.":
        "Lòng thù hận truyền vào càng lớn thì Thần Khí ngưng tụ được sẽ càng khổng lồ. Nhưng ta thì lại chẳng có ai để mà căm ghét cả.",
    "Heheh...==W== Ahahaha! Hatred? I have plenty of that.":
        "Hê hê...==W== A ha ha ha! Thù hận á? Thứ đó thì bà đây có thừa!",
    "The hatred I feel for those Trekkers, for all of Emor is practically boiling over!":
        "Mối thù mà tao dành cho lũ Lữ Khách kia, dành cho cả cái đất Emor này đang sôi sùng sục trong huyết quản đây này!",
    "God of Grace, hear my hatred!":
        "Hỡi Thần Ban Ân, hãy lắng nghe mối thù hận của ta!",
    "Grant me an ==W==<size=55>Artifact to crush those savages</size>!":
        "Hãy ban cho ta một ==W==<size=55>Thần Khí để nghiền nát lũ mọi rợ đó</size>!"
}

ADDITIONAL_RECURRING_FIXES = {
    # Fix Lady titles
    "Collate the quarterlies. Adjust Lady Firenze's schedule… So much to do, but if I skip lunch, I can definitely make the deadline...":
        "Đối chiếu các quý. Điều chỉnh lịch trình của Tiểu thư Firenze... Nhiều việc quá, nhưng nếu nhịn bữa trưa thì chắc chắn mình sẽ kịp hạn chót thôi...",
    'It says as long as I follow Lady Gray\'s orders to the letter and search for "that thing"...':
        'Nó nói rằng miễn là tôi tuân thủ mệnh lệnh của Tiểu thư Gray từng li từng tí và tìm kiếm "thứ đó"...',
    "Phew...==W== After all that, Lady Firenze's schedule has to be clear now!":
        "Phù...==W== Sau ngần ấy chuyện, lịch trình của Tiểu thư Firenze chắc chắn đã thảnh thơi rồi!",
    "We ...==W== don't think so.==W== She's not on Lady Angie's list, but her magic looks a lot like Nocturn Eterna's.==W== We weren't sure what to make of it, so we thought we'd report back first.":
        "Tụi em...==W== không nghĩ vậy.==W== Cô ấy không có tên trong danh sách của Tiểu thư Angie, nhưng ma thuật của cô ấy trông rất giống Dạ Vĩnh Hằng.==W== Tụi em không chắc nên tính về báo cáo trước đã.",
    "We wanted to repay Lady Firenze for her kindness, but she's never free, so we thought that we should shoulder some of the load.":
        "Chúng tôi muốn báo đáp ân tình của Tiểu thư Firenze, nhưng ngài ấy chẳng bao giờ rảnh rỗi cả, nên chúng tôi nghĩ mình nên gánh vác bớt phần nào nhọc nhằn.",
    "Lady Firenze": "Tiểu thư Firenze",
    "Lady Angie": "Tiểu thư Angie",
    "Lady Gray": "Tiểu thư Gray",
    "Lord Tanikaze": "Ngài Tanikaze",
}

def patch_avguitext_entry(bin_path: Path):
    enc = bin_path.read_bytes()
    dec = xxtea_decrypt(enc, XXTEA_KEY)
    chunk = Lua53Chunk(dec)
    hdr = chunk.read_bytes(33)
    size_up = chunk.read_byte()
    proto = chunk.parse_proto()
    
    stats = {'patched': 0}
    
    def patch_p(p):
        new_constants = []
        for ktype, val in p['constants']:
            if ktype in (4, 20):
                try:
                    s = val[1].decode('utf-8')
                    s_strip = s.strip()
                    if s_strip in AVGUITEXT_TRANSLATIONS:
                        new_text = AVGUITEXT_TRANSLATIONS[s_strip]
                        l_pad = len(s) - len(s.lstrip())
                        r_pad = len(s) - len(s.rstrip())
                        full_new = (" " * l_pad) + new_text + (" " * r_pad)
                        new_s_bytes = full_new.encode('utf-8')
                        new_len = len(new_s_bytes) + 1
                        new_tag = 0xFF if new_len >= 0xFF else new_len
                        new_constants.append((ktype, (new_tag, new_s_bytes)))
                        stats['patched'] += 1
                        continue
                except:
                    pass
            new_constants.append((ktype, val))
        p['constants'] = new_constants
        for child in p['protos']:
            patch_p(child)
            
    patch_p(proto)
    rebuilt = hdr + bytes([size_up]) + serialize_proto(proto)
    re_enc = xxtea_encrypt(rebuilt, XXTEA_KEY)
    bin_path.write_bytes(re_enc)
    print(f"SUCCESS: Patched {stats['patched']} AvgUIText strings (including ==SEX== tags) in {bin_path.name}")
    return stats['patched']
