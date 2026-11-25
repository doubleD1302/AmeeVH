/** Read-only current versions, proposal diffs and immutable history. */
(() => {
    const V = window.CollaborationView = {};
    const M = () => window.Collaboration;
    const make = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
    const action = (text, handler, cls = 'btn-direction') => { const b = make('button', cls, text); b.type = 'button'; b.addEventListener('click', handler); return b; };
    const reasonLabels = { meaning:'Sai nghĩa', pronouns:'Sai xưng hô', naturalness:'Câu chưa tự nhiên', other:'Khác' };
    let requestSerial = 0, previousFocus = null, mobileReturnY = null;
    // Moderators skip the admin queue, so the primary button says what really happens.
    V.saveText = line => M().canModerate ? 'Lưu & duyệt ngay' : M().hasText(line) ? 'Gửi đề xuất sửa' : 'Lưu bản dịch · Chờ duyệt';
    const copyText = async text => {
        try { if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(text); return true; } } catch (_) {}
        // Fallback for older browsers / blocked Clipboard API. Inside an open modal dialog the helper must live in the dialog, or it is inert.
        try {
            const holder = make('textarea'); holder.value = text; holder.readOnly = true; holder.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
            (dialog()?.open ? dialog() : document.body).append(holder); holder.select(); holder.setSelectionRange(0, text.length);
            const ok = document.execCommand('copy'); holder.remove(); return ok;
        } catch (_) { return false; }
    };
    V.copyButton = text => {
        const button = make('button', 'collab-copy'); button.type = 'button';
        button.title = 'Sao chép bản Việt hóa'; button.setAttribute('aria-label', 'Sao chép bản Việt hóa');
        button.innerHTML = tramIcon('copy'); // static, whitelisted icon markup only
        let timer = 0;
        button.addEventListener('click', async event => {
            event.preventDefault(); event.stopPropagation();
            const ok = await copyText(text);
            button.focus({ preventScroll: true });
            if (ok) { button.innerHTML = tramIcon('check'); button.classList.add('is-copied'); clearTimeout(timer); timer = setTimeout(() => { button.innerHTML = tramIcon('copy'); button.classList.remove('is-copied'); }, 1400); }
            showToastAlert(ok ? 'Đã sao chép bản Việt hóa. Dán vào ô soạn để sửa tiếp.' : 'Trình duyệt chặn việc sao chép. Hãy bôi đen văn bản rồi nhấn Ctrl+C.');
        });
        return button;
    };
    V.badge = line => { const legacy = line.provenance === 'legacy_import' && !line.approved_at && M().status(line) === 'approved'; const badge = make('span', 'collab-badge collab-' + M().status(line), legacy ? 'Đã duyệt · Nhập cũ' : M().labels[M().status(line)]); if (legacy) badge.title = 'Trạng thái từ dữ liệu nhập cũ; lịch sử duyệt trước khi cộng tác chưa được xác minh.'; return badge; };
    V.metadata = line => {
        const wrap = make('div','collab-meta');
        wrap.append(make('span','', 'Người dịch: ' + (line.translator || 'Chưa có')));
        const time = make('time','', 'Cập nhật: ' + M().time(line.updated_at)); if (line.updated_at) { time.dateTime = line.updated_at; time.title = new Date(line.updated_at).toLocaleString('vi-VN'); } wrap.append(time);
        if (M().hasText(line)) wrap.append(make('span','collab-origin',M().origin(line)));
        if (line.provenance === 'moderator' && line.status === 'approved') wrap.append(make('span','collab-mod-tag','Moderator đã duyệt'));
        if (line.pending_proposals) wrap.append(action(`${line.pending_proposals} đề xuất chờ duyệt`,()=>V.openHistory(line),'collab-proposal-link'));
        return wrap;
    };
    V.summary = line => {
        const e = make('div','collab-summary'); e.append(V.badge(line));
        const heading = make('span','collab-current-label','Bản đang dùng');
        if (M().hasText(line)) heading.append(V.copyButton(line.new_vi));
        e.append(heading);
        e.append(make('p','collab-current-text',line.new_vi || 'Chưa có bản dịch tiếng Việt.'));
        e.append(V.metadata(line));
        if (line.notes) e.append(make('p','collab-context','Ngữ cảnh: ' + line.notes));
        if (line.provenance === 'legacy_import') e.append(make('small','collab-muted','Bản dịch có nguồn từ dữ liệu cũ; lịch sử trước khi bật cộng tác chưa được xác minh.'));
        return e;
    };
    V.sources = line => {
        const grid=make('div','collab-source-grid');
        if(line.sheet_sync_status==='unavailable')grid.append(make('p','collab-error','Không kết nối được Google Sheet; nguồn đối chiếu có thể chưa cập nhật.'));
        for(const [label,value] of [['EN',line.en],['JP',line.jp ?? line.text_jp ?? line.source_jp],['CN',line.cn ?? line.text_cn ?? line.source_cn]]){
            const panel=make('section','collab-source-panel');
            panel.append(make('strong','',label),make('p','collab-source',typeof value==='string'&&value?value:'Chưa có nguồn '+label+' cho câu này.'));
            grid.append(panel);
        }
        return grid;
    };
    V.diff = (before, after) => {
        const grid = make('div','collab-diff');
        let prefix = 0, suffix = 0;
        while (prefix < before.length && prefix < after.length && before[prefix] === after[prefix]) prefix++;
        while (suffix < before.length - prefix && suffix < after.length - prefix && before[before.length - 1 - suffix] === after[after.length - 1 - suffix]) suffix++;
        for (const [text,label,tag] of [[before,'Bản hiện tại','del'],[after,'Đề xuất / phiên bản chọn','ins']]) {
            const panel = make('div'); panel.append(make('strong','',label)); const body = make('p','collab-diff-text');
            if (before === after) body.textContent = text || '(Trống)';
            else { body.append(document.createTextNode(text.slice(0,prefix))); const changed = make(tag,'',text.slice(prefix,text.length-suffix)); body.append(changed,document.createTextNode(suffix ? text.slice(-suffix) : '')); }
            panel.append(body); grid.append(panel);
        }
        return grid;
    };
    const showError = (box,error) => { box.hidden = false; box.textContent = error.message || String(error); };
    const dialog = () => document.getElementById('collaborationDialog');
    const clear = title => {
        const d = dialog(); if(!d.open && matchMedia('(max-width:700px)').matches)mobileReturnY=scrollY; requestSerial++; previousFocus = d.open ? previousFocus : document.activeElement; d.replaceChildren();
        const header = make('div','collab-dialog-header'), h = make('h2','',title); h.id = 'collabDialogTitle'; h.tabIndex = -1;
        header.append(h,action('Đóng',()=>d.close(),'collab-close'));
        const content = make('div','collab-dialog-body'); d.append(header,content);
        if (!d.open) d.showModal(); h.focus({preventScroll:true});
        return content;
    };
    const rerender = () => { if (viewMode === 'list') renderListMode(); else renderCurrentLine(); };
    V.init = () => {
        const d = dialog();
        d.addEventListener('keydown', e => {
            e.stopPropagation();
            if (e.key !== 'Tab') return;
            const controls = [...d.querySelectorAll('button,input,textarea,select,[tabindex="0"]')].filter(x=>!x.disabled && x.getClientRects().length);
            const first=controls[0],last=controls.at(-1);
            if (e.shiftKey && (document.activeElement===first || !controls.includes(document.activeElement))) { e.preventDefault();last?.focus(); }
            else if (!e.shiftKey && document.activeElement===last) { e.preventDefault();first?.focus(); }
        });
        d.addEventListener('close',()=>{ if(d.open)return;requestSerial++; if(previousFocus?.isConnected)previousFocus.focus({preventScroll:true}); if(mobileReturnY!==null){const y=mobileReturnY;mobileReturnY=null;requestAnimationFrame(()=>window.scrollTo({top:y,behavior:'instant'}));} });
    };
    V.login = () => {
        const body = clear('Admin Portal'), serial=requestSerial;
        if (M().canReview) { body.append(make('p','', 'Quyền duyệt đang bật trong tab này.'),action('Mở Admin Portal',()=>{M().openAdminPortal()}),action('Quản lý phiên dữ liệu',()=>V.release()),action('Tắt quyền duyệt',()=>{M().logout();sessionStorage.removeItem('tramvh_reviewer_key');dialog().close();rerender();}));return; }
        const form=make('form','collab-form'),label=make('label','','Mã quản trị'),input=make('input');input.type='password';input.autocomplete='off';input.required=true;label.append(input);
        const error=make('p','collab-error');error.hidden=true;error.role='alert';const submit=make('button','btn-save-glow','Bật quyền duyệt');submit.type='submit';form.append(label,error,submit);body.append(form);
        form.addEventListener('submit',async e=>{e.preventDefault();submit.disabled=true;const key=input.value;try{await M().login(key);input.value='';M().openAdminPortal();}catch(err){input.value='';showError(error,err);}finally{submit.disabled=false;}});
    };
    V.moderator = () => {
        const body = clear('Moderator'), serial = requestSerial;
        const nameNow = (M().user?.display_name || '').trim();
        if (M().canModerate) {
            body.append(make('p','collab-info',`Moderator đang bật cho "${nameNow}". Bản dịch và bản sửa của bạn được duyệt tự động, không cần admin duyệt lại; dữ liệu vẫn về admin để tổng hợp.`),
                make('p','collab-muted','Quyền này gắn với tên dịch giả của bạn và nằm trên máy chủ, không phụ thuộc trình duyệt. Trên thiết bị khác, đặt đúng tên này trong Hồ sơ rồi nhập mã là dùng được. Đổi sang tên khác sẽ tắt Moderator.'),
                action('Tắt Moderator trên thiết bị này',async()=>{try{await M().deactivateModerator();dialog().close();rerender();showToastAlert('Đã tắt Moderator trên thiết bị này.');}catch(err){showToastAlert(err.message);}}));
            return;
        }
        body.append(make('p','',`Nhập mã Moderator riêng của bạn. Mã sẽ được gắn với tên dịch giả hiện tại${nameNow ? ` ("${nameNow}")` : ''} và chỉ dùng được cho tên đó. Sau khi xác nhận, phần Việt hóa của bạn được duyệt tự động; admin vẫn nhận đủ dữ liệu để tổng hợp.`),
            make('p','collab-muted','Hãy kiểm tra biệt danh trong Hồ sơ trước khi nhập mã. Mã đã gắn với một tên thì không thể dùng cho tên khác.'));
        const form = make('form','collab-form'), label = make('label','','Mã Moderator'), input = make('input'); input.type = 'password'; input.autocomplete = 'off'; input.required = true; input.maxLength = 200; label.append(input);
        const error = make('p','collab-error'); error.hidden = true; error.role = 'alert';
        const submit = make('button','btn-save-glow','Xác nhận Moderator'); submit.type = 'submit'; form.append(label,error,submit); body.append(form);
        input.focus({preventScroll:true});
        form.addEventListener('submit', async e => {
            e.preventDefault(); submit.disabled = true; error.hidden = true;
            try { await M().activateModerator(input.value); input.value = ''; if (serial === requestSerial && dialog().open) { dialog().close(); rerender(); } showToastAlert('Đã bật Moderator. Bản dịch của bạn sẽ được duyệt tự động.'); }
            catch (err) { input.value = ''; showError(error,err); input.focus({preventScroll:true}); }
            finally { submit.disabled = false; }
        });
    };
    V.refresh = () => { try { rerender(); } catch (_) {} };
    V.release = async () => {
        const body=clear('Quản lý phiên dữ liệu'),serial=requestSerial;
        body.append(make('p','','Đang tải trạng thái phiên…'));
        try {
            const data=await M().request('release',null,true);
            if(serial!==requestSerial||!dialog().open)return;
            const state=data.dataset;
            body.replaceChildren(make('p','collab-info',`Phiên ${state.version} · ${state.phase} · ${data.pending_proposals} đề xuất chờ duyệt`));
            const form=make('form','collab-form');
            const reasonLabel=make('label','','Lý do chuyển trạng thái'),reason=make('textarea');reason.required=true;reason.maxLength=2000;reason.rows=2;reasonLabel.append(reason);form.append(reasonLabel);
            let version,hash;
            if(state.phase==='publishing'){
                const versionLabel=make('label','','Phiên mới'),hashLabel=make('label','','Hash manifest đã triển khai');
                version=make('input');version.maxLength=120;hash=make('input');hash.maxLength=64;
                versionLabel.append(version);hashLabel.append(hash);form.append(versionLabel,hashLabel);
                try { const response=await fetch('/data/dataset-manifest.json',{cache:'no-store'});if(response.ok){const manifest=await response.json();version.value=manifest.version||'';hash.value=manifest.hash||'';} } catch (_) {}
            }
            const error=make('p','collab-error');error.hidden=true;error.role='alert';form.append(error);
            const choices=state.phase==='open'?[['lock','Khóa gửi đề xuất']]:state.phase==='locked'?[['open','Mở lại'],['publish','Bắt đầu xuất bản']]:[['abort','Hủy xuất bản sau khi khôi phục dữ liệu cũ'],['activate','Kích hoạt phiên mới']];
            for(const [operation,label] of choices){
                const button=action(label,async()=>{
                    if(!reason.value.trim()){showError(error,new Error('Nhập lý do chuyển trạng thái.'));reason.focus();return;}
                    button.disabled=true;
                    try{
                        const payload={action:operation,reason:reason.value.trim(),expected_version:state.version,expected_phase:state.phase};
                        if(operation==='activate')Object.assign(payload,{new_version:version.value.trim(),manifest_hash:hash.value.trim()});
                        await M().request('release',payload,true);await M().init();if(serial===requestSerial&&dialog().open)V.release();
                    }catch(err){showError(error,err);}finally{button.disabled=false;}
                });
                if(operation==='publish'&&data.pending_proposals)button.disabled=true;
                form.append(button);
            }
            body.append(form);
        }catch(err){if(serial===requestSerial)body.replaceChildren(make('p','collab-error',err.message));}
    };
    V.openLineAction = async (item, { mode, history }) => {
        const report = mode === 'report';
        const body = clear(report ? 'Báo câu cần xem lại' : 'Khôi phục phiên bản');
        const serial = requestSerial;
        const active = () => serial === requestSerial && dialog().open;
        body.append(make('p', '', 'Đang lấy bản hiện tại…'));
        let base;
        try {
            base = { ...item, ...await M().getLine(item) };
        } catch (error) {
            if (active()) body.replaceChildren(make('p', 'collab-error', error.message));
            return;
        }
        if (!active()) return;
        M().patch(base);

        const source = make('details', 'collab-sources-details');
        source.append(make('summary', '', 'Xem nguồn EN / JP / CN'));
        const sourcePreview = make('div', 'collab-source-preview');
        sourcePreview.append(make('strong', '', 'Gốc (EN)'), make('p', '', base.en || 'Chưa có nguồn EN cho câu này.'));
        const canonical = make('div');
        body.replaceChildren(make('p', 'collab-line-id', '#' + base.line_id), sourcePreview, source, canonical);

        const text = history?.new_text || history?.snapshot?.new_vi || '';
        const diff = make('details', 'collab-diff-details');
        diff.append(make('summary', '', 'So sánh thay đổi'));
        const showBase = () => {
            canonical.replaceChildren(V.summary(base));
            source.querySelector('.collab-source-grid')?.remove();
            source.append(V.sources(base));
            sourcePreview.lastChild.textContent = base.en || 'Chưa có nguồn EN cho câu này.';
            if (!report) {
                diff.querySelector('.collab-diff')?.remove();
                diff.append(V.diff(base.new_vi || '', text));
            }
        };
        showBase();

        const form = make('form', 'collab-form');
        form.id = 'collabLineActionForm';
        if (!report) {
            const label = make('label', '', 'Phiên bản sẽ khôi phục');
            const input = make('textarea');
            input.rows = 3;
            input.value = text;
            input.readOnly = true;
            label.append(input);
            form.append(label, diff);
        }

        const reasonLabel = make('label', '', 'Lý do');
        const reason = make('select');
        const empty = make('option', '', 'Chọn lý do');
        empty.value = '';
        reason.append(empty);
        for (const [value, label] of Object.entries(reasonLabels)) {
            const option = make('option', '', label);
            option.value = value;
            reason.append(option);
        }
        reason.required = true;
        reasonLabel.append(reason);
        const detailLabel = make('label', '', 'Giải thích thêm (không bắt buộc)');
        const detail = make('textarea');
        detail.rows = 2;
        detailLabel.append(detail);
        const error = make('p', 'collab-error');
        error.hidden = true;
        error.role = 'alert';
        const submit = make('button', 'btn-save-glow', report ? 'Báo cần xem lại' : 'Khôi phục phiên bản');
        submit.type = 'submit';
        submit.disabled = !M().ready;
        const reload = action('Tải bản mới để đối chiếu', async () => {
            try {
                const latest = await M().getLine(base);
                if (!active()) return;
                base = { ...base, ...latest };
                M().patch(base);
                showBase();
                error.hidden = true;
                reload.hidden = true;
                submit.disabled = !M().ready;
            } catch (err) {
                if (active()) showError(error, err);
            }
        }, 'collab-link');
        reload.hidden = true;
        form.append(reasonLabel, detailLabel, error, reload);
        body.append(form);
        const footer = make('div', 'collab-dialog-footer');
        submit.setAttribute('form', form.id);
        footer.append(submit);
        dialog().append(footer);

        let payloadKey, requestId;
        form.addEventListener('submit', async event => {
            event.preventDefault();
            if (submit.disabled || !active()) return;
            error.hidden = true;
            const payload = {
                ...M().ref(base),
                base_revision: base.revision,
                base_source_hash: base.source_hash,
                base_dataset_version: base.dataset_version,
                reason: [reasonLabels[reason.value], detail.value].filter(Boolean).join(': '),
                reason_detail: detail.value,
                ...(!report ? { action: 'restore', history_id: history.id } : {})
            };
            const key = JSON.stringify(payload);
            if (key !== payloadKey) {
                payloadKey = key;
                requestId = crypto.randomUUID();
            }
            submit.disabled = true;
            try {
                const result = await M().request(report ? 'report' : 'review', { ...payload, request_id: requestId }, !report);
                if (result.line) M().patch(result.line);
                if (active()) dialog().close();
                rerender();
                showToastAlert(report ? 'Đã báo câu cần xem lại.' : 'Đã khôi phục thành một phiên bản mới.');
            } catch (err) {
                if (!active()) return;
                showError(error, err);
                if (err.code === 'dataset_stale' || err.code === 'dataset_locked') await M().init();
                if (err.status === 409) reload.hidden = false;
            } finally {
                submit.disabled = !M().ready;
            }
        });
    };
    V.openHistory = async item => {
        const body=clear('Lịch sử & đề xuất');const serial=requestSerial;body.append(make('p','','Đang tải lịch sử…'));
        try{
            const data=await M().history(item);if(serial!==requestSerial||!dialog().open)return;
            const line={...item,...data.line};M().patch(line);body.replaceChildren(make('p','collab-line-id','#'+line.line_id),V.summary(line));
            const error=make('p','collab-error');error.hidden=true;error.role='alert';body.append(error);
            let busy=false;
            const review=async(actionType,proposal)=>{if(busy)return;busy=true;try{const result=await M().request('review',{...M().ref(line),base_revision:line.revision,base_source_hash:line.source_hash,base_dataset_version:line.dataset_version,action:actionType,proposal_id:proposal?.id,reason:actionType==='accept'?'Chấp nhận đề xuất':actionType==='reject'?'Không chấp nhận đề xuất':'Duyệt bản dịch hiện tại',request_id:crypto.randomUUID()},true);if(result.line)M().patch(result.line);if(requestSerial===serial && dialog().open)await V.openHistory(result.line || line);}catch(err){showError(error,err);}finally{busy=false;}};
            if(M().canReview&&M().hasText(line)&&M().status(line)!=='approved')body.append(action('Duyệt bản hiện tại',()=>review('approve')));
            body.append(make('h3','','Đề xuất sửa'));
            const pending=(data.proposals || []).filter(p=>p.state==='pending');
            if(!pending.length)body.append(make('p','collab-muted','Chưa có đề xuất đang chờ duyệt.'));
            const proposalList=make('div');body.append(proposalList);
            const renderProposals=items=>{for(const proposal of items){
                const card=make('section','collab-event');const mine=proposal.user_id&&proposal.user_id===M().user?.id;card.append(make('strong','',(mine?'Của bạn · ':'')+(proposal.translator || 'Ẩn danh')),make('p','collab-muted',M().time(proposal.updated_at || proposal.created_at)+' · '+(reasonLabels[proposal.reason] || proposal.reason || 'Đề xuất sửa')),V.diff(line.new_vi || '',proposal.text_vi || ''));
                card.append(make('p','collab-origin',proposal.origin==='machine'?'Bản dịch máy · Chưa duyệt':proposal.origin==='human'?'Người dịch tự nhập':'Nguồn đề xuất chưa rõ'));
                if(proposal.reason_detail)card.append(make('p','',proposal.reason_detail));if(proposal.notes)card.append(make('p','collab-context','Ngữ cảnh: '+proposal.notes));
                if(mine&&M().ready)card.append(action('Sửa đề xuất của tôi',()=>{
                    dialog().addEventListener('close', () => requestAnimationFrame(() => editOwnProposal(line, proposal)), { once: true });
                    dialog().close();
                }));
                if(M().canReview){const buttons=make('div','collab-actions');buttons.append(action('Chấp nhận',()=>review('accept',proposal)),action('Từ chối',()=>review('reject',proposal)));card.append(buttons);}proposalList.append(card);
            }};renderProposals(pending);
            if(data.proposals_next_cursor){const more=action('Xem thêm đề xuất',async()=>{more.disabled=true;try{const page=await M().history(line,undefined,more.dataset.cursor);if(serial!==requestSerial||!dialog().open)return;renderProposals(page.proposals || []);more.dataset.cursor=page.proposals_next_cursor || '';more.hidden=!page.proposals_next_cursor;}catch(err){showError(error,err);}finally{more.disabled=false;}});more.dataset.cursor=data.proposals_next_cursor;body.append(more);}
            body.append(make('h3','','Các lần thay đổi'));
            const historyList=make('div');body.append(historyList);
            const renderEvents=events=>{for(const event of events){const card=make('section','collab-event');const types={import:'Nhập dữ liệu cũ',legacy_import:'Nhập dữ liệu cũ',translation_created:'Tạo bản dịch',translation_saved:'Lưu bản dịch',proposal_created:'Gửi đề xuất',proposal_updated:'Sửa đề xuất',proposal_accepted:'Chấp nhận đề xuất',proposal_rejected:'Từ chối đề xuất',approved:'Duyệt bản dịch',moderator_approved:'Moderator sửa & duyệt',restored:'Khôi phục phiên bản',reported:'Báo cần xem lại',source_changed:'Câu gốc thay đổi'};card.append(make('strong','',types[event.event_type] || event.event_type),make('p','collab-muted',(event.actor || 'Chưa ghi nhận người sửa')+' · '+M().time(event.created_at)));if(event.reason)card.append(make('p','',event.reason));if(typeof event.new_text==='string')card.append(V.diff(event.old_text || '',event.new_text));if(M().canReview&&event.new_text)card.append(action('Khôi phục bản này',()=>V.openLineAction(line,{mode:'restore',history:event})));historyList.append(card);}};
            renderEvents(data.history || []);if(!(data.history || []).length)historyList.append(make('p','collab-muted','Chưa có lịch sử trước khi bật tính năng cộng tác.'));
            if(data.next_cursor){const more=action('Xem các lần trước',async()=>{more.disabled=true;try{const page=await M().history(line,more.dataset.cursor);renderEvents(page.history || []);more.dataset.cursor=page.next_cursor || '';more.hidden=!page.next_cursor;}catch(err){showError(error,err);}finally{more.disabled=false;}});more.dataset.cursor=data.next_cursor;body.append(more);}
        }catch(err){if(serial===requestSerial)body.replaceChildren(make('p','collab-error',err.message));}
    };
    V.renderCurrent = item => {
        const target=document.getElementById('currentLineCollaboration');if(!target)return;
        const summary=V.summary(item), details=make('details','current-translation-details');details.append(make('summary','','Thông tin bản dịch'));
        for(const extra of summary.querySelectorAll('.collab-meta, .collab-context, .collab-muted'))details.append(extra);
        target.replaceChildren(summary,details);
        const buttons=make('div','collab-actions');buttons.append(action(item.pending_proposals?`Xem ${item.pending_proposals} đề xuất`:'Xem lịch sử',()=>V.openHistory(item)),action('Báo vấn đề',()=>V.openLineAction(item,{mode:'report'})));target.append(buttons);
        const save=document.querySelector('#saveCurrentTranslation > span');if(save)save.textContent=V.saveText(item);
        const title=document.querySelector('.translation-input-box .input-title');if(title)title.textContent=M().canModerate?'SỬA BẢN DỊCH (MODERATOR · DUYỆT NGAY)':M().hasText(item)?'SOẠN ĐỀ XUẤT SỬA':'BẢN DỊCH TIẾNG VIỆT MỚI';
    };
    window.openReviewerAccess=()=>V.login();
    window.openModeratorAccess=()=>V.moderator();
})();
