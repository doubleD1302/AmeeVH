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

function isCodeOnlySource(value) {
    const raw = String(value ?? '').trim();
    if (!raw) return true;
    const text = raw
        .replace(/==[A-Za-z0-9_]+==/g, '')
        .replace(/<[^>]*>/g, '')
        .replace(/\{[^{}]+\}/g, '')
        .trim();
    if (!text || /^#(?:ERROR|N\/A)!?$/i.test(text)) return true;
    if (/\s/.test(text) || /[.,!?;:'"“”‘’()[\]<>/\\]/.test(text)) return false;
    if (/^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+$/.test(text)) return true;
    if (/^(?:Set|Get|Add|Remove|Play|Stop|Open|Close|Show|Hide|Load|Save|Jump|Choice|Wait|End|Start|Ctrl|On|Off)[A-Z][A-Za-z0-9]*$/.test(text)) return true;
    return /^(?:ep|fx|q?story|vo|cg|bg|bgm|ui|sfx|se|audio|sound|asset|char|item|quest|battle|event|avg)[A-Za-z0-9_]*$/i.test(text);
}

function isTranslatableLine(line) {
    return !!line && !isCodeOnlySource(line.en);
}

function showChapterLoading(chapterId = '') {
    const overlay = document.getElementById('chapterLoadingOverlay');
    if (!overlay) return;
    overlay.hidden = false;
    overlay.classList.remove('is-error');
    const chapter = document.getElementById('chapterLoadingChapter');
    if (chapter) chapter.textContent = chapterId ? (allChapters.find(item => item.id === chapterId)?.title || chapterId) : 'Đang kết nối';
    updateChapterLoading('catalog', 12, 'Kết nối kho dữ liệu', 'Đang chuẩn bị nguồn EN, JP, CN và trạng thái cộng tác.');
}

function updateChapterLoading(stepName, percent, phase, subtitle) {
    const overlay = document.getElementById('chapterLoadingOverlay');
    if (!overlay) return;
    const title = document.getElementById('chapterLoadingTitle');
    const sub = document.getElementById('chapterLoadingSubtitle');
    const phaseEl = document.getElementById('chapterLoadingPhase');
    const percentEl = document.getElementById('chapterLoadingPercent');
    const bar = document.getElementById('chapterLoadingBar');
    const progress = overlay.querySelector('[role="progressbar"]');
    if (title) title.innerHTML = 'Đang nạp chương<span class="chapter-loading-dots"></span>';
    if (sub && subtitle) sub.textContent = subtitle;
    if (phaseEl) phaseEl.textContent = phase;
    if (percentEl) percentEl.textContent = `${percent}%`;
    if (bar) bar.style.width = `${percent}%`;
    if (progress) progress.setAttribute('aria-valuenow', String(percent));
    overlay.querySelectorAll('[data-loading-step]').forEach(step => {
        const order = { catalog: 1, collab: 2, sources: 3 }[step.dataset.loadingStep] || 0;
        const current = { catalog: 1, collab: 2, sources: 3 }[stepName] || 1;
        step.classList.toggle('is-done', order < current);
        step.classList.toggle('is-active', order === current);
        const icon = step.querySelector('span:first-child');
        if (icon) icon.textContent = order < current ? '✓' : '·';
    });
}

function hideChapterLoading() {
    const overlay = document.getElementById('chapterLoadingOverlay');
    if (!overlay) return;
    overlay.hidden = true;
    overlay.classList.remove('is-error');
}

function failChapterLoading(message) {
    const overlay = document.getElementById('chapterLoadingOverlay');
    if (!overlay) return;
    overlay.hidden = false;
    overlay.classList.add('is-error');
    const title = document.getElementById('chapterLoadingTitle');
    const sub = document.getElementById('chapterLoadingSubtitle');
    const phase = document.getElementById('chapterLoadingPhase');
    const state = document.getElementById('chapterLoadingState');
    if (title) title.textContent = 'Không thể nạp chương';
    if (sub) sub.textContent = message || 'Hãy thử chọn lại chương hoặc tải lại trang.';
    if (phase) phase.textContent = 'Đã dừng';
    if (state) state.textContent = 'Có lỗi';
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
    showChapterLoading();
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
        updateChapterLoading('catalog', 28, 'Nạp danh sách chương', 'Đang mở danh sách chương và các cảnh có thể dịch.');
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
        failChapterLoading(e.message);
    }
}

async function loadChapterData(chapterId) {
    showChapterLoading(chapterId);
    document.getElementById("progressSummaryText").innerText = "Đang nạp dữ liệu chương...";
    try {
        let data = null;
        updateChapterLoading('collab', 48, 'Khôi phục bản dịch cộng tác', 'Đang lấy trạng thái D1 và các đề xuất hiện tại.');
        try {
            const res = await fetch(`/api/chapter_data?id=${chapterId}`);
            if (res.ok) data = await res.json();
        } catch (_) {}
        if (!data) {
            const res = await fetch(`data/chapters/${chapterId}.json`);
            if (res.ok) { data = await res.json(); data.collaboration_available = false; }
        }
        updateChapterLoading('sources', 76, 'Đối chiếu nguồn đa ngôn ngữ', 'Đang ghép EN, JP, CN và lọc các mục thuần mã hệ thống.');
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

            sc.lines = (sc.lines || []).filter(isTranslatableLine);
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
        updateChapterLoading('sources', 100, 'Hoàn tất', 'Chương đã sẵn sàng để dịch.');
        setTimeout(hideChapterLoading, 260);
    } catch (e) {
        console.error("Lỗi nạp chapter data:", e);
        failChapterLoading(e.message);
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
