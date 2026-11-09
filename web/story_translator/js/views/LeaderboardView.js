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
            if (res.ok) {
                const payload = await res.json();
                if (payload?.success === false) throw new Error(payload.error || "Không thể tải bảng xếp hạng.");
                leaders = normalizeLeaderboardPayload(payload);
            }
        } catch (_) {}
        if (!leaders) {
            const res = await fetch("data/leaderboard.json");
            if (res.ok) leaders = await res.json();
        }
        leaders = normalizeLeaderboardPayload(leaders);
        list.innerHTML = "";
        if (leaders.length === 0) {
            list.innerHTML = "<p style='color:var(--text-sub); text-align:center;'>Chưa có ai ghi danh! Hãy là người đầu tiên dịch!</p>";
            return;
        }
        leaders.forEach((u, i) => {
            const row = document.createElement("div");
            row.style.cssText = "display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.04); padding:12px 16px; border-radius:14px; border:1px solid rgba(255,255,255,0.06);";
            const left = document.createElement('div'); left.style.cssText = 'display:flex; align-items:center; gap:12px;';
            const rank = document.createElement('span'); rank.style.cssText = 'font-family:var(--font-display); font-size:1.2rem; font-weight:800; color:var(--gold-accent); width:28px;'; rank.textContent = `#${i + 1}`;
            const identity = document.createElement('div');
            const name = document.createElement('div'); name.style.cssText = 'font-weight:800; color:#ffffff;'; name.textContent = String(u.name || 'Ẩn danh');
            const level = document.createElement('span'); level.className = 'hud-level-tag'; level.textContent = formatLeaderboardLevel(u.level); name.append(' ', level);
            const title = document.createElement('div'); title.style.cssText = 'font-size:0.75rem; color:var(--cyan-light);'; title.textContent = String(u.title || 'Tân Binh');
            identity.append(name, title); left.append(rank, identity);
            const score = document.createElement('div'); score.style.textAlign = 'right';
            const translated = document.createElement('div'); translated.style.cssText = 'font-weight:800; color:var(--green-accent); font-size:1.05rem;'; translated.textContent = `${Number(u.translated_count) || 0} câu`;
            const exp = document.createElement('div'); exp.style.cssText = 'font-size:0.75rem; color:var(--text-dim);'; exp.textContent = `${Number(u.exp) || 0} EXP`;
            score.append(translated, exp); row.append(left, score);
            list.appendChild(row);
        });
    } catch (e) {
        list.innerHTML = "<p>Lỗi nạp bảng xếp hạng.</p>";
    }
}

function normalizeLeaderboardPayload(payload) {
    const leaders = Array.isArray(payload) ? payload : payload?.leaders;
    if (!Array.isArray(leaders)) throw new Error('Dữ liệu bảng xếp hạng không hợp lệ.');
    return leaders.filter(item => item && typeof item === 'object');
}

function formatLeaderboardLevel(level) {
    if (typeof level === 'number' && Number.isFinite(level)) return `Lv. ${level}`;
    const text = String(level || '').trim();
    if (!text) return 'Lv. 1';
    return /^lv\.?\s/i.test(text) ? text : text.replace(/^cấp\s+/i, 'Lv. ');
}

function closeLeaderboardModal() {
    const modal = document.getElementById("leaderboardModal");
    if (modal) modal.classList.remove("open");
}
