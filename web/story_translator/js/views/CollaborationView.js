/** Read-only current versions, proposal diffs and immutable history. */
(() => {
    const V = window.CollaborationView = {};
    const M = () => window.Collaboration;
    const make = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
    const action = (text, handler, cls = 'btn-direction') => { const b = make('button', cls, text); b.type = 'button'; b.addEventListener('click', handler); return b; };
    const reasonLabels = { meaning:'Sai nghĩa', pronouns:'Sai xưng hô', naturalness:'Câu chưa tự nhiên', other:'Khác' };
    let session = null, requestSerial = 0, previousFocus = null;
    V.badge = line => make('span', 'collab-badge collab-' + M().status(line), M().labels[M().status(line)]);
    V.metadata = line => {
        const wrap = make('div','collab-meta');
        wrap.append(make('span','', 'Người dịch: ' + (line.translator || 'Chưa có')));
        const time = make('time','', 'Cập nhật: ' + M().time(line.updated_at)); if (line.updated_at) { time.dateTime = line.updated_at; time.title = new Date(line.updated_at).toLocaleString('vi-VN'); } wrap.append(time);
        if (M().hasText(line)) wrap.append(make('span','collab-origin',M().origin(line)));
        if (line.pending_proposals) wrap.append(action(`${line.pending_proposals} đề xuất chờ duyệt`,()=>V.openHistory(line),'collab-proposal-link'));
        return wrap;
    };
    V.summary = line => {
        const e = make('div','collab-summary'); e.append(V.badge(line));
        e.append(make('span','collab-current-label','Bản đang dùng'));
        e.append(make('p','collab-current-text',line.new_vi || 'Chưa có bản dịch tiếng Việt.'));
        e.append(V.metadata(line));
        if (line.notes) e.append(make('p','collab-context','Ngữ cảnh: ' + line.notes));
        if (line.provenance === 'legacy_import') e.append(make('small','collab-muted','Dữ liệu nhập từ bản cũ; chưa có nhật ký hoặc thời gian của các lần sửa trước.'));
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
        if(line.sheet_vi||line.sheet_old_vi){const panel=make('section','collab-source-panel');panel.append(make('strong','',line.sheet_vi?'VI trên Google Sheet':'VI cũ trên Google Sheet'),make('p','collab-source',line.sheet_vi||line.sheet_old_vi));grid.append(panel);}
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
        const d = dialog(); requestSerial++; previousFocus = d.open ? previousFocus : document.activeElement; d.replaceChildren();
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
        d.addEventListener('close',()=>{ if(d.open)return;requestSerial++; session=null; if(previousFocus?.isConnected)previousFocus.focus({preventScroll:true}); });
    };
    V.login = () => {
        const body = clear('Quyền duyệt'), serial=requestSerial;
        if (M().canReview) { body.append(make('p','', 'Quyền duyệt đang bật trong tab này.'),action('Quản lý phiên dữ liệu',()=>V.release()),action('Tắt quyền duyệt',()=>{M().logout();dialog().close();rerender();}));return; }
        body.append(make('p','','Nhập mã quản trị được cấp để duyệt, chấp nhận đề xuất hoặc khôi phục phiên bản. Mã chỉ giữ trong bộ nhớ của tab đang mở.'));
        const form=make('form','collab-form'),label=make('label','','Mã quản trị'),input=make('input');input.type='password';input.autocomplete='off';input.required=true;label.append(input);
        const error=make('p','collab-error');error.hidden=true;error.role='alert';const submit=make('button','btn-save-glow','Bật quyền duyệt');submit.type='submit';form.append(label,error,submit);body.append(form);
        form.addEventListener('submit',async e=>{e.preventDefault();submit.disabled=true;try{await M().login(input.value);input.value='';if(serial===requestSerial&&dialog().open){dialog().close();rerender();}showToastAlert('Đã bật quyền duyệt.');}catch(err){input.value='';showError(error,err);}finally{submit.disabled=false;}});
    };
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
    V.openEdit = async (item, suppliedDraft, options={}) => {
        const body=clear(options.mode==='report'?'Báo câu cần xem lại':options.mode==='restore'?'Khôi phục phiên bản':M().hasText(item)?'Đề xuất sửa bản dịch':'Dịch câu mới');
        const serial=requestSerial;body.append(make('p','','Đang lấy bản hiện tại…'));
        let base;
        try { base={...item,...await M().getLine(item)}; } catch(error) { body.replaceChildren(make('p','collab-error',error.message));return; }
        if (serial!==requestSerial || !dialog().open) return;
        M().patch(base);body.replaceChildren();body.append(make('p','collab-line-id','#'+base.line_id),V.sources(base),V.summary(base));
        const mode=options.mode || 'edit';
        let ownProposal=null;
        if(mode==='edit')try{ownProposal=await M().myProposal(base);}catch(_){}
        if(serial!==requestSerial || !dialog().open)return;
        const ownDraft=ownProposal?.state==='pending'?{text:ownProposal.text_vi,origin:ownProposal.origin,notes:ownProposal.notes,reason:ownProposal.reason,reason_detail:ownProposal.reason_detail}:null;
        const stored=M().readDraft(base)||ownDraft;
        const form=make('form','collab-form'),label=make('label','',mode==='restore'?'Phiên bản sẽ khôi phục':'Bản đề xuất');
        const input=make('textarea');input.id='collabDraft';input.rows=5;input.value=mode==='restore'?(options.history.new_text || options.history.snapshot?.new_vi || ''):(suppliedDraft!==undefined?suppliedDraft:stored?.text ?? base.new_vi ?? '');input.readOnly=mode==='restore';label.append(input);
        const diff=make('div','collab-diff-wrap');
        const originLabel=make('label','','Nguồn bản dịch'),origin=make('select');for(const [value,text]of [['human','Tự dịch / biên tập'],['machine','Bản dịch máy/AI'],['','Chọn nguồn bản đề xuất']]){const o=make('option','',text);o.value=value;origin.append(o);}origin.value=stored?.origin || (M().hasText(base) ? base.translation_origin || '' : 'human');originLabel.append(origin);
        const notesLabel=make('label','','Ghi chú ngữ cảnh'),notes=make('textarea');notes.rows=2;notes.value=stored?.notes ?? base.notes ?? '';notesLabel.append(notes);
        const reasonLabel=make('label','','Lý do'),reason=make('select');const empty=make('option','','Chọn lý do');empty.value='';reason.append(empty);for(const [value,text]of Object.entries(reasonLabels)){const o=make('option','',text);o.value=value;reason.append(o);}reason.value=stored?.reason || '';reason.required=mode!=='edit' || M().hasText(base);reasonLabel.append(reason);
        const detailLabel=make('label','','Giải thích thêm (bắt buộc nếu chọn Khác)'),detail=make('textarea');detail.rows=2;detail.value=stored?.reason_detail || '';detailLabel.append(detail);
        const error=make('p','collab-error');error.hidden=true;error.role='alert';const reload=action('Tải bản mới để đối chiếu',async()=>{const active=session,activeSerial=requestSerial;if(!active)return;try{const latest={...active.base,...await M().getLine(active.base)};if(requestSerial!==activeSerial||session!==active||!dialog().open)return;active.base=latest;M().patch(latest);canonical.replaceChildren(V.summary(latest));const refreshed=V.sources(latest);sourceNode.replaceWith(refreshed);sourceNode=refreshed;reason.required=mode!=='edit'||M().hasText(latest);if(reason.required&&!reasonLabel.isConnected){form.insertBefore(reasonLabel,error);form.insertBefore(detailLabel,error);}if(mode==='edit')submit.textContent=M().hasText(latest)?'Gửi đề xuất sửa':'Lưu bản dịch · Chờ duyệt';error.textContent='Đã tải bản mới. Bản nháp của bạn được giữ nguyên; kiểm tra phần khác biệt rồi gửi lại.';reload.hidden=true;active.payloadKey='';updateDiff();}catch(err){if(requestSerial===activeSerial&&session===active)showError(error,err);}},'collab-link');reload.hidden=true;
        const submit=make('button','btn-save-glow',mode==='report'?'Báo cần xem lại':mode==='restore'?'Khôi phục phiên bản':M().hasText(base)?'Gửi đề xuất sửa':'Lưu bản dịch · Chờ duyệt');submit.type='submit';submit.disabled=!M().ready;
        let sourceNode=body.querySelector('.collab-source-grid');
        const canonical=make('div');canonical.append(V.summary(base));body.lastChild.replaceWith(canonical);
        if(mode!=='report')form.append(label,diff);
        origin.required=mode==='edit';
        if(!['human','machine'].includes(origin.value))origin.value='';
        reason.addEventListener('change',()=>{detail.required=reason.value==='other';});
        if(mode==='edit')form.append(originLabel,notesLabel);
        if(reason.required)form.append(reasonLabel,detailLabel);
        form.append(error,reload,submit);body.append(form);
        if(ownProposal?.state==='pending')body.prepend(make('p','collab-info','Bạn đã có một đề xuất cho câu này trong phiên hiện tại. Gửi lại sẽ sửa đề xuất đó.'));
        if(stored?.legacy||stored?.base_dataset_version&&stored.base_dataset_version!==base.dataset_version)body.prepend(make('p','collab-info','Bản nháp thuộc phiên cũ. Kiểm tra với bản hiện tại trước khi gửi; nội dung nháp vẫn được giữ.'));
        session={base,mode,payloadKey:'',requestId:'',input};
        const updateDiff=()=>{diff.replaceChildren(V.diff(session?.base.new_vi || base.new_vi || '',input.value));};updateDiff();
        const saveLocal=()=>{if(mode==='edit')M().saveDraft(base,{text:input.value,origin:origin.value,notes:notes.value,reason:reason.value,reason_detail:detail.value,base_revision:base.revision});};
        for(const field of [input,origin,notes,reason,detail])field.addEventListener('input',()=>{saveLocal();updateDiff();});
        input.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();form.requestSubmit();}});
        form.addEventListener('submit',async e=>{
            e.preventDefault();if(!session || submit.disabled)return;error.hidden=true;
            if(mode!=='report'&&!input.value.trim()){showError(error,new Error('Nhập bản dịch trước khi gửi.'));return;}
            if(mode==='edit'&&!validateTokens(session.base.en || '',input.value).isValid){showError(error,new Error('Bản đề xuất đang thiếu token. Hãy bổ sung đúng các mã từ câu gốc.'));return;}
            if(reason.required&&!reason.value){showError(error,new Error('Chọn lý do trước khi gửi.'));return;}
            const state=session,hadCurrent=M().hasText(state.base),ref=M().ref(state.base),reasonText=reasonLabels[reason.value] || '';
            const payload={...ref,base_revision:state.base.revision,base_source_hash:state.base.source_hash,base_dataset_version:state.base.dataset_version,reason:mode==='edit'?reason.value:[reasonText,detail.value].filter(Boolean).join(': '),reason_detail:detail.value};
            if(mode==='edit')Object.assign(payload,{text_vi:input.value,origin:origin.value,notes:notes.value});
            if(mode==='restore')Object.assign(payload,{action:'restore',history_id:options.history.id});
            const payloadKey=JSON.stringify(payload);if(state.payloadKey!==payloadKey){state.payloadKey=payloadKey;state.requestId=crypto.randomUUID();}payload.request_id=state.requestId;
            submit.disabled=true;saveLocal();
            try{
                const result=await M().request(mode==='edit'?'submit':mode==='report'?'report':'review',payload,mode==='restore');
                if(result.line)M().patch(result.line);
                if(mode==='edit'){M().clearDraft(base,payload.text_vi);M().award(payload.request_id,result.replayed);}
                if(requestSerial===serial && session===state){dialog().close();rerender();}
                else if(viewMode==='list')renderListMode();
                showToastAlert(mode==='edit'?(hadCurrent?'Đã gửi đề xuất sửa. Bản đang dùng vẫn được giữ nguyên.':'Đã lưu bản dịch · Chờ duyệt.'):mode==='report'?'Đã báo câu cần xem lại.':'Đã khôi phục thành một phiên bản mới.');
            }catch(err){if(requestSerial!==serial || session!==state){showToastAlert(err.message);return;}showError(error,err);if(err.code==='dataset_stale'||err.code==='dataset_locked'){await M().init();reload.hidden=false;}else if(err.status===409){error.textContent='Câu này đã được cập nhật hoặc câu gốc thay đổi. Bản nháp của bạn vẫn được giữ. Tải bản mới để đối chiếu trước khi gửi lại.';reload.hidden=false;}}
            finally{submit.disabled=!M().ready;}
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
                if(mine&&M().ready)card.append(action('Sửa đề xuất của tôi',()=>V.openEdit(line)));
                if(M().canReview){const buttons=make('div','collab-actions');buttons.append(action('Chấp nhận',()=>review('accept',proposal)),action('Từ chối',()=>review('reject',proposal)));card.append(buttons);}proposalList.append(card);
            }};renderProposals(pending);
            if(data.proposals_next_cursor){const more=action('Xem thêm đề xuất',async()=>{more.disabled=true;try{const page=await M().history(line,undefined,more.dataset.cursor);if(serial!==requestSerial||!dialog().open)return;renderProposals(page.proposals || []);more.dataset.cursor=page.proposals_next_cursor || '';more.hidden=!page.proposals_next_cursor;}catch(err){showError(error,err);}finally{more.disabled=false;}});more.dataset.cursor=data.proposals_next_cursor;body.append(more);}
            body.append(make('h3','','Các lần thay đổi'));
            const historyList=make('div');body.append(historyList);
            const renderEvents=events=>{for(const event of events){const card=make('section','collab-event');const types={import:'Nhập dữ liệu cũ',legacy_import:'Nhập dữ liệu cũ',translation_created:'Tạo bản dịch',translation_saved:'Lưu bản dịch',proposal_created:'Gửi đề xuất',proposal_updated:'Sửa đề xuất',proposal_accepted:'Chấp nhận đề xuất',proposal_rejected:'Từ chối đề xuất',approved:'Duyệt bản dịch',restored:'Khôi phục phiên bản',reported:'Báo cần xem lại',source_changed:'Câu gốc thay đổi'};card.append(make('strong','',types[event.event_type] || event.event_type),make('p','collab-muted',(event.actor || 'Chưa ghi nhận người sửa')+' · '+M().time(event.created_at)));if(event.reason)card.append(make('p','',event.reason));if(typeof event.new_text==='string')card.append(V.diff(event.old_text || '',event.new_text));if(M().canReview&&event.new_text)card.append(action('Khôi phục bản này',()=>V.openEdit(line,undefined,{mode:'restore',history:event})));historyList.append(card);}};
            renderEvents(data.history || []);if(!(data.history || []).length)historyList.append(make('p','collab-muted','Chưa có lịch sử trước khi bật tính năng cộng tác.'));
            if(data.next_cursor){const more=action('Xem các lần trước',async()=>{more.disabled=true;try{const page=await M().history(line,more.dataset.cursor);renderEvents(page.history || []);more.dataset.cursor=page.next_cursor || '';more.hidden=!page.next_cursor;}catch(err){showError(error,err);}finally{more.disabled=false;}});more.dataset.cursor=data.next_cursor;body.append(more);}
        }catch(err){if(serial===requestSerial)body.replaceChildren(make('p','collab-error',err.message));}
    };
    V.renderCurrent = item => {
        const target=document.getElementById('currentLineCollaboration');if(!target)return;target.replaceChildren(V.summary(item));
        const buttons=make('div','collab-actions');buttons.append(action(item.pending_proposals?`Xem ${item.pending_proposals} đề xuất`:'Xem lịch sử',()=>V.openHistory(item)),action('Báo vấn đề',()=>V.openEdit(item,undefined,{mode:'report'})));target.append(buttons);
        const save=document.querySelector('.btn-save-glow[onclick="saveCurrentLine()"] span');if(save)save.textContent=M().hasText(item)?'Đề xuất sửa':'Lưu bản dịch · Chờ duyệt';
        const title=document.querySelector('.translation-input-box .input-title');if(title)title.textContent=M().hasText(item)?'SOẠN ĐỀ XUẤT SỬA':'BẢN DỊCH TIẾNG VIỆT MỚI';
    };
    window.openReviewerAccess=()=>V.login();
})();
