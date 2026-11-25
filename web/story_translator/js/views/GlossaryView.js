/**
 * GlossaryView.js
 * Giao diện Từ Điển Thuật Ngữ Chuẩn: Trình diễn thẻ thuật ngữ cao cấp,
 * hỗ trợ đa nền tảng PC & Android, khay thêm thuật ngữ mới và tìm kiếm tức thì.
 */

let glossaryEditTarget = null;
const glossaryRenderTerms = new Map();
const GLOSSARY_PAGE_SIZE = 120;
let glossaryVisibleLimit = GLOSSARY_PAGE_SIZE;

function glossaryTermKey(term) {
    return `${term.id || ""}::${term.en || ""}::${term.vi || ""}`;
}

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

/**
 * Hiển thị các thuật ngữ gợi ý tương ứng với câu thoại đang chọn
 */
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
        chip.className = "glossary-suggestion-chip";
        const grp = getGlossaryGroupById(glossaryGroupOf(item, allGlossaryTerms));
        const grpName = grp ? grp.label : (item.category || "Thuật ngữ");
        let tooltip = `[${grpName}] ${item.en} ➔ ${item.vi}`;
        if (item.notes) tooltip += `\n(${item.notes})`;
        chip.title = tooltip;

        chip.innerHTML = `
            <span class="chip-en">${escapeHtml(item.en)}</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-vi">${escapeHtml(item.vi)}</span>
        `;

        chip.onclick = (e) => {
            e.stopPropagation();
            insertGlossaryTerm(item.vi);
        };

        tray.appendChild(chip);
    });
}

/**
 * Mở modal từ điển
 */
function openGlossaryModal() {
    const modal = document.getElementById("glossaryModal");
    if (!modal) return;
    glossaryVisibleLimit = GLOSSARY_PAGE_SIZE;
    modal.classList.add("open");
    renderGlossaryCategories();
    renderGlossaryList();
    setTimeout(() => {
        const search = document.getElementById("glossarySearchInput");
        if (search) {
            search.focus({ preventScroll: true });
            search.select();
        }
    }, 120);
}

/**
 * Đóng modal từ điển
 */
function closeGlossaryModal() {
    const modal = document.getElementById("glossaryModal");
    if (modal) modal.classList.remove("open");
    closeGlossaryFilterMenu(false);
    toggleAddTermDrawer(false);
}

/**
 * Xử lý nhấp chuột vào nền tối ngoài modal để đóng
 */
function handleGlossaryModalBackdropClick(event) {
    if (event.target && event.target.id === "glossaryModal") {
        closeGlossaryModal();
    }
}

/**
 * Đóng / Mở ngăn kéo Thêm Thuật Ngữ Mới
 */
function toggleAddTermDrawer(forceState) {
    const drawer = document.getElementById("addTermDrawer");
    const btn = document.getElementById("btnOpenAddTerm");
    if (!drawer) return;

    const isOpen = drawer.style.display !== "none" && drawer.classList.contains("open");
    const shouldOpen = forceState !== undefined ? forceState : !isOpen;

    if (shouldOpen) {
        if (!glossaryEditTarget) resetGlossaryTermForm();
        drawer.style.display = "block";
        requestAnimationFrame(() => {
            drawer.classList.add("open");
        });
        if (btn) btn.classList.add("active");
        setTimeout(() => {
            const inputEn = document.getElementById("inputTermEn");
            if (inputEn) inputEn.focus();
        }, 150);
    } else {
        drawer.classList.remove("open");
        if (btn) btn.classList.remove("active");
        setTimeout(() => {
            if (!drawer.classList.contains("open")) {
                drawer.style.display = "none";
            }
        }, 220);
    }
}

function resetGlossaryTermForm() {
    glossaryEditTarget = null;
    const title = document.getElementById("addTermDrawerTitle");
    const submit = document.getElementById("btnSubmitAddTerm");
    const en = document.getElementById("inputTermEn");
    const vi = document.getElementById("inputTermVi");
    const notes = document.getElementById("inputTermNotes");
    if (title) title.textContent = "THÊM THUẬT NGỮ MỚI · LƯU TRÊN MÁY";
    if (submit) submit.querySelector(".btn-submit-text").textContent = "Lưu thuật ngữ";
    if (en) en.value = "";
    if (vi) vi.value = "";
    if (notes) notes.value = "";
    const category = document.getElementById("selectTermCategory");
    if (category) category.value = getGlossaryGroupById(GLOSSARY_DEFAULT_GROUP).label;
}

function openGlossaryEdit(term) {
    if (!term) return;
    glossaryEditTarget = { ...term };
    const drawer = document.getElementById("addTermDrawer");
    if (!drawer) return;
    drawer.style.display = "block";
    requestAnimationFrame(() => drawer.classList.add("open"));
    const title = document.getElementById("addTermDrawerTitle");
    const submit = document.getElementById("btnSubmitAddTerm");
    const en = document.getElementById("inputTermEn");
    const vi = document.getElementById("inputTermVi");
    const category = document.getElementById("selectTermCategory");
    const notes = document.getElementById("inputTermNotes");
    if (title) title.textContent = "CHỈNH SỬA THUẬT NGỮ · LƯU TRÊN MÁY";
    if (submit) submit.querySelector(".btn-submit-text").textContent = "Lưu chỉnh sửa";
    if (en) en.value = term.en || "";
    if (vi) vi.value = term.vi || "";
    if (category) {
        const group = getGlossaryGroupById(glossaryGroupOf(term, allGlossaryTerms));
        category.value = group ? group.label : getGlossaryGroupById(GLOSSARY_DEFAULT_GROUP).label;
    }
    if (notes) notes.value = term.notes || "";
    const btn = document.getElementById("btnOpenAddTerm");
    if (btn) btn.classList.add("active");
    setTimeout(() => en?.focus(), 100);
}

function openGlossaryEditByKey(encodedKey) {
    const term = glossaryRenderTerms.get(decodeURIComponent(encodedKey || ""));
    if (term) openGlossaryEdit(term);
}

/**
 * Gửi form thêm thuật ngữ mới
 */
async function submitAddTermForm() {
    const inputEn = document.getElementById("inputTermEn");
    const inputVi = document.getElementById("inputTermVi");
    const selectCat = document.getElementById("selectTermCategory");
    const inputNotes = document.getElementById("inputTermNotes");
    const submitBtn = document.getElementById("btnSubmitAddTerm");

    const en = inputEn ? inputEn.value.trim() : "";
    const vi = inputVi ? inputVi.value.trim() : "";
    const category = selectCat ? selectCat.value.trim() : getGlossaryGroupById(GLOSSARY_DEFAULT_GROUP).label;
    const notes = inputNotes ? inputNotes.value.trim() : "";

    if (!en || !vi) {
        showToastAlert("⚠️ Vui lòng điền đầy đủ cả Thuật ngữ gốc (EN) và Bản dịch chuẩn (VI)!");
        if (!en && inputEn) inputEn.focus();
        else if (inputVi) inputVi.focus();
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add("loading");
    }

    try {
        if (glossaryEditTarget) {
            await updateGlossaryTerm({ id: glossaryEditTarget.id, previous_en: glossaryEditTarget.en, en, vi, category, notes });
        } else {
            await addGlossaryTerm({ en, vi, category, notes });
        }

        // Reset form và đóng ngăn kéo
        resetGlossaryTermForm();
        toggleAddTermDrawer(false);

        // Đặt từ khóa tìm kiếm vào thuật ngữ vừa thêm để người dùng nhìn thấy ngay
        const searchInput = document.getElementById("glossarySearchInput");
        if (searchInput) {
            searchInput.value = en;
            onGlossarySearch(en);
        }
    } catch (err) {
        showToastAlert(`❌ Lỗi thêm thuật ngữ: ${err.message}`);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove("loading");
        }
    }
}

/**
 * Render menu "Bộ lọc", thanh chip lọc nhanh và thanh mô tả trạng thái lọc (với số lượng động theo từ khóa)
 */
function renderGlossaryCategories() {
    const menu = document.getElementById("glossaryFilterMenu");
    const btn = document.getElementById("glossaryFilterBtn");
    const bar = document.getElementById("glossaryFilterBar");
    const statusBar = document.getElementById("glossaryFilterStatus");
    if (!menu || !btn) return;

    const matchedAll = searchGlossaryTerms(glossarySearchTerm, "ALL");
    const counts = {};
    matchedAll.forEach(t => {
        const id = glossaryGroupOf(t, allGlossaryTerms);
        counts[id] = (counts[id] || 0) + 1;
    });

    const items = [
        {
            id: "ALL",
            label: "Tất cả nhóm",
            shortLabel: "Tất cả",
            labelEn: "All",
            desc: "Hiển thị toàn bộ từ điển chuẩn",
            count: matchedAll.length
        }
    ].concat(getGlossaryGroups().map(g => ({
        id: g.id,
        label: g.label,
        shortLabel: g.shortLabel || g.label,
        labelEn: g.labelEn,
        desc: g.desc || g.labelEn,
        count: counts[g.id] || 0
    })));

    menu.innerHTML = items.map(c => {
        const active = activeGlossaryCategory === c.id;
        return `
        <button type="button" role="menuitemradio" aria-checked="${active}"
                class="glossary-filter-item pill-g-${c.id} ${active ? 'active' : ''} ${c.count === 0 ? 'is-empty' : ''}"
                data-group="${c.id}" title="${escapeHtml(c.label + ' — ' + c.desc)}"
                onclick="chooseGlossaryFilter('${c.id}')">
            <span class="item-dot" aria-hidden="true"></span>
            <span class="item-text">
                <span class="item-label">${escapeHtml(c.label)}</span>
                <span class="item-desc">${escapeHtml(c.desc)}</span>
            </span>
            <span class="item-count">${c.count}</span>
            <span class="item-check" aria-hidden="true"></span>
        </button>`;
    }).join('');

    if (bar) {
        bar.innerHTML = items.map(c => {
            const active = activeGlossaryCategory === c.id;
            return `
            <button type="button" role="tab" aria-selected="${active}"
                    class="glossary-filter-chip pill-g-${c.id} ${active ? 'active' : ''} ${c.count === 0 ? 'is-empty' : ''}"
                    data-group="${c.id}" title="${escapeHtml(c.label + ' — ' + c.desc)}"
                    onclick="setGlossaryCategory('${c.id}')">
                <span class="item-dot" aria-hidden="true"></span>
                <span class="chip-label">${escapeHtml(c.shortLabel)}</span>
                <span class="chip-count">${c.count}</span>
            </button>`;
        }).join('');
    }

    const current = items.find(c => c.id === activeGlossaryCategory && c.id !== "ALL") || null;
    const value = document.getElementById("glossaryFilterValue");
    const clear = document.getElementById("glossaryFilterClear");
    btn.classList.toggle("has-filter", !!current);
    btn.setAttribute("aria-label", current ? `Bộ lọc: ${current.label}` : "Bộ lọc");
    if (value) {
        value.className = "filter-btn-value" + (current ? ` pill-g-${current.id}` : "");
        value.hidden = !current;
        value.innerHTML = current
            ? `<span class="item-dot" aria-hidden="true"></span><span class="value-text">${escapeHtml(current.shortLabel)}</span>`
            : "";
    }
    if (clear) clear.hidden = !current;

    if (statusBar) {
        if (current || glossarySearchTerm) {
            const activeCount = current ? current.count : matchedAll.length;
            const titleText = current ? current.label : "Tìm kiếm toàn bộ từ điển";
            const descText = current ? current.desc : `Đang lọc theo từ khóa "${glossarySearchTerm}"`;
            statusBar.className = `glossary-filter-status pill-g-${current ? current.id : 'ALL'}`;
            statusBar.hidden = false;
            statusBar.innerHTML = `
                <span class="status-dot" aria-hidden="true"></span>
                <span class="status-info">
                    <strong>${escapeHtml(titleText)}</strong>: ${escapeHtml(descText)}
                    <span class="status-count">(${activeCount} mục)</span>
                </span>
                ${current ? `<button type="button" class="status-reset-btn" onclick="setGlossaryCategory('ALL')">Hiện tất cả</button>` : ''}
            `;
        } else {
            statusBar.hidden = true;
            statusBar.innerHTML = "";
        }
    }
}

function isGlossaryFilterMenuOpen() {
    const menu = document.getElementById("glossaryFilterMenu");
    return !!menu && !menu.hidden;
}

function openGlossaryFilterMenu() {
    const menu = document.getElementById("glossaryFilterMenu");
    const btn = document.getElementById("glossaryFilterBtn");
    const box = document.getElementById("glossaryFilter");
    if (!menu || !btn) return;
    menu.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    if (box) box.classList.add("open");
    fitGlossaryFilterMenu(menu);
    const target = menu.querySelector(".glossary-filter-item.active") || menu.querySelector(".glossary-filter-item");
    if (target) target.focus({ preventScroll: true });
}

/** Giới hạn chiều cao menu theo khoảng trống còn lại trong khung từ điển (menu cuộn được). */
function fitGlossaryFilterMenu(menu) {
    const host = menu.closest(".glossary-modal-panel") || document.documentElement;
    const space = host.getBoundingClientRect().bottom - menu.getBoundingClientRect().top - 14;
    menu.style.maxHeight = `${Math.max(160, Math.floor(space))}px`;
}

function closeGlossaryFilterMenu(returnFocus) {
    const menu = document.getElementById("glossaryFilterMenu");
    const btn = document.getElementById("glossaryFilterBtn");
    const box = document.getElementById("glossaryFilter");
    if (!menu || menu.hidden) return;
    menu.hidden = true;
    if (btn) {
        btn.setAttribute("aria-expanded", "false");
        if (returnFocus) btn.focus({ preventScroll: true });
    }
    if (box) box.classList.remove("open");
}

function toggleGlossaryFilterMenu() {
    if (isGlossaryFilterMenuOpen()) closeGlossaryFilterMenu(false);
    else openGlossaryFilterMenu();
}

function chooseGlossaryFilter(id) {
    setGlossaryCategory(id);
    closeGlossaryFilterMenu(true);
}

// Đóng menu khi bấm ra ngoài; phím mũi tên / Esc trong menu.
document.addEventListener("click", event => {
    if (!isGlossaryFilterMenuOpen()) return;
    const box = document.getElementById("glossaryFilter");
    if (box && !box.contains(event.target)) closeGlossaryFilterMenu(false);
});

document.addEventListener("keydown", event => {
    if (!isGlossaryFilterMenuOpen()) return;
    const menu = document.getElementById("glossaryFilterMenu");
    const items = Array.from(menu.querySelectorAll(".glossary-filter-item"));
    const index = items.indexOf(document.activeElement);
    if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeGlossaryFilterMenu(true);
    } else if (event.key === "ArrowDown") {
        event.preventDefault();
        items[(index + 1) % items.length].focus({ preventScroll: true });
    } else if (event.key === "ArrowUp") {
        event.preventDefault();
        items[(index - 1 + items.length) % items.length].focus({ preventScroll: true });
    } else if (event.key === "Home") {
        event.preventDefault();
        items[0].focus({ preventScroll: true });
    } else if (event.key === "End") {
        event.preventDefault();
        items[items.length - 1].focus({ preventScroll: true });
    } else if (event.key === "Tab") {
        closeGlossaryFilterMenu(false);
    }
}, true);

function setGlossaryCategory(catId) {
    activeGlossaryCategory = catId;
    glossaryVisibleLimit = GLOSSARY_PAGE_SIZE;
    renderGlossaryCategories();
    renderGlossaryList();
}

function showMoreGlossaryTerms() {
    glossaryVisibleLimit += GLOSSARY_PAGE_SIZE;
    renderGlossaryList();
}

function onGlossarySearch(val) {
    glossarySearchTerm = (val || "").trim();
    glossaryVisibleLimit = GLOSSARY_PAGE_SIZE;
    const clearBtn = document.getElementById("glossarySearchClear");
    if (clearBtn) {
        clearBtn.style.display = glossarySearchTerm ? "flex" : "none";
    }
    renderGlossaryCategories();
    renderGlossaryList();
}

function clearGlossarySearch() {
    const input = document.getElementById("glossarySearchInput");
    if (input) {
        input.value = "";
        input.focus();
    }
    onGlossarySearch("");
}

/**
 * Render danh sách thẻ thuật ngữ
 */
function renderGlossaryList() {
    const container = document.getElementById("glossaryListContainer");
    if (!container) return;

    const filtered = searchGlossaryTerms(glossarySearchTerm, activeGlossaryCategory);

    // Cập nhật nhãn trạng thái đếm số lượng
    const badge = document.getElementById("glossaryTotalBadge");
    if (badge) {
        if (glossarySearchTerm || activeGlossaryCategory !== "ALL") {
            badge.innerText = `${filtered.length} / ${allGlossaryTerms.length} Mục`;
        } else {
            badge.innerText = `${allGlossaryTerms.length} Mục`;
        }
    }

    if (filtered.length === 0) {
        const emptyAddLabel = glossarySearchTerm
            ? `➕ Thêm "${escapeHtml(glossarySearchTerm)}" Vào Từ Điển`
            : "➕ Thêm Thuật Ngữ Mới";
        container.innerHTML = `<div class="glossary-empty-state">
            <div class="empty-icon">${tramIcon("search")}</div>
            <p class="empty-title">${activeGlossaryCategory !== "ALL" ? "Không có thuật ngữ nào trong nhóm này khớp với tìm kiếm!" : "Không tìm thấy thuật ngữ phù hợp!"}</p>
            <p class="empty-desc">
                Bạn có thể thử tìm bằng từ tiếng Anh, tiếng Việt (có dấu hoặc không dấu), hoặc bấm <b>"+ Thêm Thuật Ngữ"</b> để lưu một mục mới trên máy.
            </p>
            <button class="btn-action-primary empty-add-btn" onclick="toggleAddTermDrawer(true)">
                <span>${emptyAddLabel}</span>
            </button>
        </div>`;
        return;
    }

    const visible = filtered.slice(0, glossaryVisibleLimit);
    glossaryRenderTerms.clear();
    visible.forEach(item => glossaryRenderTerms.set(glossaryTermKey(item), item));

    const cardsHtml = visible.map(item => {
        const encodedKey = encodeURIComponent(glossaryTermKey(item));
        return `
        <div class="glossary-card">
            <div class="glossary-card-topbar">
                ${renderGlossaryGroupBadge(item)}
                <div class="glossary-card-actions">
                    <button class="glossary-action-btn btn-copy" onclick="handleCopyTermByKey(this, '${encodedKey}')" title="Sao chép bản dịch vào bộ nhớ tạm">
                        <span class="btn-act-icon">${tramIcon("copy")}</span>
                        <span class="btn-act-text">Sao chép</span>
                    </button>
                    <button class="glossary-action-btn action-edit" onclick="openGlossaryEditByKey('${encodedKey}')" title="Chỉnh sửa thuật ngữ này trên máy">
                        <span class="btn-act-icon">✎</span>
                        <span class="btn-act-text">Chỉnh sửa</span>
                    </button>
                </div>
            </div>

            <div class="glossary-card-body">
                <div class="glossary-pair-en">
                    <span class="pair-label">EN</span>
                    <span class="pair-text glossary-term-en">${highlightGlossaryMatch(item.en, glossarySearchTerm)}</span>
                </div>
                <div class="glossary-pair-arrow">➔</div>
                <div class="glossary-pair-vi">
                    <span class="pair-label">VI</span>
                    <span class="pair-text glossary-term-vi">${highlightGlossaryMatch(item.vi, glossarySearchTerm)}</span>
                </div>
            </div>

            ${item.notes ? `
                <div class="glossary-card-notes">
                    <span class="notes-icon">${tramIcon('info')}</span>
                    <span class="notes-text">${highlightGlossaryMatch(item.notes, glossarySearchTerm)}</span>
                </div>
            ` : ''}
        </div>`;
    }).join('');

    const remaining = filtered.length - visible.length;
    const moreHtml = remaining > 0 ? `
        <div class="glossary-load-more-wrap">
            <button type="button" class="glossary-load-more-btn" onclick="showMoreGlossaryTerms()">
                Xem thêm ${Math.min(remaining, GLOSSARY_PAGE_SIZE)} mục nữa (còn ${remaining} / ${filtered.length} mục)
            </button>
        </div>
    ` : '';

    container.innerHTML = cardsHtml + moreHtml;
}

function renderGlossaryGroupBadge(item) {
    const groupId = glossaryGroupOf(item, allGlossaryTerms);
    const group = getGlossaryGroupById(groupId);
    const label = group ? group.label : "Thuật ngữ";
    const sub = typeof getGlossarySubTypeLabel === "function" ? getGlossarySubTypeLabel(item) : "";
    const showSub = sub && sub.toLowerCase() !== label.toLowerCase();
    const title = group ? `${group.label} — ${group.desc}` : label;
    return `<span class="glossary-badge-group">
        <span class="glossary-term-badge cat-group-${group ? group.id : "default"}" title="${escapeHtml(title)}">${escapeHtml(label)}</span>
        ${showSub ? `<span class="glossary-subtype-tag">${escapeHtml(sub)}</span>` : ""}
    </span>`;
}

function handleCopyTermByKey(btn, encodedKey) {
    const term = glossaryRenderTerms.get(decodeURIComponent(encodedKey || ""));
    if (term) handleCopyTermClick(btn, term.vi || "");
}

/**
 * Xử lý sao chép từ và hiển thị phản hồi trên nút
 */
function handleCopyTermClick(btn, text) {
    copyGlossaryTerm(text);
    if (!btn) return;
    const originalHtml = btn.innerHTML;
    btn.classList.add("copied");
    btn.innerHTML = `<span>✓</span> <span>Đã chép!</span>`;
    setTimeout(() => {
        btn.classList.remove("copied");
        btn.innerHTML = originalHtml;
    }, 1500);
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
        tray.innerHTML = `<span style="font-size:0.82rem; color:var(--text-sub); padding:6px 8px; display:inline-flex; align-items:center; gap:6px;">
            ${tramIcon("search")} Không tìm thấy thuật ngữ nào khớp với "${escapeHtml(term)}". 
            <button class="quick-add-link-btn" onclick="openGlossaryModal(); setTimeout(() => { toggleAddTermDrawer(true); const enIn = document.getElementById('inputTermEn'); if(enIn) enIn.value='${escapeHtml(term)}'; }, 150);">
                ➕ Thêm vào từ điển?
            </button>
        </span>`;
        return;
    }

    tray.style.display = "flex";
    tray.innerHTML = matches.slice(0, 20).map(item => {
        const grp = getGlossaryGroupById(glossaryGroupOf(item, allGlossaryTerms));
        const grpName = grp ? grp.label : (item.category || "Thuật ngữ");
        const encodedVi = encodeURIComponent(item.vi || "");
        return `
        <div class="glossary-suggestion-chip" 
             title="[${escapeHtml(grpName)}] ${escapeHtml(item.en)} ➔ ${escapeHtml(item.vi)}${item.notes ? ' (' + escapeHtml(item.notes) + ')' : ''}"
             onclick="insertGlossaryTerm(decodeURIComponent('${encodedVi}'));">
            <span class="chip-en">${escapeHtml(item.en)}</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-vi">${escapeHtml(item.vi)}</span>
        </div>`;
    }).join('');
}

function clearQuickGlossarySearch() {
    const input = document.getElementById("quickGlossaryInput");
    if (input) input.value = "";
    onQuickGlossarySearch("");
}
