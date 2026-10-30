/**
 * ProfileView.js
 * Quản lý Modal hồ sơ dịch giả và lưới chọn hình đại diện nhân vật
 */

function openProfileModal() {
    const input = document.getElementById("inputUsername");
    if (input) input.value = currentUser.name || "";
    renderAvatarGrid();
    const modal = document.getElementById("profileModal");
    if (modal) modal.classList.add("open");
}

function closeProfileModal() {
    const modal = document.getElementById("profileModal");
    if (modal) modal.classList.remove("open");
}

function renderAvatarGrid() {
    const grid = document.getElementById("avatarSelectionGrid");
    if (!grid) return;
    grid.innerHTML = "";
    const seen = new Set();
    Object.values(charactersDict).forEach(c => {
        if (!c || !c.nameEN || seen.has(c.nameEN)) return;
        seen.add(c.nameEN);
        const item = document.createElement("div");
        item.className = `avatar-card-item ${currentUser.avatar === c.avatar ? "selected" : ""}`;
        item.onclick = () => {
            document.querySelectorAll(".avatar-card-item").forEach(x => x.classList.remove("selected"));
            item.classList.add("selected");
            currentUser.avatar = c.avatar;
        };
        item.innerHTML = `
            <img src="official_assets/${c.avatar}" alt="${c.nameEN}" onerror="this.src='web_assets/favicon.png'">
            <span>${c.nameEN}</span>
        `;
        grid.appendChild(item);
    });
}
