/**
 * GlossaryView.js
 * Giao diện Từ Điển Thuật Ngữ Chuẩn: Trình diễn thẻ thuật ngữ cao cấp,
 * hỗ trợ đa nền tảng PC & Android, khay thêm thuật ngữ mới và tìm kiếm tức thì.
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
        
        let tooltip = `[${item.category}] ${item.en} ➔ ${item.vi}`;
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
    const category = selectCat ? selectCat.value.trim() : "Chung";
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
        await addGlossaryTerm({
            en: en,
            vi: vi,
            category: category,
            notes: notes
        });

        // Reset form và đóng ngăn kéo
        if (inputEn) inputEn.value = "";
        if (inputVi) inputVi.value = "";
        if (inputNotes) inputNotes.value = "";
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
 * Render thanh lọc danh mục
 */
function renderGlossaryCategories() {
    const tray = document.getElementById("glossaryCatPills");
    if (!tray) return;

    const counts = {};
    allGlossaryTerms.forEach(t => {
        const cat = t.category || "Chung";
        counts[cat] = (counts[cat] || 0) + 1;
    });

    const catList = [
        { id: "ALL", label: `Tất cả (${allGlossaryTerms.length})` }
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
        if (!presetCats.includes(c) && c !== "ALL") {
            catList.push({ id: c, label: `${c} (${counts[c]})` });
        }
    });

    tray.innerHTML = catList.map(c => `
        <button class="glossary-cat-pill ${activeGlossaryCategory === c.id ? 'active' : ''}" onclick="setGlossaryCategory('${c.id}')">
            ${c.label}
        </button>
    `).join('');
}

function setGlossaryCategory(catId) {
    activeGlossaryCategory = catId;
    renderGlossaryCategories();
    renderGlossaryList();
}

function onGlossarySearch(val) {
    glossarySearchTerm = (val || "").trim();
    const clearBtn = document.getElementById("glossarySearchClear");
    if (clearBtn) {
        clearBtn.style.display = glossarySearchTerm ? "flex" : "none";
    }
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
        container.innerHTML = `<div class="glossary-empty-state">
            <div class="empty-icon">${tramIcon("search")}</div>
            <p class="empty-title">Không tìm thấy thuật ngữ phù hợp!</p>
            <p class="empty-desc">
                Bạn có thể thử tìm bằng từ tiếng Anh, tiếng Việt (có dấu hoặc không dấu), hoặc bấm <b>"+ Thêm Thuật Ngữ"</b> để đóng góp từ mới.
            </p>
            <button class="btn-action-primary empty-add-btn" onclick="toggleAddTermDrawer(true)">
                <span>➕ Thêm "${escapeHtml(glossarySearchTerm)}" Vào Từ Điển</span>
            </button>
        </div>`;
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="glossary-card">
            <div class="glossary-card-topbar">
                <span class="glossary-term-badge cat-${getCategoryCssClass(item.category)}">${escapeHtml(item.category || 'Chung')}</span>
                <div class="glossary-card-actions">
                    <button class="glossary-action-btn btn-copy" onclick="handleCopyTermClick(this, '${escapeHtml(item.vi)}')" title="Sao chép bản dịch vào bộ nhớ tạm">
                        <span class="btn-act-icon">${tramIcon("copy")}</span>
                        <span class="btn-act-text">Sao chép</span>
                    </button>
                    <button class="glossary-action-btn action-insert" onclick="insertGlossaryFromModal('${escapeHtml(item.vi)}')" title="Chèn trực tiếp vào ô dịch câu hiện tại">
                        <span class="btn-act-icon">➕</span>
                        <span class="btn-act-text">Chèn</span>
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
        </div>
    `).join('');
}

function getCategoryCssClass(category) {
    if (!category) return "default";
    const c = category.toLowerCase();
    if (c.includes("cốt truyện") || c.includes("thế giới")) return "story";
    if (c.includes("chiến đấu") || c.includes("kỹ năng")) return "combat";
    if (c.includes("nhân vật") || c.includes("đại từ")) return "character";
    if (c.includes("quái vật") || c.includes("boss")) return "monster";
    if (c.includes("hệ thống") || c.includes("giao diện")) return "system";
    if (c.includes("địa danh") || c.includes("bản đồ")) return "location";
    if (c.includes("vật phẩm") || c.includes("trang bị")) return "item";
    return "default";
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
    tray.innerHTML = matches.slice(0, 20).map(item => `
        <div class="glossary-suggestion-chip" 
             title="[${item.category}] ${item.en} ➔ ${item.vi}${item.notes ? ' (' + item.notes + ')' : ''}"
             onclick="insertGlossaryTerm('${escapeHtml(item.vi)}');">
            <span class="chip-en">${escapeHtml(item.en)}</span>
            <span class="chip-arrow">➔</span>
            <span class="chip-vi">${escapeHtml(item.vi)}</span>
        </div>
    `).join('');
}

function clearQuickGlossarySearch() {
    const input = document.getElementById("quickGlossaryInput");
    if (input) input.value = "";
    onQuickGlossarySearch("");
}
