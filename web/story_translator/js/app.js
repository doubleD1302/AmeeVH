/**
 * app.js
 * Điểm khởi chạy chính của ứng dụng Web Trạm Dịch Thuật Stella Sora (SS-Trans)
 * Kết nối các thành phần Model - View - Controller và khởi chạy chu trình ứng dụng
 */

// Đăng ký khởi chạy khi toàn bộ DOM sẵn sàng
window.addEventListener("DOMContentLoaded", async () => {
    await AppController.init();
});

// Đăng ký phím tắt toàn cục
window.addEventListener("keydown", (e) => {
    // Alt + G: Mở nhanh từ điển thuật ngữ
    if (e.altKey && (e.key === "g" || e.key === "G")) {
        e.preventDefault();
        openGlossaryModal();
        return;
    }
    // Alt + M: Bật/Tắt nhạc nền hoặc đổi bài
    if (e.altKey && (e.key === "m" || e.key === "M")) {
        e.preventDefault();
        toggleBgm();
        return;
    }
    // Alt + Mũi tên Trái: Câu trước
    if (e.altKey && e.key === "ArrowLeft") {
        e.preventDefault();
        navigateLine(-1);
    }
    // Alt + Mũi tên Phải: Câu tiếp
    if (e.altKey && e.key === "ArrowRight") {
        e.preventDefault();
        navigateLine(1);
    }
    // Alt + S: Lưu câu hiện tại
    if (e.altKey && (e.key === "s" || e.key === "S")) {
        e.preventDefault();
        saveCurrentLine();
    }
});
