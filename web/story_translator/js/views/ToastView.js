/**
 * ToastView.js
 * Quản lý thông báo toast nổi và tiện ích mã hóa ký tự HTML an toàn
 */

function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function showToastAlert(msg) {
    const toast = document.getElementById("toastNotification");
    if (!toast) return;
    document.getElementById("toastNotificationText").innerText = msg;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}
