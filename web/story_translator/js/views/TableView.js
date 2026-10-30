/**
 * TableView.js
 * Quản lý chế độ xem dạng Bảng / Table Grid Mode (Song ngữ, nhập liệu trực tiếp, cảnh báo dòng)
 */

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

function renderListMode() {
    const container = document.getElementById("listModeContainer");
    if (!container) return;
    container.innerHTML = "";
    filteredLines.forEach((item, idx) => {
        const card = document.createElement("div");
        card.className = "table-row-card";
        card.innerHTML = `
            <div class="table-row-top">
                <div class="table-row-speaker">
                    <span>🗣️ ${item.speaker}</span>
                    <span style="font-size:0.75rem; color:var(--cyan-light); font-weight:normal; font-family:var(--font-code);">#${item.line_id}</span>
                </div>
                <span class="badge-status ${item.status === 'Đã duyệt' ? 'approved' : item.status === 'Đã dịch' ? 'translated' : 'pending'}">${item.status}</span>
            </div>
            <p class="table-row-en">${highlightTokensInText(item.en)}</p>

            ${renderListGlossaryChipsHtml(idx, item.en)}
            ${renderListTokenWarningHtml(idx, item.en, item.new_vi || '')}
            <input type="text" class="table-row-input ${!validateTokens(item.en, item.new_vi || '').isValid && extractTokens(item.en).length > 0 ? 'token-invalid' : ''}" value="${item.new_vi || ''}" placeholder="Nhập câu dịch tiếng Việt..." oninput="onListInput(${idx}, this)" onchange="onListChange(${idx}, this.value)">
            <div class="table-row-bottom">
                <span style="color:var(--gold-light);">👤 Dịch giả: ${item.translator || 'Chưa có'}</span>
                <button class="btn-direction" style="padding:6px 14px; font-size:0.8rem;" onclick="saveListRow(${idx})">💾 Lưu câu này</button>
            </div>
        `;
        container.appendChild(card);
    });
}
