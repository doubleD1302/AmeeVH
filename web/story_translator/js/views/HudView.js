/**
 * HudView.js
 * Quản lý thanh trạng thái HUD, thông tin dịch giả, cấp độ, thanh EXP và chuyển đổi giao diện sáng/tối
 */

function updateThemeButton() {
    const dark = document.documentElement.dataset.theme === "dark";
    const button = document.getElementById("themeToggleBtn");
    if (!button) return;
    const label = dark ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối";
    button.title = label;
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-pressed", String(dark));
}

function toggleTheme() {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("stella_theme", next); } catch (_) {}
    updateThemeButton();
}

function updateHud() {
    const nameEl = document.getElementById("hudUsername");
    if (nameEl) nameEl.innerText = currentUser.name || "Nhà Thám Hiểm";
    
    const badgeEl = document.getElementById("hudLevelBadge");
    if (badgeEl) badgeEl.innerText = `Lv. ${currentUser.level || 1}`;
    
    if (currentUser.avatar) {
        const avatarEl = document.getElementById("hudAvatar");
        if (avatarEl) avatarEl.src = `official_assets/${currentUser.avatar}`;
    }
    
    const expInLvl = (currentUser.exp || 0) % 250;
    const pct = Math.min(100, Math.round((expInLvl / 250) * 100));
    const expFillEl = document.getElementById("hudExpFill");
    if (expFillEl) expFillEl.style.width = `${pct}%`;
}

function updateProgressBar() {
    if (!currentLines || currentLines.length === 0) return;
    let trans = 0;
    currentLines.forEach(l => {
        if (l.new_vi && l.new_vi !== l.en && l.status !== "Chờ dịch") {
            trans++;
        }
    });
    const pct = Math.round((trans / currentLines.length) * 100);
    const fillEl = document.getElementById("progressBarFill");
    if (fillEl) fillEl.style.width = `${pct}%`;
    const pctEl = document.getElementById("progressPercent");
    if (pctEl) pctEl.innerText = `${pct}%`;
    const summaryEl = document.getElementById("progressSummaryText");
    if (summaryEl && currentChapterData) {
        summaryEl.innerText = `Tiến độ ${currentChapterData.title}: Đã dịch ${trans} / ${currentLines.length} câu`;
    }
}
