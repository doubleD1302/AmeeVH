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
    onTranslationDraftInput();
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
    onTranslationDraftInput();

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

const translationSaves = new Map();

function persistTranslationDraft(item, text) {
    const previous = Collaboration.readDraft(item);
    const draft = {
        ...previous,
        text,
        origin: previous?.origin || item.translation_origin || 'human',
        notes: previous?.notes ?? item.notes ?? '',
        base_revision: item.revision
    };
    Collaboration.saveDraft(item, draft);
    return draft;
}

async function submitTranslation(item, text, refresh, button) {
    const ref = Collaboration.ref(item);
    const key = JSON.stringify(ref);
    const attempt = translationSaves.get(key) || {};
    if (attempt.busy) return false;

    if (!text.trim()) {
        showToastAlert('Nhập bản dịch trước khi gửi.');
        return false;
    }
    const draft = persistTranslationDraft(item, text);
    if (!validateTokens(item.en || '', text).isValid) {
        showToastAlert('Bản dịch đang thiếu token. Hãy bổ sung đúng các mã từ câu gốc.');
        return false;
    }
    if (!Collaboration.ready) {
        showToastAlert('Chưa thể gửi bản dịch. Bản nháp đã được giữ trên máy.');
        return false;
    }

    const base = { ...item };
    const revising = Collaboration.hasText(base);
    attempt.busy = true;
    translationSaves.set(key, attempt);
    if (button) button.disabled = true;
    try {
        // Retain the reason and notes of an existing proposal when editing it.
        const own = revising && base.pending_proposals && !draft.reason
            ? await Collaboration.myProposal(base)
            : null;
        const pending = own?.state === 'pending' ? own : null;
        const previousReason = draft.reason || pending?.reason;
        const reason = ['meaning', 'pronouns', 'naturalness', 'other'].includes(previousReason) ? previousReason : 'other';
        const payload = {
            ...ref,
            base_revision: base.revision,
            base_source_hash: base.source_hash,
            base_dataset_version: base.dataset_version,
            text_vi: text,
            origin: (pending?.origin || draft.origin) === 'machine' ? 'machine' : 'human',
            notes: pending?.notes ?? draft.notes,
            reason: revising ? reason : '',
            reason_detail: draft.reason_detail ?? pending?.reason_detail ?? '',
            ...(Collaboration.canModerate ? { expect_moderator: true } : {})
        };
        const payloadKey = JSON.stringify(payload);
        if (attempt.payloadKey !== payloadKey) {
            attempt.payloadKey = payloadKey;
            attempt.requestId = crypto.randomUUID();
        }
        const result = await Collaboration.request('submit', { ...payload, request_id: attempt.requestId });
        Collaboration.patch(result.line);
        Collaboration.clearDraft(base, text);
        Collaboration.award(attempt.requestId, result.replayed);
        refresh(result);
        showToastAlert(result.result === 'moderator_saved' ? 'Đã lưu và duyệt tự động (Moderator).'
            : revising ? 'Đã gửi đề xuất sửa · Chờ duyệt.' : 'Đã lưu bản dịch · Chờ duyệt.');
        translationSaves.delete(key);
        return true;
    } catch (error) {
        if (error.code === 'moderator_invalid') await Collaboration.syncModerator();
        if (error.code === 'dataset_locked') await Collaboration.init();
        if (error.code === 'conflict' || error.code === 'dataset_stale') {
            try {
                const latest = error.latest || await Collaboration.getLine(base);
                Collaboration.patch({ ...base, ...latest });
                refresh();
                showToastAlert('Câu đã cập nhật. Hãy kiểm tra bản hiện tại rồi gửi lại. Bản nháp vẫn được giữ.');
            } catch {
                showToastAlert(error.message);
            }
        } else {
            showToastAlert(error.message);
        }
        return false;
    } finally {
        attempt.busy = false;
        if (button) button.disabled = false;
    }
}

async function saveCurrentLine() {
    const item = filteredLines[currentIndex];
    if (viewMode !== 'game' || !item) return;
    const input = document.getElementById('vietnameseInput');
    return submitTranslation(item, input.value, () => {
        if (viewMode === 'game' && filteredLines[currentIndex] === item) renderCurrentLine();
    });
}

function editOwnProposal(line, proposal) {
    const idx = filteredLines.findIndex(item => item.chapter_id === line.chapter_id && item.line_id === line.line_id);
    if (idx < 0) return;
    const item = filteredLines[idx];
    if (!Collaboration.readDraft(item)) {
        Collaboration.saveDraft(item, {
            text: proposal.text_vi,
            origin: proposal.origin,
            notes: proposal.notes,
            reason: proposal.reason,
            reason_detail: proposal.reason_detail,
            base_revision: item.revision
        });
    }
    currentIndex = idx;
    switchMode('game');
    renderCurrentLine();
    document.getElementById('vietnameseInput').focus();
}
// Kept as a compatibility hook: old offline saves require manual comparison first.
async function flushOfflineQueue() { Collaboration.updateNotice(); }
window.addEventListener('online',()=>{ Collaboration.init(); });

function onTranslationDraftInput() {
    updateTokenValidationUI();
    const item = filteredLines[currentIndex];
    if (item) persistTranslationDraft(item, document.getElementById('vietnameseInput').value);
}
