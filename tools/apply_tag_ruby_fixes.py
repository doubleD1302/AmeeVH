import json

with open('StellaSora_VietHoa/work/batches/batch_10k_b3_partB_translated.json', encoding='utf-8') as f:
    dst = json.load(f)

fixes = {
    'STm07_07.77': 'Đã rõ. Vì ==SEX11== của tôi yêu thích cả hai bộ <r=trang phục>vỏ kiếm</r>, kể từ ngày mai tôi sẽ mặc luân phiên hai bộ này.',
    'STm07_07.79': 'Hơn nữa, ==W== tôi có thể nhắm mắt lại ==W== và hình dung ra người trong từng bộ <r=trang phục>vỏ kiếm</r>.',
    'STm07_07.80': '==SEX11== của tôi... ==W== Tấm lòng thưởng thức sâu sắc của người dành cho các bộ <r=trang phục>vỏ kiếm</r> của tôi khiến tôi vô cùng cảm động.',
    'STm07_07.83': 'Tùy ý người cả thôi. ==W== Bộ <r=trang phục>vỏ kiếm</r> mà người thích nhất cũng chính là sở thích của tôi.',
    'STm07_07.84': 'Đã rõ, ==SEX11== của tôi. ==W== Hiện tại tôi sẽ tiếp tục gắn bó với bộ <r=trang phục>vỏ kiếm</r> này.',
    'STm07_07.87': 'Nếu người muốn tôi mặc lại bộ <r=trang phục>vỏ kiếm</r> màu đen, tôi sẽ thay đổi ngay lập tức.',
    'STm07_07.88': 'Không, không phải vậy đâu. ==W== Chỉ hai bộ thôi là không đủ. ==W== Cô phải cần thêm thật nhiều bộ <r=trang phục>vỏ kiếm</r> nữa cơ! ==W==',
    'STm07_13.45': '(Khoan đã. Đám <r=ninja>hầu gái</r> của chúng ta dùng hoa để chế tạo đạo cụ thì đúng rồi, nhưng tại sao Otoha lại đột kích nhà kính của họ làm gì chứ?)',
    'STm07_15.104': 'Hơn nữa... Mọi người bên cạnh người đều đã lập <color=#3faeae>khế ước linh hồn</color> với người rồi. Chỉ có mỗi mình tôi là bị bỏ lại. Cảm giác thật là... bất công.',
    'STm07_15.105': 'Một <color=#3faeae>khế ước linh hồn</color> ư... Trông có vẻ đủ an toàn. Xét về lâu dài, lợi ích mang lại chắc chắn vượt trội hơn nhiều so với rủi ro.',
    'STm08_02.111': '<size=47>Đây không phải là một <color=#3faeae>hình phạt</color>. Đây là một bài <color=#3faeae>kiểm tra</color>.</size>',
    'STm07_06_ba.140': 'Tôi sẽ quay lại... ==W== Lần này, tôi phải quay trở về <color=#bd3059>quá khứ xa xăm hơn nữa.</color>',
    'STm07_06_bc.143': 'Tôi sẽ quay lại... ==W== Lần này, tôi phải quay trở về <color=#bd3059>quá khứ xa xăm hơn nữa.</color>',
    'STm07_14.110': '<size=50>Ngươi bảo ai là tay sai của Khiên Thanh Không hả? Bọn ta không bao giờ làm việc cho lũ khốn đó!</size>',
    'STm07_15.53': '<size=70>Lặp lại lịch sử.</size>',
    'STm07_15.54': '<size=38>==RT====RT====RT==<align="right">Bên cạnh là một dòng ghi chú nhỏ: Nguy hiểm. Hãy cẩn thận.==RT==Mà nếu cậu không nhận việc ở đây thì tôi lại mất lý do để trốn việc mất.</align></size>',
    'STm07_15.130': '<color=#bd3059>Nơi này sẽ bị tước đoạt danh xưng.==RT==Chỉ còn lại cằn cỗi và hoang tàn...</color>'
}

for k, v in fixes.items():
    dst[k] = v

with open('StellaSora_VietHoa/work/batches/batch_10k_b3_partB_translated.json', 'w', encoding='utf-8') as f:
    json.dump(dst, f, ensure_ascii=False, indent=2)

# Also update approved batch
with open('StellaSora_VietHoa/work/batches/batch_10k_b3_approved.json', encoding='utf-8') as f:
    appr = json.load(f)
for k, v in fixes.items():
    appr[k] = v
with open('StellaSora_VietHoa/work/batches/batch_10k_b3_approved.json', 'w', encoding='utf-8') as f:
    json.dump(appr, f, ensure_ascii=False, indent=2)

print('Updated 17 targeted lines in both batch_10k_b3_partB_translated.json and batch_10k_b3_approved.json!')
