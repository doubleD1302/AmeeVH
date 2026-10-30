#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to update index.html with:
1. Glossary Modal (Search, Categories, Sync from Google Sheets)
2. Translation Suggestions (Auto-detection of terms in current sentence and insertion)
"""

from pathlib import Path

INDEX_PATH = Path("StellaSora_VietHoa/web/story_translator/index.html")

def update_index_html():
    content = INDEX_PATH.read_text(encoding="utf-8")

    # 1. CSS for Glossary & Suggestions
    css_anchor = "/* ================= MODALS & POPUPS ================= */"
    css_new = """        /* ================= GLOSSARY & TRANSLATION SUGGESTIONS ================= */
        .glossary-suggestions-box {
            background: rgba(14, 28, 48, 0.85);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 14px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.05);
            animation: fadeInSuggestions 0.25s ease-out;
        }

        @keyframes fadeInSuggestions {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .suggestions-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .suggestions-title {
            font-size: 0.78rem;
            font-weight: 800;
            color: var(--gold-accent);
            letter-spacing: 0.8px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .suggestions-count {
            font-size: 0.72rem;
            color: var(--cyan-light);
            font-family: var(--font-code);
            background: rgba(56, 189, 248, 0.15);
            padding: 2px 7px;
            border-radius: 10px;
        }

        .suggestions-chips-tray {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .glossary-suggestion-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(15, 23, 42, 0.92);
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 10px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 0.88rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
            position: relative;
        }

        .glossary-suggestion-chip:hover {
            background: rgba(56, 189, 248, 0.22);
            border-color: var(--cyan-primary);
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.35);
        }

        .glossary-suggestion-chip .chip-en {
            color: var(--cyan-light);
            font-weight: 700;
            font-family: var(--font-display);
        }

        .glossary-suggestion-chip .chip-arrow {
            color: var(--text-dim);
            font-size: 0.8rem;
        }

        .glossary-suggestion-chip .chip-vi {
            color: var(--gold-light);
            font-weight: 700;
        }

        .glossary-suggestion-chip.warn {
            border-color: rgba(251, 113, 133, 0.7);
            background: rgba(251, 113, 133, 0.15);
        }

        .glossary-suggestion-chip.warn:hover {
            background: rgba(251, 113, 133, 0.28);
            border-color: var(--rose-accent);
            box-shadow: 0 4px 14px rgba(251, 113, 133, 0.4);
        }

        .chip-warn-badge {
            background: rgba(251, 113, 133, 0.35);
            color: #ffd4db;
            font-size: 0.68rem;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 6px;
            letter-spacing: 0.5px;
        }

        /* List Mode Suggestions */
        .table-glossary-tray {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 6px;
            margin: 4px 0 8px 0;
        }

        .table-glossary-label {
            font-size: 0.74rem;
            color: var(--gold-accent);
            font-weight: 700;
        }

        .table-glossary-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 0.78rem;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .table-glossary-chip:hover {
            border-color: var(--cyan-primary);
            background: rgba(56, 189, 248, 0.2);
            transform: translateY(-1px);
        }

        .table-glossary-chip.warn {
            border-color: rgba(251, 113, 133, 0.5);
            background: rgba(251, 113, 133, 0.12);
        }

        .table-glossary-chip .chip-en {
            color: var(--cyan-light);
            font-weight: 600;
        }

        .table-glossary-chip .chip-vi {
            color: var(--gold-light);
            font-weight: 700;
        }

        /* Glossary Modal Wide */
        .modal-panel.modal-panel-wide {
            max-width: 920px;
            max-height: 88vh;
            padding: 28px 32px;
        }

        .glossary-counter-badge {
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: var(--cyan-light);
            font-family: var(--font-code);
            font-size: 0.78rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 20px;
        }

        .btn-sync-glossary {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(14, 165, 233, 0.3));
            border: 1px solid rgba(56, 189, 248, 0.45);
            color: var(--cyan-light);
            font-size: 0.84rem;
            font-weight: 700;
            padding: 8px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-sync-glossary:hover {
            background: var(--cyan-primary);
            color: #000;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.5);
            transform: translateY(-1px);
        }

        .btn-sync-glossary.syncing .sync-icon {
            display: inline-block;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .glossary-toolbar {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .glossary-search-wrapper {
            position: relative;
            width: 100%;
        }

        .glossary-search-wrapper .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1rem;
            color: var(--text-dim);
            pointer-events: none;
        }

        .glossary-search-input {
            width: 100%;
            background: rgba(5, 9, 18, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 12px;
            padding: 12px 42px 12px 42px;
            color: #fff;
            font-family: var(--font-main);
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .glossary-search-input:focus {
            border-color: var(--cyan-primary);
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
            background: rgba(5, 9, 18, 0.98);
        }

        .search-clear-btn {
            position: absolute;
            right: 14px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 1rem;
            cursor: pointer;
            padding: 4px;
        }

        .search-clear-btn:hover {
            color: #fff;
        }

        .glossary-cat-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .glossary-cat-pill {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: var(--text-sub);
            font-size: 0.78rem;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
        }

        .glossary-cat-pill:hover {
            border-color: var(--cyan-primary);
            color: var(--cyan-light);
            background: rgba(56, 189, 248, 0.1);
        }

        .glossary-cat-pill.active {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--cyan-primary);
            color: #fff;
            font-weight: 700;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.35);
        }

        .glossary-cat-pill.critical-pill {
            border-color: rgba(251, 113, 133, 0.45);
            color: #fda4af;
        }

        .glossary-cat-pill.critical-pill.active {
            background: rgba(251, 113, 133, 0.25);
            border-color: var(--rose-accent);
            color: #fff;
            box-shadow: 0 0 12px rgba(251, 113, 133, 0.45);
        }

        .glossary-list-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 480px;
            overflow-y: auto;
            padding-right: 6px;
        }

        .glossary-list-container::-webkit-scrollbar {
            width: 6px;
        }

        .glossary-list-container::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.3);
            border-radius: 3px;
        }

        .glossary-card {
            background: rgba(11, 20, 36, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            padding: 14px 18px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: all 0.2s ease;
        }

        .glossary-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            background: rgba(14, 25, 46, 0.9);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        }

        .glossary-card.critical-card {
            border-color: rgba(251, 113, 133, 0.4);
            background: rgba(30, 16, 28, 0.7);
        }

        .glossary-card.critical-card:hover {
            border-color: rgba(251, 113, 133, 0.7);
            background: rgba(38, 20, 35, 0.85);
        }

        .glossary-card-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }

        .glossary-card-terms {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.02rem;
        }

        .glossary-term-en {
            font-family: var(--font-display);
            color: var(--cyan-light);
            font-weight: 700;
        }

        .glossary-term-arrow {
            color: var(--text-dim);
            font-size: 0.85rem;
        }

        .glossary-term-vi {
            color: var(--gold-light);
            font-weight: 700;
        }

        .glossary-card-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .glossary-term-badge {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: var(--cyan-light);
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 8px;
        }

        .glossary-action-btn {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: var(--text-body);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .glossary-action-btn:hover {
            background: rgba(56, 189, 248, 0.2);
            border-color: var(--cyan-primary);
            color: #fff;
        }

        .glossary-action-btn.action-insert {
            background: rgba(245, 158, 11, 0.15);
            border-color: rgba(245, 158, 11, 0.35);
            color: var(--gold-light);
        }

        .glossary-action-btn.action-insert:hover {
            background: var(--gold-accent);
            color: #000;
        }

        .glossary-card-notes {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            font-size: 0.82rem;
            line-height: 1.5;
            padding: 6px 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-sub);
        }

        .glossary-card-notes.critical-notes {
            background: rgba(251, 113, 133, 0.18);
            border-left: 3px solid var(--rose-accent);
            color: #fecdd3;
            font-weight: 600;
        }

        .notes-icon {
            flex-shrink: 0;
            font-size: 0.95rem;
        }

        .glossary-empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-dim);
            font-size: 0.95rem;
        }

        /* Light Theme Overrides for Soft-Sky */
        html:not([data-theme="dark"]) .glossary-suggestions-box {
            background: #f1f8fa;
            border-color: #c9e4ea;
        }
        html:not([data-theme="dark"]) .glossary-suggestion-chip {
            background: #fff;
            border-color: #c3e2e8;
        }
        html:not([data-theme="dark"]) .glossary-suggestion-chip .chip-en {
            color: #246d84;
        }
        html:not([data-theme="dark"]) .glossary-suggestion-chip .chip-vi {
            color: #8c6422;
        }
        html:not([data-theme="dark"]) .glossary-card {
            background: #fff;
            border-color: #d6e8ec;
        }
        html:not([data-theme="dark"]) .glossary-search-input {
            background: #fff;
            color: #29495a;
            border-color: #d2e3e8;
        }
        html:not([data-theme="dark"]) .glossary-term-en {
            color: #246d84;
        }
        html:not([data-theme="dark"]) .glossary-term-vi {
            color: #8c6422;
        }
        html:not([data-theme="dark"]) .glossary-card-notes {
            background: #f4f9f9;
            color: #496c78;
        }
        html:not([data-theme="dark"]) .glossary-cat-pill {
            background: #f6fafb;
            border-color: #dbe9ed;
            color: #527584;
        }
        html:not([data-theme="dark"]) .glossary-cat-pill.active {
            background: #c8e8ee;
            color: #285c6e;
            border-color: #79bed0;
        }

        /* ================= MODALS & POPUPS ================= */"""

    if css_anchor in content:
        content = content.replace(css_anchor, css_new, 1)
        print("[+] Added CSS styles")
    else:
        print("[-] CSS anchor not found!")

    # 2. Add suggestions box in translation input box
    box_anchor = '<div class="smart-tag-tray" id="smartTagTray"></div>\r\n                    </div>\r\n                    <textarea id="vietnameseInput"'
    box_new = '<div class="smart-tag-tray" id="smartTagTray"></div>\r\n                    </div>\r\n                    <!-- Gợi ý thuật ngữ từ điển xuất hiện trong câu -->\r\n                    <div class="glossary-suggestions-box" id="glossarySuggestionsBox" style="display:none;">\r\n                        <div class="suggestions-header">\r\n                            <span class="suggestions-title">💡 GỢI Ý THUẬT NGỮ TRONG CÂU:</span>\r\n                            <span class="suggestions-count" id="suggestionsCount">0</span>\r\n                        </div>\r\n                        <div class="suggestions-chips-tray" id="suggestionsChipsTray"></div>\r\n                    </div>\r\n                    <textarea id="vietnameseInput"'
    
    if box_anchor in content:
        content = content.replace(box_anchor, box_new, 1)
        print("[+] Added glossary suggestions box into translation-input-box")
    else:
        # Try with \n
        box_anchor_lf = box_anchor.replace('\r\n', '\n')
        box_new_lf = box_new.replace('\r\n', '\n')
        if box_anchor_lf in content:
            content = content.replace(box_anchor_lf, box_new_lf, 1)
            print("[+] Added glossary suggestions box into translation-input-box (LF)")
        else:
            print("[-] Translation input box anchor not found!")

    # 3. Replace Glossary Modal
    modal_anchor_start = '    <!-- Modal: Glossary -->'
    modal_anchor_end = '    </div>\r\n\r\n    <script>'
    modal_anchor_end_lf = '    </div>\n\n    <script>'

    new_modal = """    <!-- Modal: Glossary -->
    <div class="modal-shade" id="glossaryModal">
        <div class="modal-panel modal-panel-wide">
            <div class="modal-panel-header">
                <div style="display:flex; align-items:center; gap:12px;">
                    <h2>📖 TỪ ĐIỂN THUẬT NGỮ CHUẨN</h2>
                    <span class="glossary-counter-badge" id="glossaryTotalBadge">322 Mục</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <button class="btn-sync-glossary" id="btnSyncGlossary" onclick="syncGlossaryFromSheets()" title="Đồng bộ trực tiếp từ Google Sheet '01. Thống Nhất Danh Từ'">
                        <span class="sync-icon">🔄</span>
                        <span class="sync-text">Đồng Bộ Sheet</span>
                    </button>
                    <button class="btn-circle" onclick="closeGlossaryModal()" aria-label="Đóng từ điển">✕</button>
                </div>
            </div>

            <!-- Search and Filter Bar -->
            <div class="glossary-toolbar">
                <div class="glossary-search-wrapper">
                    <span class="search-icon">🔍</span>
                    <input type="text" class="glossary-search-input" id="glossarySearchInput" placeholder="Tìm theo tiếng Anh, tiếng Việt, hoặc ghi chú cảnh báo..." oninput="onGlossarySearch(this.value)">
                    <button class="search-clear-btn" id="glossarySearchClear" onclick="clearGlossarySearch()" style="display:none;">✕</button>
                </div>
                <div class="glossary-cat-pills" id="glossaryCatPills"></div>
            </div>

            <!-- Terms List Container -->
            <div class="glossary-list-container" id="glossaryListContainer"></div>
        </div>
    </div>

    <script>"""

    pos_start = content.find(modal_anchor_start)
    if pos_start != -1:
        pos_end = content.find(modal_anchor_end, pos_start)
        if pos_end == -1:
            pos_end = content.find(modal_anchor_end_lf, pos_start)
        
        if pos_end != -1:
            end_len = len(modal_anchor_end) if modal_anchor_end in content else len(modal_anchor_end_lf)
            content = content[:pos_start] + new_modal + content[pos_end + end_len:]
            print("[+] Replaced Glossary Modal with modern wide searchable component")
        else:
            print("[-] Modal end anchor not found!")
    else:
        print("[-] Modal start anchor not found!")

    # 4. State & Initialization
    state_anchor = "let charactersDict = {};"
    state_new = """let charactersDict = {};
        let allGlossaryTerms = [];
        let activeGlossaryCategory = "ALL";
        let glossarySearchTerm = "";"""
    if state_anchor in content:
        content = content.replace(state_anchor, state_new, 1)
        print("[+] Added glossary state variables")

    init_anchor = "await loadChaptersList();"
    init_new = """await loadChaptersList();
            await loadGlossaryTerms();"""
    if init_anchor in content:
        content = content.replace(init_anchor, init_new, 1)
        print("[+] Added loadGlossaryTerms to DOMContentLoaded")

    # 5. renderCurrentLine: call renderGlossarySuggestions
    render_anchor = "renderSmartTags(item.en);"
    render_new = """renderSmartTags(item.en);
            renderGlossarySuggestions(item.en);"""
    if render_anchor in content:
        content = content.replace(render_anchor, render_new, 1)
        print("[+] Wired renderGlossarySuggestions in renderCurrentLine")

    # 6. List Mode suggestions
    list_anchor = '<p class="table-row-en">${item.en}</p>'
    list_new = '<p class="table-row-en">${item.en}</p>\r\n                    ${renderListGlossaryChipsHtml(idx, item.en)}'
    if list_anchor in content:
        content = content.replace(list_anchor, list_new, 1)
        print("[+] Wired suggestions in List Mode")

    # 7. Replace old glossary functions at bottom of script
    old_gloss_fn = """        // Glossary Modal
        function openGlossaryModal() {
            document.getElementById("glossaryModal").classList.add("open");
        }
        function closeGlossaryModal() {
            document.getElementById("glossaryModal").classList.remove("open");
        }"""
    
    new_gloss_fn = """        // ================= GLOSSARY & SUGGESTIONS LOGIC =================
        function escapeHtml(str) {
            if (!str) return "";
            return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        async function loadGlossaryTerms(refresh = false) {
            try {
                const url = refresh ? "/api/glossary?refresh=true" : "/api/glossary";
                const res = await fetch(url);
                const data = await res.json();
                if (data && data.terms) {
                    allGlossaryTerms = data.terms;
                    // Sort by English length descending so longer compound phrases match before single words
                    allGlossaryTerms.sort((a, b) => b.en.length - a.en.length);
                    updateGlossaryCountBadge();
                    if (document.getElementById("glossaryModal").classList.contains("open")) {
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

        function updateGlossaryCountBadge() {
            const badge = document.getElementById("glossaryTotalBadge");
            if (badge) {
                badge.innerText = `${allGlossaryTerms.length} Mục`;
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
                const escaped = item.en.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
                // Word boundary with optional plural suffix (s / es)
                const regex = new RegExp(`\\\\b${escaped}(?:s|es)?\\\\b`, 'i');
                if (regex.test(text)) {
                    matches.push(item);
                    matchedEn.add(enLower);
                }
            }
            return matches;
        }

        // Render Suggestions in Stage Mode
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
            if (countLabel) countLabel.innerText = `${matches.length} thuật ngữ`;
            tray.innerHTML = "";

            matches.forEach(item => {
                const chip = document.createElement("div");
                chip.className = `glossary-suggestion-chip ${item.is_critical ? 'warn' : ''}`;
                
                let tooltip = `[${item.category}] ${item.en} ➔ ${item.vi}`;
                if (item.notes) tooltip += `\\n⚠️ Lưu ý: ${item.notes}`;
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

        // Insert suggestion into Stage Mode textarea at cursor position
        function insertGlossaryTerm(term) {
            const input = document.getElementById("vietnameseInput");
            if (!input) return;
            const start = input.selectionStart || input.value.length;
            const end = input.selectionEnd || input.value.length;
            const text = input.value;
            
            let insertText = term;
            if (start > 0 && text[start - 1] !== ' ' && text[start - 1] !== '\\n') {
                insertText = ' ' + insertText;
            }
            if (end < text.length && text[end] !== ' ' && text[end] !== '\\n' && text[end] !== '.' && text[end] !== ',') {
                insertText = insertText + ' ';
            }

            input.value = text.substring(0, start) + insertText + text.substring(end);
            input.focus();
            const newPos = start + insertText.length;
            input.selectionStart = input.selectionEnd = newPos;

            showToastAlert(`💡 Đã chèn thuật ngữ: "${term}"`);
        }

        // Render List Mode Suggestions HTML
        function renderListGlossaryChipsHtml(idx, enText) {
            const matches = detectGlossaryMatches(enText);
            if (!matches || matches.length === 0) return "";
            
            const chipsHtml = matches.map(m => {
                const tip = escapeHtml(`[${m.category}] ${m.en} ➔ ${m.vi}` + (m.notes ? ` (Lưu ý: ${m.notes})` : ''));
                return `<span class="table-glossary-chip ${m.is_critical ? 'warn' : ''}" onclick="insertListGlossaryTerm(${idx}, '${escapeHtml(m.vi)}')" title="${tip}">
                    <span class="chip-en">${escapeHtml(m.en)}</span>
                    <span class="chip-arrow">➔</span>
                    <span class="chip-vi">${escapeHtml(m.vi)}</span>
                    ${m.is_critical ? '⚠️' : ''}
                </span>`;
            }).join('');

            return `<div class="table-glossary-tray">
                <span class="table-glossary-label">💡 Gợi ý:</span>
                ${chipsHtml}
            </div>`;
        }

        // Insert suggestion into List Mode input row
        function insertListGlossaryTerm(idx, term) {
            const inputs = document.querySelectorAll(".table-row-input");
            if (!inputs || !inputs[idx]) return;
            const rowInput = inputs[idx];
            let val = rowInput.value || "";
            if (val.length > 0 && !val.endsWith(' ')) val += ' ';
            val += term;
            rowInput.value = val;
            onListChange(idx, val);
            showToastAlert(`💡 Đã chèn thuật ngữ: "${term}"`);
        }

        // ================= GLOSSARY MODAL MANAGEMENT =================
        function openGlossaryModal() {
            const modal = document.getElementById("glossaryModal");
            modal.classList.add("open");
            renderGlossaryCategories();
            renderGlossaryList();
            setTimeout(() => {
                const search = document.getElementById("glossarySearchInput");
                if (search) search.focus();
            }, 100);
        }

        function closeGlossaryModal() {
            document.getElementById("glossaryModal").classList.remove("open");
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

        function setGlossaryCategory(catId) {
            activeGlossaryCategory = catId;
            renderGlossaryCategories();
            renderGlossaryList();
        }

        function onGlossarySearch(val) {
            glossarySearchTerm = (val || "").trim().toLowerCase();
            const clearBtn = document.getElementById("glossarySearchClear");
            if (clearBtn) {
                clearBtn.style.display = glossarySearchTerm ? "block" : "none";
            }
            renderGlossaryList();
        }

        function clearGlossarySearch() {
            const input = document.getElementById("glossarySearchInput");
            if (input) input.value = "";
            onGlossarySearch("");
            if (input) input.focus();
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

        function copyGlossaryTerm(term) {
            navigator.clipboard.writeText(term).then(() => {
                showToastAlert(`📋 Đã sao chép: "${term}"`);
            }).catch(() => {
                showToastAlert(`📋 Thuật ngữ: "${term}"`);
            });
        }

        function insertGlossaryFromModal(term) {
            insertGlossaryTerm(term);
            closeGlossaryModal();
        }"""

    if old_gloss_fn in content:
        content = content.replace(old_gloss_fn, new_gloss_fn, 1)
        print("[+] Replaced glossary functions with complete logic")
    else:
        # Try with LF
        old_gloss_fn_lf = old_gloss_fn.replace('\r\n', '\n')
        new_gloss_fn_lf = new_gloss_fn.replace('\r\n', '\n')
        if old_gloss_fn_lf in content:
            content = content.replace(old_gloss_fn_lf, new_gloss_fn_lf, 1)
            print("[+] Replaced glossary functions with complete logic (LF)")
        else:
            print("[-] Old glossary functions not found!")

    INDEX_PATH.write_text(content, encoding="utf-8")
    print("[*] Update finished successfully!")

if __name__ == "__main__":
    update_index_html()
