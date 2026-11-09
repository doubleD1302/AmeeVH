/** Compact, expandable previews keep the surrounding dialogue readable. */
function renderListMode() {
    const container = document.getElementById('listModeContainer');
    if (!container) return;
    container.replaceChildren();
    const el = (tag, cls, text) => { const node = document.createElement(tag); node.className = cls; if (text !== undefined) node.textContent = text; return node; };
    const notice = el('p', 'list-context-notice', 'Nhấn vào một câu để đề xuất sửa. Dữ liệu nhập cũ có thể không có lịch sử duyệt trước khi nhập.');
    container.append(notice);
    let rendered = 0;
    const more = el('button', 'btn-direction collab-load-more'); more.type = 'button';
    const append = () => {
        more.remove(); const end = Math.min(filteredLines.length, rendered + 80);
        for (let idx = rendered; idx < end; idx++) {
            const item = filteredLines[idx], card = el('article', 'table-row-card compact-row'); card.dataset.lineId = item.line_id; card.dataset.rowTone = idx % 2 ? 'alternate' : 'default';
            card.tabIndex = 0;
            card.setAttribute('role', 'group');
            card.setAttribute('aria-label', `${item.speaker || 'Dẫn chuyện'}, ${item.line_id}. Nhấn Enter để mở đề xuất sửa.`);
            card.title = 'Nhấn để đề xuất sửa';
            card.addEventListener('click', event => {
                if (event.target.closest('button, a, summary, input, textarea, select, details')) return;
                if (window.getSelection()?.toString()) return;
                CollaborationView.openEdit(item);
            });
            card.addEventListener('keydown', event => {
                if (event.target !== card || !['Enter', ' '].includes(event.key)) return;
                event.preventDefault();
                CollaborationView.openEdit(item);
            });
            const top = el('div', 'table-row-top');
            const speaker = el('div', 'table-row-speaker', item.speaker || 'Dẫn chuyện');
            speaker.append(el('span', 'collab-line-id', '#' + item.line_id));
            top.append(speaker, CollaborationView.badge(item));
            const texts = el('div', 'compact-row-texts');
            for (const [title, text] of [['Gốc (EN)', item.en || 'Chưa có nguồn EN.'], ['Bản đang dùng', item.new_vi || 'Chưa có bản dịch tiếng Việt.']]) {
                const section = el('div', 'compact-row-column'); section.append(el('span', 'compact-row-label', title), el('p', '', text)); texts.append(section);
            }
            const details = el('details', 'compact-row-details'), summary = el('summary', '', 'Chi tiết & thao tác');
            const panel = el('div', 'compact-detail-panel');
            panel.append(el('div', 'compact-detail-heading', 'Thông tin bản dịch'), CollaborationView.metadata(item));
            if (item.notes) panel.append(el('p', 'collab-context', 'Ngữ cảnh: ' + item.notes));
            if (item.provenance === 'legacy_import') panel.append(el('p', 'compact-detail-note', 'Dữ liệu nhập cũ: lịch sử trước khi bật cộng tác chưa được xác minh.'));
            details.append(summary, panel);
            const buttons = el('div', 'collab-actions');
            for (const [text, handler] of [[Collaboration.hasText(item) ? 'Đề xuất sửa' : 'Dịch câu này', () => CollaborationView.openEdit(item)], ['Xem lịch sử', () => CollaborationView.openHistory(item)], ['Báo vấn đề', () => CollaborationView.openEdit(item, undefined, { mode: 'report' })]]) {
                const button = el('button', 'btn-direction', text); button.type = 'button'; button.addEventListener('click', handler); buttons.append(button);
            }
            panel.append(buttons); card.append(top, texts, details); container.append(card);
        }
        rendered = end;
        if (rendered < filteredLines.length) { more.textContent = `Xem thêm câu (${rendered}/${filteredLines.length})`; container.append(more); }
    };
    more.onclick = append; append();
}
