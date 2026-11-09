/**
 * CardView.js
 * Quản lý chế độ Studio / Card Mode (Hộp thoại câu, Standee nhân vật, mã thẻ thông minh và cảnh báo token)
 */

let originalLanguage = (() => {
    try {
        const value = localStorage.getItem('tramvh_original_language');
        return ['en', 'jp', 'cn'].includes(value) ? value : 'en';
    } catch (_) { return 'en'; }
})();

function originalTextForLanguage(item, language) {
    if (language === 'jp') return item.jp ?? item.text_jp ?? item.source_jp ?? '';
    if (language === 'cn') return item.cn ?? item.text_cn ?? item.source_cn ?? '';
    return item.en ?? item.text_en ?? '';
}

function setOriginalLanguage(language) {
    if (!['en', 'jp', 'cn'].includes(language)) return;
    originalLanguage = language;
    try { localStorage.setItem('tramvh_original_language', language); } catch (_) {}
    renderCurrentLine();
}

function renderOriginalLanguage(item) {
    const title = document.getElementById('originalLanguageTitle');
    const text = document.getElementById('speechOriginalText');
    const labels = { en: 'EN', jp: 'JP', cn: 'CN' };
    const value = originalTextForLanguage(item, originalLanguage);
    if (title) title.textContent = `LỜI THOẠI GỐC (${labels[originalLanguage]})`;
    if (text) text.innerHTML = highlightTokensInText(value || `Chưa có nguồn ${labels[originalLanguage]} cho câu này.`);
    document.querySelectorAll('[data-original-language]').forEach(button => {
        const active = button.dataset.originalLanguage === originalLanguage;
        const available = !!originalTextForLanguage(item, button.dataset.originalLanguage);
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
        button.disabled = !available;
    });
}

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

function renderCurrentLine() {
    if (filteredLines.length === 0) {
        document.getElementById("speechOriginalText").innerText = "Không có câu thoại nào phù hợp với bộ lọc!";
        document.getElementById("vietnameseInput").value = "";
        document.getElementById("actorNameText").innerText = "Trống";
        document.getElementById("counterIndicator").innerText = "0 / 0";
        document.getElementById("actorStandee").style.display = "none";
        document.getElementById("voiceControlsBox").style.display = "none";
        document.getElementById("currentLineCollaboration")?.replaceChildren();
        return;
    }

    const item = filteredLines[currentIndex];
    document.getElementById("counterIndicator").innerText = `${currentIndex + 1} / ${filteredLines.length}`;
    document.getElementById("lineIdLabel").innerText = `${item.line_id} [${item.sceneBadge || item.scene_id || ''}]`;
    renderOriginalLanguage(item);
    const speechFrame = document.querySelector(".speech-original-frame");
    if (speechFrame) speechFrame.scrollTop = 0;

    // Actor info & Standee artwork
    const spk = item.speaker.trim();
    document.getElementById("actorNameText").innerText = spk;
    document.getElementById("actorSceneTag").innerText = item.sceneBadge || item.scene_id || "Thoại";

    const spkLower = spk.toLowerCase();
    const charData = charactersDict[spkLower] || charactersDict[spkLower.split(" ").pop()];

    const avatarImg = document.getElementById("actorAvatarImg");
    const avatarCircle = document.getElementById("actorAvatarCircle");
    const standeeImg = document.getElementById("actorStandee");
    const voiceBox = document.getElementById("voiceControlsBox");

    if (charData) {
        // Official Character Details
        avatarImg.src = `official_assets/${charData.avatar}`;
        avatarCircle.style.borderColor = charData.color || "#38bdf8";
        avatarCircle.style.boxShadow = `0 0 20px ${charData.color}88`;
        document.getElementById("actorQuoteText").innerText = charData.quote || charData.title || "Nhà Thám Hiểm";

        // Standee Artwork
        if (charData.bigImg) {
            standeeImg.src = `official_assets/${charData.bigImg}`;
            standeeImg.style.display = "block";
            standeeImg.classList.remove("enter");
            void standeeImg.offsetWidth; // trigger reflow
            standeeImg.classList.add("enter");
        } else {
            standeeImg.style.display = "none";
        }

        // Voice controls
        if (charData.voices_jp && charData.voices_jp.length > 0) {
            voiceBox.style.display = "flex";
        } else {
            voiceBox.style.display = "none";
        }
    } else {
        // Narrator / System
        avatarImg.src = "web_assets/favicon.png";
        avatarCircle.style.borderColor = "#38bdf8";
        avatarCircle.style.boxShadow = "0 0 15px rgba(56, 189, 248, 0.4)";
        document.getElementById("actorQuoteText").innerText = spk.includes("Hệ thống") ? "Lệnh hệ thống game" : "Bối cảnh câu chuyện";
        standeeImg.style.display = "none";
        voiceBox.style.display = "none";
    }

    // Reference old translation
    const refBox = document.getElementById("referenceQuoteBox");
    if (item.old_vi && item.old_vi !== item.en) {
        refBox.style.display = "flex";
        document.getElementById("referenceQuoteText").innerText = item.old_vi;
    } else {
        refBox.style.display = "none";
    }

    // Translation textarea
    const input = document.getElementById("vietnameseInput");
    input.value = window.Collaboration ? (Collaboration.readDraft(item)?.text ?? item.new_vi ?? item.old_vi ?? "") : (item.new_vi || item.old_vi || "");
    renderSmartTags(item.en);
    renderGlossarySuggestions(item.en);
    if (typeof clearQuickGlossarySearch === "function") clearQuickGlossarySearch();
    updateTokenValidationUI();
    if (window.CollaborationView) CollaborationView.renderCurrent(item);
}

function renderSmartTags(enText) {
    const tray = document.getElementById("smartTagTray");
    if (!tray) return;
    tray.innerHTML = "";
    const tags = enText.match(/==[A-Z_]+==|<[^>]+>|\{[0-9]+\}/g);
    if (tags) {
        const uniqueTags = [...new Set(tags)];
        uniqueTags.forEach(t => {
            const btn = document.createElement("button");
            btn.className = "smart-tag-btn";
            btn.innerText = `+ ${t}`;
            btn.onclick = () => insertTag(t);
            tray.appendChild(btn);
        });
    }
}

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
                <span class="token-alert-icon">${tramIcon("warning")}</span>
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
                <span class="token-valid-icon">${tramIcon("approved")}</span>
                <span class="token-valid-text">Đã điền đủ tất cả <b>${res.sourceTokens.length}</b> token hệ thống & định dạng.</span>
            </div>
        `;
    }
}
