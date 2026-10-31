/** Theme-aware icon selects. Native selects retain values and existing change handlers. */
(() => {
    const controls = new Map();
    const definitions = {
        chapterSelect: { label: "Chọn chương", icon: () => "chapters" },
        sceneSelect: { label: "Chọn cảnh", icon: value => value === "all" ? "star" : "scenes" },
        filterSelect: { label: "Lọc câu thoại", icon: value => ({ all: "search", untranslated: "pending", translated: "translated", approved: "approved", dialogue_only: "dialogue" })[value] || "filter" }
    };
    const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[đĐ]/g, "d").toLowerCase();

    function close(state) {
        state.menu.hidden = true;
        state.button.setAttribute("aria-expanded", "false");
        state.button.removeAttribute("aria-activedescendant");
    }
    function position(state) {
        if (state.menu.hidden) return;
        const rect = state.button.getBoundingClientRect();
        const margin = 12;
        const width = Math.min(Math.max(rect.width, 240), window.innerWidth - margin * 2);
        const below = window.innerHeight - rect.bottom - margin - 6;
        const above = rect.top - margin - 6;
        const upwards = below < 170 && above > below;
        const available = Math.max(48, upwards ? above : below);
        state.menu.style.width = `${width}px`;
        state.menu.style.maxHeight = `${Math.min(340, available)}px`;
        state.menu.style.left = `${Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin))}px`;
        if (upwards) {
            state.menu.style.top = "auto";
            state.menu.style.bottom = `${window.innerHeight - rect.top + 6}px`;
        } else {
            state.menu.style.bottom = "auto";
            state.menu.style.top = `${rect.bottom + 6}px`;
        }
    }
    function highlight(state, index) {
        state.active = index;
        [...state.menu.children].forEach((option, i) => option.classList.toggle("is-active", i === index));
        const option = state.menu.children[index];
        if (option && !state.menu.hidden) {
            state.button.setAttribute("aria-activedescendant", option.id);
            option.scrollIntoView({ block: "nearest" });
        }
    }
    function refresh(state) {
        const options = [...state.select.options];
        const signature = JSON.stringify(options.map(option => [option.value, option.label, option.disabled]));
        if (signature !== state.signature) {
            state.signature = signature;
            state.menu.replaceChildren();
            options.forEach((option, index) => {
                const row = document.createElement("div");
                row.id = `${state.select.id}-option-${index}`;
                row.className = "tram-select-option";
                row.setAttribute("role", "option");
                row.setAttribute("aria-disabled", String(option.disabled));
                row.dataset.index = index;
                row.innerHTML = tramIcon(state.definition.icon(option.value));
                const label = document.createElement("span");
                label.className = "tram-select-option-label";
                label.textContent = option.label;
                row.append(label);
                state.menu.append(row);
            });
            state.active = state.select.selectedIndex;
        }
        const selected = options[state.select.selectedIndex];
        state.button.disabled = state.select.disabled || !selected;
        state.buttonIcon.innerHTML = tramIcon(state.definition.icon(selected?.value));
        state.buttonLabel.textContent = selected?.label || state.definition.label;
        state.button.setAttribute("aria-label", `${state.definition.label}: ${state.buttonLabel.textContent}`);
        [...state.menu.children].forEach((option, i) => option.setAttribute("aria-selected", String(i === state.select.selectedIndex)));
        if (!state.menu.hidden) {
            highlight(state, state.active);
            position(state);
        }
    }
    function open(state) {
        controls.forEach(other => { if (other !== state) close(other); });
        refresh(state);
        state.menu.hidden = false;
        state.button.setAttribute("aria-expanded", "true");
        position(state);
        highlight(state, state.select.selectedIndex);
    }
    function choose(state, index) {
        const option = state.select.options[index];
        if (!option || option.disabled) return;
        state.select.value = option.value;
        close(state);
        refresh(state);
        state.select.dispatchEvent(new Event("change", { bubbles: true }));
        state.button.focus({ preventScroll: true });
    }
    function move(state, step) {
        const options = [...state.select.options];
        if (!options.length) return;
        let index = state.active;
        for (let count = 0; count < options.length; count++) {
            index = (index + step + options.length) % options.length;
            if (!options[index].disabled) { highlight(state, index); return; }
        }
    }
    function keydown(state, event) {
        const opened = !state.menu.hidden;
        if (event.key === "Escape") { close(state); event.preventDefault(); return; }
        if (event.key === "Tab") { close(state); return; }
        if (["Enter", " "].includes(event.key)) {
            event.preventDefault();
            if (opened) choose(state, state.active); else open(state);
        } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
            event.preventDefault();
            if (!opened) open(state);
            if (event.key === "ArrowDown") move(state, 1);
            if (event.key === "ArrowUp") move(state, -1);
            if (event.key === "Home") { highlight(state, -1); move(state, 1); }
            if (event.key === "End") { highlight(state, 0); move(state, -1); }
        } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
            event.preventDefault();
            if (!opened) open(state);
            const now = Date.now();
            state.query = now - state.typedAt < 800 ? state.query + event.key : event.key;
            state.typedAt = now;
            const query = normalize(state.query);
            const options = [...state.select.options];
            for (let i = 1; i <= options.length; i++) {
                const index = (state.active + i) % options.length;
                if (!options[index].disabled && normalize(options[index].label).startsWith(query)) { highlight(state, index); break; }
            }
        }
    }
    window.syncTramSelects = () => controls.forEach(refresh);
    window.initTramSelects = () => {
        for (const [id, definition] of Object.entries(definitions)) {
            const select = document.getElementById(id);
            if (!select || controls.has(id)) continue;
            const wrapper = document.createElement("div");
            wrapper.className = "tram-select-wrap";
            select.before(wrapper);
            wrapper.append(select);
            select.classList.add("tram-native-select");
            select.setAttribute("aria-hidden", "true");
            select.tabIndex = -1;
            const button = document.createElement("button");
            button.type = "button";
            button.id = `${id}-trigger`;
            button.className = "app-select tram-select-trigger";
            button.setAttribute("role", "combobox");
            button.setAttribute("aria-haspopup", "listbox");
            button.setAttribute("aria-expanded", "false");
            button.setAttribute("aria-controls", `${id}-listbox`);
            button.innerHTML = '<span class="tram-select-icon"></span><span class="tram-select-label"></span><span class="tram-select-chevron" aria-hidden="true"></span>';
            wrapper.append(button);
            const menu = document.createElement("div");
            menu.id = `${id}-listbox`;
            menu.className = "tram-select-menu";
            menu.hidden = true;
            menu.setAttribute("role", "listbox");
            menu.setAttribute("aria-label", definition.label);
            document.body.append(menu);
            const state = { select, definition, wrapper, button, menu, buttonIcon: button.querySelector(".tram-select-icon"), buttonLabel: button.querySelector(".tram-select-label"), signature: "", active: -1, query: "", typedAt: 0 };
            controls.set(id, state);
            button.addEventListener("click", () => menu.hidden ? open(state) : close(state));
            button.addEventListener("keydown", event => keydown(state, event));
            menu.addEventListener("mousedown", event => event.preventDefault());
            menu.addEventListener("click", event => {
                const row = event.target.closest(".tram-select-option");
                if (row && menu.contains(row)) choose(state, Number(row.dataset.index));
            });
            select.addEventListener("change", () => refresh(state));
            state.observer = new MutationObserver(() => refresh(state));
            state.observer.observe(select, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["disabled", "selected", "label"] });
            refresh(state);
        }
    };
    document.addEventListener("pointerdown", event => controls.forEach(state => {
        if (!state.wrapper.contains(event.target) && !state.menu.contains(event.target)) close(state);
    }));
    window.addEventListener("resize", () => controls.forEach(position));
    window.addEventListener("scroll", () => controls.forEach(position), true);
})();
