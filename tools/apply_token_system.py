#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applies System Code Token Highlighting & Validation to index.html:
1. Distinct visual styling for all formatting and system tokens in original dialogue text.
2. Real-time validation of tokens in translation input.
3. Red outline + glow when tokens are missing.
4. Warning alert banner with 1-click token insertion chips.
5. Protection before save to prevent accidental corrupted uploads.
6. List Mode support with red outline and quick-insert codes.
"""

from pathlib import Path

INDEX_PATH = Path("StellaSora_VietHoa/web/story_translator/index.html")

def apply_token_features():
    content = INDEX_PATH.read_text(encoding="utf-8")

    # 1. Add CSS rules
    css_anchor = "/* ================= GLOSSARY & TRANSLATION SUGGESTIONS ================= */"
    css_token_block = """/* ================= SYSTEM CODE & FORMAT TOKEN STYLING ================= */
        .sys-code-token {
            display: inline-block;
            background: rgba(244, 63, 94, 0.2);
            border: 1px solid rgba(244, 63, 94, 0.55);
            color: #ff7597;
            font-family: var(--font-code);
            font-size: 0.88em;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 6px;
            margin: 0 2px;
            user-select: all;
            cursor: pointer;
            vertical-align: baseline;
            transition: all 0.2s ease;
        }

        .sys-code-token:hover {
            background: rgba(244, 63, 94, 0.35);
            border-color: var(--rose-accent);
            color: #ffffff;
            box-shadow: 0 0 14px rgba(244, 63, 94, 0.6);
            transform: translateY(-1px);
        }

        html:not([data-theme="dark"]) .sys-code-token {
            background: #fde8ec;
            border-color: #fca5b3;
            color: #be123c;
        }
        html:not([data-theme="dark"]) .sys-code-token:hover {
            background: #fecdd3;
            color: #9f1239;
            box-shadow: 0 0 10px rgba(225, 29, 72, 0.35);
        }

        /* Token Validation: Red Input Highlight & Glow */
        textarea#vietnameseInput.token-invalid,
        .table-row-input.token-invalid {
            border-color: #ef4444 !important;
            background: rgba(35, 12, 18, 0.96) !important;
            box-shadow: 0 0 22px rgba(239, 68, 68, 0.45) !important;
            color: #fecaca !important;
        }

        html:not([data-theme="dark"]) textarea#vietnameseInput.token-invalid,
        html:not([data-theme="dark"]) .table-row-input.token-invalid {
            background: #fff5f5 !important;
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.25) !important;
            color: #991b1b !important;
        }

        textarea#vietnameseInput.token-valid {
            border-color: var(--green-accent) !important;
            box-shadow: 0 0 16px rgba(52, 211, 153, 0.25) !important;
        }

        /* Token Validation Alert Banner */
        .token-validation-alert {
            border-radius: 12px;
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            animation: fadeInAlert 0.25s ease-out;
        }

        @keyframes fadeInAlert {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .token-validation-alert.alert-missing {
            background: rgba(239, 68, 68, 0.14);
            border: 1px solid rgba(239, 68, 68, 0.55);
        }

        .token-validation-alert.alert-valid {
            background: rgba(52, 211, 153, 0.12);
            border: 1px solid rgba(52, 211, 153, 0.45);
            padding: 8px 14px;
        }

        html:not([data-theme="dark"]) .token-validation-alert.alert-missing {
            background: #fef2f2;
            border-color: #f87171;
        }

        html:not([data-theme="dark"]) .token-validation-alert.alert-valid {
            background: #f0fdf4;
            border-color: #86efac;
        }

        .token-alert-header {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .token-alert-icon {
            font-size: 1.1rem;
            flex-shrink: 0;
        }

        .token-alert-title {
            font-size: 0.82rem;
            font-weight: 800;
            color: #f87171;
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }

        html:not([data-theme="dark"]) .token-alert-title {
            color: #b91c1c;
        }

        .token-alert-body {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .token-alert-desc {
            font-size: 0.82rem;
            color: var(--text-sub);
            line-height: 1.4;
        }

        .token-missing-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 2px;
        }

        .btn-token-chip {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.6);
            color: #fecaca;
            font-family: var(--font-code);
            font-size: 0.78rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-token-chip:hover {
            background: #ef4444;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
            transform: translateY(-1px);
        }

        html:not([data-theme="dark"]) .btn-token-chip {
            background: #fee2e2;
            border-color: #f87171;
            color: #991b1b;
        }

        html:not([data-theme="dark"]) .btn-token-chip:hover {
            background: #dc2626;
            color: #ffffff;
        }

        .token-valid-row {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .token-valid-icon {
            font-size: 1rem;
        }

        .token-valid-text {
            font-size: 0.82rem;
            color: var(--green-accent);
            font-weight: 600;
        }

        /* Shake Animation */
        @keyframes alertShake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-6px); }
            40%, 80% { transform: translateX(6px); }
        }
        .shake-alert {
            animation: alertShake 0.4s ease-in-out;
        }

        /* List Mode Token Warning */
        .list-token-warning {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
            font-size: 0.76rem;
            color: #f87171;
            margin: 4px 0;
            padding: 4px 8px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-radius: 6px;
        }
        .list-token-warning code {
            background: rgba(239, 68, 68, 0.25);
            color: #fecaca;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--font-code);
            font-weight: 700;
            cursor: pointer;
        }
        .list-token-warning code:hover {
            background: #ef4444;
            color: #fff;
        }

        """
    if css_anchor in content:
        content = content.replace(css_anchor, css_token_block + css_anchor, 1)
        print("[+] Added Token Highlighting & Validation CSS")
    else:
        print("[-] CSS anchor not found!")

    # 2. Add #tokenValidationAlert inside translation-input-box
    box_anchor = '<div class="glossary-suggestions-box" id="glossarySuggestionsBox" style="display:none;">'
    box_new = """<!-- Cảnh báo kiểm tra Token hệ thống -->
                    <div class="token-validation-alert" id="tokenValidationAlert" style="display:none;"></div>
                    <div class="glossary-suggestions-box" id="glossarySuggestionsBox" style="display:none;">"""
    if box_anchor in content:
        content = content.replace(box_anchor, box_new, 1)
        print("[+] Added #tokenValidationAlert into translation-input-box")
    else:
        print("[-] Box anchor not found!")

    # 3. Add oninput="updateTokenValidationUI()" to textarea#vietnameseInput
    ta_old = '<textarea id="vietnameseInput" placeholder="Nhập câu dịch tiếng Việt mượt mà, văn phong anime RPG tự nhiên..." onkeydown="handleTextareaKeydown(event)"></textarea>'
    ta_new = '<textarea id="vietnameseInput" placeholder="Nhập câu dịch tiếng Việt mượt mà, văn phong anime RPG tự nhiên..." oninput="updateTokenValidationUI()" onkeydown="handleTextareaKeydown(event)"></textarea>'
    if ta_old in content:
        content = content.replace(ta_old, ta_new, 1)
        print("[+] Added oninput handler to textarea#vietnameseInput")
    else:
        print("[-] Textarea anchor not found!")

    # 4. In renderCurrentLine: Highlight original speech text & validate on load
    speech_old = 'document.getElementById("speechOriginalText").innerText = item.en;'
    speech_new = 'document.getElementById("speechOriginalText").innerHTML = highlightTokensInText(item.en);'
    if speech_old in content:
        content = content.replace(speech_old, speech_new, 1)
        print("[+] Updated speechOriginalText to use highlightTokensInText")
    else:
        print("[-] speechOriginalText anchor not found!")

    render_call_old = "renderGlossarySuggestions(item.en);"
    render_call_new = """renderGlossarySuggestions(item.en);
            updateTokenValidationUI();"""
    if render_call_old in content:
        content = content.replace(render_call_old, render_call_new, 1)
        print("[+] Added updateTokenValidationUI call in renderCurrentLine")

    # 5. In insertTag & insertGlossaryTerm: call updateTokenValidationUI
    tag_ins_old = "input.selectionStart = input.selectionEnd = start + tag.length;"
    tag_ins_new = """input.selectionStart = input.selectionEnd = start + tag.length;
            updateTokenValidationUI();"""
    if tag_ins_old in content:
        content = content.replace(tag_ins_old, tag_ins_new, 1)
        print("[+] Added updateTokenValidationUI in insertTag")

    # 6. Guard in saveCurrentLine
    save_old = """        async function saveCurrentLine() {
            if (filteredLines.length === 0) return;
            const item = filteredLines[currentIndex];
            const newText = document.getElementById("vietnameseInput").value.trim();
            if (!newText) return;"""
    
    save_new = """        async function saveCurrentLine() {
            if (filteredLines.length === 0) return;
            const item = filteredLines[currentIndex];
            const newText = document.getElementById("vietnameseInput").value.trim();
            if (!newText) return;

            // Kiểm tra Token hệ thống bắt buộc
            const valCheck = validateTokens(item.en, newText);
            if (!valCheck.isValid) {
                const alertBox = document.getElementById("tokenValidationAlert");
                if (alertBox) {
                    alertBox.classList.add("shake-alert");
                    setTimeout(() => alertBox.classList.remove("shake-alert"), 600);
                }
                const confirmSave = confirm(
                    "⚠️ CẢNH BÁO BẢN DỊCH THIẾU TOKEN HỆ THỐNG / ĐỊNH DẠNG!\\n\\n" +
                    "Các mã code/token còn thiếu trong câu:\\n" +
                    valCheck.missing.map(t => "  • " + t).join("\\n") + "\\n\\n" +
                    "Việc thiếu token hoặc sai định dạng có thể gây lỗi hiển thị hoặc crash game khi nạp!\\n" +
                    "Bấm 'Hủy' (Cancel) để bổ sung token, hoặc 'OK' nếu bạn thực sự chắc chắn muốn lưu."
                );
                if (!confirmSave) {
                    document.getElementById("vietnameseInput").focus();
                    return;
                }
            }"""

    # Try both CRLF and LF
    if save_old in content:
        content = content.replace(save_old, save_new, 1)
        print("[+] Added token validation guard in saveCurrentLine")
    else:
        save_old_lf = save_old.replace("\r\n", "\n")
        save_new_lf = save_new.replace("\r\n", "\n")
        if save_old_lf in content:
            content = content.replace(save_old_lf, save_new_lf, 1)
            print("[+] Added token validation guard in saveCurrentLine (LF)")
        else:
            print("[-] saveCurrentLine anchor not found!")

    # 7. List Mode: highlight original text and show token validation
    list_en_old = '<p class="table-row-en">${item.en}</p>'
    list_en_new = '<p class="table-row-en">${highlightTokensInText(item.en)}</p>'
    if list_en_old in content:
        content = content.replace(list_en_old, list_en_new, 1)
        print("[+] Highlighted tokens in List Mode original text")

    list_inp_old = '<input type="text" class="table-row-input" value="${item.new_vi || \'\'}" placeholder="Nhập câu dịch tiếng Việt..." onchange="onListChange(${idx}, this.value)">'
    list_inp_new = """${renderListTokenWarningHtml(idx, item.en, item.new_vi || '')}
                    <input type="text" class="table-row-input ${!validateTokens(item.en, item.new_vi || '').isValid && extractTokens(item.en).length > 0 ? 'token-invalid' : ''}" value="${item.new_vi || ''}" placeholder="Nhập câu dịch tiếng Việt..." oninput="onListInput(${idx}, this)" onchange="onListChange(${idx}, this.value)">"""
    if list_inp_old in content:
        content = content.replace(list_inp_old, list_inp_new, 1)
        print("[+] Added token validation support in List Mode row inputs")

    # 8. Add Token Helper Functions into <script>
    fn_anchor = "// ================= GLOSSARY & SUGGESTIONS LOGIC ================="
    token_fns = """// ================= SYSTEM CODE TOKEN HIGHLIGHTING & VALIDATION =================
        const SYSTEM_TOKEN_REGEX = /==[A-Za-z0-9_]+==|<[^<>\\n]+>|\\{[0-9]+\\}|\\$\\{[^{}\\n]+\\}|\\$[A-Za-z_][\\w.]*\\$|%(?:\\d+\\$)?[-+#0]*\\d*(?:\\.\\d+)?[diuoxXfFeEgGcs]|\\[\\/?(?:color|size|b|i|url|sprite)[^\\]\\n]*\\]/g;

        // Extracts all system tokens from a string
        function extractTokens(text) {
            if (!text) return [];
            const regex = new RegExp(SYSTEM_TOKEN_REGEX.source, 'g');
            const matches = text.match(regex);
            return matches || [];
        }

        // Highlights system tokens in original dialogue text with eye-catching badges
        function highlightTokensInText(rawText) {
            if (!rawText) return "";
            const regex = new RegExp(SYSTEM_TOKEN_REGEX.source, 'g');
            let lastIndex = 0;
            let html = "";
            let match;
            while ((match = regex.exec(rawText)) !== null) {
                html += escapeHtml(rawText.substring(lastIndex, match.index));
                const token = match[0];
                html += `<span class="sys-code-token" title="Mã hệ thống / Định dạng: Bấm để chèn vào bản dịch" onclick="insertTag('${escapeHtml(token)}')">${escapeHtml(token)}</span>`;
                lastIndex = regex.lastIndex;
            }
            html += escapeHtml(rawText.substring(lastIndex));
            return html;
        }

        // Validates if all tokens in sourceText exist in targetText
        function validateTokens(sourceText, targetText) {
            const srcTokens = extractTokens(sourceText);
            if (srcTokens.length === 0) {
                return { isValid: true, sourceTokens: [], missing: [] };
            }

            const tgtTokens = extractTokens(targetText);
            const tgtCounts = {};
            tgtTokens.forEach(t => {
                tgtCounts[t] = (tgtCounts[t] || 0) + 1;
            });

            const missing = [];
            const srcCounts = {};
            srcTokens.forEach(t => {
                srcCounts[t] = (srcCounts[t] || 0) + 1;
            });

            for (const [token, count] of Object.entries(srcCounts)) {
                const inTarget = tgtCounts[token] || 0;
                if (inTarget < count) {
                    for (let i = 0; i < (count - inTarget); i++) {
                        missing.push(token);
                    }
                }
            }

            return {
                isValid: missing.length === 0,
                sourceTokens: srcTokens,
                missing: missing
            };
        }

        // Updates UI for Stage Mode: red outline + glow, and warning banner
        function updateTokenValidationUI() {
            if (filteredLines.length === 0 || !filteredLines[currentIndex]) return;
            const item = filteredLines[currentIndex];
            const input = document.getElementById("vietnameseInput");
            const alertBox = document.getElementById("tokenValidationAlert");
            if (!input || !alertBox) return;

            const val = input.value || "";
            const res = validateTokens(item.en, val);

            if (res.sourceTokens.length === 0) {
                input.classList.remove("token-invalid");
                input.classList.remove("token-valid");
                alertBox.style.display = "none";
                alertBox.innerHTML = "";
                return;
            }

            if (!res.isValid) {
                input.classList.add("token-invalid");
                input.classList.remove("token-valid");
                alertBox.style.display = "flex";
                alertBox.className = "token-validation-alert alert-missing";

                const uniqueMissing = [...new Set(res.missing)];
                alertBox.innerHTML = `
                    <div class="token-alert-header">
                        <span class="token-alert-icon">⚠️</span>
                        <span class="token-alert-title">THIẾU TOKEN HỆ THỐNG / ĐỊNH DẠNG (${res.missing.length}):</span>
                    </div>
                    <div class="token-alert-body">
                        <span class="token-alert-desc">Bản dịch mới bắt buộc chứa đủ mã định dạng để không gây lỗi game. Bấm để chèn:</span>
                        <div class="token-missing-chips">
                            ${uniqueMissing.map(t => `
                                <button class="btn-token-chip" type="button" onclick="insertTag('${escapeHtml(t)}')">
                                    ➕ ${escapeHtml(t)}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else {
                input.classList.remove("token-invalid");
                input.classList.add("token-valid");
                alertBox.style.display = "flex";
                alertBox.className = "token-validation-alert alert-valid";
                alertBox.innerHTML = `
                    <div class="token-valid-row">
                        <span class="token-valid-icon">✅</span>
                        <span class="token-valid-text">Đã điền đủ tất cả <b>${res.sourceTokens.length}</b> token hệ thống & định dạng.</span>
                    </div>
                `;
            }
        }

        // List Mode helper to render token warning
        function renderListTokenWarningHtml(idx, enText, viText) {
            const res = validateTokens(enText, viText);
            if (res.sourceTokens.length === 0 || res.isValid) {
                return `<div class="list-token-warning" id="listTokenWarn_${idx}" style="display:none;"></div>`;
            }
            const uniqueMissing = [...new Set(res.missing)];
            return `<div class="list-token-warning" id="listTokenWarn_${idx}">
                <span>⚠️ Thiếu ${res.missing.length} token:</span>
                ${uniqueMissing.map(t => `<code onclick="insertListTag(${idx}, '${escapeHtml(t)}')" title="Bấm để chèn vào câu">+ ${escapeHtml(t)}</code>`).join(' ')}
            </div>`;
        }

        function onListInput(idx, inputElem) {
            const item = filteredLines[idx];
            if (!item) return;
            const val = inputElem.value;
            item.new_vi = val;
            const res = validateTokens(item.en, val);
            const warnElem = document.getElementById(`listTokenWarn_${idx}`);

            if (res.sourceTokens.length === 0 || res.isValid) {
                inputElem.classList.remove("token-invalid");
                if (warnElem) warnElem.style.display = "none";
            } else {
                inputElem.classList.add("token-invalid");
                if (warnElem) {
                    const uniqueMissing = [...new Set(res.missing)];
                    warnElem.style.display = "flex";
                    warnElem.innerHTML = `<span>⚠️ Thiếu ${res.missing.length} token:</span>
                        ${uniqueMissing.map(t => `<code onclick="insertListTag(${idx}, '${escapeHtml(t)}')" title="Bấm để chèn vào câu">+ ${escapeHtml(t)}</code>`).join(' ')}`;
                }
            }
        }

        function insertListTag(idx, tag) {
            const inputs = document.querySelectorAll(".table-row-input");
            if (!inputs || !inputs[idx]) return;
            const rowInput = inputs[idx];
            let val = rowInput.value || "";
            if (val.length > 0 && !val.endsWith(' ')) val += ' ';
            val += tag;
            rowInput.value = val;
            onListInput(idx, rowInput);
            onListChange(idx, val);
            showToastAlert(`💡 Đã chèn token: "${tag}"`);
        }

        """

    if fn_anchor in content:
        content = content.replace(fn_anchor, token_fns + fn_anchor, 1)
        print("[+] Added Token Validation & Highlighting functions")
    else:
        print("[-] Function anchor not found!")

    INDEX_PATH.write_text(content, encoding="utf-8")
    print("[*] All token system updates applied successfully!")

if __name__ == "__main__":
    apply_token_features()
