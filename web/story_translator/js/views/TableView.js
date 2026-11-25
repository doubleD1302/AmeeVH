/** Compact, expandable previews keep the surrounding dialogue readable. */
function renderListMode() {
    const container = document.getElementById('listModeContainer');
    if (!container) return;
    container.replaceChildren();
    const el = (tag, cls, text) => { const node = document.createElement(tag); node.className = cls; if (text !== undefined) node.textContent = text; return node; };
    const mobile=matchMedia('(max-width:700px)').matches;
    const scope=filteredLines.map(line=>line.line_id).join('|');
    const saved=window.tramMobileListState;
    if(mobile && (!saved || saved.scope!==scope))window.tramMobileListState={scope,query:'',count:30};
    const state=mobile?window.tramMobileListState:null;
    const query=state?.query || '';
    const search=mobile?el('input','mobile-line-search'):null;
    const count=mobile?el('p','mobile-list-count'):null;
    if(mobile){const label=el('label','mobile-list-search','Tìm câu trong phạm vi đang chọn');search.type='search';search.placeholder='Nội dung hoặc mã câu…';search.value=query;search.setAttribute('aria-label','Tìm câu theo nội dung hoặc mã');label.append(search);container.append(label,count);search.addEventListener('input',()=>{state.query=search.value;state.count=30;const position=search.selectionStart;renderListMode();const next=container.querySelector('.mobile-line-search');next.focus({preventScroll:true});try{next.setSelectionRange(position,position);}catch{}});}
    const needle=query.trim().toLocaleLowerCase('vi');
    const visible=mobile && needle?filteredLines.filter(line=>[line.line_id,line.en,line.new_vi,line.speaker].join(' ').toLocaleLowerCase('vi').includes(needle)):filteredLines;
    let rendered = 0;
    const more = el('button', 'btn-direction collab-load-more'); more.type = 'button';
    const append = () => {
        more.remove(); const end = Math.min(visible.length, rendered + (mobile ? Math.max(30,state.count-rendered) : 80));
        for (let idx = rendered; idx < end; idx++) {
            const item = visible[idx], card = el('article', 'table-row-card compact-row'); card.dataset.lineId = item.line_id; card.dataset.rowTone = idx % 2 ? 'alternate' : 'default';
            card.tabIndex = 0;
            card.setAttribute('role', 'group');
            card.setAttribute('aria-label', `${item.speaker || 'Dẫn chuyện'}, ${item.line_id}. Nhấn Enter để sửa bản dịch.`);
            const button = (text, handler) => {
                const node = el('button', 'btn-direction', text);
                node.type = 'button';
                node.addEventListener('click', handler);
                return node;
            };
            let editor, savedProposal;
            const openEditor = () => {
                if (editor) {
                    editor.querySelector('textarea').focus();
                    return;
                }
                const form = el('form', 'collab-form');
                const label = el('label', '', 'Bản dịch tiếng Việt');
                const input = el('textarea', '');
                input.rows = 3;
                input.value = Collaboration.readDraft(item)?.text ?? savedProposal ?? item.new_vi ?? '';
                input.addEventListener('input', () => persistTranslationDraft(item, input.value));
                input.addEventListener('keydown', event => {
                    if ((event.ctrlKey && event.key === 'Enter') || (event.altKey && event.key.toLowerCase() === 's')) {
                        event.preventDefault();
                        event.stopPropagation();
                        form.requestSubmit();
                    }
                });
                label.append(input);
                const closeEditor = () => {
                    if (form.contains(document.activeElement)) editButton.focus();
                    form.remove();
                    editor = null;
                };
                const save = el('button', 'btn-save-glow', CollaborationView.saveText(item));
                save.type = 'submit';
                const actions = el('div', 'collab-actions');
                actions.append(save, button('Thu gọn', closeEditor));
                form.append(label, actions);
                form.addEventListener('submit', event => {
                    event.preventDefault();
                    const text = input.value;
                    submitTranslation(item, text, result => {
                        refreshPreview();
                        save.textContent = CollaborationView.saveText(item);
                        if (result?.proposal?.state === 'pending') savedProposal = result.proposal.text_vi;
                        if (result && editor === form && input.value === text) closeEditor();
                    }, save);
                });
                editor = form;
                texts.after(form);
                input.focus();
            };
            card.addEventListener('click', event => {
                if (event.target.closest('button, a, details, form')) return;
                if (window.getSelection()?.toString()) return;
                openEditor();
            });
            card.addEventListener('keydown', event => {
                if (event.target !== card || !['Enter', ' '].includes(event.key)) return;
                event.preventDefault();
                openEditor();
            });
            const top = el('div', 'table-row-top');
            const speaker = el('div', 'table-row-speaker', item.speaker || 'Dẫn chuyện');
            speaker.append(el('span', 'collab-line-id', '#' + item.line_id));
            top.append(speaker);
            const texts = el('div', 'compact-row-texts');
            for (const title of ['Gốc (EN)', 'Bản đang dùng']) {
                const section = el('div', 'compact-row-column');
                section.append(el('span', 'compact-row-label', title), el('p', ''));
                texts.append(section);
            }
            const details = el('details', 'compact-row-details'), summary = el('summary', '', 'Chi tiết & thao tác');
            const panel = el('div', 'compact-detail-panel');
            const metadata = el('div', '');
            const sources = el('details', '');
            sources.append(el('summary', '', 'Xem nguồn EN / JP / CN'));
            const updateSources = () => {
                sources.querySelector('.collab-source-grid')?.remove();
                if (sources.open) sources.append(CollaborationView.sources(item));
            };
            sources.addEventListener('toggle', updateSources);
            details.append(summary, panel);
            const editActions = el('div', 'collab-actions');
            const editButton = button('', openEditor);
            editActions.append(editButton);
            const buttons = el('div', 'collab-actions');
            buttons.append(
                button('Xem lịch sử', () => CollaborationView.openHistory(item)),
                button('Báo vấn đề', () => CollaborationView.openLineAction(item, { mode: 'report' }))
            );
            const refreshPreview = () => {
                top.querySelector('.collab-badge')?.remove();
                top.append(CollaborationView.badge(item));
                const [en, vi] = texts.querySelectorAll('p');
                en.textContent = item.en || 'Chưa có nguồn EN.';
                vi.textContent = item.new_vi || 'Chưa có bản dịch tiếng Việt.';
                editButton.textContent = Collaboration.hasText(item) ? 'Sửa bản dịch' : 'Dịch câu này';
                metadata.replaceChildren(CollaborationView.metadata(item));
                if (item.notes) metadata.append(el('p', 'collab-context', 'Ngữ cảnh: ' + item.notes));
                if (item.provenance === 'legacy_import') metadata.append(el('p', 'compact-detail-note', 'Dữ liệu nhập cũ: lịch sử trước khi bật cộng tác chưa được xác minh.'));
                updateSources();
            };
            panel.append(el('div', 'compact-detail-heading', 'Thông tin bản dịch'), metadata, sources, buttons);
            refreshPreview();
            card.append(top, texts, editActions, details);
            container.append(card);
        }
        rendered = end;
        if(mobile){state.count=rendered;count.textContent=visible.length?`Đang hiện ${rendered} / ${visible.length} câu${needle?' tìm được':''}`:'Không tìm thấy câu phù hợp.';}
        if (rendered < visible.length) { more.textContent = `Xem thêm câu (${rendered}/${visible.length})`; container.append(more); }
    };
    more.onclick = append; append();
}
