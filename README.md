# StellaSoraKnowledge — tri thức cho chatbot lore

Folder này gom **mọi nội dung đã Việt hóa** của Stella Sora thành dữ liệu sạch cho chatbot
Discord chuyên lore. Nó tách riêng khỏi `StellaSoraVietHoaData` (repo dịch) để bạn đưa lên
GitHub/host riêng mà không kéo theo 600MB+ dữ liệu thô.

```
StellaSoraKnowledge/
├─ build_knowledge.py        # script dựng tri thức (chỉ cần Python, không cài gói)
├─ Cap_Nhat_Tri_Thuc.bat     # bấm đúp để cập nhật thủ công
├─ tools/extract_patched_vi.cjs  # (Node) trích text tiếng Việt từ gói arcx của dự án patch
├─ test_build_knowledge.py   # test nhanh cho script
└─ knowledge/                # ĐẦU RA — đây là thứ chatbot dùng, đừng sửa tay
   ├─ STATUS.md              # độ phủ: đã dịch bao nhiêu, chưa dịch gì
   ├─ manifest.json          # danh sách file nguồn + hash + đếm
   ├─ chunks.jsonl           # đoạn ~1500 ký tự, sẵn để embedding/RAG  ← dùng cái này
   ├─ blocks.jsonl           # từng khối thoại, đủ VI/EN/JP/CN + người nói
   ├─ glossary.md            # bảng thuật ngữ EN→VI (tên riêng, thuật ngữ, chữ UI)
   └─ docs/                  # markdown từng cảnh/bảng, đọc được bằng mắt
```

## Chatbot nên lấy file nào

| Mục đích | File |
|---|---|
| RAG / vector DB (khuyến nghị) | `knowledge/chunks.jsonl` — mỗi dòng một chunk, đã có tiền tố ngữ cảnh |
| Cần đối chiếu EN/JP/CN, tra theo người nói | `knowledge/blocks.jsonl` |
| Cho người đọc, hoặc nạp thẳng làm file kiến thức của một nền tảng bot | `knowledge/docs/**/*.md`, `glossary.md` |
| Cho bot biết phần nào chưa có dữ liệu | `knowledge/STATUS.md`, `manifest.json` |

Trường của một dòng `chunks.jsonl`: `id`, `doc_id`, `category` (`story`, `character`,
`game_text`, `subtitle`, `extra`, `glossary`), `group`, `file_id`, `title`, `block_start`,
`block_end`, `speakers`, `origin`, `chars`, `source`, `text`. Embedding trên `text`; giữ `id`/`doc_id`
để trích nguồn khi trả lời.

## Cái gì được nạp

Tất cả file `*_Merge.txt` **đã có bản VI** ở `01_CotTruyen` (cốt truyện, sự kiện, ngoại
truyện), `02_NhanVat`, `03_BangText_UI_KyNang` (vật phẩm, kỹ năng, giao diện),
`04_PhuDeVideo`, `90_CN_Moi_2.0.1`, cộng bảng thuật ngữ từ `glossary/glossary.csv`
(loại `term`, `character_name`, `ui_text`; bỏ các mục chỉ dùng cho xưng hô giới tính).

Ngoài ra nạp **bản Việt hóa đang chạy trong game** từ dự án patch AmeeVH
(`StellaSora_EN/StellaSora_VietHoa`), theo thứ tự ưu tiên:

1. `merge` — Merge đã review (nguồn trên). Cảnh/bảng trùng với nguồn dưới thì **luôn dùng Merge**.
2. `patch_game` — gói `dist/lua_patched_vi.arcx` + `dist/data_patched_vi.arcx`: toàn bộ văn bản tiếng
   Việt người chơi thấy trong game (cốt truyện chính STm, sự kiện STev/STsp, chương đặc biệt STm10001
   hồi 10–20, hẹn hò/nhân vật CG/PM/DP, bong bóng thoại BB, bảng vật phẩm, kỹ năng, thiên phú, hồ sơ
   nhân vật, thoại giọng nói, giao diện...). Script gọi Node (`tools/extract_patched_vi.cjs`, dùng module
   đọc arcx có sẵn của dự án patch) để giải mã; kết quả cache ở `.cache/` và chỉ chạy lại khi gói đổi.
   Tài liệu ở `docs/patch/story|character|game_text/...`. Các cột cùng một bản ghi trong bảng được
   gộp một dòng (vd. `Item.1: tên | mô tả`).
3. `patch_<phiên bản>` — bản tổng hợp `work/runs/localize_*/delivery/*/Van_ban_EN_VI.jsonl` cộng
   `work/hotfix_*/*.jsonl`, chỉ để bổ sung phần gói arcx chưa có. Dòng "Giữ EN" không được nạp.

Trường `origin` của mỗi khối/chunk cho biết nguồn. Cảnh trong gói còn nguyên tiếng Anh (dưới 20%
dòng thoại có dấu tiếng Việt) bị bỏ qua và liệt kê trong `STATUS.md`.

**Chú ý thuật ngữ:** hai bản dịch dùng từ khác nhau cho cùng một khái niệm. Merge (theo glossary):
Ma vương, Tuần du giả, Tháp sao. Bản trong game: Bạo Chúa, Lữ Khách, (Vạn) Cự Tháp. Bot nên coi các cặp này
là đồng nghĩa khi tra cứu và nhắc rõ nếu người hỏi dùng từ khác với đoạn đang trích.

- Merge chưa dịch (chưa có dòng VI) không được nạp, chỉ liệt kê trong `STATUS.md`.
- Thẻ định dạng (`<size>`, `<r=...>`, `==RT==`, `==W==`, `==A0.001==`...) đã được lọc;
  `==PLAYER_NAME==` thành `[tên người chơi]`.
- Tên người nói trong patch giữ EN nếu glossary chưa có bản VI (ví dụ "Leita the Saintess").
- Cần Node.js trong PATH để đọc gói arcx; thiếu Node thì script cảnh báo và chỉ nạp Merge + delivery.
- Gói arcx không có bản gốc EN đi kèm nên `text_en` trong `blocks.jsonl` của `patch_game` để trống.
- `STATUS.md` có bảng độ phủ từng nguồn. Bot phải biết nói "chưa có dữ liệu" thay vì bịa.

## Cập nhật khi có bản dịch/bản update mới

**Tự động:** `AGENTS.md` và các skill `translate`, `workflow`, `update-term` của project
Việt hóa đã được ghi chú để cuối mỗi lượt dịch/cập nhật thuật ngữ, agent chạy
`build_knowledge.py` (skill `update-knowledge`). Merge mới ở nhóm nào cũng được nạp,
kể cả nhân vật/vật phẩm/kỹ năng; bản tài nguyên mới `StellaSora_TaiNguyen_*_rNN` được
tự nhận (lấy bản có tên lớn nhất). Dự án patch cũng đã được ghi chú tương tự: delivery/hotfix
mới (2.1.x, 2.2...) tự được nạp khi chạy lại script. Nếu dự án patch nằm chỗ khác, dùng
`--patch-root <đường dẫn>` hoặc biến môi trường `SS_PATCH_ROOT` (`--patch-root none` để bỏ qua).

**Thủ công:**

```bash
python build_knowledge.py            # dựng/cập nhật
python build_knowledge.py --check    # chỉ kiểm tra tri thức có cũ không (exit 1 nếu cũ)
python build_knowledge.py --source D:\duong\dan\StellaSoraVietHoaData
```

Mỗi lần chạy dựng lại toàn bộ trong vài giây và chỉ ghi khi có thay đổi thật, nên diff
Git gọn. Sau khi chạy lại, nạp lại `chunks.jsonl` vào vector DB (so `content_sha256`
trong `manifest.json` để biết có đổi không).

## Đưa lên GitHub / host bot

- Chỉ cần folder này (hoặc chỉ `knowledge/`). Không push `StellaSoraVietHoaData`.
- Để repo **private**: text game thuộc Yostar; bản dịch thuộc người dịch.
- Có thể `git init` ngay trong folder này; chưa có commit/push nào được thực hiện.

## Gợi ý system prompt cho bot

> Bạn là trợ lý lore Stella Sora. Chỉ trả lời dựa trên các đoạn tri thức được cung cấp;
> nếu không có đoạn liên quan, nói rõ "mình chưa có dữ liệu Việt hóa phần này" thay vì
> đoán. Dùng đúng tên/thuật ngữ trong bảng thuật ngữ. Cảnh báo spoiler trước khi kể
> nội dung cốt truyện. Khi trả lời, nêu nguồn (chương/cảnh, vd. STm01_02). Nếu EN/JP/CN
> khác nhau và có cả hai trong dữ liệu, nói rõ khác biệt thay vì trộn. Coi Ma vương = Bạo Chúa,
> Tuần du giả = Lữ Khách, Tháp sao = (Vạn) Cự Tháp là cùng một khái niệm (hai bản dịch dùng từ khác nhau).
