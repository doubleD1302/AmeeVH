/** Translation help is read-only. Checklist ticks last only for one opening. */
(() => {
    const guideIcon = id => `<span class="tram-icon" aria-hidden="true"><img class="tram-icon-light" src="assets/translation-guide-r01/${id}-light.svg" alt=""><img class="tram-icon-dark" src="assets/translation-guide-r01/${id}-dark.svg" alt=""></span>`;
    const sections = [
        { id: 'workflow', title: 'Quy trình dịch', keywords: 'quy trinh bat dau luu dong bo sheets phim tat', body: `
            <ol>
                <li><strong>Ghé qua cả cảnh trước đã.</strong> Chọn chương, đọc vài câu trước và sau để bắt nhịp câu chuyện. Đang lọc “Chưa dịch”? Bạn có thể về “Tất cả câu thoại” để xem thêm ngữ cảnh.</li>
                <li><strong>Lượm chút chất liệu.</strong> Đọc bản EN, ngó bản dịch cũ và tra từ điển khi cần. Bản cũ là một gợi ý để tham khảo, bạn hoàn toàn có thể tìm ra cách kể hay hơn.</li>
                <li><strong>Thử viết theo cách của bạn.</strong> Cứ viết nháp thoải mái, rồi đọc lại thành tiếng. Đổi nhịp, tách câu hay đảo ý cho thuận tiếng Việt đều được, miễn ý nghĩa và cảm xúc vẫn còn nguyên.</li>
                <li><strong>Ưng rồi thì lưu.</strong> Ở Visual Novel, dùng “Lưu &amp; Tiếp tục” hoặc <kbd>Ctrl+Enter</kbd>. Ở Danh Sách, nhớ bấm lưu từng dòng nhé; nhập vào ô mới chỉ là bước soạn nháp.</li>
                <li><strong>Gửi đi, rồi cùng nhau trau chuốt.</strong> Lưu sẽ đặt câu ở “Đã dịch”; “Đã duyệt” là bước review riêng. Nếu muốn chắc bản dịch đã đến nơi, mở Google Sheets và xem đúng ID, nội dung. EXP hiện lên chưa đủ xác nhận đồng bộ; mất mạng thì kiểm tra lại Sheet khi kết nối trở lại, trước khi đóng trang.</li>
            </ol>
            <p class="guide-note">Bản EN trên màn hình là điểm xuất phát. Bạn có thể nghe JP/CN để cảm nhận ngữ điệu, nhưng lời lồng tiếng chưa chắc khớp từng câu EN. Gặp chỗ khó hiểu, cứ ghi lại ID rồi rủ người review cùng gỡ.</p>
            <p><strong>Phím tắt khi đang biên tập:</strong> <kbd>Alt+G</kbd> mở từ điển, <kbd>Alt+←</kbd> / <kbd>Alt+→</kbd> chuyển câu, <kbd>Alt+S</kbd> lưu. Đóng hướng dẫn để tiếp tục dùng các phím này.</p>` },
        { id: 'style', title: 'Văn phong', keywords: 'van phong light novel tu nhien hai huoc dau cau ten rieng', body: `
            <ul>
                <li><strong>Dịch đúng ý, viết cho ra chất của bạn.</strong> Hãy tưởng tượng nhân vật đang nói tiếng Việt thật sự. Bạn có thể đảo câu, đổi nhịp, dùng khẩu ngữ hoặc một cách ví von duyên hơn, thay vì bám từng chữ EN.</li>
                <li><strong>Cho lời thoại chút cá tính.</strong> Có cảnh cần ngắn, có cảnh cần mềm, có lúc một câu cụt lại rất đúng cảm xúc. Thử nhiều cách, đọc lên và chọn câu khiến bạn nghe ra nhân vật.</li>
                <li><strong>Cứ sáng tạo với câu đùa.</strong> Bạn có thể biến tấu lối chơi chữ hoặc cách tung hứng cho hợp người đọc Việt. Chỉ cần tiếng cười vẫn hợp tình huống và nhân vật; nếu bản địa hóa khá xa, để lại ghi chú để mọi người hiểu lựa chọn của bạn.</li>
                <li><strong>Tên gọi là điểm hẹn chung.</strong> Tra từ điển để tên nhân vật và thuật ngữ liền mạch giữa các cảnh. Bạn có đề xuất mới hay hơn? Cứ mang ra trao đổi. Tên chiêu có thể hào sảng, còn lời trò chuyện cứ gần gũi, dễ hiểu là đẹp.</li>
                <li><strong>Thả sức ở cách kể, chắc tay ở ý nghĩa.</strong> Sau khi viết, liếc lại ai làm gì, phủ định, điều kiện, số và mức độ. “Có thể” hay “chắc chắn” đôi khi chỉ khác vài chữ mà khác cả ý.</li>
                <li><strong>Một lượt đọc cuối.</strong> Sửa dấu, lỗi gõ, chỗ hụt hơi và những từ lặp. Không cần ép mọi câu vào một khuôn; câu đọc tự nhiên và đúng cảm xúc là điều mình hướng tới.</li>
            </ul>` },
        { id: 'pronouns', title: 'Xưng hô', keywords: 'xung ho nguoi noi nguoi nghe quan he dai tu tinh cach', body: `
            <ol>
                <li><strong>Nghe xem ai đang nói với ai.</strong> Lời gọi và lượt đáp là những manh mối tốt. Ảnh nhân vật trên màn hình hay một cái tên được nhắc tới đôi khi chưa nói hết tình huống.</li>
                <li><strong>Chọn cách gọi hợp khoảnh khắc.</strong> Hai người có thể nói khác khi ở riêng, trước đám đông hoặc trong hồi tưởng. Cách A gọi B cũng có thể khác cách B gọi A.</li>
                <li><strong>Để quan hệ dẫn đường.</strong> Tham khảo cách xưng hô đã thống nhất ở cùng giai đoạn. Muốn đổi để diễn tả một bước ngoặt? Cứ đề xuất, kèm dấu hiệu trong cảnh để người review cùng cân nhắc.</li>
                <li><strong>Chưa rõ cũng không sao.</strong> Có lúc lược đại từ hoặc gọi tên sẽ tự nhiên hơn, miễn vẫn rõ ý. Nếu lựa chọn phụ thuộc tuổi, vai vế hay người nghe chưa rõ, giữ câu hỏi mở và ghi lại ID để trao đổi.</li>
            </ol>
            <p class="guide-note">Xưng hô là chỗ tiếng Việt rất giàu sắc thái. Cứ linh hoạt theo cảnh; khi thiếu thông tin, chưa cần ép thành “tôi–bạn” hay đoán quan hệ từ ngoại hình. Một ghi chú nhỏ có thể giúp cả nhóm chọn cách gọi hay hơn.</p>` },
        { id: 'tokens', title: 'Token & tag', keywords: 'token tag the dinh dang bien placeholder ma code rich text xuong dong', body: `
            <p><strong>Phần chữ cứ bay bổng, phần mã mình giữ nguyên nhé.</strong> Token là chỗ game điền tên, số hoặc định dạng. Bạn có thể chuyển biến tới vị trí thuận câu Việt; nhớ giữ đúng mã, số lần xuất hiện và đoạn chữ mà thẻ bao quanh.</p>
            <ul>
                <li><strong>Biến và mã thay thế:</strong> <code>{0}</code>, <code>{name}</code>, <code>$\{value}</code>, <code>%s</code>, <code>%1$d</code>, <code>==PLAYER_NAME==</code>. Để nguyên phần bên trong, game sẽ tự điền lúc hiển thị.</li>
                <li><strong>Thẻ hiển thị:</strong> <code>&lt;color=#FFCC00&gt;…&lt;/color&gt;</code>, <code>&lt;b&gt;…&lt;/b&gt;</code>, <code>&lt;sprite=2&gt;</code>. Giữ cặp mở–đóng, thứ tự lồng và đúng đoạn chữ được nhấn mạnh; không đổi màu, chỉ số sprite hay tên thuộc tính.</li>
                <li><strong>Xuống dòng và dữ liệu khác:</strong> giữ mã <code>\\n</code> nếu nguồn có, cùng URL, ID, tên khóa và công thức. Phân biệt hai ký tự “\\n” với một lần nhấn Enter trong ô nhập.</li>
                <li><strong>Dùng khay token để chèn đúng mã.</strong> Sau khi chèn, đọc lại vị trí trong câu. Nếu một token có hai lần ở nguồn, một lần ở bản Việt vẫn là thiếu.</li>
            </ul>
            <p class="guide-note">Cảnh báo giúp tìm một số token còn thiếu, nhưng chưa nhìn ra mọi trường hợp. Bạn giúp xem thêm mã thừa, cặp/thứ tự thẻ, biến có tên như <code>{name}</code> và <code>\\n</code> nhé. Gặp mã lạ thì giữ nguyên và ghi ID để cùng kiểm tra.</p>
            <p class="guide-footer">Các mã trên là ví dụ minh họa cú pháp, không phải trích dẫn câu thoại game.</p>` },
        { id: 'checklist', title: 'Checklist trước khi lưu', keywords: 'checklist tu kiem ra soat truoc khi luu review duyet', body: `
            <p>Trước khi gửi, dành một lượt đọc lại thật nhẹ nhàng. Đánh dấu nếu bạn thấy tiện; đây là lời nhắc cho mình, không phải bài thi hay điều kiện bắt buộc để lưu.</p>
            <fieldset class="guide-checklist">
                <legend>Mỗi lần mở sẽ có checklist mới. Chuyển câu thì bạn bỏ tích để xem lại nhé.</legend>
                <label><input type="checkbox" data-guide-check> <span>Đúng nghĩa: đủ ý, phủ định, điều kiện, số và đối tượng.</span></label>
                <label><input type="checkbox" data-guide-check> <span>Đúng giọng và xưng hô: đã đọc câu trước/sau, biết ai nói với ai.</span></label>
                <label><input type="checkbox" data-guide-check> <span>Nhất quán tên riêng và thuật ngữ của dự án.</span></label>
                <label><input type="checkbox" data-guide-check> <span>Đủ token/tag, đúng số lần, cặp thẻ, phạm vi và mã xuống dòng.</span></label>
                <label><input type="checkbox" data-guide-check> <span>Câu Việt nghe tự nhiên, có cảm xúc, đủ dấu và đúng tinh thần nguồn.</span></label>
                <label><input type="checkbox" data-guide-check> <span>Đã ghi lại ID và vấn đề cần hỏi nếu nguồn hoặc ngữ cảnh chưa rõ.</span></label>
            </fieldset>
            <p id="guideCheckStatus" class="guide-check-status" role="status">Đã tự kiểm 0/6 mục.</p>
            <button type="button" class="guide-reset" id="guideResetChecklist">Bỏ chọn tất cả</button>
            <p class="guide-note">Ưng câu chữ rồi? Đóng sổ tay và lưu ở ô biên tập nhé. Checklist chỉ giúp bạn tự đọc lại, không lưu câu hay chuyển sang “Đã duyệt”; phần review là dịp để cả nhóm cùng làm câu dịch tốt hơn.</p>` }
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
        dialog.querySelector('#guideResultCount').textContent = `${count}/5 mục hướng dẫn`;
        dialog.querySelector('#guideEmpty').hidden = count !== 0;
    }

    function resetChecklist() {
        const dialog = document.getElementById('translationGuideDialog');
        dialog.querySelectorAll('[data-guide-check]').forEach(input => { input.checked = false; });
        updateChecklist();
    }

    function updateChecklist() {
        const dialog = document.getElementById('translationGuideDialog');
        const count = dialog.querySelectorAll('[data-guide-check]:checked').length;
        dialog.querySelector('#guideCheckStatus').textContent = `Đã tự kiểm ${count}/6 mục.${count === 6 ? ' Hãy đóng hướng dẫn để quay lại câu dịch; phần review vẫn là bước riêng.' : ''}`;
    }

    function init() {
        const dialog = document.getElementById('translationGuideDialog');
        dialog.innerHTML = `<div class="guide-shell">
            <div class="guide-header"><div><h2 id="translationGuideTitle" tabindex="-1">Sổ tay dịch thuật</h2><p id="translationGuideIntro">Một chút gợi ý, thật nhiều chỗ cho sáng tạo.</p></div><button type="button" id="guideClose" class="btn-circle" aria-label="Đóng hướng dẫn">${guideIcon('close')}</button></div>
            <div class="guide-layout">
                <nav class="guide-nav" aria-label="Các mục hướng dẫn"><button type="button" data-guide-topic="all" aria-pressed="true">${guideIcon('guide')}<span>Tất cả hướng dẫn</span></button>${sections.map(section => `<button type="button" data-guide-topic="${section.id}" aria-pressed="false">${guideIcon(section.id)}<span>${section.title}</span></button>`).join('')}</nav>
                <div class="guide-mobile-toolbar"><label class="guide-visually-hidden" for="guideTopicSelect">Chọn mục hướng dẫn</label><select id="guideTopicSelect"><option value="all">Tất cả hướng dẫn</option>${sections.map(section => `<option value="${section.id}">${section.title}</option>`).join('')}</select><button type="button" id="guideToggleSearch" class="guide-reset" aria-expanded="false" aria-controls="guideSearchTools" aria-label="Tìm trong hướng dẫn">${guideIcon('search')}</button></div>
                <div class="guide-reading" tabindex="0" role="region" aria-label="Nội dung hướng dẫn">
                    <div id="guideSearchTools" class="guide-search-tools"><label class="guide-search-label" for="guideSearch">Bạn muốn tìm gì? Gõ có dấu hay không dấu đều được.</label><div class="guide-search-row"><input id="guideSearch" type="search" placeholder="Xưng hô, token, cách lưu…" autocomplete="off"><button type="button" id="guideClearSearch" class="guide-reset">Xóa tìm</button></div></div>
                    <p id="guideResultCount" class="guide-result-count" role="status"></p>
                    <p id="guideEmpty" class="guide-empty" hidden>Không tìm thấy mục phù hợp. Thử từ khóa khác hoặc chọn “Tất cả hướng dẫn”.</p>
                    ${sections.map(section => `<article class="guide-section" data-guide-section="${section.id}" aria-labelledby="guideHeading-${section.id}"><div class="guide-section-heading">${guideIcon(section.id)}<h3 id="guideHeading-${section.id}">${section.title}</h3></div>${section.body}</article>`).join('')}
                    <p class="guide-footer">Sổ tay đồng hành cùng người dịch Stella Sora. Cứ thử, trao đổi và cùng nhau trau chuốt. Bản nháp vẫn chờ bạn ở ô biên tập; nhấn Esc hoặc nút đóng để quay lại.</p>
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
        dialog.querySelectorAll('[data-guide-check]').forEach(input => input.addEventListener('change', updateChecklist));
        dialog.querySelector('#guideResetChecklist').addEventListener('click', resetChecklist);
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
        resetChecklist();
        filterSections();
        dialog.showModal();
        // Do not bring up the phone keyboard just to read the guide.
        dialog.querySelector(window.matchMedia('(max-width:700px), (max-width:900px) and (max-height:500px)').matches ? '#translationGuideTitle' : '#guideSearch').focus({ preventScroll: true });
        dialog.querySelector('.guide-reading').scrollTop = 0;
    };
})();
