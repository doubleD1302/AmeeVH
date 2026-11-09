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

const chapterGroups = {
    main: 'Cốt truyện chính',
    side: 'Ngoại truyện',
    guild: 'Ủy thác hội quán',
    dating: 'Hẹn hò',
    messages: 'Tin nhắn điện thoại',
    events: 'Cốt truyện sự kiện',
    memory: 'Ký ức CG',
    other: 'Nội dung khác'
};
function groupForChapter(id) {
    if (id.includes('MainStory')) return 'main';
    if (id.startsWith('Ngoai_Truyen')) return 'side';
    if (id.startsWith('Uy_Thac')) return 'guild';
    if (id.startsWith('Hen_Ho')) return 'dating';
    if (id.startsWith('Tin_Nhan')) return 'messages';
    if (id.startsWith('Cot_Truyen_Su_Kien')) return 'events';
    if (id.startsWith('Kich_Ban_CG')) return 'memory';
    return 'other';
}
function renderChapterOptions(group, preferredId) {
    const select = document.getElementById('chapterSelect');
    select.replaceChildren();
    for (const chapter of allChapters.filter(item => groupForChapter(item.id) === group)) {
        const option = document.createElement('option');
        option.value = chapter.id;
        option.textContent = `${chapter.title} (${chapter.progress_pct}%)`;
        select.append(option);
    }
    if (preferredId && [...select.options].some(option => option.value === preferredId)) select.value = preferredId;
    if (typeof syncTramSelects === 'function') syncTramSelects();
}

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
        const groupSelect = document.getElementById('groupSelect');
        groupSelect.replaceChildren();
        for (const [id,label] of Object.entries(chapterGroups)) {
            if (!allChapters.some(chapter => groupForChapter(chapter.id) === id)) continue;
            const option=document.createElement('option'); option.value=id; option.textContent=label; groupSelect.append(option);
        }
        if (allChapters.length > 0) {
            const preferred=allChapters.some(chapter=>chapter.id==='Chuong_3_MainStory')?'Chuong_3_MainStory':allChapters[0].id;
            groupSelect.value=groupForChapter(preferred);
            renderChapterOptions(groupSelect.value,preferred);
            await loadChapterData(document.getElementById('chapterSelect').value);
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
            if (res.ok) { data = await res.json(); data.collaboration_available = false; }
        }
        currentChapterData = data || { scenes: [] };
        if (data && typeof data.collaboration_available === "boolean") {
            Collaboration.available = data.collaboration_available;
            if (data.dataset_version) Collaboration.datasetVersion = data.dataset_version;
            Collaboration.phase = data.dataset_phase || 'unavailable';
            Collaboration.ready = Collaboration.available && Collaboration.phase === 'open';
            Collaboration.updateNotice();
        }

        const sceneSel = document.getElementById("sceneSelect");
        const drawer = document.getElementById("scenesDrawer");
        sceneSel.innerHTML = '<option value="all">Toàn bộ các Màn</option>';
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
                l.chapter_id = cidFromChapter();
                l.sheet_sync_status = data?.sheet_sync?.status || 'unavailable';
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
function cidFromChapter() { return currentChapterData.chapter_id || document.getElementById("chapterSelect").value; }

function applyFilters() {
    if (typeof syncTramSelects === "function") syncTramSelects();
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
            return Collaboration.status(l) === "untranslated";
        }
        if (filterVal === "translated") {
            return ["pending","machine_pending"].includes(Collaboration.status(l));
        }
        if (filterVal === "approved") {
            return Collaboration.status(l) === "approved";
        }
        if (filterVal === "needs_review") return Collaboration.status(l) === "needs_review";
        if (filterVal === "machine") return l.translation_origin === "machine";
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
