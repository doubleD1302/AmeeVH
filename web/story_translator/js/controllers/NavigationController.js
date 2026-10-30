/**
 * NavigationController.js
 * Quản lý điều hướng câu thoại, chuyển đổi chế độ xem, bộ lọc và tìm kiếm thuật ngữ
 */

function switchMode(mode) {
    viewMode = mode;
    document.getElementById("tabGameMode").classList.toggle("active", mode === "game");
    document.getElementById("tabListMode").classList.toggle("active", mode === "list");
    document.getElementById("vnStageContainer").style.display = mode === "game" ? "flex" : "none";
    document.getElementById("listModeContainer").style.display = mode === "list" ? "flex" : "none";
    if (mode === "list") {
        renderListMode();
    }
}

function navigateLine(step) {
    const target = currentIndex + step;
    if (target >= 0 && target < filteredLines.length) {
        currentIndex = target;
        renderCurrentLine();
    }
}

function onChapterChange() {
    const cid = document.getElementById("chapterSelect").value;
    loadChapterData(cid);
}

function onSceneChange() {
    applyFilters();
}

function selectScene(idx) {
    document.getElementById("sceneSelect").value = idx;
    document.querySelectorAll(".scene-card-btn").forEach((b, i) => {
        b.classList.toggle("active", i === idx);
    });
    applyFilters();
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
    if (input) input.focus({ preventScroll: true });
}
