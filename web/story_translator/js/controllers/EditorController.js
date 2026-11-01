/**
 * EditorController.js
 * Quản lý nhập liệu, phím tắt biên dịch, chèn thẻ token, chèn thuật ngữ và lưu bản dịch
 */

function handleTextareaKeydown(e) {
    if (e.ctrlKey && e.key === "Enter") {
        e.preventDefault();
        saveCurrentLine();
    }
}

function insertTag(tag) {
    const input = document.getElementById("vietnameseInput");
    if (!input) return;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const text = input.value;
    input.value = text.substring(0, start) + tag + text.substring(end);
    input.focus({ preventScroll: true });
    input.selectionStart = input.selectionEnd = start + tag.length;
    updateTokenValidationUI();
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

function insertGlossaryTerm(term) {
    const input = document.getElementById("vietnameseInput");
    if (!input) return;
    const start = input.selectionStart || input.value.length;
    const end = input.selectionEnd || input.value.length;
    const text = input.value;
    
    let insertText = term;
    if (start > 0 && text[start - 1] !== ' ' && text[start - 1] !== '\n') {
        insertText = ' ' + insertText;
    }
    if (end < text.length && text[end] !== ' ' && text[end] !== '\n' && text[end] !== '.' && text[end] !== ',') {
        insertText = insertText + ' ';
    }

    input.value = text.substring(0, start) + insertText + text.substring(end);
    input.focus({ preventScroll: true });
    const newPos = start + insertText.length;
    input.selectionStart = input.selectionEnd = newPos;

    showToastAlert(`💡 Đã chèn thuật ngữ: "${term}"`);
}

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

function insertGlossaryFromModal(term) {
    insertGlossaryTerm(term);
    closeGlossaryModal();
}

function copyGlossaryTerm(term) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(term).then(() => {
            showToastAlert(`📋 Đã sao chép: "${term}"`);
        }).catch(() => {
            showToastAlert(`📋 Thuật ngữ: "${term}"`);
        });
    } else {
        showToastAlert(`📋 Thuật ngữ: "${term}"`);
    }
}

function onListChange(idx, val) {
    if (filteredLines[idx]) {
        filteredLines[idx].new_vi = val.trim();
    }
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

// Always submit with the revision captured by the proposal dialog. No GAS fallback.
async function saveCurrentLine() {
    const item=filteredLines[currentIndex];if(!item)return;
    const text=document.getElementById('vietnameseInput').value;
    return CollaborationView.openEdit(item,text);
}
async function saveListRow(idx) {const item=filteredLines[idx];if(item)return CollaborationView.openEdit(item);}
// Kept as a compatibility hook: old offline saves require manual comparison first.
async function flushOfflineQueue() { Collaboration.updateNotice(); }
window.addEventListener('online',()=>{ Collaboration.init(); });

function onTranslationDraftInput() {
    updateTokenValidationUI();
    const item=filteredLines[currentIndex];if(!item)return;
    Collaboration.saveDraft(item,{text:document.getElementById('vietnameseInput').value,origin:item.translation_origin || 'human',notes:item.notes || '',base_revision:item.revision});
}
