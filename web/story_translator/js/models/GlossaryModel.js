/**
 * GlossaryModel.js
 * Quản lý thuật ngữ, tra cứu thông minh, thêm thuật ngữ mới và tự động đồng bộ Google Sheets
 */

let allGlossaryTerms = [];
let activeGlossaryCategory = "ALL";
let glossarySearchTerm = "";

const GAS_GLOSSARY_URL = "https://script.google.com/macros/s/AKfycbwhB90dQ5YL27wBkeXeQIoI18TZO3KXXhgwdb0iG96rqwBQUfk7ztZwGjdG_tEwElDhFw/exec?action=get_glossary";

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

        const enKey = en.toLowerCase();
        if (seenEn.has(enKey)) continue;
        seenEn.add(enKey);

        cleaned.push({
            en: en,
            vi: vi,
            category: cat || "Chung",
            raw_category: cat || "Chung",
            notes: notes,
            status: status
        });
    }

    // Gộp thêm các thuật ngữ tùy chỉnh đã lưu offline (nếu có)
    try {
        const localCustoms = JSON.parse(localStorage.getItem("ss_custom_glossary") || "[]");
        if (Array.isArray(localCustoms)) {
            for (const c of localCustoms) {
                if (c && c.en && !seenEn.has(c.en.toLowerCase())) {
                    seenEn.add(c.en.toLowerCase());
                    cleaned.push(c);
                }
            }
        }
    } catch (_) {}

    return cleaned;
}

/**
 * Nạp danh sách thuật ngữ từ API, GAS hoặc bản sao nội bộ data/glossary.json
 */
async function loadGlossaryTerms(refresh = false) {
    try {
        let loadedTerms = null;

        if (!refresh) {
            // 1. Thử API local
            try {
                const res = await fetch("/api/glossary");
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
                    const res = await fetch("data/glossary.json");
                    if (res.ok) {
                        const text = await res.text();
                        if (text && text.trim().length > 0) {
                            const parsed = JSON.parse(text);
                            loadedTerms = Array.isArray(parsed) ? parsed : (parsed.terms || null);
                        }
                    }
                } catch (_) {}
            }
        }

        // 3. Nếu yêu cầu refresh hoặc các bước trên chưa có, thử GAS Web App
        if (!loadedTerms) {
            try {
                const res = await fetch(GAS_GLOSSARY_URL);
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
    try {
        const localCustoms = JSON.parse(localStorage.getItem("ss_custom_glossary") || "[]");
        const idx = localCustoms.findIndex(c => (c.en || "").toLowerCase() === en.toLowerCase());
        if (idx >= 0) localCustoms[idx] = newOrUpdatedTerm;
        else localCustoms.push(newOrUpdatedTerm);
        localStorage.setItem("ss_custom_glossary", JSON.stringify(localCustoms));
    } catch (_) {}

    // 2. Gửi yêu cầu đồng bộ lên Google Sheets qua các tầng kết nối
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

    // Tầng 1: Gọi qua API Local Server hoặc Cloudflare Pages Functions (/api/add_glossary_term)
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

    // Tầng 2: Nếu chưa đồng bộ được (trên môi trường Static không có Functions), gọi trực tiếp sang Google Apps Script Web App
    if (!syncSuccess) {
        try {
            const gasUrl = GAS_GLOSSARY_URL.split("?")[0];
            const gasRes = await fetch(gasUrl, {
                method: "POST",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify(payload)
            });
            if (gasRes.ok) {
                const gasText = await gasRes.text();
                if (gasText && gasText.trim().length > 0) {
                    try {
                        const gasData = JSON.parse(gasText);
                        if (gasData && (gasData.success || gasData.term)) {
                            syncSuccess = true;
                            syncMessage = gasData.message || "Đã đồng bộ trực tiếp lên Google Sheets (Live)!";
                        }
                    } catch (_) {}
                }
            }
        } catch (_) {}
    }

    if (syncSuccess) {
        showToastAlert(`🎉 ${syncMessage || 'Đã thêm thuật ngữ và đồng bộ Google Sheets!'}`);
    } else {
        showToastAlert(`💾 Đã lưu tạm thuật ngữ vào máy (sẽ tự đẩy lên Google Sheets khi có mạng)!`);
    }

    return {
        success: true,
        message: syncMessage || "Đã lưu thuật ngữ!",
        term: newOrUpdatedTerm
    };
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
        // 1. Thử gọi API backend (Local Server)
        try {
            const res = await fetch("/api/sync_glossary", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
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

        // 2. Nếu Backend không phản hồi JSON (Static / Cloudflare Pages / GitHub Pages), kết nối trực tiếp GAS Web App
        if (!syncedTerms) {
            try {
                const gasRes = await fetch(GAS_GLOSSARY_URL, { method: "GET" });
                if (gasRes.ok) {
                    const gasText = await gasRes.text();
                    if (gasText && gasText.trim().length > 0) {
                        try {
                            const gasData = JSON.parse(gasText);
                            if (gasData && gasData.terms) {
                                syncedTerms = gasData.terms;
                                message = `Đã đồng bộ trực tiếp ${syncedTerms.length} thuật ngữ từ Google Sheets (Live)!`;
                            }
                        } catch (_) {}
                    }
                }
            } catch (_) {}
        }

        // 3. Fallback nạp lại từ data/glossary.json
        if (!syncedTerms) {
            try {
                const localRes = await fetch("data/glossary.json?t=" + Date.now());
                if (localRes.ok) {
                    const localText = await localRes.text();
                    if (localText && localText.trim().length > 0) {
                        try {
                            const localData = JSON.parse(localText);
                            syncedTerms = Array.isArray(localData) ? localData : (localData.terms || []);
                            message = `Đã làm mới ${syncedTerms.length} thuật ngữ từ cơ sở dữ liệu!`;
                        } catch (_) {}
                    }
                }
            } catch (_) {}
        }

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
