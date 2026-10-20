# Việt hóa chữ trong texture `.en.unity3d`

Lộ trình hiện tại xử lý tài nguyên offline cho bản PC. Bắt đầu từ ảnh trích thật; hậu tố `.en` không chứng minh mọi object trong bundle đều là chữ cần dịch. Không đổi tên bundle/texture/sprite để dịch tên kỹ thuật.

## Kết quả đợt đầu — 20/10/2026

- Nguồn đọc trực tiếp: client/game **2.0.0**, resource **2610201624**. Báo cáo version cũ không áp dụng cho snapshot này.
- Kiểm kê 433 bản file ở hai nhóm nguồn, tương ứng 219 tên bundle duy nhất. Catalog chọn một nguồn tường minh cho mỗi tên, ưu tiên Persistent_Store để làm candidate; điều này chưa chứng minh ưu tiên loader trong game.
- Catalog metadata: 1.276 Texture2D và 1.322 Sprite. Nhiều mục là nền/hiệu ứng, cần xem ảnh trước khi phân loại chữ.
- Pilot hoàn tất 5 ảnh loading comic trong `icon-0.en.unity3d`: `loading_comic_04`, `_06`, `_09`, `_14`, `_15`; 9 vùng chữ, 820×600, BC7, mip 1. Review nghĩa và ảnh offline độc lập đã đạt.
- Candidate nằm tại `staging/texture_vi_20261020_r01/candidate/files/Persistent_Store/AssetBundles/icon-0.en.unity3d`. Đọc báo cáo bàn giao trước khi dùng: [TEXTURE_PILOT_20261020.md](../reports/TEXTURE_PILOT_20261020.md).

## Công cụ

`tools/texture_localize.py` dùng môi trường `.venv/Scripts/python.exe` hiện có UnityPy 1.25.4 và Pillow 12.3.0. Các lệnh `probe`, `export`, `noop`, `patch` đều yêu cầu SHA256 nguồn, output mới chỉ dưới project work/reports/staging. Source game chỉ đọc. `patch` yêu cầu cả hash ảnh thay thế và CAB/path_id chính xác.

Chạy tại thư mục `StellaSora_VietHoa`, xem cú pháp:

```powershell
.\.venv\Scripts\python.exe tools/texture_localize.py --help
.\.venv\Scripts\python.exe tools/texture_localize.py patch --help
```

Ví dụ khung lệnh (điền đúng hash/path/ID của snapshot, không copy giá trị từ bản cũ):

```powershell
.\.venv\Scripts\python.exe tools/texture_localize.py probe --source ../Persistent_Store/AssetBundles/icon-0.en.unity3d --source-sha256 <SHA256_NGUON> --out work/textures/run_moi/probe
.\.venv\Scripts\python.exe tools/texture_localize.py patch --source ../Persistent_Store/AssetBundles/icon-0.en.unity3d --source-sha256 <SHA256_NGUON> --asset <CAB_CHINH_XAC> --path-id <TEXTURE_PATH_ID> --image <PNG_DUNG_KICH_THUOC> --image-sha256 <SHA256_PNG> --out staging/run_moi/patch01
```

`export --sprite` chỉ xuất ảnh xem trước của Sprite. Khi patch cần chọn Texture2D thực, không nhầm Sprite path_id với Texture2D path_id. Với nhiều texture trong một bundle, có thể patch tuần tự trên candidate staging; lần sau dùng đúng hash candidate lần trước. QA cuối phải so với nguồn gốc và hợp của toàn bộ vùng được sửa.

## Quy trình mỗi batch ảnh

1. Chốt version, bundle/source SHA256, CAB + Texture2D path_id, Sprite consumers, kích thước, định dạng, mipmap, alpha và vị trí `.resS`.
2. Xuất ảnh và nhìn trực tiếp. Ghi text EN đọc được, dịch VI theo context/glossary, giữ tên riêng/biểu tượng/glyph hư cấu. OCR nếu có chỉ là gợi ý, không thay xem ảnh.
3. Đóng băng proposal có hash; gọi LOCALIZATION_QA_REVIEWER/SEMANTIC_REVIEWER độc lập theo `docs/SUBAGENT_POLICY.md`. Chốt câu chữ trước khi tạo ảnh để giảm sửa lại.
4. Sửa chữ bằng built-in imagegen theo ảnh gốc; ghi prompt nguyên văn và ảnh nguồn. Giữ frame, palette, bố cục, nhân vật và đồ vật. Nếu output có kích thước khác, lưu bản raw và chuyển riêng về kích thước texture gốc để nhập asset; không bỏ bản gốc hoặc ghi đè nguồn.
5. Đọc ảnh VI ở native size, kiểm dấu, bố cục, không còn EN trong vùng đã giao. Chất lượng giữ artwork cần được reviewer đánh giá: imagegen có thể làm mượt/đổi nét, không mặc nhiên pixel-identical ngoài chữ.
6. Patch vào bundle staging; giữ format/mip/dimensions và sprite references, đọc lại candidate để xuất PNG lần hai. Với BC7, pixel có sai số lượng tử hóa; kiểm ảnh decode thực tế, không chỉ PNG trước nén.
7. QA độc lập đối chiếu raw objects, resource ngoài các đoạn được phép sửa, tất cả texture không thuộc scope và Sprite geometry. Reviewer nhìn PNG đọc lại từ bundle để kết luận visual.
8. Lưu manifest/acceptance/checkpoint. Runtime/gameplay/cài đặt là gate riêng, chưa được chứng minh bằng UnityPy readback.

## Giới hạn quan trọng của phiên bản tool đầu

- Chỉ xử lý texture có payload trong resource node được hỗ trợ và không alias/overlap với texture khác. Nếu encoder đổi format hoặc chiều dài payload, tool từ chối.
- Atlas BC7 sửa một vùng bị từ chối: encode lại toàn atlas có thể đổi sprite khác. Cần triển khai bảo toàn block ngoài vùng đích hoặc mở scope toàn atlas với QA tương ứng trước khi tiếp tục.
- Tight mesh/cropped sprite bị chặn. Các mesh ôm sát nét chữ EN có thể cắt dấu/kiểu chữ VI dù PNG đúng kích thước. Cần lộ trình mesh repair có guard và QA riêng; không sửa hình rồi bỏ qua mesh.
- Alpha thật không được biến thành ảnh nền đặc. Alpha 254–255 ở comic BC7 có thể là lượng tử hóa, khác asset có vùng trong suốt rõ rệt.
- No-op giữ nội dung mọi node giải nén và raw object; container nén có thể khác byte. Manifest/checksum game và khả năng loader chấp nhận cần kiểm ở giai đoạn runtime.
- Các định dạng/mipmap có trong catalog không đồng nghĩa đã được thử thành công bằng asset native tương ứng. Phạm vi native pilot xác minh là BC7 mip1; không gọi toàn bộ Alpha8/DXT/mip-chain đã đạt.
- Đây là texture PC; không áp bundle PC/BC7 lên Android rồi kết luận tương thích.

## Dữ liệu tiếp tục

Trong `work/textures/texture_vi_20261020_r01/` có `bundle_inventory.json`, `texture_catalog.json`, `texture_queue_r01.json`, ảnh trích, contact sheets, proposal r01/r02, ảnh imagegen raw/native, prompt trong `image_candidates_r01.json`, ảnh readback và bảng đối chiếu trước/sau.

Queue có trạng thái `offline_reviewed_staging` cho 5 mục pilot; các mục khác là `pending_visual_classification`, chưa chắc đều có chữ cần dịch. Không dùng 5/1.276 để suy phần trăm Việt hóa ảnh chữ toàn game. Ưu tiên các ảnh chữ nhật độc lập tiếp theo, rồi giải quyết atlas/tight mesh bằng task kỹ thuật có scope rõ.
