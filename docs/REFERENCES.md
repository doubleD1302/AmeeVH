# Tham khảo kỹ thuật

Kiểm tra ngày 19/10/2026. Tài liệu sau giải thích công cụ/Unity; không chứng minh một patch cụ thể hoạt động trên Stella Sora.

- [UnityPy — repository chính thức](https://github.com/K0lb3/UnityPy): thư viện đọc/sửa Unity assets; ứng viên nghiên cứu, chưa cài hoặc thử với game này. Không dùng tài liệu thư viện thay bằng chứng roundtrip.
- [Unity — Introduction to AssetBundles](https://docs.unity.com/en-us/engine/6000.0/manual/assets-and-media/assets-managing-runtime/assetbundles-section/asset-bundles-intro): khái niệm bundle và dữ liệu phụ thuộc nền tảng. Trang thuộc Unity 6; bản cài đọc được là 2022.3.62f2, cần đối chiếu API/format đúng phiên bản khi triển khai.
- [TextMeshPro 3.0 — fallbackFontAssetTable](https://docs.unity3d.com/ja/Packages/com.unity.textmeshpro%403.0/api/TMPro.TMP_FontAsset.fallbackFontAssetTable.html): danh sách fallback của TMP font asset.
- [TextMeshPro 3.0 — TMP_FontAsset](https://docs.unity3d.com/ja/Packages/com.unity.textmeshpro%403.0/api/TMPro.TMP_FontAsset.html): API kiểm ký tự/font; package version thực của game chưa xác minh.

Nguồn có thẩm quyền cho version/hash/layout archive cục bộ là các file của bản cài và báo cáo trong `reports/`, không phải suy đoán từ wiki hay game khác. Không tìm thấy/không kiểm chứng tài liệu `.arcx` ở lượt chuẩn bị này; trạng thái adapter vẫn unimplemented.
