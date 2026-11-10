import { createZip } from './handoff-zip.js?v=1';

const NAV = [
    { group: 'Workspace', items: [
        { id: 'overview', label: 'Tổng quan', icon: '◫' },
        { id: 'queue', label: 'Hàng chờ duyệt', icon: '✓', count: 0 },
        { id: 'issues', label: 'Câu cần kiểm tra', icon: '!', count: 0 },
        { id: 'export', label: 'Xuất dữ liệu', icon: '⇩' },
    ] },
    { group: 'Handoff', items: [
        { id: 'history', label: 'Lịch sử bản xuất', icon: '◷' },
        { id: 'recovery', label: 'Lịch sử & khôi phục', icon: '↻' },
        { id: 'sessions', label: 'Phiên dữ liệu', icon: '▣' },
        { id: 'prompt', label: 'Prompt cho agent', icon: '✎' },
    ] },
    { group: 'Governance', items: [{ id: 'governance', label: 'Phân quyền & nhật ký', icon: '♙' }] },
];

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));
const state = {
    key: '',
    view: 'overview',
    chapterId: 'Chuong_0_MainStory',
    chapters: [],
    chapter: null,
    lines: [],
    release: null,
    selectedLineId: '',
    history: null,
    loading: false,
    error: '',
    exports: [],
    exportRecords: [],
    queueItems: [],
    issueItems: [],
    overview: null,
    permissions: null,
    queueFilter: 'all',
    queueSearch: '',
    exportType: 'handoff',
    agentInstructions: '',
    completedHandoff: null,
    lastDownload: null,
    feedback: '',
    mobileOpen: false,
};
const previewMode = new URLSearchParams(window.location.search).get('preview') === '1' && /^(localhost|127\.0\.0\.1|\[::1\])$/.test(window.location.hostname);
const HANDOFF_KEY = 'tramvh_reviewer_key';
const AGENT_PROMPT_TEMPLATE = `Bạn là coding agent tiếp tục dự án Stella Sora Việt Hóa.

Nhiệm vụ: đối chiếu Merge và chuẩn bị proposal tích hợp theo gói TrạmVH.
Đọc trước: docs/HACHIMINH_WORKFLOW_INTEGRATION.md và SS/.agents/skills/workflow/SKILL.md.
Đọc changes.jsonl để biết câu VI được giao, mapping.jsonl để kiểm tra đích, issues.jsonl để xử lý blocker.
Bảo toàn source, ID, token, thứ tự block và nội dung ngoài phạm vi. Không ghi trực tiếp vào game khi locator chưa được xác minh.
Khi đủ căn cứ, tạo proposal/staging theo workflow repo; chạy audit đúng phạm vi và trả receipt/checkpoint.
Dừng ngay nếu source_hash đổi, locator trùng, thiếu source thật hoặc mapping chưa đủ bằng chứng.`;

state.agentInstructions = AGENT_PROMPT_TEMPLATE;

function statusOf(line) {
    const status = String(line?.status || '').toLowerCase();
    if (status === 'approved' || status === 'đã duyệt') return 'approved';
    if (status === 'needs_review' || status === 'cần xem lại') return 'needs_review';
    if (status === 'pending' || status.includes('chờ duyệt')) return 'pending';
    if (status === 'machine_pending') return 'machine_pending';
    if (status === 'untranslated' || status === 'chờ dịch') return 'untranslated';
    return line?.new_vi ? 'translated' : 'untranslated';
}

function labelStatus(status) {
    return ({ approved: 'Đã duyệt', pending: 'Chờ duyệt', needs_review: 'Cần xem lại', machine_pending: 'Chờ kiểm tra máy', untranslated: 'Chưa có bản dịch', translated: 'Đã dịch' })[status] || status;
}

function toneFor(status) {
    return status === 'approved' || status === 'translated' ? 'green' : status === 'needs_review' ? 'red' : status === 'pending' || status === 'machine_pending' ? 'gold' : 'blue';
}

function flattenChapter(chapter) {
    return (chapter?.scenes || []).flatMap(scene => (scene.lines || []).map(line => ({ ...line, scene_title: scene.title, scene_id: scene.scene_id, chapter_id: chapter.chapter_id })));
}

function stats() {
    if (state.overview && !previewMode) {
        const row = state.overview;
        return { total: Number(row.total || 0), approved: Number(row.approved || 0), translated: Number(row.translated || 0), queue: Number(row.queue || 0), issues: Number(row.issues || 0), ready: Math.max(0, Number(row.approved || 0) - Number(row.issues || 0)) };
    }
    const lines = state.lines;
    const approved = lines.filter(line => statusOf(line) === 'approved').length;
    const translated = lines.filter(line => Boolean(String(line.new_vi || '').trim())).length;
    const queue = lines.filter(line => ['pending', 'needs_review', 'machine_pending'].includes(statusOf(line)) || Number(line.pending_proposals) > 0).length;
    const issues = lines.filter(line => statusOf(line) === 'needs_review' || (!String(line.new_vi || '').trim() && String(line.en || '').trim())).length;
    return { total: lines.length, approved, translated, queue, issues, ready: Math.max(0, approved - issues) };
}

function queueLines() {
    if (state.queueItems.length && !previewMode) return state.queueItems;
    const list = state.lines.filter(line => ['pending', 'needs_review', 'machine_pending'].includes(statusOf(line)) || Number(line.pending_proposals) > 0);
    return list;
}

function issueLines() {
    if (state.issueItems.length && !previewMode) return state.issueItems;
    return state.lines.filter(line => statusOf(line) === 'needs_review' || (!String(line.new_vi || '').trim() && String(line.en || '').trim())).slice(0, 80);
}

async function request(path, options = {}, raw = false) {
    const headers = { Accept: 'application/json', ...(options.headers || {}) };
    if (state.key) headers['X-Reviewer-Key'] = state.key;
    const response = await fetch(path, { ...options, headers });
    const type = response.headers.get('content-type') || '';
    if (!response.ok) {
        let message = `Yêu cầu thất bại (HTTP ${response.status}).`;
        if (type.includes('json')) { const body = await response.json().catch(() => null); message = body?.message || body?.error || message; }
        throw Object.assign(new Error(message), { status: response.status });
    }
    if (!raw && type.includes('json')) return response.json();
    return response;
}

async function loadChapters() {
    try { state.chapters = await request('/api/chapters'); }
    catch (_) { state.chapters = await fetch('data/chapters.json', { cache: 'no-store' }).then(response => response.json()); }
    if (!state.chapters.some(chapter => chapter.id === state.chapterId)) state.chapterId = state.chapters[0]?.id || 'Chuong_0_MainStory';
}

async function loadChapter(id = state.chapterId) {
    state.chapterId = id;
    if (previewMode) state.chapter = await fetch(`data/chapters/${encodeURIComponent(id)}.json`, { cache: 'no-store' }).then(response => { if (!response.ok) throw new Error('Không tải được dữ liệu xem thử.'); return response.json(); });
    else state.chapter = await request(`/api/chapter_data?id=${encodeURIComponent(id)}`);
    state.lines = flattenChapter(state.chapter);
    state.selectedLineId = state.selectedLineId && state.lines.some(line => line.line_id === state.selectedLineId) ? state.selectedLineId : state.lines[0]?.line_id || '';
}

async function loadWorkspace() {
    state.loading = true;
    state.error = '';
    render();
    try {
        if (!previewMode) await request('/api/collab/me');
        await loadChapters();
        await loadChapter();
        if (!previewMode) {
            const [release, overview, queue, issues, exports, permissions] = await Promise.all([
                request('/api/collab/release'), request('/api/admin/overview'), request('/api/admin/queue?limit=200'),
                request('/api/admin/issues?limit=200'), request('/api/admin/exports'), request('/api/admin/permissions'),
            ]);
            state.release = release;
            state.overview = overview.data;
            state.queueItems = overview.data ? (queue.data?.items || []) : [];
            state.issueItems = issues.data?.items || [];
            state.exportRecords = exports.data?.items || [];
            state.permissions = permissions.data || null;
        } else state.release = { dataset: { version: 'local-preview-2026.11.10', phase: 'open', hash: 'local-only' }, pending_proposals: stats().queue };
    } catch (error) {
        state.error = error.message || 'Không thể tải dữ liệu TrạmVH.';
    } finally {
        state.loading = false;
        render();
    }
}

function icon(name, className = '') { return `<span class="${className}" aria-hidden="true">${esc(name)}</span>`; }

function pill(text, tone = '') { return `<span class="pill ${tone}">${esc(text)}</span>`; }

function emptyState(title, message, action = 'reload', label = 'Tải lại dữ liệu') {
    return `<div class="empty-state"><div><strong>${esc(title)}</strong><p>${esc(message)}</p>${action ? `<button type="button" class="btn small" data-action="${esc(action)}">${esc(label)}</button>` : ''}</div></div>`;
}

function openModal({ title, message = '', fields = [], confirmLabel = 'Xác nhận', tone = 'primary' }) {
    const dialog = $('#adminDialog');
    return new Promise(resolve => {
        let settled = false;
        const finish = value => {
            if (settled) return;
            settled = true;
            if (dialog.open) dialog.close();
            resolve(value);
        };
        const fieldMarkup = fields.map(field => {
            const control = field.type === 'select'
                ? `<select name="${esc(field.name)}" ${field.required ? 'required' : ''}>${(field.options || []).map(option => `<option value="${esc(option.value)}" ${option.value === field.value ? 'selected' : ''}>${esc(option.label)}</option>`).join('')}</select>`
                : field.type === 'textarea'
                    ? `<textarea name="${esc(field.name)}" rows="${field.rows || 3}" placeholder="${esc(field.placeholder || '')}" ${field.required ? 'required' : ''}>${esc(field.value || '')}</textarea>`
                    : `<input name="${esc(field.name)}" type="${esc(field.type || 'text')}" value="${esc(field.value || '')}" placeholder="${esc(field.placeholder || '')}" ${field.required ? 'required' : ''}>`;
            return `<label class="modal-field"><span>${esc(field.label)}</span>${control}</label>`;
        }).join('');
        dialog.innerHTML = `<form method="dialog" class="admin-modal-card"><div class="admin-modal-head"><div><p class="eyebrow">TrạmVH · Admin Portal</p><h2>${esc(title)}</h2></div><button type="button" class="icon-btn" data-modal-cancel aria-label="Đóng">×</button></div>${message ? `<p class="admin-modal-message">${esc(message)}</p>` : ''}<div class="admin-modal-fields">${fieldMarkup}</div><div class="admin-modal-actions"><button type="button" class="btn" data-modal-cancel>Hủy</button><button type="submit" class="btn ${tone === 'danger' ? 'danger' : 'primary'}">${esc(confirmLabel)}</button></div></form>`;
        const cancel = () => finish(null);
        dialog.querySelectorAll('[data-modal-cancel]').forEach(button => { button.addEventListener('click', cancel); });
        dialog.querySelector('form').addEventListener('submit', event => {
            event.preventDefault();
            finish(Object.fromEntries(new FormData(event.currentTarget).entries()));
        });
        dialog.addEventListener('cancel', event => { event.preventDefault(); cancel(); }, { once: true });
        dialog.showModal();
    });
}

function openAdminGuide() {
    const dialog = $('#adminDialog');
    dialog.innerHTML = `<div class="admin-modal-card admin-guide"><div class="admin-modal-head"><div><p class="eyebrow">TrạmVH · Admin Portal</p><h2>Hướng dẫn cho admin</h2></div><button type="button" class="icon-btn" data-guide-close aria-label="Đóng">×</button></div>
    <p class="admin-guide-intro">Mới dùng trang này? Bạn cứ làm lần lượt từ phần 1. Bấm vào từng mục để xem các bước.</p>
    <div class="admin-guide-sections">
    <details open><summary><span>01</span> Vào trang quản trị</summary><div><ol><li>Nhập mã được cấp vào ô <b>Mã quản trị</b>, rồi bấm <b>Đăng nhập</b>.</li><li>Vào <b>Tổng quan</b> để xem còn bao nhiêu câu đang chờ bạn kiểm tra.</li><li>Nếu cần biết trang đang dùng phiên bản dữ liệu nào, mở <b>Phiên dữ liệu</b>. Mã reviewer là mã riêng của bạn, đừng gửi mã này cho agent.</li></ol><p><b>Đang xem thử trên máy?</b> Bấm “Mở bản xem trước local”. Những gì bạn làm ở bản này chỉ để xem thử, không cập nhật lên trang chính.</p></div></details>
    <details><summary><span>02</span> Duyệt câu dịch</summary><div><ol><li>Bấm <b>Hàng chờ duyệt</b> bên trái. Nếu cần tìm một câu cụ thể, nhập nội dung hoặc mã câu vào ô tìm kiếm.</li><li>Bấm vào câu cần xem. Đọc bản tiếng Anh trong ô <b>EN · nguồn gốc</b>, rồi đọc bản dịch trong ô <b>VI · đang dùng</b>.</li><li>Để xem bản dịch người khác đề xuất, bấm <b>Xem lịch sử &amp; đề xuất</b>. Đọc xong, bấm <b>Chấp nhận</b> nếu đồng ý hoặc <b>Từ chối</b> nếu không đồng ý.</li><li>Nếu bản dịch đang dùng đã ổn, bấm <b>Duyệt bản hiện tại</b>. Nếu cần sửa câu, bấm <b>Mở workspace</b> để về trang dịch.</li></ol><p>Nếu chưa biết câu dịch có đúng không, đừng vội duyệt. Hãy báo lại theo phần 3.</p></div></details>
    <details><summary><span>03</span> Báo câu cần kiểm tra</summary><div><ol><li>Chọn câu cần kiểm tra, rồi bấm <b>Báo issue</b>.</li><li>Ghi lý do, ví dụ: “Chưa rõ câu này đang nói về ai”. Sau đó bấm <b>Ghi issue</b>.</li><li>Mở <b>Câu cần kiểm tra</b> để xem lại danh sách. Nếu cần lưu riêng, bấm <b>Tải issues.jsonl</b>.</li></ol><p>Những câu này sẽ được ghi lại để người xử lý sau biết cần kiểm tra chỗ nào.</p></div></details>
    <details><summary><span>04</span> Chuẩn bị lời nhắn cho agent</summary><div><ol><li>Bấm <b>Prompt cho agent</b> trong menu. “Prompt” ở đây là lời nhắn bạn gửi cho Codex hoặc AI đang giúp bạn.</li><li>Đọc lời nhắn mẫu, rồi sửa theo việc bạn muốn giao: làm chương nào, cần làm gì và báo lại cho bạn những gì.</li><li>Nếu mẫu đã đúng ý, bạn có thể để nguyên. Nhớ giữ lời dặn kiểm tra nguồn và không sửa ngoài phần được giao.</li></ol><p><b>Ví dụ bạn có thể thêm:</b> “Chỉ xử lý chương đã chọn. Nếu không tìm thấy câu gốc, hãy dừng và liệt kê câu cần tôi kiểm tra.” Lời nhắn bạn sửa được giữ trong tab này. Khi tạo gói, trang sẽ lưu lời nhắn vào gói.</p></div></details>
    <details><summary><span>05</span> Tạo gói bàn giao</summary><div><ol><li>Chọn <b>Xuất dữ liệu</b>, rồi chọn <b>Gói bàn giao agent</b>.</li><li>Trong <b>Phạm vi dữ liệu</b>, chọn chương bạn muốn giao. Xem lại tên phiên và số câu trên trang.</li><li>Xem phần <b>Kiểm tra input gate</b> và số câu cần kiểm tra. Nếu còn câu chưa rõ, bạn có thể quay lại phần 3 để xem.</li><li>Bấm <b>Tạo gói xem trước</b>. Tạo xong, trang sẽ mở <b>Lịch sử bản xuất</b> và hiện mã gói vừa tạo.</li></ol><p>Nếu có lỗi, đọc thông báo trên trang rồi thử lại sau khi xử lý. Tạo gói xong chưa có nghĩa là bản dịch đã vào game.</p></div></details>
    <details><summary><span>06</span> Gửi gói cho agent</summary><div><ol><li>Trong <b>Lịch sử bản xuất</b>, tìm mã gói vừa tạo. Bấm từng nút <b>Tải</b> để tải đủ các tệp.</li><li>Để các tệp vào cùng một thư mục. Giữ nguyên tên tệp và đừng trộn với tệp của gói khác.</li><li>Ở phần “Đã tạo gói”, bấm <b>Sao chép prompt</b>. Nếu nút không hoạt động, bạn có thể tự chọn và sao chép chữ trong ô, hoặc mở tệp <b>AGENT_PROMPT.md</b> vừa tải.</li><li>Dán lời nhắn vào Codex hoặc công cụ AI bạn dùng. Gửi kèm các tệp đã tải, hoặc cho agent biết đường dẫn đến thư mục chứa chúng.</li></ol><p><b>Sau đó:</b> Nhờ agent báo lại đã làm gì, còn vướng gì và tạo những tệp nào. Đọc kết quả trước khi chuyển sang bước tiếp theo.</p></div></details>
    <details><summary><span>07</span> Đưa bản dịch lên GitHub</summary><div><p>Sau khi agent làm xong, xem lại kết quả và xác định phần nào đã sẵn sàng đưa lên GitHub. Tạo gói ở phần trên chưa tự đưa bản dịch lên GitHub.</p><ol><li>Mở Codex trong thư mục dự án trên máy có cài skill <b>stella-github-translation-sync</b> (Nếu chưa có skill, hãy bấm <a class="admin-guide-link" href="https://drive.google.com/file/d/1nfqQ1SFXZC5kqOGJjmYl87zykW7aJN54/view?usp=sharing" target="_blank" rel="noopener noreferrer">vào đây</a> để tải)</li><li>Sao chép lời nhắn bên dưới, điền phần bản dịch cần đưa lên, rồi gửi cho agent. Bạn cũng có thể ghi rõ nhánh đích nếu đã biết.</li><li>Đợi agent kiểm tra và đưa thay đổi lên GitHub. Nếu agent hỏi thiếu repo, nhánh hoặc quyền chia sẻ, hãy cung cấp thêm thông tin.</li><li>Làm xong, agent cần gửi lại link commit, tên nhánh, danh sách tệp đã đưa lên và kết quả kiểm tra. Nếu chưa thấy, hãy hỏi lại agent.</li></ol><p><b>Lời nhắn mẫu:</b></p><textarea class="prompt-editor admin-guide-prompt" rows="9" readonly aria-label="Lời nhắn đưa bản dịch lên GitHub">Dùng skill $stella-github-translation-sync để đồng bộ bản dịch Stella Sora đã hoàn tất lên GitHub.

Phạm vi được phép đưa lên: [ghi chương, tệp hoặc phần việc đã kiểm tra].
Nhánh đích: [ghi nhánh nếu biết; nếu chưa biết, hãy kiểm tra và báo lại khi không xác định được].

Hãy kiểm tra repo, thay đổi và kết quả kiểm tra; chỉ commit và push nội dung trong phạm vi trên. Giữ nguyên các thay đổi khác. Sau khi push, xác minh trên GitHub và báo link commit, nhánh, các tệp đã cập nhật và những việc còn vướng.</textarea><button type="button" class="btn small" data-guide-copy>Sao chép lời nhắn</button><p>Nếu Codex không tìm thấy skill, hãy tải và cài skill trên máy đang dùng. Đưa bản dịch lên GitHub không tự cập nhật game cho người chơi.</p></div></details>
    <details><summary><span>08</span> Một vài từ trên trang</summary><div><ul><li><b>Reviewer:</b> người xem và duyệt bản dịch.</li><li><b>Issue:</b> vấn đề hoặc câu cần kiểm tra thêm.</li><li><b>Agent:</b> AI bạn giao việc, ví dụ Codex.</li><li><b>Prompt:</b> lời nhắn hướng dẫn gửi cho agent.</li><li><b>Manifest:</b> tệp liệt kê thông tin và mã kiểm tra của các tệp trong gói.</li><li><b>Phiên dữ liệu / dataset:</b> phiên bản dữ liệu mà gói được tạo từ đó.</li></ul></div></details>
    </div><div class="admin-modal-actions"><button type="button" class="btn primary" data-guide-close>Đã hiểu</button></div></div>`;
    dialog.querySelectorAll('[data-guide-close]').forEach(button => button.addEventListener('click', () => dialog.close()));
    dialog.querySelector('[data-guide-copy]').addEventListener('click', async event => { const field = dialog.querySelector('.admin-guide-prompt'); try { await navigator.clipboard.writeText(field.value); event.currentTarget.textContent = 'Đã sao chép'; } catch (_) { field.focus(); field.select(); event.currentTarget.textContent = 'Chọn và sao chép trong ô'; } });
    dialog.showModal();
}

function brandMarkup() {
    return `<a class="brand admin-brand" href="index.html" aria-label="Trạm Việt Hóa - về trang dịch"><span class="admin-brand-lockup"><img class="admin-brand-logo" src="web_assets/viet-hoa-admin-transparent.png" alt="Việt Hóa Admin"></span></a>`;
}

function renderSidebar() {
    const side = $('#adminSidebar');
    const s = stats();
    side.classList.toggle('open', state.mobileOpen);
    $('#adminBackdrop').hidden = !state.mobileOpen;
    document.body.classList.toggle('mobile-menu-open', state.mobileOpen);
    const toggle = $('[data-action="toggle-mobile"]');
    if (toggle) toggle.setAttribute('aria-expanded', String(state.mobileOpen));
    const ready = Boolean(state.key);
    side.innerHTML = `${brandMarkup()}<div class="workspace-status ${ready ? '' : 'is-locked'}"><div class="workspace-status-row"><span class="pulse"></span> ${ready ? 'SYNC READY' : 'REVIEWER REQUIRED'}</div><p>${ready && state.release?.dataset?.version ? esc(state.release.dataset.version) : 'Chưa mở phiên reviewer'}<br>${ready && state.release?.dataset?.phase ? `Phase · ${esc(state.release.dataset.phase)}` : 'Nhập mã để truy cập workspace'}</p></div>${state.key ? `<nav class="side-nav">${NAV.map(group => `<section class="nav-group"><p class="nav-label">${esc(group.group)}</p><div>${group.items.map(item => { const count = item.id === 'queue' ? s.queue : item.id === 'issues' ? s.issues : item.count; return `<button type="button" class="nav-item ${state.view === item.id ? 'active' : ''}" aria-current="${state.view === item.id ? 'page' : 'false'}" data-nav="${item.id}"><span class="nav-item-main">${icon(item.icon, 'nav-icon')}<span>${esc(item.label)}</span></span>${count ? `<span class="nav-count">${count}</span>` : ''}</button>`; }).join('')}</div></section>`).join('')}</nav>` : '<div class="side-nav"></div>'}<div class="side-footer">${state.key ? `<div class="side-user"><span class="avatar">R</span><span class="side-user-copy"><strong>Reviewer session</strong><span>Key chỉ giữ trong tab này</span></span><button type="button" data-action="logout" title="Tắt quyền duyệt">×</button></div>` : `<a class="side-user" href="index.html"><span class="avatar">←</span><span class="side-user-copy"><strong>Quay lại workspace</strong><span>Trang dịch hiện tại</span></span></a>`}</div>`;
}

function renderHeader() {
    const label = state.key ? (NAV.flatMap(group => group.items).find(item => item.id === state.view)?.label || 'Tổng quan') : 'Đăng nhập';
    $('#adminHeader').innerHTML = `<div class="header-left"><button type="button" class="mobile-menu" data-action="toggle-mobile" aria-controls="adminSidebar" aria-expanded="${state.mobileOpen}" aria-label="Mở menu">☰</button><div><div class="crumbs"><span>TrạmVH</span><b>/</b><span>Admin</span><b>/</b><b>${esc(label)}</b></div><p class="header-title">${esc(label)}</p></div></div><div class="header-right">${state.key ? '<label class="quick-search"><svg class="search-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.75" cy="10.75" r="6.75"/><path d="m16 16 4 4"/></svg><input id="globalSearch" aria-label="Tìm câu dịch" placeholder="Tìm câu dịch, mã câu..." autocomplete="off"></label>' : ''}${state.key ? '<button type="button" class="mobile-search" data-action="mobile-search" aria-label="Tìm câu dịch" title="Tìm câu dịch"><svg class="search-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.75" cy="10.75" r="6.75"/><path d="m16 16 4 4"/></svg></button>' : ''}<button type="button" class="btn header-guide" data-action="help">Hướng dẫn</button><span class="header-avatar"><span class="avatar">${state.key ? 'R' : '?'}</span><span>${state.key ? 'Reviewer' : 'Chưa xác thực'}</span></span></div>`;
}

function renderLogin() {
    return `<div class="login-wrap"><div class="login-card">${brandMarkup()}<h1>Admin Portal TrạmVH</h1><p>Điều phối duyệt câu, kiểm tra ánh xạ và tạo gói bàn giao bất biến cho coding agent.</p>${state.error ? `<div class="error" role="alert">${esc(state.error)}</div>` : ''}<form data-form="login"><label class="login-label">Mã quản trị<span class="login-input-wrap"><input id="reviewerKeyInput" class="login-input" name="key" type="password" autocomplete="off" placeholder="Nhập mã được cấp" required><button type="button" class="login-toggle" data-action="toggle-key" aria-controls="reviewerKeyInput" aria-pressed="false">Hiện</button></span></label><button class="btn primary" type="submit">Đăng nhập <span>→</span></button></form>${previewMode ? '<button type="button" class="btn" data-action="preview-login" style="width:100%;margin-top:9px">Mở bản xem trước local</button>' : ''}<div class="login-note">Mã chỉ nằm trong bộ nhớ của tab này và được gửi qua header <code>X-Reviewer-Key</code>. Portal không ghi mã vào gói bàn giao hay repository.</div></div></div>`;
}

function renderOverview() {
    const s = stats();
    const pct = s.total ? Math.round((s.ready / s.total) * 100) : 0;
    const chapter = state.chapters.find(item => item.id === state.chapterId);
    return `<div class="view-head"><div><p class="eyebrow">TrạmVH · workspace</p><h1>Tổng quan công việc</h1><p>Theo dõi những gì đã sẵn sàng để bàn giao và những điểm cần xác minh trước khi agent được phép ghi file.</p></div><button class="btn primary" type="button" data-nav="export">Tạo gói bàn giao <span>→</span></button></div><div class="stats-grid"><article class="stat-card"><div class="stat-top"><div><p class="stat-label">Chờ duyệt</p><p class="stat-value">${s.queue}</p></div><span class="stat-icon gold">◷</span></div><p class="stat-note">Câu đang chờ kiểm tra</p></article><article class="stat-card"><div class="stat-top"><div><p class="stat-label">Đã duyệt trên web</p><p class="stat-value">${s.approved}</p></div><span class="stat-icon green">✓</span></div><p class="stat-note">Trong dữ liệu đã ghi nhận</p></article><article class="stat-card"><div class="stat-top"><div><p class="stat-label">Đủ điều kiện bàn giao</p><p class="stat-value">${s.ready}</p></div><span class="stat-icon">♢</span></div><p class="stat-note">Sẵn sàng để kiểm tra trước khi giao</p></article></div><details class="secondary-stats"><summary>Chỉ số bổ sung <span>Issue và bản xuất đã khóa</span></summary><div class="secondary-stats-grid"><article class="stat-card"><div class="stat-top"><div><p class="stat-label">Kẹt ánh xạ / bằng chứng</p><p class="stat-value">${s.issues}</p></div><span class="stat-icon red">!</span></div><p class="stat-note">Tách khỏi changes.jsonl</p></article><article class="stat-card"><div class="stat-top"><div><p class="stat-label">Bản xuất đã khóa</p><p class="stat-value">${state.overview?.exports ?? state.exportRecords.length ?? 0}</p></div><span class="stat-icon purple">▣</span></div><p class="stat-note">Persisted export history</p></article></div></details><div class="grid-two"><section class="panel"><div class="panel-pad"><div class="scope-line"><div><p class="eyebrow">Phạm vi đang mở</p><h2>${esc(chapter?.title || 'Chương đang chọn')}</h2><p>${esc(state.chapterId)} · ${esc(state.release?.dataset?.version || 'dataset chưa tải')}</p></div>${pill(state.release?.dataset?.phase === 'open' ? 'Snapshot nhất quán' : 'Cần kiểm tra phase', state.release?.dataset?.phase === 'open' ? 'green' : 'gold')}</div><div class="readiness"><div class="ring" style="background:conic-gradient(var(--admin-cyan) 0 ${pct}%, #e4edf0 ${pct}% 100%)"><div class="ring-inner"><div><strong>${pct}%</strong><span>sẵn sàng</span></div></div></div><div class="readiness-copy"><strong>${s.ready} / ${s.total || 0} dòng</strong><p>Đã có bản dịch, source hash và trạng thái đủ để kiểm tra trước khi giao cho agent.</p><button type="button" class="text-link" data-nav="issues">Xem blockers <span>›</span></button></div></div><div class="bar-list" style="margin-top:24px"><div><div class="bar-row-head"><span>Đã dịch</span><b>${s.translated}</b></div><div class="bar-track"><div class="bar-fill green" style="width:${s.total ? Math.round(s.translated * 100 / s.total) : 0}%"></div></div></div><div><div class="bar-row-head"><span>Đã duyệt</span><b>${s.approved}</b></div><div class="bar-track"><div class="bar-fill" style="width:${s.total ? Math.round(s.approved * 100 / s.total) : 0}%"></div></div></div><div><div class="bar-row-head"><span>Cần reviewer</span><b>${s.queue}</b></div><div class="bar-track"><div class="bar-fill gold" style="width:${s.total ? Math.max(2, Math.round(s.queue * 100 / s.total)) : 0}%"></div></div></div></div></div></section><section class="panel"><div class="panel-pad"><p class="eyebrow">Cần chú ý</p><h2 class="panel-title">Ba việc trước khi xuất</h2><div class="attention-list"><button type="button" class="attention" data-nav="issues"><span class="attention-dot"></span><span><b>${s.issues ? `${s.issues} dòng cần kiểm tra` : 'Chưa có issue rõ ràng'}</b><span>Đưa issue ra khỏi nhóm có thể tích hợp.</span></span></button><button type="button" class="attention" data-nav="sessions"><span class="attention-dot gold"></span><span><b>Dataset ${esc(state.release?.dataset?.phase || 'chưa tải')}</b><span>Kiểm tra phiên web, Merge và catalog nguồn.</span></span></button><button type="button" class="attention" data-nav="governance"><span class="attention-dot blue"></span><span><b>Quyền server-side</b><span>${esc((state.permissions?.scopes || []).join(', ') || 'Chưa tải')}</span></span></button></div></div></section></div><div class="grid-two"><section class="panel"><div class="panel-head"><div><h2>Hàng chờ gần đây</h2><p>Những dòng đang cần reviewer nhìn lại</p></div><button type="button" class="text-link" data-nav="queue">Mở hàng chờ →</button></div><div class="queue-mini">${queueLines().slice(0, 4).map(line => `<button type="button" class="queue-mini-row" data-line="${esc(line.line_id)}" data-chapter="${esc(line.chapter_id || state.chapterId)}" data-nav="queue"><div><b>${esc(line.line_id)}</b><span>${esc(line.speaker || line.scene_title || line.chapter_id || 'Không có cảnh')}</span></div>${pill(labelStatus(statusOf(line)), toneFor(statusOf(line)))}</button>`).join('') || emptyState('Hàng chờ đang trống', 'Không có câu cần reviewer trong phạm vi hiện tại.', 'queue', 'Mở hàng chờ')}</div></section><section class="panel"><div class="panel-pad"><p class="eyebrow">Audit trail</p><h2 class="panel-title">Dòng thời gian phiên</h2><div class="timeline"><div class="timeline-item"><span class="timeline-dot"></span><div><p><b>Reviewer session</b> đã bật quyền đọc gói</p><small>Trong tab hiện tại</small></div></div><div class="timeline-item"><span class="timeline-dot"></span><div><p><b>${esc(state.release?.dataset?.version || 'Dataset')}</b> đang được theo dõi</p><small>Phạm vi ${esc(state.chapterId)}</small></div></div><div class="timeline-item"><span class="timeline-dot"></span><div><p><b>Snapshot server-side</b> được ghi theo dataset version</p><small>Không tự ghi receipt agent</small></div></div></div></div></section></div>`;
}

function renderQueue() {
    const all = queueLines();
    const list = all.filter(line => (state.queueFilter === 'all' || statusOf(line) === state.queueFilter) && `${line.line_id} ${line.en || ''} ${line.new_vi || ''} ${line.chapter_id || ''}`.toLowerCase().includes(state.queueSearch.toLowerCase()));
    const selected = state.lines.find(line => line.line_id === state.selectedLineId) || all.find(line => line.line_id === state.selectedLineId) || list[0];
    if (selected && selected.line_id !== state.selectedLineId) state.selectedLineId = selected.line_id;
    const filters = ['all', 'pending', 'needs_review', 'untranslated'];
    const rows = list.length ? list.map(line => `<button type="button" class="queue-row ${line.line_id === state.selectedLineId ? 'selected' : ''}" data-line="${esc(line.line_id)}" data-chapter="${esc(line.chapter_id || state.chapterId)}"><div class="queue-row-top"><b>${esc(line.line_id)}</b><time>${esc(line.updated_at ? new Date(line.updated_at).toLocaleDateString('vi-VN') : 'Chưa ghi thời gian')}</time></div><p>${esc(line.scene_title || line.speaker || line.chapter_id || 'Không có cảnh')} · ${esc(line.speaker || 'Hệ thống')}</p><div class="queue-row-bottom"><span>${esc(line.en || 'Chưa có EN')}</span>${pill(labelStatus(statusOf(line)), toneFor(statusOf(line)))}</div></button>`).join('') : emptyState('Hàng chờ đang trống', 'Không có câu phù hợp với bộ lọc hiện tại. Tải lại dữ liệu hoặc đổi bộ lọc.', 'reload', 'Tải lại dữ liệu');
    return `<div class="view-head"><div><p class="eyebrow">Review gate · 01</p><h1>Hàng chờ duyệt</h1><p>Duyệt câu dịch với đúng nguồn, bản đang dùng và đề xuất. Quyết định thật được gửi qua API cộng tác với revision guard.</p></div><div class="button-row"><button type="button" class="btn" data-action="reload">↻ Tải lại</button><button type="button" class="btn" data-nav="export">Đối chiếu trước khi xuất →</button></div></div><div class="toolbar"><label class="search-box"><svg class="search-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.75" cy="10.75" r="6.75"/><path d="m16 16 4 4"/></svg><input id="queueSearch" aria-label="Tìm trong hàng chờ duyệt" value="${esc(state.queueSearch)}" placeholder="Tìm mã câu hoặc nội dung..." autocomplete="off"></label>${filters.map(filter => `<button type="button" class="filter-btn ${filter === state.queueFilter ? 'active' : ''}" data-filter="${filter}">${filter === 'all' ? `Tất cả · ${all.length}` : labelStatus(filter)}</button>`).join('')}</div><section class="panel queue-shell"><div class="queue-list" id="queueList"><div class="queue-list-head"><strong>${list.length} dòng trong phạm vi</strong>${pill('Reviewer gate', 'gold')}</div><div id="queueRows">${rows}</div></div><div class="detail-pane" id="queueDetail" tabindex="-1"><button type="button" class="btn mobile-queue-back" data-action="queue-back">← Quay lại danh sách</button>${selected ? detailMarkup(selected) : emptyState('Chưa chọn câu', 'Chọn một dòng ở hàng chờ để xem nguồn và bằng chứng.')}</div></section>`;
}

function detailMarkup(line) {
    const status = statusOf(line);
    const refs = [line.scene_id, line.row_index ? `row ${line.row_index}` : '', line.source_hash ? `source ${String(line.source_hash).slice(0, 12)}…` : 'source hash chưa có'].filter(Boolean);
    return `<div class="detail-head"><div><span class="detail-id">${esc(line.line_id)}</span><h2>Đối chiếu bản dịch</h2><p>${esc(line.chapter_id || state.chapterId)} · ${esc(line.scene_title || 'Cảnh chưa đặt tên')} · ${esc(line.speaker || 'Không có speaker')}</p></div>${pill(labelStatus(status), toneFor(status))}</div>${line.source_hash ? '' : '<div class="warning"><span>!</span><div><b>Thiếu source hash trong dữ liệu đang đọc</b><p>Đây là bản preview local. Hãy tải qua Worker trước khi gửi quyết định review để kích hoạt revision guard.</p></div></div>'}<div class="source-card"><label>EN · nguồn gốc</label><p>${esc(line.en || 'Chưa có nguồn EN cho câu này.')}</p><div class="source-refs">${refs.map(ref => pill(ref)).join('')}</div></div><div class="compare-grid"><div class="compare-card"><label>VI · đang dùng</label><p>${esc(line.new_vi || line.old_vi || 'Chưa có bản dịch tiếng Việt.')}</p></div><div class="compare-card proposed"><label>VI · đề xuất / cần xử lý</label><p>${esc(line.proposed_vi || line.pending_text || 'Tải lịch sử để xem đề xuất đang chờ duyệt.')}</p></div></div><div class="detail-meta"><div class="meta-cell"><span>Revision</span><b>${esc(line.revision ?? 'legacy')}</b></div><div class="meta-cell"><span>Reviewer</span><b>${esc(line.approved_by || 'Chưa ghi nhận')}</b></div><div class="meta-cell"><span>Dataset</span><b>${esc(line.dataset_version || state.release?.dataset?.version || 'local')}</b></div></div><div class="detail-actions"><div class="left"><button type="button" class="text-link" data-action="history" data-id="${esc(line.line_id)}">Xem lịch sử & đề xuất</button><button type="button" class="text-link" data-action="open-editor">Mở workspace ↗</button></div><div class="button-row"><button type="button" class="btn danger" data-action="report" data-id="${esc(line.line_id)}">Báo issue</button><button type="button" class="btn primary" data-action="approve" data-id="${esc(line.line_id)}">✓ Duyệt bản hiện tại</button></div></div>${state.history?.line?.line_id === line.line_id ? historyMarkup(state.history) : ''}${state.error ? `<div class="error" style="margin-top:12px">${esc(state.error)}</div>` : ''}`;
}

function historyMarkup(data) {
    const pending = data.proposals || [];
    const events = data.history || [];
    return `<div class="history-detail"><div class="panel-head" style="padding:0 0 12px;border:0"><div><h2>Lịch sử & đề xuất</h2><p>${pending.length} đề xuất chờ · ${events.length} mốc lịch sử</p></div>${pill(data.history_provenance === 'History records reflect operations since collaboration was enabled; earlier edits may be unavailable.' ? 'Có thể thiếu lịch sử cũ' : 'Đã tải', data.history_provenance ? 'gold' : 'green')}</div>${pending.map(proposal => `<div class="compare-card proposed" style="margin-top:8px"><label>Đề xuất · ${esc(proposal.translator || 'Ẩn danh')}</label><p>${esc(proposal.text_vi || '')}</p><div class="button-row" style="margin-top:10px"><button class="btn small primary" type="button" data-action="accept" data-proposal="${esc(proposal.id)}">Chấp nhận</button><button class="btn small danger" type="button" data-action="reject" data-proposal="${esc(proposal.id)}">Từ chối</button></div></div>`).join('') || '<p class="panel-sub">Chưa có đề xuất đang chờ duyệt.</p>'}<div class="timeline" style="margin-top:15px">${events.slice(0, 5).map(event => `<div class="timeline-item"><span class="timeline-dot"></span><div><p><b>${esc(event.event_type || 'event')}</b> · ${esc(event.actor || 'Chưa ghi nhận')}</p><small>${esc(event.reason || '')} · ${esc(event.created_at || '')}</small></div></div>`).join('') || '<p class="panel-sub">Chưa có lịch sử trước khi bật cộng tác.</p>'}</div></div>`;
}

function renderIssues() {
    const issues = issueLines();
    const rows = issues.length ? issues.map(line => { const severe = line.event_type === 'needs_review' || statusOf(line) === 'needs_review'; return `<div class="table-row"><div><code>${esc(line.issue_id || 'ISS-REVIEW')}</code><small>${esc(line.line_id)}</small></div><div><b>${esc(line.reason || 'Cần đối chiếu')}</b><small>${esc(line.en || 'Không có EN')}</small></div><div>${pill(severe ? 'Cao' : 'Vừa', severe ? 'red' : 'gold')}</div><div>${icon('→')} Mở lịch sử và đối chiếu</div><div>${esc(line.translator || line.actor || 'Chưa giao')}</div></div>`; }).join('') : emptyState('Chưa có issue', 'Các câu cần kiểm tra sẽ xuất hiện ở đây sau khi reviewer báo vấn đề hoặc nguồn thay đổi.', 'queue', 'Mở hàng chờ');
    return `<div class="view-head"><div><p class="eyebrow">Evidence gate · 02</p><h1>Câu cần kiểm tra</h1><p>Danh sách vướng được lấy từ history/needs_review server-side. Mỗi issue có ID ổn định và bằng chứng nguồn.</p></div><button type="button" class="btn" data-action="download-issues">⇩ Tải issues.jsonl</button></div><div class="toolbar"><span class="pill red">${issues.length} issue trong phạm vi hiện tại</span><span class="pill">Nguồn: server audit</span></div><div class="table issues-table"><div class="table-head"><span>Issue / line</span><span>Nguyên nhân</span><span>Mức độ</span><span>Hành động tiếp theo</span><span>Owner</span></div>${rows}</div>`;
}

function renderExport() {
    const chapter = state.chapters.find(item => item.id === state.chapterId);
    const s = stats();
    return `<div class="view-head"><div><p class="eyebrow">Handoff builder · 03</p><h1>Đối chiếu trước khi xuất</h1><p>Đóng băng phạm vi, kiểm tra manifest và tạo dữ liệu bàn giao. Bản xem trước này dùng dataset thật đang đọc từ TrạmVH.</p></div>${pill(state.release?.dataset?.version || 'local preview', 'green')}</div><div class="export-grid"><div><section class="panel panel-pad"><div class="scope-line"><div><h2 class="panel-title">1. Chọn loại bản xuất</h2><p>Loại gói quyết định tệp và gate tiếp theo.</p></div><span class="pill">Bước 1 / 3</span></div><div class="export-options">${[['snapshot', 'Snapshot đầy đủ', 'Toàn bộ dòng trong phạm vi để đối chiếu.', '▣'], ['delta', 'Delta thay đổi', 'Các dòng khác với dữ liệu hiện tại.', '↻'], ['handoff', 'Gói bàn giao agent', 'manifest + changes + mapping + issues + TASK.', '♢']].map(([id, title, desc, glyph]) => `<button type="button" class="export-option ${state.exportType === id || (!state.exportType && id === 'handoff') ? 'selected' : ''}" data-export-type="${id}"><span class="option-icon">${glyph}</span><strong>${title}</strong><p>${desc}</p></button>`).join('')}</div></section><section class="panel panel-pad" style="margin-top:16px"><div class="scope-line"><div><h2 class="panel-title">2. Phạm vi dữ liệu</h2><p>Chỉ dòng đã qua input gate mới được đưa vào handoff.</p></div>${pill(`${s.ready} dòng đủ điều kiện`, 'blue')}</div><div class="select-grid"><label class="field"><span>Dataset version</span><select id="datasetSelect"><option>${esc(state.release?.dataset?.version || 'local-preview')}</option></select></label><label class="field"><span>Chapter</span><select id="chapterSelect">${state.chapters.map(item => `<option value="${esc(item.id)}" ${item.id === state.chapterId ? 'selected' : ''}>${esc(item.title || item.id)}</option>`).join('')}</select></label></div><div class="check-grid"><label class="check"><input type="checkbox" checked> Chỉ lấy câu đã duyệt</label><label class="check"><input type="checkbox" checked> Kèm ngữ cảnh tham khảo</label><label class="check"><input type="checkbox" checked> Khóa hash từng tệp</label><label class="check"><input type="checkbox" checked> Tạo TASK.json</label></div></section><section class="panel panel-pad" style="margin-top:16px"><h2 class="panel-title">3. Kiểm tra input gate</h2><div class="gate-list"><div class="gate-row"><span class="gate-main"><i class="gate-dot">✓</i> Nguồn EN và source_hash</span><b>${s.translated} / ${s.total}</b></div><div class="gate-row"><span class="gate-main"><i class="gate-dot">✓</i> Dataset version hiện tại</span><b>${esc(state.release?.dataset?.version || 'local')}</b></div><div class="gate-row"><span class="gate-main"><i class="gate-dot warn">!</i> Dòng cần xác minh locator</span><b>${s.issues}</b></div><div class="gate-row"><span class="gate-main"><i class="gate-dot">✓</i> Glossary scope</span><b>Đọc-only</b></div></div></section></div><aside class="handoff-card"><p class="eyebrow">Ready to handoff</p><h2>Gói bàn giao agent</h2><p>Gói xem trước sẽ được đóng băng với manifest, hash và bằng chứng ánh xạ. Portal không sinh receipt hoàn tất thay coding agent.</p><div class="handoff-metrics"><div class="handoff-metric"><span>Dòng được giao</span><b>${s.ready}</b></div><div class="handoff-metric"><span>Issues đính kèm</span><b>${s.issues}</b></div><div class="handoff-metric"><span>Phiên nguồn</span><b>${esc(state.release?.dataset?.version || 'local')}</b></div></div><div class="handoff-alert">${s.issues ? `${s.issues} dòng sẽ bị loại khỏi changes.jsonl vì chưa đủ bằng chứng.` : 'Không có issue bị loại trong phạm vi hiện tại.'}</div><button type="button" class="btn" data-action="create-handoff">Tạo gói xem trước <span>→</span></button></aside></div>`;
}

function renderHistory() {
    const records = state.exportRecords.length ? state.exportRecords : (state.exports.length ? state.exports : [{ id: 'LOCAL-PREVIEW', kind: 'Bản xem trước', chapter_id: state.chapterId, status: 'Chưa tải xuống', rows: stats().ready, hash: 'sẽ tính khi tải', created_at: 'Trong tab hiện tại', created_by: 'Reviewer session' }]);
    return `<div class="view-head"><div><p class="eyebrow">Immutable exports · 04</p><h1>Lịch sử bản xuất</h1><p>Mỗi bản xuất được lưu server-side theo export_id; tải lại cùng ID trả về đúng tệp đã khóa.</p></div><button type="button" class="btn" data-nav="export">+ Tạo bản xuất</button></div>${state.completedHandoff ? `<section class="panel panel-pad completed-handoff" style="margin-bottom:16px"><h2 class="panel-title">Đã tạo gói ${esc(state.completedHandoff.id)}</h2><p class="panel-sub">Tải các tệp của gói bên dưới và gửi cùng prompt cho agent.</p>${state.completedHandoff.prompt ? `<textarea class="prompt-editor" rows="8" readonly aria-label="Prompt của gói vừa tạo">${esc(state.completedHandoff.prompt)}</textarea><button type="button" class="btn primary" data-action="copy-handoff-prompt">Sao chép prompt</button>` : `<p>Không tải được prompt. Hãy tải AGENT_PROMPT.md trong danh sách tệp bên dưới.</p>`}</section>` : ''}${state.lastDownload ? `<div class="panel panel-pad" style="margin-bottom:16px"><p class="panel-sub">Gói ZIP đã sẵn sàng. Nếu trình duyệt chưa tải xuống, bấm nút bên dưới.</p><a class="btn primary" href="${esc(state.lastDownload.url)}" download="${esc(state.lastDownload.name)}">Tải lại ZIP</a></div>` : ''}<div class="export-history">${records.map(record => { const manifest = record.manifest || {}; return `<article class="history-card"><div class="history-main"><span class="history-icon">▣</span><div><b>${esc(record.id || record.export_id)}</b><span>${esc(record.kind || manifest.kind)} · ${esc(record.chapter_id || manifest.chapter_id || state.chapterId)}</span></div></div><div class="history-meta"><label>Rows</label><strong>${esc(manifest.scope?.lines ?? record.rows ?? '—')}</strong></div><div class="history-meta"><label>Hash</label><strong>${esc(manifest.files?.['changes.jsonl']?.sha256?.slice(0, 12) || record.hash || '—')}…</strong></div><div class="button-row">${record.manifest ? `<button type="button" class="btn primary download-zip-btn" data-action="download-zip" data-id="${esc(record.id || record.export_id)}">Tải cả gói (.zip)</button>` : ''}${record.manifest ? ['manifest.json', ...Object.keys(record.manifest.files || {})].map(file => `<button type="button" class="btn small" data-action="download-export" data-id="${esc(record.id || record.export_id)}" data-file="${esc(file)}">Tải ${esc(file)}</button>`).join('') : ''}${pill(record.status || 'ready', 'green')}</div></article>`; }).join('')}</div><div class="history-detail"><div class="panel-head" style="padding:0 0 12px;border:0"><div><h2>Contract của gói</h2><p>File được lưu cùng manifest và hash server-side.</p></div>${pill('6 tệp lõi', 'blue')}</div><div class="file-grid">${['manifest.json', 'changes.jsonl', 'mapping.jsonl', 'issues.jsonl', 'TASK.json', 'AGENT_PROMPT.md / README.md'].map(file => `<div class="file-chip"><b>${file}</b><span>hash locked · server</span></div>`).join('')}</div></div>`;
}

function renderRecovery() {
    const line = state.lines.find(item => item.line_id === state.selectedLineId) || state.lines[0];
    const history = state.history?.line?.line_id === line?.line_id ? state.history.history || [] : [];
    return `<div class="view-head"><div><p class="eyebrow">Traceability · 05</p><h1>Lịch sử & khôi phục</h1><p>Khôi phục luôn tạo revision mới. Nếu source_hash đã đổi, API sẽ từ chối thao tác và yêu cầu review lại.</p></div>${pill('Revision-aware', 'purple')}</div><div class="split-layout"><section class="panel panel-pad"><label class="field"><span>Chọn line để truy vết</span><select id="recoveryLine">${state.lines.slice(0, 120).map(item => `<option value="${esc(item.line_id)}" ${item.line_id === line?.line_id ? 'selected' : ''}>${esc(item.line_id)} · ${esc((item.en || '').slice(0, 45))}</option>`).join('')}</select></label><div class="revision-timeline">${history.length ? history.slice(0, 12).map(event => `<div class="revision"><div class="revision-top"><strong>r${esc(event.revision ?? '?')}</strong>${pill(event.event_type || 'event', event.event_type === 'approved' ? 'green' : 'blue')}</div><p>${esc(event.new_text || event.reason || 'Không có snapshot hiển thị.')}</p><small>${esc(event.actor || 'Chưa ghi nhận')} · ${esc(event.created_at || '')}</small><button type="button" class="btn small" data-action="restore" data-history="${esc(event.id)}" style="margin-top:8px">Khôi phục bản này</button></div>`).join('') : '<div class="empty-state">Bấm “Tải lịch sử” để lấy timeline của line.</div>'}</div><div class="button-row" style="margin-top:18px"><button type="button" class="btn primary" data-action="history" data-id="${esc(line?.line_id || '')}">Tải lịch sử & đề xuất</button></div></section><aside><div class="callout"><h3>Gate khôi phục</h3><p>Portal chỉ cho gửi yêu cầu. Worker vẫn kiểm tra source_hash hiện tại, dataset version và revision trước khi ghi.</p></div><div class="panel panel-pad" style="margin-top:15px"><p class="eyebrow">Bằng chứng hiện tại</p><div class="detail-list"><div class="detail-list-row"><span>Line</span><b>${esc(line?.line_id || '—')}</b></div><div class="detail-list-row"><span>Source hash</span><b>${esc(line?.source_hash ? `${String(line.source_hash).slice(0, 14)}…` : 'chưa có')}</b></div><div class="detail-list-row"><span>Revision</span><b>${esc(line?.revision ?? 'legacy')}</b></div><div class="detail-list-row"><span>Provenance</span><b>${esc(line?.provenance || 'legacy_import')}</b></div></div></div></aside></div>`;
}

function renderSessions() {
    const dataset = state.release?.dataset || {};
    return `<div class="view-head"><div><p class="eyebrow">Data lifecycle · 06</p><h1>Quản lý phiên dữ liệu</h1><p>Chụp dữ liệu để xuất tách biệt với thay bộ dữ liệu web. Dataset web, Merge và nguồn game luôn có version riêng.</p></div><button type="button" class="btn" data-action="reload">↻ Kiểm tra consistency</button></div><div class="split-layout"><div class="session-stack"><article class="session-card selected"><div class="session-top"><div><strong>${esc(dataset.version || 'dataset chưa tải')}</strong><p>Web translation workspace · ${esc(dataset.phase || 'unknown')}</p></div>${pill('Đang chọn', 'green')}</div><div class="session-steps"><span class="session-step"><i>✓</i> Captured</span><span class="session-step"><i>✓</i> Reviewed</span><span class="session-step"><i>✓</i> Exportable</span><span class="session-step pending"><i>4</i> Activated</span></div></article><article class="session-card"><div class="session-top"><div><strong>merge-reference</strong><p>Merge HaChiMinh · nguồn tham khảo UI tĩnh</p></div>${pill('Read-only', 'blue')}</div><div class="session-steps"><span class="session-step"><i>✓</i> Captured</span><span class="session-step"><i>✓</i> Reviewed</span><span class="session-step pending"><i>3</i> Exportable</span><span class="session-step pending"><i>4</i> Activated</span></div></article><article class="session-card"><div class="session-top"><div><strong>game-catalog</strong><p>Catalog nguồn build · cần đối chiếu locator thật</p></div>${pill('Chậm phiên', 'gold')}</div><div class="session-steps"><span class="session-step"><i>✓</i> Captured</span><span class="session-step pending"><i>2</i> Reviewed</span><span class="session-step pending"><i>3</i> Exportable</span><span class="session-step pending"><i>4</i> Activated</span></div></article></div><aside class="session-aside"><p class="eyebrow">Selected dataset</p><h2>${esc(dataset.version || 'local-preview')}</h2><p>Phiên này sẽ được ghi vào manifest của mọi handoff mới.</p><div class="detail-list"><div class="detail-list-row"><span>Phase</span><b>${esc(dataset.phase || 'unknown')}</b></div><div class="detail-list-row"><span>Manifest hash</span><b>${esc(dataset.manifest_hash || dataset.hash || 'chưa cung cấp')}</b></div><div class="detail-list-row"><span>Pending proposals</span><b>${esc(state.release?.pending_proposals ?? stats().queue)}</b></div></div><button type="button" class="btn" data-action="manage-release">Mở quy trình phiên</button></aside></div>`;
}

function renderPrompt() {
    return `<div class="view-head"><div><p class="eyebrow">Handoff · prompt</p><h1>Prompt cho agent</h1><p>Chỉnh prompt cho gói tiếp theo. Phạm vi chương và phiên dữ liệu sẽ được thêm tự động.</p></div></div><section class="panel panel-pad"><label for="agentInstructions" class="panel-title">Nội dung prompt</label><textarea id="agentInstructions" class="prompt-editor" rows="13" maxlength="4000" placeholder="Nhập phạm vi, yêu cầu hoặc điều kiện dừng bổ sung…">${esc(state.agentInstructions)}</textarea><p class="panel-sub">Được lưu trong tab hiện tại và ghi vào TASK.json cùng AGENT_PROMPT.md khi tạo bản xuất. Sau khi tạo gói, bạn có thể sao chép prompt hoàn chỉnh.</p></section>`;
}

function renderGovernance() {
    const roles = [['reviewer', 'Reviewer', 'Duyệt câu và chấp nhận đề xuất', true], ['exporter', 'Handoff exporter', 'Tạo snapshot, delta và gói agent', true], ['recovery', 'Recovery operator', 'Khôi phục revision sau khi hash hợp lệ', false], ['reader', 'Package reader', 'Chỉ đọc và tải gói đã xuất', true]];
    return `<div class="view-head"><div><p class="eyebrow">Governance · 07</p><h1>Phân quyền & nhật ký</h1><p>Quyền duyệt, xuất, khôi phục và đọc gói được tách riêng. Backend hiện tại dùng reviewer key; tài khoản ổn định là bước tiếp theo.</p></div><span class="pill gold">Key mode · đang dùng</span></div><div class="grid-two"><section class="panel panel-pad"><div class="scope-line"><div><h2 class="panel-title">Vai trò trong workspace</h2><p>Policy UI để chuẩn bị cho account-based access.</p></div><button type="button" class="text-link" data-action="policy">+ Thêm role</button></div><div class="role-grid" style="margin-top:16px">${roles.map(([id, title, detail, enabled]) => `<div class="role-row"><div class="role-copy"><span class="role-icon">♙</span><span><strong>${title}</strong><span>${detail}</span></span></div><button type="button" class="switch ${enabled ? 'on' : ''}" data-role="${id}" aria-label="Bật tắt ${title}"></button></div>`).join('')}</div></section><section class="panel panel-pad"><div class="scope-line"><div><h2 class="panel-title">Audit log</h2><p>Sự kiện của portal trong tab hiện tại</p></div><span class="pill blue">Live</span></div><div class="audit-list" style="margin-top:16px"><div class="audit-row"><time>NOW</time><div><p><b>Reviewer session</b> đã bật quyền đọc</p><code>X-Reviewer-Key · memory only</code></div><span class="audit-dot green"></span></div><div class="audit-row"><time>DATA</time><div><p><b>${esc(state.release?.dataset?.version || 'Dataset')}</b> đã được tải</p><code>${esc(state.chapterId)} · ${state.lines.length} lines</code></div><span class="audit-dot"></span></div><div class="audit-row"><time>GATE</time><div><p><b>${stats().issues} issue</b> đang nằm ngoài nhóm export</p><code>issues.jsonl preview</code></div><span class="audit-dot gold"></span></div></div><div class="policy-note">♢ Mọi handoff cần lưu actor, timestamp, dataset_version và hash tệp. Portal không tự sinh receipt “đã tích hợp”.</div></section></div>`;
}

function renderContent() {
    const content = $('#adminContent');
    if (!state.key) { content.innerHTML = renderLogin(); return; }
    if (state.loading) { content.innerHTML = '<div class="loading"><span class="spinner"></span> Đang tải dữ liệu TrạmVH…</div>'; return; }
    if (state.error && !state.lines.length) { content.innerHTML = `<div class="error">${esc(state.error)}<div style="margin-top:10px"><button type="button" class="btn" data-action="logout">Nhập lại mã reviewer</button></div></div>`; return; }
    const views = { overview: renderOverview, queue: renderQueue, issues: renderIssues, export: renderExport, history: renderHistory, recovery: renderRecovery, sessions: renderSessions, prompt: renderPrompt, governance: renderGovernance };
    content.innerHTML = `${state.feedback ? `<div class="feedback" role="status" style="margin-bottom:14px">${esc(state.feedback)}</div>` : ''}${state.error ? `<div class="error" role="alert" style="margin-bottom:14px">${esc(state.error)} <button type="button" class="btn small" data-action="reload">Tải lại</button></div>` : ''}${(views[state.view] || renderOverview)()}`;
}

function render() { renderSidebar(); renderHeader(); renderContent(); }

async function approveLine(line, action = 'approve', proposalId = null, historyId = null) {
    if (!Number.isSafeInteger(line?.revision) || line.revision < 0 || typeof line.source_hash !== 'string' || !/^[a-f0-9]{64}$/.test(line.source_hash) || typeof line.dataset_version !== 'string' || !line.dataset_version.trim()) {
        state.error = previewMode ? 'Bản xem thử không gửi quyết định duyệt. Hãy mở web chính thức để duyệt câu.' : 'Chưa tải đủ thông tin của câu. Bấm Tải lại rồi kiểm tra câu trước khi duyệt.';
        render();
        return;
    }
    const payload = { chapter_id: line.chapter_id || state.chapterId, line_id: line.line_id, base_revision: line.revision, base_source_hash: line.source_hash, base_dataset_version: line.dataset_version, action, proposal_id: proposalId, history_id: historyId, reason: action === 'approve' ? 'Duyệt từ Admin Portal' : action === 'accept' ? 'Chấp nhận đề xuất từ Admin Portal' : action === 'restore' ? 'Khôi phục từ Admin Portal' : 'Không chấp nhận đề xuất từ Admin Portal', request_id: crypto.randomUUID() };
    state.loading = true; state.error = ''; state.feedback = ''; render();
    try { const result = await request('/api/collab/review', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); if (result.line) { const index = state.lines.findIndex(item => item.line_id === result.line.line_id); if (index >= 0) state.lines[index] = { ...state.lines[index], ...result.line }; } state.history = null; state.error = ''; state.feedback = ({ approve: 'Đã duyệt bản hiện tại.', accept: 'Đã chấp nhận đề xuất.', reject: 'Đã từ chối đề xuất.', restore: 'Đã khôi phục phiên bản.' })[action]; await loadWorkspace(); }
    catch (error) { state.error = error.status === 409 ? 'Câu hoặc đề xuất đã thay đổi. Bấm Tải lại, xem bản mới rồi duyệt lại.' : (error.message || 'Không thể ghi quyết định duyệt.'); }
    finally { state.loading = false; render(); }
}

async function loadHistory(lineId) {
    const line = state.lines.find(item => item.line_id === lineId) || state.queueItems.find(item => item.line_id === lineId);
    if (!line) return;
    state.loading = true; state.error = ''; render();
    try { state.history = await request(`/api/collab/history?chapter_id=${encodeURIComponent(line.chapter_id || state.chapterId)}&line_id=${encodeURIComponent(line.line_id)}`); if (state.history.line) { const index = state.lines.findIndex(item => item.line_id === line.line_id); if (index >= 0) state.lines[index] = { ...state.lines[index], ...state.history.line }; } state.selectedLineId = line.line_id; state.view = 'queue'; }
    catch (error) { state.error = error.message || 'Không thể tải lịch sử.'; }
    finally { state.loading = false; render(); }
}

async function sha256(text) {
    const bytes = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest('SHA-256', bytes);
    return [...new Uint8Array(hash)].map(value => value.toString(16).padStart(2, '0')).join('');
}

function download(name, text, type = 'application/json') {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const link = document.createElement('a'); link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function reportLine(line) {
    if (!line?.line_id) return;
    const values = await openModal({ title: 'Báo câu cần kiểm tra', message: `Ghi issue cho ${line.line_id}. Reviewer khác sẽ thấy lý do này trong audit log.`, fields: [{ name: 'reason', label: 'Lý do', type: 'textarea', rows: 4, value: 'Cần đối chiếu nguồn và locator.', required: true }], confirmLabel: 'Ghi issue', tone: 'danger' });
    if (!values?.reason?.trim()) return;
    state.loading = true; state.error = ''; render();
    try {
        const payload = { chapter_id: line.chapter_id || state.chapterId, line_id: line.line_id, base_revision: line.revision ?? 0, base_source_hash: line.source_hash || '', base_dataset_version: line.dataset_version || state.release?.dataset?.version, reason: values.reason.trim(), request_id: crypto.randomUUID() };
        const result = await request('/api/collab/report', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (result.line) { const index = state.lines.findIndex(item => item.line_id === line.line_id); if (index >= 0) state.lines[index] = { ...state.lines[index], ...result.line }; }
        if (!previewMode) { const issues = await request('/api/admin/issues?limit=200'); state.issueItems = issues.data?.items || []; }
    } catch (error) { state.error = error.message || 'Không thể ghi issue.'; }
    finally { state.loading = false; render(); }
}

async function downloadExport(exportId, file = 'manifest.json') {
    try {
        const response = await request(`/api/admin/exports/${encodeURIComponent(exportId)}/download?file=${encodeURIComponent(file)}`, {}, true);
        const body = await response.text();
        download(file.replace(/[^A-Za-z0-9._-]/g, '_'), body, response.headers.get('content-type') || 'application/json');
    } catch (error) { state.error = error.message || 'Không thể tải tệp export.'; render(); }
}

async function downloadHandoffZip(exportId, button = null) {
    if (!exportId || button?.disabled) return;
    const previous = button?.textContent; if (button) { button.disabled = true; button.textContent = 'Đang chuẩn bị…'; }
    try {
        const path = `/api/admin/exports/${encodeURIComponent(exportId)}/download?file=`;
        const manifestResponse = await request(path + 'manifest.json', {}, true);
        const manifestBytes = new Uint8Array(await manifestResponse.arrayBuffer());
        const manifest = JSON.parse(new TextDecoder().decode(manifestBytes));
        if (manifest.export_id !== exportId || !manifest.files || typeof manifest.files !== 'object') throw new Error('Manifest không khớp với gói đã chọn.');
        const names = Object.keys(manifest.files);
        if (!names.length || names.includes('manifest.json') || names.some(name => !/^[A-Za-z0-9._-]+$/.test(name))) throw new Error('Danh sách tệp trong gói không hợp lệ.');
        const files = [{ name: 'manifest.json', bytes: manifestBytes }];
        for (const name of names) {
            const response = await request(path + encodeURIComponent(name), {}, true);
            const bytes = new Uint8Array(await response.arrayBuffer()), expected = manifest.files[name];
            if (bytes.length !== expected.bytes) throw new Error(`Tệp ${name} không đúng kích thước.`);
            if (!crypto.subtle) throw new Error('Trình duyệt không hỗ trợ kiểm tra tệp. Hãy mở trang bằng HTTPS.');
            const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(value => value.toString(16).padStart(2, '0')).join('');
            if (hash !== expected.sha256) throw new Error(`Tệp ${name} không khớp mã kiểm tra.`);
            files.push({ name, bytes });
        }
        const blob = createZip(files), url = URL.createObjectURL(blob), link = document.createElement('a');
        link.href = url; link.download = `${exportId.replace(/[^A-Za-z0-9._-]/g, '_')}.zip`;
        if (state.lastDownload) URL.revokeObjectURL(state.lastDownload.url);
        state.lastDownload = { id: exportId, url, name: link.download };
        state.feedback = 'Gói ZIP đã sẵn sàng để tải.';
        document.body.append(link); link.click(); link.remove();
        render();
    } catch (error) { state.feedback = 'Gói vẫn được lưu trong lịch sử. Bấm Tải cả gói để thử tải lại.'; render(); await openModal({ title: 'Chưa tải được gói', message: `${error.message || 'Không thể tải đủ tệp.'} Hãy thử lại hoặc tải từng tệp bên dưới.`, confirmLabel: 'Đóng' }); }
    finally { if (button) { button.disabled = false; button.textContent = previous; } }
}

async function createHandoff() {
    if (!previewMode) {
        state.loading = true; state.error = ''; render();
        try {
            const base = state.exportType === 'delta' ? (state.exportRecords[0]?.id || null) : null;
            const result = await request('/api/admin/exports', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind: state.exportType, chapter_id: state.chapterId, base_export_id: base, agent_instructions: state.agentInstructions.trim() }) });
            state.exportRecords.unshift({ id: result.data.export_id, export_id: result.data.export_id, kind: state.exportType, chapter_id: state.chapterId, status: 'ready', manifest: result.data.manifest });
            if (state.lastDownload) { URL.revokeObjectURL(state.lastDownload.url); state.lastDownload = null; }
            state.completedHandoff = null;
            if (state.exportType === 'handoff') {
                try { const task = await request(`/api/admin/exports/${encodeURIComponent(result.data.export_id)}/download?file=TASK.json`); state.completedHandoff = { id: result.data.export_id, prompt: task.agent_prompt }; }
                catch { state.completedHandoff = { id: result.data.export_id, prompt: '' }; }
            }
            state.view = 'history'; state.loading = false; state.feedback = 'Đã lưu gói. Đang chuẩn bị file ZIP…'; render();
            await downloadHandoffZip(result.data.export_id);
        } catch (error) { state.error = error.message || 'Không thể tạo bản xuất server-side.'; }
        finally { state.loading = false; render(); }
        return;
    }
    const lines = state.lines.filter(line => statusOf(line) === 'approved' && String(line.new_vi || '').trim());
    const issues = issueLines().map(line => ({ line_id: line.line_id, chapter_id: line.chapter_id || state.chapterId, reason: statusOf(line) === 'needs_review' ? 'needs_review' : 'missing_translation', en: line.en || '', source_hash: line.source_hash || null }));
    const changes = lines.map(line => ({ chapter_id: line.chapter_id || state.chapterId, line_id: line.line_id, event: 'approved', en: line.en || '', vi: line.new_vi || '', source_hash: line.source_hash || null, revision: line.revision || null, status: statusOf(line) }));
    const mapping = lines.map(line => ({ chapter_id: line.chapter_id || state.chapterId, line_id: line.line_id, source_ref: line.source_refs_json || null, mapping_status: line.source_hash ? 'needs_catalog_verification' : 'missing_source_hash' }));
    const manifest = { export_id: `TRAMVH-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`, created_at: new Date().toISOString(), dataset_version: state.release?.dataset?.version || 'local-preview', scope: { chapter_id: state.chapterId, line_count: changes.length }, source: { dataset_hash: state.release?.dataset?.manifest_hash || state.release?.dataset?.hash || null, glossary: 'read-only Google Sheet' }, files: {} };
    const prompt = state.agentInstructions.trim() || AGENT_PROMPT_TEMPLATE;
    const files = { 'changes.jsonl': changes.map(item => JSON.stringify(item)).join('\n'), 'mapping.jsonl': mapping.map(item => JSON.stringify(item)).join('\n'), 'issues.jsonl': issues.map(item => JSON.stringify(item)).join('\n'), 'TASK.json': JSON.stringify({ task: 'Đối chiếu Merge / chuẩn bị proposal tích hợp', read_first: ['docs/HACHIMINH_WORKFLOW_INTEGRATION.md', 'SS/.agents/skills/workflow/SKILL.md'], allowed_paths: ['SS/', 'proposals/'], stop_when: ['source hash thay đổi', 'locator trùng', 'thiếu bằng chứng'], agent_prompt: prompt }, null, 2), 'AGENT_PROMPT.md': `# Prompt cho coding agent\n\n${prompt}\n` };
    for (const [name, body] of Object.entries(files)) manifest.files[name] = { sha256: await sha256(body), bytes: new TextEncoder().encode(body).byteLength };
    const packageText = JSON.stringify({ manifest, changes, mapping, issues, TASK: JSON.parse(files['TASK.json']) }, null, 2);
    manifest.files['package.preview.json'] = { sha256: await sha256(packageText), bytes: new TextEncoder().encode(packageText).byteLength };
    const finalText = JSON.stringify({ manifest, changes, mapping, issues, TASK: JSON.parse(files['TASK.json']) }, null, 2);
    download(`${manifest.export_id}.json`, finalText);
    state.exports.unshift({ id: manifest.export_id, kind: 'Gói bàn giao · preview', scope: state.chapterId, status: 'Đã tải xuống', rows: changes.length, hash: `sha256:${manifest.files['package.preview.json'].sha256.slice(0, 12)}…`, time: 'Vừa xong', actor: 'Reviewer session' });
    state.completedHandoff = { id: manifest.export_id, prompt };
    state.view = 'history'; render();
}

async function manageRelease() {
    const dataset = state.release?.dataset;
    if (!dataset) return;
    const available = dataset.phase === 'open' ? ['lock'] : dataset.phase === 'locked' ? ['open', 'publish'] : ['activate', 'abort'];
    const values = await openModal({ title: 'Quản lý phiên dữ liệu', message: `Phiên hiện tại: ${dataset.version} · ${dataset.phase}. Chọn thao tác và ghi lý do để audit log có đầy đủ bằng chứng.`, fields: [{ name: 'action', label: 'Thao tác', type: 'select', value: available[0], options: available.map(action => ({ value: action, label: action === 'lock' ? 'Khóa gửi đề xuất' : action === 'open' ? 'Mở lại phiên' : action === 'publish' ? 'Bắt đầu xuất bản' : action === 'activate' ? 'Kích hoạt phiên mới' : 'Hủy xuất bản' })) }, { name: 'reason', label: 'Lý do', type: 'textarea', rows: 3, required: true, placeholder: 'Ví dụ: đã duyệt hết đề xuất trong phạm vi.' }, { name: 'new_version', label: 'Phiên mới (chỉ dùng khi kích hoạt)', type: 'text', placeholder: 'web-2026.11.10-r1' }, { name: 'manifest_hash', label: 'Manifest SHA-256 (chỉ dùng khi kích hoạt)', type: 'text', placeholder: '64 ký tự hex' }], confirmLabel: 'Gửi thao tác' });
    if (!values?.action || !available.includes(values.action) || !values.reason?.trim()) return;
    state.loading = true; render();
    try {
        const payload = { action: values.action, reason: values.reason.trim(), expected_version: dataset.version, expected_phase: dataset.phase, request_id: crypto.randomUUID() };
        if (values.action === 'activate') { payload.new_version = values.new_version?.trim(); payload.manifest_hash = values.manifest_hash?.trim(); }
        await request('/api/collab/release', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); await loadWorkspace();
    }
    catch (error) { state.error = error.message || 'Không thể chuyển phase phiên dữ liệu.'; state.loading = false; render(); }
}

document.addEventListener('keydown', event => { if (event.key === 'Escape' && state.mobileOpen) { state.mobileOpen = false; renderSidebar(); $('[data-action="toggle-mobile"]')?.focus(); } });

document.body.addEventListener('click', async event => {
    const nav = event.target.closest('[data-nav]');
    if (nav) { state.view = nav.dataset.nav; if (nav.dataset.line) state.selectedLineId = nav.dataset.line; state.mobileOpen = false; state.error = ''; render(); return; }
    const lineButton = event.target.closest('[data-line]');
    if (lineButton) { state.selectedLineId = lineButton.dataset.line; state.history = null; const chapter = lineButton.dataset.chapter; if (chapter && chapter !== state.chapterId && !previewMode) { try { await loadChapter(chapter); } catch (error) { state.error = error.message || 'Không tải được câu từ server.'; render(); return; } } render(); if (matchMedia('(max-width: 700px)').matches) { const detail = $('#queueDetail'); detail?.scrollIntoView({ behavior: 'smooth', block: 'start' }); detail?.focus({ preventScroll: true }); } return; }
    const filter = event.target.closest('[data-filter]');
    if (filter) { state.queueFilter = filter.dataset.filter; render(); return; }
    const exportType = event.target.closest('[data-export-type]');
    if (exportType) { state.exportType = exportType.dataset.exportType; render(); return; }
    const role = event.target.closest('[data-role]');
    if (role) { role.classList.toggle('on'); return; }
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (!action) return;
    if (action === 'mobile-search') { state.view = 'queue'; state.mobileOpen = false; state.error = ''; render(); const input = $('#queueSearch'); input?.focus(); input?.scrollIntoView({ block: 'center' }); return; }
    if (action === 'toggle-mobile') { state.mobileOpen = !state.mobileOpen; renderSidebar(); return; }
    if (action === 'close-mobile') { state.mobileOpen = false; renderSidebar(); $('[data-action="toggle-mobile"]')?.focus(); return; }
    if (action === 'queue-back') { $('#queueList')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); $('#queueList .queue-row.selected')?.focus({ preventScroll: true }); return; }
    if (action === 'download-zip') { await downloadHandoffZip(event.target.closest('[data-id]')?.dataset.id, event.target.closest('button')); return; }
    if (action === 'logout') { state.key = ''; state.release = null; state.lines = []; state.history = null; state.error = ''; sessionStorage.removeItem(HANDOFF_KEY); render(); return; }
    if (action === 'help') { openAdminGuide(); return; }
    if (action === 'reload') { await loadWorkspace(); return; }
    if (action === 'history') { await loadHistory(event.target.closest('[data-id]')?.dataset.id || state.selectedLineId); return; }
    if (action === 'approve') { const id = event.target.closest('[data-id]')?.dataset.id; await approveLine(state.lines.find(line => line.line_id === id) || state.queueItems.find(line => line.line_id === id)); return; }
    if (action === 'accept' || action === 'reject') { const line = state.lines.find(item => item.line_id === state.selectedLineId); await approveLine(line, action, event.target.closest('[data-proposal]')?.dataset.proposal); return; }
    if (action === 'report') { const id = event.target.closest('[data-id]')?.dataset.id; await reportLine(state.lines.find(line => line.line_id === id) || state.queueItems.find(line => line.line_id === id)); return; }
    if (action === 'open-editor') { const line = state.lines.find(item => item.line_id === state.selectedLineId) || state.queueItems.find(item => item.line_id === state.selectedLineId); window.location.href = `index.html?chapter=${encodeURIComponent(line?.chapter_id || state.chapterId)}&line=${encodeURIComponent(state.selectedLineId)}`; return; }
    if (action === 'download-issues') { const body = issueLines().map(line => JSON.stringify({ issue_id: line.issue_id || null, chapter_id: line.chapter_id || state.chapterId, line_id: line.line_id, en: line.en || '', reason: line.reason || 'needs_review', source_hash: line.source_hash || null })).join('\n'); download(`${state.chapterId}.issues.jsonl`, body, 'application/jsonl'); return; }
    if (action === 'download-export') { await downloadExport(event.target.closest('[data-id]')?.dataset.id, event.target.closest('[data-file]')?.dataset.file || 'manifest.json'); return; }
    if (action === 'create-handoff') { await createHandoff(); return; }
    if (action === 'restore') { const line = state.lines.find(item => item.line_id === state.selectedLineId); const historyId = event.target.closest('[data-history]')?.dataset.history; await approveLine(line, 'restore', null, historyId); return; }
    if (action === 'manage-release') { await manageRelease(); return; }
    if (action === 'policy') { await openModal({ title: 'Quyền server-side', message: `Scopes hiện tại: ${(state.permissions?.scopes || []).join(', ') || 'chưa tải'}. Thay đổi quyền cần cập nhật secret hoặc account policy ở Worker.`, confirmLabel: 'Đóng' }); }
    if (action === 'copy-handoff-prompt') { const text = state.completedHandoff?.prompt; if (!text) return; try { await navigator.clipboard.writeText(text); await openModal({ title: 'Đã sao chép prompt', message: 'Gửi prompt này cùng các tệp của gói cho agent.', confirmLabel: 'Đóng' }); } catch (_) { await openModal({ title: 'Sao chép thủ công', fields: [{ name: 'prompt', label: 'Chọn và sao chép prompt', type: 'textarea', rows: 12, value: text }], confirmLabel: 'Đóng' }); } return; }
    if (action === 'toggle-key') { const input = $('#reviewerKeyInput'); const button = event.target.closest('[data-action="toggle-key"]'); if (input && button) { const visible = input.type === 'text'; input.type = visible ? 'password' : 'text'; button.textContent = visible ? 'Hiện' : 'Ẩn'; button.setAttribute('aria-pressed', String(!visible)); } }
    if (action === 'preview-login') { state.key = 'preview'; await loadWorkspace(); }
});

document.body.addEventListener('submit', async event => {
    const form = event.target.closest('[data-form="login"]');
    if (!form) return;
    event.preventDefault();
    const key = new FormData(form).get('key')?.toString().trim();
    if (!key) return;
    const submit = form.querySelector('button'); submit.disabled = true; submit.innerHTML = '<span class="spinner"></span> Đang kiểm tra…';
    try { const release = await fetch('/api/collab/release', { headers: { Accept: 'application/json', 'X-Reviewer-Key': key } }); if (!release.ok) { const data = await release.json().catch(() => null); throw new Error(data?.message || 'Mã reviewer không hợp lệ hoặc Worker chưa sẵn sàng.'); } sessionStorage.setItem(HANDOFF_KEY, key); state.key = key; state.release = await release.json(); await loadWorkspace(); }
    catch (error) { const old = form.querySelector('.error'); old?.remove(); const box = document.createElement('div'); box.className = 'error'; box.textContent = error.message; form.append(box); submit.disabled = false; submit.textContent = 'Bật quyền reviewer →'; }
});

document.body.addEventListener('input', event => {
    if (event.target.id === 'queueSearch') { state.queueSearch = event.target.value; render(); const input = $('#queueSearch'); input?.focus(); input?.setSelectionRange(state.queueSearch.length, state.queueSearch.length); }
    if (event.target.id === 'globalSearch' && event.target.value.trim()) { state.view = 'queue'; state.queueSearch = event.target.value.trim(); render(); }
    if (event.target.id === 'agentInstructions') state.agentInstructions = event.target.value;
});

document.addEventListener('change', async event => {
    if (event.target.id === 'chapterSelect') { state.selectedLineId = ''; state.history = null; await loadChapter(event.target.value); render(); }
    if (event.target.id === 'recoveryLine') { state.selectedLineId = event.target.value; state.history = null; render(); }
});

async function bootstrapPortal() {
    if (!previewMode) {
        const handoffKey = sessionStorage.getItem(HANDOFF_KEY);
        if (handoffKey) {
            state.key = handoffKey;
            try {
                const response = await fetch('/api/collab/release', { headers: { Accept: 'application/json', 'X-Reviewer-Key': handoffKey }, cache: 'no-store' });
                if (response.status === 401 || response.status === 403) { sessionStorage.removeItem(HANDOFF_KEY); throw new Error('Mã quản trị không còn hợp lệ.'); }
                if (!response.ok) throw new Error('Không thể kiểm tra quyền quản trị. Hãy tải lại trang.');
                await loadWorkspace();
                return;
            } catch (error) {
                state.key = '';
                state.error = error.message || 'Không thể kiểm tra quyền quản trị. Hãy tải lại trang.';
            }
        }
    }
    render();
}
bootstrapPortal();
