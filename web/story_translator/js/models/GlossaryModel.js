/**
 * GlossaryModel.js
 * Quản lý thuật ngữ, tra cứu thông minh, thêm thuật ngữ mới và tự động đồng bộ Google Sheets
 */

let allGlossaryTerms = [];
let activeGlossaryCategory = "ALL";
let glossarySearchTerm = "";

/**
 * Xóa dấu tiếng Việt phục vụ tra cứu linh hoạt (không dấu vẫn tìm ra có dấu)
 */
function removeVietnameseTones(str) {
    if (!str) return "";
    str = str.toLowerCase();
    str = str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    str = str.replace(/[đĐ]/g, "d");
    return str;
}

/**
 * Chuẩn hóa và làm sạch mảng thuật ngữ, bỏ dòng tiêu đề và gộp cache offline
 */
function normalizeLoadedGlossaryTerms(rawList) {
    if (!rawList || !Array.isArray(rawList)) return [];

    const cleaned = [];
    const seenEn = new Set();

    for (const item of rawList) {
        if (!item) continue;
        let en = (item.en || item.term_en || item.source || "").trim();
        let vi = (item.vi || item.term_vi || item.target || "").trim();
        let cat = (item.category || item.group || "Chung").trim();
        let notes = (item.notes || "").trim();
        let status = (item.status || "approved").trim();

        // Xử lý nếu gặp dữ liệu dạng ngược (category chứa tên tiếng Anh)
        if (!en && cat && vi && cat.length > 0 && !cat.startsWith("---")) {
            en = cat;
            cat = "Chung";
        }

        // Bỏ qua các dòng tiêu đề bảng tính
        if (!en || en.startsWith("---") || en.startsWith("BẢNG THỐNG NHẤT") || en.startsWith("Danh từ")) {
            continue;
        }

        const enKey = item.id ? `id:${item.id}` : `en:${en.toLowerCase()}`;
        if (seenEn.has(enKey)) continue;
        seenEn.add(enKey);

        cleaned.push({
            id: item.id || "",
            en: en,
            vi: vi,
            category: cat || "Chung",
            raw_category: cat || "Chung",
            notes: notes,
            status: status
        });
    }

    // Áp dụng các chỉnh sửa cục bộ trước đó; Sheet vẫn là nguồn đọc mặc định.
    try {
        const localCustoms = JSON.parse(localStorage.getItem("ss_custom_glossary") || "[]");
        if (Array.isArray(localCustoms)) {
            for (const c of localCustoms) {
                if (!c || !c.en) continue;
                const index = c.id
                    ? cleaned.findIndex(item => item.id && item.id === c.id)
                    : cleaned.findIndex(item => item.en.toLowerCase() === c.en.toLowerCase());
                if (index >= 0) cleaned[index] = { ...cleaned[index], ...c };
                else if (!seenEn.has(`en:${c.en.toLowerCase()}`)) {
                    seenEn.add(`en:${c.en.toLowerCase()}`);
                    cleaned.push(c);
                }
            }
        }
    } catch (_) {}

    return cleaned;
}

/**
 * Nạp danh sách thuật ngữ từ API hoặc bản sao nội bộ data/glossary.json
 */
async function loadGlossaryTerms(refresh = false) {
    try {
        let loadedTerms = null;

        // 1. Thử API local
        try {
            const res = await fetch("/api/glossary", { cache: refresh ? "no-store" : "default" });
            if (res.ok) {
                const text = await res.text();
                if (text && text.trim().length > 0) {
                    const parsed = JSON.parse(text);
                    loadedTerms = Array.isArray(parsed) ? parsed : (parsed.terms || null);
                }
            }
        } catch (_) {}

        // 2. Thử tệp data/glossary.json
        if (!loadedTerms) {
            try {
                const res = await fetch("data/glossary.json", { cache: refresh ? "no-store" : "default" });
                if (res.ok) {
                    const text = await res.text();
                    if (text && text.trim().length > 0) {
                        const parsed = JSON.parse(text);
                        loadedTerms = Array.isArray(parsed) ? parsed : (parsed.terms || null);
                    }
                }
            } catch (_) {}
        }

        if (loadedTerms && Array.isArray(loadedTerms) && loadedTerms.length > 0) {
            allGlossaryTerms = normalizeLoadedGlossaryTerms(loadedTerms);
            // Chuẩn hóa và sắp xếp theo độ dài tiếng Anh giảm dần (để cụm từ dài được ưu tiên quét trước từ đơn)
            allGlossaryTerms.sort((a, b) => ((b.en || "").length) - ((a.en || "").length));
            updateGlossaryCountBadge();
            if (document.getElementById("glossaryModal") && document.getElementById("glossaryModal").classList.contains("open")) {
                renderGlossaryCategories();
                renderGlossaryList();
            }
            if (typeof filteredLines !== "undefined" && filteredLines.length > 0 && filteredLines[currentIndex]) {
                renderGlossarySuggestions(filteredLines[currentIndex].en);
            }
            console.log(`[GlossaryModel] Đã nạp ${allGlossaryTerms.length} thuật ngữ thành công.`);
        }
    } catch (e) {
        console.error("Lỗi nạp từ điển thuật ngữ:", e);
    }
}

/**
 * Tra cứu thuật ngữ theo từ khóa (hỗ trợ cả tiếng Anh, tiếng Việt có dấu/không dấu, ghi chú)
 */
function searchGlossaryTerms(searchTerm, category = "ALL") {
    if (!allGlossaryTerms || allGlossaryTerms.length === 0) return [];
    
    let list = allGlossaryTerms;
    if (category && category !== "ALL") {
        list = list.filter(t => t.category === category);
    }

    if (!searchTerm || !searchTerm.trim()) {
        return list;
    }

    const rawTerm = searchTerm.trim().toLowerCase();
    const cleanTerm = removeVietnameseTones(rawTerm);

    return list.filter(item => {
        const en = (item.en || "").toLowerCase();
        const vi = (item.vi || "").toLowerCase();
        const viClean = removeVietnameseTones(vi);
        const notes = (item.notes || "").toLowerCase();
        const notesClean = removeVietnameseTones(notes);
        const cat = (item.category || "").toLowerCase();

        return en.includes(rawTerm) ||
               vi.includes(rawTerm) ||
               viClean.includes(cleanTerm) ||
               notes.includes(rawTerm) ||
               notesClean.includes(cleanTerm) ||
               cat.includes(rawTerm);
    });
}

/**
 * Quét tự động danh từ thuật ngữ xuất hiện trong câu tiếng Anh
 */
function detectGlossaryMatches(text) {
    if (!text || !allGlossaryTerms || allGlossaryTerms.length === 0) return [];
    const matches = [];
    const matchedEn = new Set();

    for (const item of allGlossaryTerms) {
        if (!item.en) continue;
        const enLower = item.en.toLowerCase();
        if (matchedEn.has(enLower)) continue;

        // Thoát ký tự đặc biệt của regex
        const escaped = item.en.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Quét ranh giới từ kèm dạng số nhiều s/es
        const regex = new RegExp(`\\b${escaped}(?:s|es)?\\b`, 'i');
        if (regex.test(text)) {
            matches.push(item);
            matchedEn.add(enLower);
        }
    }
    return matches;
}

/**
 * Thêm thuật ngữ mới và tự động đồng bộ lên Google Sheets
 * @param {Object} termData - { en, vi, category, notes }
 * @returns {Promise<{success: boolean, message: string, term: Object}>}
 */
async function addGlossaryTerm(termData) {
    const en = (termData.en || "").trim();
    const vi = (termData.vi || "").trim();
    const category = (termData.category || "").trim() || "Chung";
    const notes = (termData.notes || "").trim();
    const translator = (typeof currentTranslator !== "undefined" && currentTranslator) ? currentTranslator : "Nhà Thám Hiểm";

    if (!en || !vi) {
        throw new Error("Vui lòng điền đầy đủ Thuật ngữ tiếng Anh (EN) và Bản dịch tiếng Việt (VI)!");
    }

    // 1. Cập nhật lạc quan (Optimistic UI Update) ngay trên giao diện
    let existingIndex = allGlossaryTerms.findIndex(t => (t.en || "").trim().toLowerCase() === en.toLowerCase());
    let newOrUpdatedTerm = {
        id: termData.id || "",
        en: en,
        vi: vi,
        category: category,
        raw_category: category,
        notes: notes,
        status: "approved"
    };

    if (existingIndex >= 0) {
        allGlossaryTerms[existingIndex] = newOrUpdatedTerm;
    } else {
        allGlossaryTerms.unshift(newOrUpdatedTerm);
    }

    // Sắp xếp lại theo độ dài EN giảm dần
    allGlossaryTerms.sort((a, b) => ((b.en || "").length) - ((a.en || "").length));
    updateGlossaryCountBadge();
    renderGlossaryCategories();
    renderGlossaryList();
    if (typeof filteredLines !== "undefined" && filteredLines.length > 0 && filteredLines[currentIndex]) {
        renderGlossarySuggestions(filteredLines[currentIndex].en);
    }

    // Lưu vào cache offline localStorage
    persistLocalGlossaryTerm(newOrUpdatedTerm, termData.previous_en || "");

    // 2. Gửi yêu cầu đồng bộ qua backend
    let syncSuccess = false;
    let syncMessage = "";

    const payload = {
        action: "add_glossary_term",
        en: en,
        vi: vi,
        category: category,
        notes: notes,
        status: "approved",
        translator: translator
    };

    // Google Sheets chỉ được truy cập từ backend.
    try {
        const res = await fetch("/api/add_glossary_term", {
            method: "POST",
            headers: { "Content-Type": "application/json;charset=utf-8" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const text = await res.text();
            if (text && text.trim().length > 0) {
                try {
                    const data = JSON.parse(text);
                    if (data && (data.success || data.term)) {
                        syncSuccess = true;
                        syncMessage = data.message || "Đã lưu và đồng bộ Google Sheets thành công!";
                    }
                } catch (_) {}
            }
        }
    } catch (_) {}

    if (syncSuccess) {
        showToastAlert(`🎉 ${syncMessage || 'Đã thêm thuật ngữ và đồng bộ Google Sheets!'}`);
    } else {
        showToastAlert(`💾 Chỉ lưu trên máy; chưa gửi lên máy chủ. Hãy thử đồng bộ lại khi có mạng.`);
    }

    return {
        success: true,
        message: syncMessage || "Chỉ lưu thuật ngữ trên máy; chưa đồng bộ.",
        term: newOrUpdatedTerm
    };
}

function persistLocalGlossaryTerm(term, previousEn = "") {
    try {
        const localCustoms = JSON.parse(localStorage.getItem("ss_custom_glossary") || "[]");
        const index = localCustoms.findIndex(item =>
            (term.id && item.id === term.id) ||
            (previousEn && (item.en || "").toLowerCase() === previousEn.toLowerCase()) ||
            (!previousEn && !term.id && (item.en || "").toLowerCase() === term.en.toLowerCase())
        );
        if (index >= 0) localCustoms[index] = term;
        else localCustoms.push(term);
        localStorage.setItem("ss_custom_glossary", JSON.stringify(localCustoms));
    } catch (_) {}
}

async function updateGlossaryTerm(termData) {
    const en = (termData.en || "").trim();
    const vi = (termData.vi || "").trim();
    if (!en || !vi) throw new Error("Thuật ngữ EN và bản dịch VI không được để trống.");
    const index = allGlossaryTerms.findIndex(item =>
        (termData.id && item.id === termData.id) ||
        (!termData.id && item.en.toLowerCase() === (termData.previous_en || en).toLowerCase())
    );
    if (index < 0) throw new Error("Không tìm thấy thuật ngữ cần chỉnh sửa.");
    const updated = {
        ...allGlossaryTerms[index],
        id: termData.id || allGlossaryTerms[index].id || "",
        en,
        vi,
        category: (termData.category || "Chung").trim() || "Chung",
        raw_category: (termData.category || "Chung").trim() || "Chung",
        notes: (termData.notes || "").trim(),
        status: allGlossaryTerms[index].status || "approved"
    };
    allGlossaryTerms[index] = updated;
    persistLocalGlossaryTerm(updated, termData.previous_en || "");
    allGlossaryTerms.sort((a, b) => (b.en || "").length - (a.en || "").length);
    updateGlossaryCountBadge();
    renderGlossaryCategories();
    renderGlossaryList();
    showToastAlert("✏️ Đã cập nhật thuật ngữ trên máy. Google Sheet hiện chỉ đọc.");
    return { success: true, term: updated };
}

/**
 * Đồng bộ thuật ngữ thời gian thực từ Google Sheets (Bảo vệ tuyệt đối khỏi lỗi Unexpected end of JSON)
 */
async function syncGlossaryFromSheets() {
    const btn = document.getElementById("btnSyncGlossary");
    if (btn) btn.classList.add("syncing");
    showToastAlert("🔄 Đang đồng bộ từ điển từ Google Sheets...");

    let syncedTerms = null;
    let message = "";

    try {
        // Chỉ gọi API backend.
        try {
            const res = await fetch("/api/sync_glossary", { cache: "no-store" });
            if (res.ok) {
                const text = await res.text();
                if (text && text.trim().length > 0) {
                    try {
                        const data = JSON.parse(text);
                        if (data && (data.terms || Array.isArray(data))) {
                            syncedTerms = Array.isArray(data) ? data : data.terms;
                            message = data.message || `Đã đồng bộ ${syncedTerms.length} thuật ngữ!`;
                        }
                    } catch (_) {}
                }
            }
        } catch (_) {}

        if (syncedTerms && Array.isArray(syncedTerms) && syncedTerms.length > 0) {
            allGlossaryTerms = normalizeLoadedGlossaryTerms(syncedTerms);
            allGlossaryTerms.sort((a, b) => ((b.en || "").length) - ((a.en || "").length));
            updateGlossaryCountBadge();
            renderGlossaryCategories();
            renderGlossaryList();
            if (typeof filteredLines !== "undefined" && filteredLines.length > 0 && filteredLines[currentIndex]) {
                renderGlossarySuggestions(filteredLines[currentIndex].en);
            }
            showToastAlert(`🎉 ${message}`);
        } else {
            showToastAlert("❌ Không thể đồng bộ thuật ngữ, vui lòng kiểm tra kết nối mạng!");
        }
    } catch (e) {
        showToastAlert(`❌ Ngoại lệ đồng bộ: ${e.message}`);
    } finally {
        if (btn) btn.classList.remove("syncing");
    }
}
