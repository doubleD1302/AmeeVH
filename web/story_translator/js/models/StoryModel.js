/**
 * StoryModel.js
 * Quản lý danh sách chương, các màn chơi, câu thoại và lưu trữ dữ liệu bản dịch
 */

let allChapters = [];
let currentChapterData = null;
let currentLines = [];
let filteredLines = [];
let currentIndex = 0;
let viewMode = "game";

async function loadChaptersList() {
    try {
        let data = null;
        try {
            const res = await fetch("/api/chapters");
            if (res.ok) data = await res.json();
        } catch (_) {}
        if (!data) {
            const res = await fetch("data/chapters.json");
            if (res.ok) data = await res.json();
        }
        allChapters = data || [];
        const sel = document.getElementById("chapterSelect");
        sel.innerHTML = "";
        allChapters.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.id;
            opt.innerText = `${c.title} (${c.progress_pct}%)`;
            sel.appendChild(opt);
        });
        if (allChapters.length > 0) {
            sel.value = "Chuong_3_MainStory";
            await loadChapterData(sel.value);
        }
    } catch (e) {
        console.error("Lỗi nạp chapters:", e);
    }
}

async function loadChapterData(chapterId) {
    document.getElementById("progressSummaryText").innerText = "Đang nạp dữ liệu chương...";
    try {
        let data = null;
        try {
            const res = await fetch(`/api/chapter_data?id=${chapterId}`);
            if (res.ok) data = await res.json();
        } catch (_) {}
        if (!data) {
            const res = await fetch(`data/chapters/${chapterId}.json`);
            if (res.ok) data = await res.json();
        }
        currentChapterData = data || { scenes: [] };

        const sceneSel = document.getElementById("sceneSelect");
        const drawer = document.getElementById("scenesDrawer");
        sceneSel.innerHTML = '<option value="all">🌟 Toàn bộ các Màn</option>';
        drawer.innerHTML = '<div class="scenes-nav-header"><span>DANH SÁCH MÀN</span></div>';

        currentLines = [];
        currentChapterData.scenes.forEach((sc, scIdx) => {
            const opt = document.createElement("option");
            opt.value = scIdx;
            opt.innerText = sc.scene_id ? `${sc.title} [${sc.scene_id}]` : sc.title;
            sceneSel.appendChild(opt);

            const btn = document.createElement("button");
            btn.className = `scene-card-btn ${scIdx === 0 ? "active" : ""}`;
            btn.onclick = () => selectScene(scIdx);
            btn.innerHTML = `
                <span class="scene-card-title">${sc.title}</span>
                <div class="scene-card-meta">
                    <span style="color:var(--cyan-light); font-weight:700;">${sc.badge || ''}</span>
                    <span style="color:var(--text-dim); font-family:var(--font-code); font-size:0.72rem;">${sc.scene_id ? `[${sc.scene_id}]` : ''}</span>
                    <span>${sc.lines.length} câu</span>
                </div>
            `;
            drawer.appendChild(btn);

            sc.lines.forEach(l => {
                l.sceneTitle = sc.title;
                l.sceneBadge = sc.badge || sc.scene_id;
                currentLines.push(l);
            });
        });

        applyFilters();
        updateProgressBar();
    } catch (e) {
        console.error("Lỗi nạp chapter data:", e);
    }
}

// Filtering
function applyFilters() {
    const scVal = document.getElementById("sceneSelect").value;
    const filterVal = document.getElementById("filterSelect").value;

    let lines = currentLines;
    if (scVal !== "all") {
        const scIdx = parseInt(scVal);
        if (currentChapterData && currentChapterData.scenes && currentChapterData.scenes[scIdx]) {
            lines = currentChapterData.scenes[scIdx].lines;
        }
    }

    filteredLines = lines.filter(l => {
        if (filterVal === "untranslated") {
            return !l.new_vi || l.new_vi === l.en || l.status === "Chờ dịch";
        }
        if (filterVal === "translated") {
            return l.new_vi && l.new_vi !== l.en && l.status !== "Chờ dịch";
        }
        if (filterVal === "approved") {
            return l.status === "Đã duyệt";
        }
        if (filterVal === "dialogue_only") {
            return !l.speaker.includes("[Hệ thống") && !l.speaker.includes("Dẫn chuyện");
        }
        return true;
    });

    currentIndex = 0;
    renderCurrentLine();
    if (viewMode === "list") {
        renderListMode();
    }
}
