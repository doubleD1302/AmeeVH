/**
 * GlossaryModel.js
 * Quản lý thuật ngữ, tra cứu thông minh, phân loại và thuật toán quét gợi ý danh từ trong câu
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
            allGlossaryTerms = loadedTerms;
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
            allGlossaryTerms = syncedTerms;
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
