/**
 * GlossaryModel.js
 * Quản lý thuật ngữ, tra cứu, phân loại và thuật toán quét gợi ý danh từ trong câu
 */

let allGlossaryTerms = [];
let activeGlossaryCategory = "ALL";
let glossarySearchTerm = "";

async function loadGlossaryTerms(refresh = false) {
    try {
        let data = null;
        if (!refresh) {
            try {
                const res = await fetch("/api/glossary");
                if (res.ok) data = await res.json();
            } catch (_) {}
            if (!data) {
                const res = await fetch("data/glossary.json");
                if (res.ok) data = await res.json();
            }
        } else {
            const res = await fetch("/api/glossary?refresh=true");
            if (res.ok) data = await res.json();
        }
        if (data && data.terms) {
            allGlossaryTerms = data.terms;
            // Sort by English length descending so longer compound phrases match before single words
            allGlossaryTerms.sort((a, b) => b.en.length - a.en.length);
            updateGlossaryCountBadge();
            if (document.getElementById("glossaryModal") && document.getElementById("glossaryModal").classList.contains("open")) {
                renderGlossaryCategories();
                renderGlossaryList();
            }
            if (filteredLines.length > 0 && filteredLines[currentIndex]) {
                renderGlossarySuggestions(filteredLines[currentIndex].en);
            }
        }
    } catch (e) {
        console.error("Lỗi tải từ điển thuật ngữ:", e);
    }
}

// Detection algorithm: match words/phrases with regex word boundaries and plural support
function detectGlossaryMatches(text) {
    if (!text || !allGlossaryTerms || allGlossaryTerms.length === 0) return [];
    const matches = [];
    const matchedEn = new Set();

    for (const item of allGlossaryTerms) {
        if (!item.en) continue;
        const enLower = item.en.toLowerCase();
        if (matchedEn.has(enLower)) continue;

        // Escape regex special chars
        const escaped = item.en.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Word boundary with optional plural suffix (s / es)
        const regex = new RegExp(`\\b${escaped}(?:s|es)?\\b`, 'i');
        if (regex.test(text)) {
            matches.push(item);
            matchedEn.add(enLower);
        }
    }
    return matches;
}

async function syncGlossaryFromSheets() {
    const btn = document.getElementById("btnSyncGlossary");
    if (btn) btn.classList.add("syncing");
    showToastAlert("🔄 Đang đồng bộ từ điển từ Google Sheets...");

    try {
        const res = await fetch("/api/sync_glossary", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        if (data.success) {
            await loadGlossaryTerms();
            renderGlossaryCategories();
            renderGlossaryList();
            showToastAlert(`🎉 ${data.message}`);
        } else {
            showToastAlert(`❌ Lỗi đồng bộ: ${data.message || 'Thất bại'}`);
        }
    } catch (e) {
        showToastAlert(`❌ Ngoại lệ đồng bộ: ${e.message}`);
    } finally {
        if (btn) btn.classList.remove("syncing");
    }
}
