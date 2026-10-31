/** Read-only usage guide for the translation workspace. */
(() => {
    const guideIcon = id => `<span class="tram-icon" aria-hidden="true"><img class="tram-icon-light" src="assets/translation-guide-r01/${id}-light.svg" alt=""><img class="tram-icon-dark" src="assets/translation-guide-r01/${id}-dark.svg" alt=""></span>`;
    const sections = [
        { id: 'workflow', title: 'Cách sử dụng', keywords: 'cach su dung chon chuong canh nhap luu dong bo sheets phim tat thuat ngu', body: `
            <ol>
                <li><strong>Chọn câu cần dịch.</strong> Chọn chương, cảnh và bộ lọc ở thanh phía trên. Dùng “Tất cả câu thoại” để xem các câu liền trước và sau.</li>
                <li><strong>Nhập bản dịch.</strong> Đọc bản EN và điền vào ô “Bản dịch tiếng Việt mới”. Bản dịch cũ và nút nghe lồng tiếng là thông tin tham khảo nếu có.</li>
                <li><strong>Tra thuật ngữ.</strong> Dùng ô tra cứu cạnh khung nhập hoặc mở Từ điển bằng <kbd>Alt+G</kbd>. Bấm vào gợi ý để chèn thuật ngữ.</li>
                <li><strong>Lưu bản dịch.</strong> Ở Visual Novel, bấm “Lưu &amp; Tiếp tục” hoặc <kbd>Ctrl+Enter</kbd>. Ở Danh Sách, bấm nút lưu của từng dòng; chỉ nhập vào ô chưa gửi bản dịch.</li>
                <li><strong>Kiểm tra đồng bộ.</strong> Mở Google Sheets từ thanh công cụ để xem đúng ID và nội dung đã lưu. Khi mất mạng, kiểm tra lại trên Sheet sau khi kết nối trở lại.</li>
            </ol>
            <p class="guide-note">Lưu câu đặt trạng thái “Đã dịch”. “Đã duyệt” là bước review riêng; thông báo EXP chưa xác nhận bản dịch đã đồng bộ.</p>
            <p><strong>Phím tắt:</strong> <kbd>Alt+←</kbd> / <kbd>Alt+→</kbd> chuyển câu; <kbd>Alt+S</kbd> lưu. Đóng hướng dẫn trước khi dùng các phím này.</p>` },
        { id: 'tokens', title: 'Token & tag', keywords: 'token tag the dinh dang bien placeholder ma code rich text xuong dong', body: `
            <p>Token và tag là mã để game điền dữ liệu hoặc định dạng chữ. Giữ nguyên cách viết và số lần xuất hiện khi dịch.</p>
            <ul>
                <li><strong>Biến:</strong> <code>{0}</code>, <code>{name}</code>, <code>$\{value}</code>. Giữ nguyên mã; có thể đổi vị trí cho phù hợp câu Việt.</li>
                <li><strong>Thẻ định dạng:</strong> <code>&lt;color=#FFCC00&gt;…&lt;/color&gt;</code>, <code>&lt;sprite=2&gt;</code>. Giữ đúng cặp mở–đóng, thứ tự lồng và phần chữ được áp dụng.</li>
                <li><strong>Xuống dòng:</strong> giữ mã <code>\\n</code> nếu nguồn có. Hai ký tự “\\n” khác với nhấn Enter trong ô nhập.</li>
            </ul>
            <p>Dùng khay token để chèn mã vào câu. Cảnh báo hiện tại chỉ phát hiện một số token còn thiếu; hãy kiểm tra thêm mã thừa, cặp thẻ và mã lạ trước khi lưu.</p>` }
    ];
    const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase();
    let initialized = false;
    let returnFocus = null;
    let activeTopic = 'all';
    let scrollBeforeOpen = '';

    function filterSections() {
        const dialog = document.getElementById('translationGuideDialog');
        const words = normalize(dialog.querySelector('#guideSearch').value.trim()).split(/\s+/).filter(Boolean);
        let count = 0;
        sections.forEach(section => {
            const element = dialog.querySelector(`[data-guide-section="${section.id}"]`);
            const text = normalize(section.title + ' ' + section.keywords + ' ' + element.textContent);
            const visible = (activeTopic === 'all' || activeTopic === section.id) && words.every(word => text.includes(word));
            element.hidden = !visible;
            if (visible) count++;
        });
        dialog.querySelector('#guideResultCount').textContent = `${count}/${sections.length} mục hướng dẫn`;
        dialog.querySelector('#guideEmpty').hidden = count !== 0;
    }

    function init() {
        const dialog = document.getElementById('translationGuideDialog');
        dialog.innerHTML = `<div class="guide-shell">
            <div class="guide-header"><div><h2 id="translationGuideTitle" tabindex="-1">Sổ tay dịch thuật</h2><p id="translationGuideIntro">Cách sử dụng TramVH và lưu bản dịch.</p></div><button type="button" id="guideClose" class="btn-circle" aria-label="Đóng hướng dẫn">${guideIcon('close')}</button></div>
            <div class="guide-layout">
                <nav class="guide-nav" aria-label="Các mục hướng dẫn"><button type="button" data-guide-topic="all" aria-pressed="true">${guideIcon('guide')}<span>Tất cả hướng dẫn</span></button>${sections.map(section => `<button type="button" data-guide-topic="${section.id}" aria-pressed="false">${guideIcon(section.id)}<span>${section.title}</span></button>`).join('')}</nav>
                <div class="guide-mobile-toolbar"><label class="guide-visually-hidden" for="guideTopicSelect">Chọn mục hướng dẫn</label><select id="guideTopicSelect"><option value="all">Tất cả hướng dẫn</option>${sections.map(section => `<option value="${section.id}">${section.title}</option>`).join('')}</select><button type="button" id="guideToggleSearch" class="guide-reset" aria-expanded="false" aria-controls="guideSearchTools" aria-label="Tìm trong hướng dẫn">${guideIcon('search')}</button></div>
                <div class="guide-reading" tabindex="0" role="region" aria-label="Nội dung hướng dẫn">
                    <div id="guideSearchTools" class="guide-search-tools"><label class="guide-search-label" for="guideSearch">Tìm trong hướng dẫn (có dấu hoặc không dấu)</label><div class="guide-search-row"><input id="guideSearch" type="search" placeholder="Lưu bản dịch, thuật ngữ, token…" autocomplete="off"><button type="button" id="guideClearSearch" class="guide-reset">Xóa tìm</button></div></div>
                    <p id="guideResultCount" class="guide-result-count" role="status"></p>
                    <p id="guideEmpty" class="guide-empty" hidden>Không tìm thấy mục phù hợp. Thử từ khóa khác hoặc chọn “Tất cả hướng dẫn”.</p>
                    ${sections.map(section => `<article class="guide-section" data-guide-section="${section.id}" aria-labelledby="guideHeading-${section.id}"><div class="guide-section-heading">${guideIcon(section.id)}<h3 id="guideHeading-${section.id}">${section.title}</h3></div>${section.body}</article>`).join('')}
                    <p class="guide-footer">Nhấn Esc hoặc nút đóng để quay lại bản dịch đang nhập.</p>
                </div>
            </div></div>`;
        dialog.querySelector('#guideClose').addEventListener('click', () => dialog.close());
        dialog.querySelector('#guideSearch').addEventListener('input', filterSections);
        dialog.querySelector('#guideClearSearch').addEventListener('click', () => {
            dialog.querySelector('#guideSearch').value = '';
            filterSections();
            dialog.querySelector('#guideSearch').focus();
        });
        const selectTopic = topic => {
            activeTopic = topic;
            dialog.querySelectorAll('[data-guide-topic]').forEach(item => item.setAttribute('aria-pressed', String(item.dataset.guideTopic === topic)));
            dialog.querySelector('#guideTopicSelect').value = topic;
            dialog.querySelector('#guideSearch').value = '';
            filterSections();
            dialog.querySelector('.guide-reading').scrollTop = 0;
        };
        dialog.querySelectorAll('[data-guide-topic]').forEach(button => button.addEventListener('click', () => selectTopic(button.dataset.guideTopic)));
        dialog.querySelector('#guideTopicSelect').addEventListener('change', event => selectTopic(event.target.value));
        dialog.querySelector('#guideToggleSearch').addEventListener('click', () => {
            const search = dialog.querySelector('#guideSearchTools');
            const open = search.classList.toggle('is-open');
            dialog.querySelector('#guideToggleSearch').setAttribute('aria-expanded', String(open));
            if (open) { dialog.querySelector('.guide-reading').scrollTop = 0; dialog.querySelector('#guideSearch').focus(); }
            else { dialog.querySelector('#guideSearch').value = ''; filterSections(); }
        });
        // Keep editor shortcuts from bubbling and cycle focus inside the guide.
        dialog.addEventListener('keydown', event => {
            event.stopPropagation();
            if (event.key !== 'Tab') return;
            const focusable = [...dialog.querySelectorAll('button, input, select, [tabindex="0"]')]
                .filter(element => !element.disabled && element.getClientRects().length > 0);
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && (document.activeElement === first || !focusable.includes(document.activeElement))) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        });
        dialog.addEventListener('click', event => {
            if (event.target !== dialog) return;
            const rect = dialog.getBoundingClientRect();
            if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
        });
        dialog.addEventListener('close', () => {
            document.body.style.overflow = scrollBeforeOpen;
            if (returnFocus && returnFocus.isConnected) returnFocus.focus({ preventScroll: true });
        });
        initialized = true;
    }

    window.openTranslationGuide = () => {
        if (!initialized) init();
        const dialog = document.getElementById('translationGuideDialog');
        if (dialog.open) return;
        returnFocus = document.activeElement;
        scrollBeforeOpen = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        activeTopic = 'all';
        dialog.querySelector('#guideSearch').value = '';
        dialog.querySelector('#guideTopicSelect').value = 'all';
        dialog.querySelector('#guideSearchTools').classList.remove('is-open');
        dialog.querySelector('#guideToggleSearch').setAttribute('aria-expanded', 'false');
        dialog.querySelectorAll('[data-guide-topic]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.guideTopic === 'all')));
        filterSections();
        dialog.showModal();
        // Do not bring up the phone keyboard just to read the guide.
        dialog.querySelector(window.matchMedia('(max-width:700px), (max-width:900px) and (max-height:500px)').matches ? '#translationGuideTitle' : '#guideSearch').focus({ preventScroll: true });
        dialog.querySelector('.guide-reading').scrollTop = 0;
    };
})();
