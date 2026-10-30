/**
 * GlossaryView.js
 * Quản lý Modal tra cứu thuật ngữ, phân loại thẻ (pills), danh sách hiển thị và khay gợi ý
 */

function updateGlossaryCountBadge() {
    const badge = document.getElementById("glossaryTotalBadge");
    if (badge) {
        badge.innerText = `${allGlossaryTerms.length} Mục`;
    }
}

function renderGlossarySuggestions(enText) {
    const container = document.getElementById("glossarySuggestionsBox");
    const tray = document.getElementById("suggestionsChipsTray");
    const countLabel = document.getElementById("suggestionsCount");
    if (!container || !tray) return;

    const matches = detectGlossaryMatches(enText);
    if (matches.length === 0) {
        container.style.display = "none";
        tray.innerHTML = "";
        return;
    }

    container.style.display = "flex";
    container.scrollTop = 0;
    if (countLabel) countLabel.innerText = `${matches.length} thuật ngữ`;
    tray.innerHTML = "";

    matches.forEach(item => {
        const chip = document.createElement("div");
        chip.className = `glossary-suggestion-chip ${item.is_critical ? 'warn' : ''}`;
        
        let tooltip = `[${item.category}] ${item.en} ➔ ${item.vi}`;
        if (item.notes) tooltip += `\n⚠️ Lưu ý: ${item.notes}`;
        chip.title = tooltip;

        chip.innerHTML = `
            <span class="chip-en">${escapeHtml(item.en)}</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-vi">${escapeHtml(item.vi)}</span>
            ${item.is_critical ? `<span class="chip-warn-badge">⚠️ LƯU Ý</span>` : ''}
        `;

        chip.onclick = (e) => {
            e.stopPropagation();
            insertGlossaryTerm(item.vi);
        };

        tray.appendChild(chip);
    });
}

function openGlossaryModal() {
    const modal = document.getElementById("glossaryModal");
    if (!modal) return;
    modal.classList.add("open");
    renderGlossaryCategories();
    renderGlossaryList();
    setTimeout(() => {
        const search = document.getElementById("glossarySearchInput");
        if (search) search.focus({ preventScroll: true });
    }, 100);
}

function closeGlossaryModal() {
    const modal = document.getElementById("glossaryModal");
    if (modal) modal.classList.remove("open");
}

function renderGlossaryCategories() {
    const tray = document.getElementById("glossaryCatPills");
    if (!tray) return;

    const counts = {};
    let criticalCount = 0;
    allGlossaryTerms.forEach(t => {
        counts[t.category] = (counts[t.category] || 0) + 1;
        if (t.is_critical) criticalCount++;
    });

    const catList = [
        { id: "ALL", label: `Tất cả (${allGlossaryTerms.length})` },
        { id: "CRITICAL", label: `⚠️ Lưu Ý Sống Còn (${criticalCount})`, isCrit: true }
    ];

    const presetCats = [
        "Cốt Truyện & Thế Giới",
        "Chiến Đấu & Kỹ Năng",
        "Nhân Vật & Đại Từ",
        "Quái Vật & Boss",
        "Giao Diện & Hệ Thống",
        "Địa Danh & Bản Đồ",
        "Vật Phẩm & Trang Bị",
        "Chung"
    ];

    presetCats.forEach(cat => {
        if (counts[cat]) {
            catList.push({ id: cat, label: `${cat} (${counts[cat]})` });
        }
    });

    tray.innerHTML = catList.map(c => `
        <button class="glossary-cat-pill ${c.isCrit ? 'critical-pill' : ''} ${activeGlossaryCategory === c.id ? 'active' : ''}" onclick="setGlossaryCategory('${c.id}')">
            ${c.label}
        </button>
    `).join('');
}

function renderGlossaryList() {
    const container = document.getElementById("glossaryListContainer");
    if (!container) return;

    let filtered = allGlossaryTerms;

    // Category filter
    if (activeGlossaryCategory === "CRITICAL") {
        filtered = filtered.filter(t => t.is_critical);
    } else if (activeGlossaryCategory !== "ALL") {
        filtered = filtered.filter(t => t.category === activeGlossaryCategory);
    }

    // Text search
    if (glossarySearchTerm) {
        filtered = filtered.filter(t => {
            const en = (t.en || "").toLowerCase();
            const vi = (t.vi || "").toLowerCase();
            const notes = (t.notes || "").toLowerCase();
            const cat = (t.category || "").toLowerCase();
            return en.includes(glossarySearchTerm) || vi.includes(glossarySearchTerm) || notes.includes(glossarySearchTerm) || cat.includes(glossarySearchTerm);
        });
    }

    if (filtered.length === 0) {
        container.innerHTML = `<div class="glossary-empty-state">
            <p style="font-size:1.1rem; margin-bottom:6px;">🔍 Không tìm thấy thuật ngữ nào!</p>
            <p style="font-size:0.85rem; color:var(--text-sub);">Hãy thử tìm từ khóa khác hoặc bấm nút 'Tất cả' để xem toàn bộ từ điển.</p>
        </div>`;
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="glossary-card ${item.is_critical ? 'critical-card' : ''}">
            <div class="glossary-card-main">
                <div class="glossary-card-terms">
                    <span class="glossary-term-en">${escapeHtml(item.en)}</span>
                    <span class="glossary-term-arrow">➔</span>
                    <span class="glossary-term-vi">${escapeHtml(item.vi)}</span>
                </div>
                <div class="glossary-card-actions">
                    <span class="glossary-term-badge">${escapeHtml(item.category)}</span>
                    <button class="glossary-action-btn" onclick="copyGlossaryTerm('${escapeHtml(item.vi)}')">📋 Sao chép</button>
                    <button class="glossary-action-btn action-insert" onclick="insertGlossaryFromModal('${escapeHtml(item.vi)}')">➕ Chèn</button>
                </div>
            </div>
            ${item.notes ? `
                <div class="glossary-card-notes ${item.is_critical ? 'critical-notes' : ''}">
                    <span class="notes-icon">${item.is_critical ? '⚠️' : 'ℹ️'}</span>
                    <span class="notes-text">${escapeHtml(item.notes)}</span>
                </div>
            ` : ''}
        </div>
    `).join('');
}
