# Lộ trình và tiêu chí qua giai đoạn

| Giai đoạn | Việc làm | Artifact bắt buộc | Điều kiện chuyển |
|---|---|---|---|
| P0 Chuẩn bị | Kiểm kê, fingerprint, công cụ/giao thức | inventory, test report, checkpoint | Tool hoạt động và scope được mô tả đúng |
| P1 Pilot SRT | Dịch 4 file theo 4 batch; review từng cue | proposal, audit, review, merged batch | Đủ cue, không lỗi guard, review giải quyết mọi warning |
| P2 Format | Xác minh `.arcx`, bảng text, ID, variant, dependency | format notes, adapter, fixtures, roundtrip report | Extract/repack không đổi nội dung đạt trên bản sao |
| P3 Catalog | Trích UI, truyện, cơ chế, vật phẩm, nhiệm vụ... | catalog có provenance, coverage và source hash | Có source locator và ngữ cảnh cho từng mục |
| P4 Dịch đợt | Khóa glossary dần, dịch + review theo cảnh/domain | batch ledger và proposal/review gắn hash | Các mục được chấp nhận có bằng chứng, mục lỗi vẫn pending |
| P5 Candidate | Font, build từng adapter, native readback | manifest candidate và báo cáo diff ngoài scope | Chỉ trường text/asset được phép thay đổi |
| P6 Runtime | Kiểm thử cảnh/màn hình thực tế, rollback | ảnh/video có ID/cảnh/build hash, rollback log | Không mất dấu, lỗi token, tràn khung hoặc sai hành vi |
| P7 Bảo trì | Đối chiếu nguồn sau update, tái review | delta catalog, bản dịch tương thích phiên bản | Không mang bản dịch cũ qua nguồn đã đổi một cách mù quáng |

P1 và nghiên cứu P2 có thể thực hiện xen kẽ. P2 chưa xong không ngăn agent dịch/review các SRT đã trích. Không tự sinh số lượng hoàn thành của P3–P7 khi chưa có catalog/runtime.

Ưu tiên toàn game sau pilot: menu/thông báo thường gặp → hướng dẫn đầu game → mô tả cơ chế/vật phẩm → truyện theo chương hoàn chỉnh → hồ sơ/nhiệm vụ/sự kiện → chữ trong texture. Phân loại lại theo dữ liệu thực sau extraction, không xem thứ tự này là cấu trúc archive có sẵn.

Mỗi milestone báo riêng `extracted`, `translated`, `static_pass`, `semantic_approved`, `staged`, `runtime_verified`. Mẫu checkpoint ở thư mục gốc; nhật ký issue theo `templates/ISSUE_TEMPLATE.md`.
