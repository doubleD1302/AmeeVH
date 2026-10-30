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

// Save Current Line to Backend & Google Sheets
async function saveCurrentLine() {
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
            "⚠️ CẢNH BÁO BẢN DỊCH THIẾU TOKEN HỆ THỐNG / ĐỊNH DẠNG!\n\n" +
            "Các mã code/token còn thiếu trong câu:\n" +
            valCheck.missing.map(t => "  • " + t).join("\n") + "\n\n" +
            "Việc thiếu token hoặc sai định dạng có thể gây lỗi hiển thị hoặc crash game khi nạp!\n" +
            "Bấm 'Hủy' (Cancel) để bổ sung token, hoặc 'OK' nếu bạn thực sự chắc chắn muốn lưu."
        );
        if (!confirmSave) {
            document.getElementById("vietnameseInput").focus({ preventScroll: true });
            return;
        }
    }

    item.new_vi = newText;
    item.translator = currentUser.name;
    item.status = "Đã dịch";

    // Award EXP
    currentUser.exp = (currentUser.exp || 0) + 50;
    const newLvl = 1 + Math.floor(currentUser.exp / 250);
    if (newLvl > currentUser.level) {
        currentUser.level = newLvl;
        showToastAlert(`🎉 THĂNG CẤP! Bạn đã đạt Cấp ${newLvl}!`);
    } else {
        showToastAlert(`⭐ +50 EXP! Đã cập nhật [${currentUser.name}] lên Google Sheets!`);
    }
    localStorage.setItem("stella_user_profile", JSON.stringify(currentUser));
    updateHud();

    // Background API Sync (Serverless GAS & Cloudflare Pages)
    const payload = {
        action: "save_line",
        chapter_id: currentChapterData.chapter_id,
        sheet_name: currentChapterData.sheet_name,
        row_index: item.row_index,
        line_id: item.line_id,
        new_vi: newText,
        translator: currentUser.name,
        status: "Đã dịch"
    };
    syncLineToBackend(payload);

    // Auto advance
    updateProgressBar();
    if (currentIndex < filteredLines.length - 1) {
        currentIndex++;
        renderCurrentLine();
    }
}

async function saveListRow(idx) {
    const item = filteredLines[idx];
    if (!item || !item.new_vi) return;
    item.translator = currentUser.name;
    item.status = "Đã dịch";
    currentUser.exp = (currentUser.exp || 0) + 50;
    localStorage.setItem("stella_user_profile", JSON.stringify(currentUser));
    updateHud();
    showToastAlert(`⭐ +50 EXP! Đã cập nhật câu ${item.line_id}!`);

    const payload = {
        action: "save_line",
        chapter_id: currentChapterData.chapter_id,
        sheet_name: currentChapterData.sheet_name,
        row_index: item.row_index,
        line_id: item.line_id,
        new_vi: item.new_vi,
        translator: currentUser.name,
        status: "Đã dịch"
    };
    syncLineToBackend(payload);

    renderListMode();
    updateProgressBar();
}

/**
 * Điều phối gửi dữ liệu lên Backend Serverless (Cloudflare Proxy hoặc Trực tiếp Google Apps Script)
 */
async function syncLineToBackend(payload) {
    const config = window.APP_CONFIG || { SYNC_MODE: "auto", GAS_URL: "" };
    let success = false;

    // 1. Thử qua Cloudflare Pages Proxy (/api/save_line)
    if (config.SYNC_MODE === "proxy" || config.SYNC_MODE === "auto") {
        try {
            const res = await fetch("/api/save_line", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                const data = await res.json();
                if (data.success !== false) {
                    success = true;
                }
            }
        } catch (proxyErr) {
            console.warn("[Cloudflare Proxy] Không khả dụng, chuyển sang kênh trực tiếp:", proxyErr);
        }
    }

    // 2. Thử gửi trực tiếp lên Google Apps Script Web App (Direct Mode)
    if (!success && config.GAS_URL && (config.SYNC_MODE === "direct" || config.SYNC_MODE === "auto")) {
        try {
            // Dùng text/plain để tránh preflight CORS OPTIONS từ trình duyệt
            const res = await fetch(config.GAS_URL, {
                method: "POST",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify(payload),
                redirect: "follow"
            });
            if (res.ok) {
                const data = await res.json();
                if (data.success !== false) {
                    success = true;
                }
            }
        } catch (gasErr) {
            console.error("[GAS Direct] Thất bại:", gasErr);
        }
    }

    // 3. Nếu chưa gửi được (mất mạng hoặc lỗi server), đưa vào hàng đợi Offline
    if (!success && config.ENABLE_OFFLINE_QUEUE) {
        enqueueOfflineSave(payload);
    }

    return success;
}

function enqueueOfflineSave(payload) {
    try {
        let queue = JSON.parse(localStorage.getItem("stella_offline_queue") || "[]");
        queue.push({
            payload: payload,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem("stella_offline_queue", JSON.stringify(queue));
        showToastAlert("💾 Đang offline: Đã lưu tạm vào máy, sẽ tự động đồng bộ khi có mạng!");
    } catch (_) {}
}

async function flushOfflineQueue() {
    try {
        let queue = JSON.parse(localStorage.getItem("stella_offline_queue") || "[]");
        if (!queue || queue.length === 0) return;
        
        console.log(`[Offline Sync] Đang đồng bộ ${queue.length} câu đã lưu tạm...`);
        let remaining = [];
        for (const item of queue) {
            const ok = await syncLineToBackend(item.payload);
            if (!ok) {
                remaining.push(item);
            }
        }
        localStorage.setItem("stella_offline_queue", JSON.stringify(remaining));
        if (remaining.length === 0) {
            showToastAlert(`🎉 Đã đồng bộ ${queue.length} câu đã lưu offline lên Google Sheets thành công!`);
        }
    } catch (_) {}
}

window.addEventListener("online", flushOfflineQueue);
