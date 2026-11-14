/** Canonical line state is server-owned. Drafts and proposals never overwrite it locally. */
(() => {
    let reviewerKey = '';
    const labels = { untranslated:'Chưa dịch', pending:'Đã Việt hoá · Chờ duyệt', approved:'Đã duyệt', needs_review:'Cần xem lại', machine_pending:'Bản dịch máy · Chưa duyệt' };
    const M = window.Collaboration = { ready:false, available:false, canReview:false, datasetVersion:null, phase:'unavailable', user:null, labels };
    M.status = line => {
        if (labels[line.status]) return line.status;
        if (line.status === 'Đã duyệt') return 'approved';
        if (line.status === 'Cần xem lại') return 'needs_review';
        return line.new_vi && line.new_vi !== line.en ? (line.translation_origin === 'machine' ? 'machine_pending' : 'pending') : 'untranslated';
    };
    M.hasText = line => Boolean((line.new_vi || '').trim());
    M.origin = line => line.translation_origin === 'machine' ? 'Bản dịch máy/AI' : line.translation_origin === 'human' ? 'Người dịch tự nhập' : 'Nguồn nhập cũ · Chưa xác minh';
    M.time = value => {
        if (!value) return 'Chưa rõ thời gian';
        const date = new Date(value), elapsed = Math.max(0, Date.now() - date.getTime());
        if (!Number.isFinite(elapsed)) return 'Chưa rõ thời gian';
        if (elapsed < 60000) return 'Vừa cập nhật';
        if (elapsed < 3600000) return Math.floor(elapsed / 60000) + ' phút trước';
        if (elapsed < 86400000) return Math.floor(elapsed / 3600000) + ' giờ trước';
        if (elapsed < 86400000 * 7) return Math.floor(elapsed / 86400000) + ' ngày trước';
        return date.toLocaleString('vi-VN');
    };
    M.request = async (path, body, privileged = false) => {
        const headers = { 'Accept':'application/json' };
        if (body) headers['Content-Type'] = 'application/json';
        if (privileged && reviewerKey) headers['X-Reviewer-Key'] = reviewerKey;
        let response;
        try { response = await fetch('/api/collab/' + path, { method:body ? 'POST' : 'GET', headers, body:body ? JSON.stringify(body) : undefined, cache:'no-store', signal:AbortSignal.timeout(body ? 30000 : 15000) }); }
        catch (_) { throw Object.assign(new Error('Không kết nối được máy chủ. Bản nháp vẫn được giữ trên máy; hãy thử lại khi có mạng.'), { code:'network' }); }
        let data;
        try { data = await response.json(); } catch (_) { throw new Error('Máy chủ chưa sẵn sàng cho tính năng cộng tác. Bản nháp chưa được gửi.'); }
        if (!response.ok || data.success === false) throw Object.assign(new Error(data.message || data.error || 'Không thể thực hiện thao tác.'), { status:response.status, code:data.code, latest:data.line });
        if (data.dataset_version) M.datasetVersion = data.dataset_version;
        if (data.dataset_phase) { M.phase = data.dataset_phase; M.ready = M.available && M.phase === 'open'; }
        return data;
    };
    M.init = async () => {
        try {
            const data = await M.request('status');
            M.available = !!data.dataset_version;
            M.datasetVersion = data.dataset_version || null;
            M.phase = data.dataset_phase || 'unavailable';
            M.ready = M.available && M.phase === 'open' && data.can_write !== false;
            if (M.available) {
                const identity = await M.request('me');
                M.user = identity.user;
                // Only migrate a name the visitor actually saved; the starter profile is shared by everyone.
                if (identity.new_user && localStorage.getItem('stella_user_profile') && currentUser.name) await M.setDisplayName(currentUser.name);
                else if (M.user?.display_name) {
                    currentUser.name = M.user.display_name;
                    localStorage.setItem('stella_user_profile', JSON.stringify(currentUser));
                    updateHud();
                }
            }
        } catch (_) { M.ready = false; }
        M.updateNotice();
    };
    M.setDisplayName = async name => { const result = await M.request('profile',{display_name:name}); M.user = result.user; return result.user; };
    M.updateNotice = () => {
        const element = document.getElementById('collabServiceNotice');
        if (!element) return;
        element.replaceChildren();
        if (!M.ready) { element.hidden = false; element.textContent = M.available ? `Phiên ${M.datasetVersion} đang ${M.phase === 'publishing' ? 'xuất bản' : 'khóa cập nhật'}. Chưa gửi thay đổi được; bản nháp vẫn ở trên máy.` : 'Chế độ chỉ đọc: chưa kết nối kho cộng tác. Chưa gửi thay đổi được; các bản nháp đã có vẫn được giữ trên máy.'; }
        else {
            const count = M.legacyQueue().length;
            element.hidden = count === 0;
            if (count) {
                element.append(document.createTextNode(`Có ${count} bản nháp từ phiên cũ, chưa gửi tự động. Mở câu tương ứng để đối chiếu và gửi lại. `));
                const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Tải bản nháp'; button.className = 'collab-link'; button.onclick = M.exportLegacyDrafts; element.append(button);
            }
        }
        const button = document.getElementById('reviewerAccessBtn');
        if (button) { button.title = M.canReview ? 'Quyền duyệt đang bật' : 'Nhập mã quản trị để duyệt'; button.setAttribute('aria-pressed', String(M.canReview)); }
    };
    M.login = async key => {
        reviewerKey = key;
        try { const result = await M.request('role', null, true); if (!result.can_review) throw new Error('Mã quản trị không hợp lệ.'); M.canReview = true; }
        catch (error) { reviewerKey = ''; M.canReview = false; throw error; }
        M.updateNotice();
    };
    M.logout = () => { reviewerKey = ''; M.canReview = false; M.updateNotice(); };
    M.ref = line => ({ chapter_id:line.chapter_id || currentChapterData.chapter_id, line_id:line.line_id });
    M.query = line => new URLSearchParams(M.ref(line)).toString();
    M.getLine = async line => (await M.request('line?' + M.query(line))).line;
    M.myProposal = async line => (await M.request('my-proposal?' + M.query(line))).proposal;
    M.history = (line, cursor, proposalCursor) => M.request('history?' + M.query(line) + (cursor ? '&cursor=' + encodeURIComponent(cursor) : '') + (proposalCursor ? '&proposal_cursor=' + encodeURIComponent(proposalCursor) : ''));
    M.patch = line => {
        if (!currentChapterData || line.chapter_id !== currentChapterData.chapter_id) return;
        const target = currentLines.find(item => item.line_id === line.line_id);
        if (target) Object.assign(target, line);
        updateProgressBar();
    };
    M.draftKey = line => { const ref = M.ref(line); return 'tramvh_draft_v2:' + ref.chapter_id + ':' + ref.line_id; };
    M.saveDraft = (line, draft) => { try { localStorage.setItem(M.draftKey(line), JSON.stringify({...draft,base_dataset_version:draft.base_dataset_version || line.dataset_version || M.datasetVersion})); } catch (_) {} };
    M.readDraft = line => {
        try { const stored = localStorage.getItem(M.draftKey(line)); if (stored) return JSON.parse(stored); } catch (_) {}
        const ref = M.ref(line), old = M.legacyQueue().find(entry => entry.payload && entry.payload.chapter_id === ref.chapter_id && entry.payload.line_id === ref.line_id);
        return old ? { text:old.payload.new_vi, origin:'unknown', notes:old.payload.notes || '', legacy:true } : null;
    };
    M.clearDraft = (line, text) => {
        try {
            const stored = M.readDraft(line);
            if (!stored || stored.text === text) localStorage.removeItem(M.draftKey(line));
            const ref = M.ref(line);
            const remaining = M.legacyQueue().filter(entry => !(entry.payload && entry.payload.chapter_id === ref.chapter_id && entry.payload.line_id === ref.line_id && entry.payload.new_vi === text));
            localStorage.setItem('stella_offline_queue', JSON.stringify(remaining));
        } catch (_) {}
        M.updateNotice();
    };
    M.legacyQueue = () => { try { const value = JSON.parse(localStorage.getItem('stella_offline_queue') || '[]'); return Array.isArray(value) ? value : []; } catch (_) { return []; } };
    M.exportLegacyDrafts = () => {
        const url = URL.createObjectURL(new Blob([JSON.stringify(M.legacyQueue(), null, 2)], {type:'application/json'}));
        const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'TramVH-ban-nhap-chua-gui.json'; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    };
    M.exportChapter = async () => {
        if (!currentChapterData?.chapter_id) return;
        try {
            const response = await fetch('/api/export_chapter?id=' + encodeURIComponent(currentChapterData.chapter_id), {cache:'no-store'});
            const data = await response.json(); if (!response.ok || !data.scenes) throw new Error(data.error || 'Chưa xuất được chương.');
            const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
            const anchor=document.createElement('a');anchor.href=url;anchor.download='TramVH-'+data.chapter_id+'.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
        }catch(error){showToastAlert(error.message);}
    };
    M.award = (requestId, replayed) => {
        if (replayed) return;
        try {
            const awarded = JSON.parse(localStorage.getItem('tramvh_awarded_requests') || '[]');
            if (awarded.includes(requestId)) return;
            currentUser.exp = (currentUser.exp || 0) + 50; currentUser.level = 1 + Math.floor(currentUser.exp / 250);
            localStorage.setItem('stella_user_profile', JSON.stringify(currentUser)); localStorage.setItem('tramvh_awarded_requests', JSON.stringify([...awarded, requestId].slice(-200))); updateHud();
        } catch (_) {}
    };
})();
