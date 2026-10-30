/**
 * GlossaryView.js
 * Quản lý Modal tra cứu thuật ngữ, phân loại thẻ (pills), tìm kiếm thông minh và khay gợi ý
 */

function updateGlossaryCountBadge() {
    const badge = document.getElementById("glossaryTotalBadge");
    if (badge) {
        badge.innerText = `${allGlossaryTerms.length} Mục`;
    }
}

/**
 * Tô sáng từ khóa tìm kiếm trong kết quả hiển thị
 */
function highlightGlossaryMatch(text, query) {
    if (!text) return "";
    const escaped = escapeHtml(text);
    if (!query || !query.trim()) return escaped;

    try {
        const rawQuery = query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${rawQuery})`, 'gi');
        return escaped.replace(regex, '<mark class="glossary-kw-highlight">$1</mark>');
    } catch (_) {
        return escaped;
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
        if (search) {
            search.focus({ preventScroll: true });
            search.select();
        }
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
        const cat = t.category || "Chung";
        counts[cat] = (counts[cat] || 0) + 1;
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

    // Thêm các danh mục khác nếu có trong sheet
    Object.keys(counts).forEach(c => {
        if (!presetCats.includes(c) && c !== "ALL" && c !== "CRITICAL") {
            catList.push({ id: c, label: `${c} (${counts[c]})` });
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

    const filtered = searchGlossaryTerms(glossarySearchTerm, activeGlossaryCategory);

    // Cập nhật nhãn trạng thái tìm kiếm
    const badge = document.getElementById("glossaryTotalBadge");
    if (badge) {
        if (glossarySearchTerm || activeGlossaryCategory !== "ALL") {
            badge.innerText = `${filtered.length} / ${allGlossaryTerms.length} Mục`;
        } else {
            badge.innerText = `${allGlossaryTerms.length} Mục`;
        }
    }

    if (filtered.length === 0) {
        container.innerHTML = `<div class="glossary-empty-state">
            <p style="font-size:1.15rem; font-weight:700; margin-bottom:8px; color:var(--text-main);">🔍 Không tìm thấy thuật ngữ phù hợp!</p>
            <p style="font-size:0.88rem; color:var(--text-sub); line-height:1.5;">
                Bạn có thể thử tìm bằng từ tiếng Anh, tiếng Việt (có dấu hoặc không dấu), hoặc bấm <b>"Tất cả"</b> để xem danh sách.
            </p>
        </div>`;
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="glossary-card ${item.is_critical ? 'critical-card' : ''}">
            <div class="glossary-card-main">
                <div class="glossary-card-terms">
                    <span class="glossary-term-en">${highlightGlossaryMatch(item.en, glossarySearchTerm)}</span>
                    <span class="glossary-term-arrow">➔</span>
                    <span class="glossary-term-vi">${highlightGlossaryMatch(item.vi, glossarySearchTerm)}</span>
                </div>
                <div class="glossary-card-actions">
                    <span class="glossary-term-badge">${escapeHtml(item.category || 'Chung')}</span>
                    <button class="glossary-action-btn" onclick="copyGlossaryTerm('${escapeHtml(item.vi)}')">📋 Sao chép</button>
                    <button class="glossary-action-btn action-insert" onclick="insertGlossaryFromModal('${escapeHtml(item.vi)}')">➕ Chèn</button>
                </div>
            </div>
            ${item.notes ? `
                <div class="glossary-card-notes ${item.is_critical ? 'critical-notes' : ''}">
                    <span class="notes-icon">${item.is_critical ? '⚠️' : 'ℹ️'}</span>
                    <span class="notes-text">${highlightGlossaryMatch(item.notes, glossarySearchTerm)}</span>
                </div>
            ` : ''}
        </div>
    `).join('');
}


/**
 * Tra cứu thuật ngữ nhanh trực tiếp ngay trong khung dịch thuật
 */
function onQuickGlossarySearch(val) {
    const tray = document.getElementById("quickGlossaryResultsTray");
    const clearBtn = document.getElementById("quickGlossaryClear");
    if (!tray) return;

    const term = (val || "").trim();
    if (clearBtn) clearBtn.style.display = term ? "block" : "none";

    if (!term) {
        tray.style.display = "none";
        tray.innerHTML = "";
        return;
    }

    const matches = searchGlossaryTerms(term, "ALL");
    if (matches.length === 0) {
        tray.style.display = "flex";
        tray.innerHTML = `<span style="font-size:0.8rem; color:var(--text-sub); padding:4px;">🔍 Không tìm thấy thuật ngữ nào khớp với "${escapeHtml(term)}" (Bấm Alt+G để mở Từ điển đầy đủ)</span>`;
        return;
    }

    tray.style.display = "flex";
    tray.innerHTML = matches.slice(0, 20).map(item => `
        <div class="glossary-suggestion-chip ${item.is_critical ? 'warn' : ''}" 
             title="[${item.category}] ${item.en} ➔ ${item.vi}${item.notes ? ' (' + item.notes + ')' : ''}"
             onclick="insertGlossaryTerm('${escapeHtml(item.vi)}');">
            <span class="chip-en">${escapeHtml(item.en)}</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-vi">${escapeHtml(item.vi)}</span>
            ${item.is_critical ? '<span class="chip-warn-badge">⚠️ LƯU Ý</span>' : ''}
        </div>
    `).join('');
}

function clearQuickGlossarySearch() {
    const input = document.getElementById("quickGlossaryInput");
    if (input) input.value = "";
    onQuickGlossarySearch("");
}
