/**
 * UserModel.js
 * Quản lý thông tin dịch giả, cấp độ, EXP, danh hiệu và lưu trữ LocalStorage
 */

let currentUser = {
    name: "KhaiMinh",
    avatar: "29-2-5b4fdfed.png",
    level: 1,
    exp: 0,
    title: "Tân Binh Lạc Lối"
};

function loadProfile() {
    const saved = localStorage.getItem("stella_user_profile");
    if (saved) {
        try {
            currentUser = JSON.parse(saved);
        } catch (e) {}
    } else {
        openProfileModal();
    }
    updateHud();
}

async function saveUserProfile() {
    const name = document.getElementById("inputUsername").value.trim();
    if (name) {
        currentUser.name = name;
    }
    localStorage.setItem("stella_user_profile", JSON.stringify(currentUser));
    updateHud();
    closeProfileModal();
    try {
        if (window.Collaboration?.available) await Collaboration.setDisplayName(currentUser.name);
        showToastAlert(`Đã cập nhật tên hiển thị: ${currentUser.name}.`);
    } catch (_) {
        showToastAlert('Tên đã lưu trên máy; máy chủ chưa cập nhật. Đề xuất mới vẫn dùng tên cũ đến khi kết nối lại.');
    }
}
