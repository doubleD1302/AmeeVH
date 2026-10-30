/**
 * LeaderboardView.js
 * Quản lý Modal bảng xếp hạng và vinh danh dịch giả đóng góp
 */

async function openLeaderboardModal() {
    const modal = document.getElementById("leaderboardModal");
    const list = document.getElementById("leaderboardListing");
    if (!modal || !list) return;
    list.innerHTML = "<p style='color:var(--text-sub);'>Đang tải bảng xếp hạng...</p>";
    modal.classList.add("open");

    try {
        let leaders = null;
        try {
            const res = await fetch("/api/leaderboard");
            if (res.ok) leaders = await res.json();
        } catch (_) {}
        if (!leaders) {
            const res = await fetch("data/leaderboard.json");
            if (res.ok) leaders = await res.json();
        }
        leaders = leaders || [];
        list.innerHTML = "";
        if (leaders.length === 0) {
            list.innerHTML = "<p style='color:var(--text-sub); text-align:center;'>Chưa có ai ghi danh! Hãy là người đầu tiên dịch!</p>";
            return;
        }
        leaders.forEach((u, i) => {
            const row = document.createElement("div");
            row.style.cssText = "display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.04); padding:12px 16px; border-radius:14px; border:1px solid rgba(255,255,255,0.06);";
            row.innerHTML = `
                <div style="display:flex; align-items:center; gap:12px;">
                    <span style="font-family:var(--font-display); font-size:1.2rem; font-weight:800; color:var(--gold-accent); width:28px;">#${i+1}</span>
                    <div>
                        <div style="font-weight:800; color:#ffffff;">${u.name} <span class="hud-level-tag">Lv. ${u.level}</span></div>
                        <div style="font-size:0.75rem; color:var(--cyan-light);">${u.title || 'Tân Binh'}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; color:var(--green-accent); font-size:1.05rem;">${u.translated_count} câu</div>
                    <div style="font-size:0.75rem; color:var(--text-dim);">${u.exp} EXP</div>
                </div>
            `;
            list.appendChild(row);
        });
    } catch (e) {
        list.innerHTML = "<p>Lỗi nạp bảng xếp hạng.</p>";
    }
}

function closeLeaderboardModal() {
    const modal = document.getElementById("leaderboardModal");
    if (modal) modal.classList.remove("open");
}
