/**
 * config.js
 * Cấu hình kết nối Backend Serverless (Google Apps Script & Cloudflare Pages)
 * cho Trạm Dịch Thuật Stella Sora
 */

window.APP_CONFIG = {
    // 1. URL của Google Apps Script Web App (sau khi deploy)
    // Mặc định kết nối thẳng tới Web App của dự án
    GAS_URL: localStorage.getItem("stella_gas_url") || "https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec",

    // 2. Chế độ đồng bộ dữ liệu:
    // "auto"   : Tự động thử qua Cloudflare Pages Proxy (/api/save_line), nếu thất bại sẽ gửi trực tiếp đến GAS_URL.
    // "proxy"  : Chỉ gửi qua Cloudflare Pages Functions (/api/save_line).
    // "direct" : Gửi trực tiếp từ trình duyệt đến GAS_URL (bằng CORS Simple Request text/plain).
    SYNC_MODE: "auto",

    // 3. ID Bảng tính Google Spreadsheet dự án
    SPREADSHEET_ID: "13ooFrJLyeP9LsSFrkzp4SWpQY5ePd6ap5muvWCwWOdM",

    // 4. Hàng đợi lưu trữ ngoại tuyến khi mất mạng
    ENABLE_OFFLINE_QUEUE: true,

    // Phương thức lưu và cập nhật GAS_URL vào localStorage
    setGasUrl(url) {
        if (url) {
            this.GAS_URL = url.trim();
            localStorage.setItem("stella_gas_url", this.GAS_URL);
        }
    },

    // Kiểm tra đã có cấu hình backend hợp lệ chưa
    hasBackend() {
        return Boolean(this.GAS_URL) || window.location.hostname.includes("pages.dev") || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    }
};
