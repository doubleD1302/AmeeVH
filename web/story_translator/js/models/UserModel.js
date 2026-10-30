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

function saveUserProfile() {
    const name = document.getElementById("inputUsername").value.trim();
    if (name) {
        currentUser.name = name;
    }
    localStorage.setItem("stella_user_profile", JSON.stringify(currentUser));
    updateHud();
    closeProfileModal();
    showToastAlert(`Chào mừng ${currentUser.name}! Chúc bạn có những bản dịch tuyệt vời!`);
}
