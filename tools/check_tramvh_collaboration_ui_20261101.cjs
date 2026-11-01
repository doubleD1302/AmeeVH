// Browser regression: isolated fixture or actual local Worker+D1. Never writes production.
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { spawn } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const base = path.join(root, 'web/story_translator');
const workerMode=process.argv.includes('--worker'),publicMode=process.argv.includes('--public-readonly');
const out=path.join(root,'reports/tramvh_collaboration_20261101_r01',publicMode?'ui_public_readonly':workerMode?'ui_worker':'ui_fixture');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));


const clone=value=>JSON.parse(JSON.stringify(value));
const fixtureLines=[
 {chapter_id:'Chuong_3_MainStory',line_id:'QA.1',scene_id:'QA',speaker:'Minh',en:'Hello {0}',old_vi:'Bản cũ {0}',new_vi:'Chào {0}',translator:'Minh',status:'approved',translation_origin:'human',updated_at:new Date(Date.now()-7200000).toISOString(),notes:'Ngữ cảnh <img src=x onerror=alert(1)>',revision:1,source_hash:'hash1',pending_proposals:0},
 {chapter_id:'Chuong_3_MainStory',line_id:'QA.2',scene_id:'QA',speaker:'Dẫn chuyện',en:'A new line',old_vi:'',new_vi:'',translator:'',status:'untranslated',translation_origin:'unknown',updated_at:null,notes:'',revision:1,source_hash:'hash2',pending_proposals:0},
 {chapter_id:'Chuong_3_MainStory',line_id:'QA.3',scene_id:'QA',speaker:'Minh',en:'AI line',old_vi:'',new_vi:'Bản máy',translator:'Công cụ AI',status:'machine_pending',translation_origin:'machine',updated_at:null,notes:'',revision:1,source_hash:'hash3',pending_proposals:0}
];
let proposals=[],history=[],nextId=1;
async function fixtureApi(req,res){
 const url=new URL(req.url,'http://localhost');const send=(data,status=200)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
 if(url.pathname==='/api/chapters')return send([{id:'Chuong_3_MainStory',title:'Chương kiểm thử',progress_pct:66.7}]);
 if(url.pathname==='/api/chapter_data')return send({chapter_id:'Chuong_3_MainStory',title:'Chương kiểm thử',scenes:[{scene_id:'QA',title:'Cảnh kiểm thử',lines:clone(fixtureLines)}],collaboration_available:true});
 if(url.pathname==='/api/glossary')return send({terms:[{en:'Hello',vi:'Chào',category:'QA'}]});
 if(url.pathname==='/api/collab/status')return send({success:true,can_write:true});
 if(url.pathname==='/api/collab/role')return send({success:true,can_review:req.headers['x-reviewer-key']==='qa-review-key'});
 if(!url.pathname.startsWith('/api/collab/'))return send({success:false},404);
 if(req.method==='GET'){
  const line=fixtureLines.find(l=>l.line_id===url.searchParams.get('line_id'));if(!line)return send({success:false},404);
  return send(url.pathname.endsWith('/history')?{success:true,line:clone(line),history:clone(history),proposals:clone(proposals)}:{success:true,line:clone(line)});
 }
 const chunks=[];for await(const chunk of req)chunks.push(chunk);const data=JSON.parse(Buffer.concat(chunks));const line=fixtureLines.find(l=>l.line_id===data.line_id);if(!line)return send({success:false},404);
 if(line.revision!==data.base_revision||line.source_hash!==data.base_source_hash)return send({success:false,code:'conflict',line:clone(line),message:'Updated'},409);
 if(url.pathname.endsWith('/submit')){
  if(line.new_vi){const proposal={id:String(nextId++),text_vi:data.text_vi,translator:data.translator,origin:data.origin,notes:data.notes,reason:data.reason,reason_detail:data.reason_detail,state:'pending',created_at:new Date().toISOString(),base_text:line.new_vi};proposals.push(proposal);line.revision++;line.pending_proposals++;return send({success:true,line:clone(line),proposal:clone(proposal),result:'proposed'});}
  line.new_vi=data.text_vi;line.translator=data.translator;line.status=data.origin==='machine'?'machine_pending':'pending';line.translation_origin=data.origin;line.updated_at=new Date().toISOString();line.revision++;return send({success:true,line:clone(line),result:'saved'});
 }
 if(url.pathname.endsWith('/review')){
  if(req.headers['x-reviewer-key']!=='qa-review-key')return send({success:false,message:'No permission'},403);
  if(data.action==='accept'){const prop=proposals.find(p=>p.id===data.proposal_id);const old=line.new_vi;line.new_vi=prop.text_vi;line.translator=prop.translator;line.status='approved';line.revision++;line.pending_proposals--;prop.state='accepted';history.push({id:String(nextId++),event_type:'proposal_accepted',actor:data.reviewer,new_text:line.new_vi,old_text:old,source_hash:line.source_hash,created_at:new Date().toISOString()});}
  return send({success:true,line:clone(line)});
 }
 return send({success:false},400);
}

(async () => {
    await fs.mkdir(out, { recursive: true });
    const requests = [], exceptions = [], checks = [];
    const server = http.createServer(async (req, res) => {
        requests.push(req.method + ' ' + req.url);
        if (req.url.startsWith('/api/')) return fixtureApi(req,res);
        if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
        try {
            let rel = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
            if (rel === '/') rel = '/index.html';
            const file = path.resolve(base, '.' + rel);
            if (!file.startsWith(base + path.sep)) throw Error('Outside static root');
            const data = await fs.readFile(file);
            const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png' };
            res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
            res.end(data);
        } catch { res.writeHead(404); res.end(); }
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const url=publicMode?'https://tramvh.doubled1302.workers.dev':workerMode?'http://127.0.0.1:8871':`http://127.0.0.1:${server.address().port}`;
    const qa=async(route,body={})=>{const r=await fetch(url+'/api/__qa/'+route,{method:'POST',headers:{'Content-Type':'application/json','X-QA-Key':'qa-fixture'},body:JSON.stringify(body)});if(!r.ok)throw Error('Local QA endpoint failed');};
    const read=async id=>(await (await fetch(url+'/api/collab/line?chapter_id=Chuong_3_MainStory&line_id='+id)).json()).line;
    const mutate=async(route,line,extra)=>{const r=await fetch(url+'/api/collab/'+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chapter_id:line.chapter_id,line_id:line.line_id,base_revision:line.revision,base_source_hash:line.source_hash,request_id:crypto.randomUUID(),translator:'Other QA',...extra})});if(!r.ok)throw Error('Local mutation failed: '+await r.text());return r.json();};
    if(workerMode)await qa('reset');
    const profile = path.join(root, 'work/runs/tramvh_collaboration_20261101_r01/chrome-ui-' + Date.now());
    await fs.mkdir(profile, { recursive: true });
    const chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless', '--disable-gpu', '--disable-extensions', '--no-first-run', '--remote-debugging-port=0', '--remote-allow-origins=*', `--user-data-dir=${profile}`, 'about:blank'], { windowsHide: true, stdio: 'ignore' });
    let ws;
    try {
        let port;
        for (let i = 0; i < 100; i++) { try { port = (await fs.readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; } catch { await pause(100); } }
        if (!port) throw Error('No Chrome DevTools port');
        const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
        ws = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
        await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
        let sequence = 0;
        const pending = new Map();
        const call = (method, params = {}) => new Promise((resolve, reject) => {
            const id = ++sequence;
            pending.set(id, { resolve, reject });
            ws.send(JSON.stringify({ id, method, params }));
        });
        ws.onmessage = event => {
            const message = JSON.parse(event.data);
            if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
            if (message.method === 'Fetch.requestPaused') {
                const { requestId, request } = message.params; requests.push(request.method + " " + request.url);
                // External fonts/audio/GAS are not needed to exercise guide behavior.
                call(request.url.startsWith(url + '/') && (request.method==='GET'||(!publicMode&&request.method==='POST')) ? 'Fetch.continueRequest' : 'Fetch.failRequest', { requestId, ...(request.url.startsWith(url + '/') && (request.method==='GET'||(!publicMode&&request.method==='POST')) ? {} : { errorReason: 'BlockedByClient' }) }).catch(() => {});
            }
            if (message.id && pending.has(message.id)) {
                const result = pending.get(message.id); pending.delete(message.id);
                message.error ? result.reject(Error(JSON.stringify(message.error))) : result.resolve(message.result);
            }
        };
        const evaluate = async expression => {
            const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
            if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
            return result.result.value;
        };
        const check = async (name, expression) => { let result;for(let attempt=0;attempt<50;attempt++){result=await evaluate(expression);if(result===true)break;await pause(100);} checks.push({ name, passed: result === true, result }); if(result!==true){await fs.writeFile(path.join(out,'FAILURE.json'),JSON.stringify({name,checks,exceptions,dialog:await evaluate("document.querySelector('#collaborationDialog')?.textContent"),cards:await evaluate("document.querySelector('.table-row-card')?.textContent")},null,2));throw Error(name+': '+JSON.stringify(result));} };
        const key = async (key, code, modifiers = 0, text) => {
            await call('Input.dispatchKeyEvent', { type: 'keyDown', key, windowsVirtualKeyCode: code, modifiers, ...(text ? { text } : {}) });
            await call('Input.dispatchKeyEvent', { type: 'keyUp', key, windowsVirtualKeyCode: code, modifiers });
        };
        const screenshot = async name => {
            await pause(80);
            const result = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
            await fs.writeFile(path.join(out, name + '.png'), Buffer.from(result.data, 'base64'));
        };
        await call('Runtime.enable'); await call('Page.enable'); await call('Fetch.enable', { patterns: [{ urlPattern: '*' }] });
        await call('Page.addScriptToEvaluateOnNewDocument', { source: `localStorage.setItem('stella_user_profile', JSON.stringify({name:'Guide QA',avatar:'',level:1,exp:0}));` });
        await call('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
        await call('Page.navigate', { url });
        for (let i = 0; i < 100; i++) { if (await evaluate(`typeof filteredLines !== 'undefined' && filteredLines.length > 0 && typeof openTranslationGuide === 'function'`)) break; await pause(100); }

        if(publicMode){
            await check('production collaboration available',`typeof Collaboration!=='undefined'&&Collaboration.ready&&currentLines.length>0`);
            await evaluate(`closeProfileModal();switchMode('list')`);
            await check('production list displays status translator history',`(()=>{const row=document.querySelector('.table-row-card');return !!row?.querySelector('.collab-badge')&&row.textContent.includes('Người dịch:')&&row.textContent.includes('Xem lịch sử')&&!row.querySelector('textarea,input')})()`);
            await evaluate(`document.querySelectorAll('.table-row-card button')[1].click()`);
            await check('production import history is visible',`document.querySelector('#collaborationDialog').textContent.includes('Nhập dữ liệu cũ')`);
            await evaluate(`document.querySelector('.collab-close').click()`);
            for(const width of [1440,390,320]){await call('Emulation.setDeviceMetricsOverride',{width,height:width===1440?1000:844,deviceScaleFactor:1,mobile:width<700});for(const theme of ['light','dark']){
                await evaluate(`document.documentElement.dataset.theme=${JSON.stringify(theme)};switchMode('list')`);
                await check(`public list layout ${width} ${theme}`,`document.documentElement.scrollWidth<=innerWidth`);await screenshot(`public-list-${width}-${theme}`);
                await evaluate(`document.querySelector('.table-row-card button').click()`);
                await check(`public proposal current version ${width} ${theme}`,`!!document.querySelector('#collabDraft')&&document.querySelector('#collaborationDialog .collab-current-text').textContent===currentLines[0].new_vi`);
                await check(`public proposal layout ${width} ${theme}`,`(()=>{const d=document.querySelector('#collaborationDialog'),r=d.getBoundingClientRect(),b=d.querySelector('.collab-dialog-body');return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight&&b.scrollWidth<=b.clientWidth+1})()`);await screenshot(`public-proposal-${width}-${theme}`);
                await evaluate(`document.querySelector('.collab-close').click()`);
            }}
        }else{
        await evaluate(`closeProfileModal();switchMode('list')`);
        await check('list previews canonical status author time before edit', `(()=>{const c=document.querySelector('.table-row-card');return c.textContent.includes('Đã duyệt')&&c.textContent.includes('Minh')&&c.textContent.includes('2 giờ trước')&&c.textContent.includes('Chào {0}')&&!c.querySelector('input,textarea')})()`);
        await check('machine translation explicitly unapproved', `document.querySelectorAll('.table-row-card')[2].textContent.includes('Bản dịch máy · Chưa duyệt')`);
        await check('notes and text rendered without HTML execution', `!document.querySelector('.table-row-card .collab-context img') && document.querySelector('.collab-context').textContent.includes('<img')`);
        await evaluate(`document.querySelector('.table-row-card button').click()`);
        for(let i=0;i<60;i++){if(await evaluate(`!!document.querySelector('#collabDraft')`))break;await pause(100);}
        await check('proposal opens with readonly current metadata', `document.querySelector('#collaborationDialog').textContent.includes('Chào {0}')&&document.querySelector('#collabDraft').value==='Chào {0}'`);
        await evaluate(`document.querySelector('#collabDraft').value='Xin chào {0}';document.querySelector('#collabDraft').dispatchEvent(new Event('input'));document.querySelector('.collab-form select').value='machine';document.querySelectorAll('.collab-form select')[1].value='naturalness'`);
        await check('diff highlights old and proposed text', `document.querySelector('.collab-diff').textContent.includes('Xin chào {0}')&&!!document.querySelector('.collab-diff ins')`);
        await evaluate(`document.querySelector('.collab-form').requestSubmit()`);
        for(let i=0;i<60;i++){if(await evaluate(`!document.querySelector('#collaborationDialog').open`))break;await pause(100);}
        await check('proposal preserves approved canonical line and author', `currentLines[0].new_vi==='Chào {0}'&&currentLines[0].translator==='Minh'&&currentLines[0].status==='approved'&&currentLines[0].pending_proposals===1`);
        await evaluate(`document.querySelector('.table-row-card button').click()`);
        for(let i=0;i<60;i++){if(await evaluate(`!!document.querySelector('#collabDraft')`))break;await pause(100);}
        await evaluate(`document.querySelector('#collabDraft').value='Bản nháp cần giữ {0}';document.querySelector('#collabDraft').dispatchEvent(new Event('input'));document.querySelectorAll('.collab-form select')[1].value='meaning'`);
        if(workerMode)await mutate('report',await read('QA.1'),{reason:'Concurrent QA update'});else fixtureLines[0].revision++;
        await evaluate(`document.querySelector('.collab-form').requestSubmit()`);await pause(400);
        await check('conflict retains draft and does not silently overwrite', `document.querySelector('#collaborationDialog').open&&document.querySelector('#collabDraft').value==='Bản nháp cần giữ {0}'&&document.querySelector('.collab-error').textContent.includes('đã được cập nhật')`);
        await evaluate(`[...document.querySelectorAll('.collab-form button')].find(b=>b.textContent==='Tải bản mới để đối chiếu').click()`);await pause(400);
        await check('explicit rebase retains proposed text', `document.querySelector('#collabDraft').value==='Bản nháp cần giữ {0}'&&document.querySelector('.collab-error').textContent.includes('Đã tải bản mới')`);
        await evaluate(`document.querySelector('.collab-close').click();openReviewerAccess()`);
        await evaluate(`document.querySelector('.collab-form input').value='bad-key';document.querySelector('.collab-form').requestSubmit()`);await pause(350);
        await check('wrong admin key cannot enable reviewer UI', `!Collaboration.canReview&&document.querySelector('.collab-error').textContent.includes('không hợp lệ')`);
        await evaluate(`document.querySelector('.collab-form input').value='qa-review-key';document.querySelector('.collab-form').requestSubmit()`);await pause(350);
        await check('reviewer access verified by server', `Collaboration.canReview&&!document.querySelector('#collaborationDialog').open`);
        await evaluate(`document.querySelectorAll('.table-row-card button')[1].click()`);await pause(400);
        await check('history includes proposal and diff', `document.querySelector('#collaborationDialog').textContent.includes('Xin chào {0}')&&[...document.querySelectorAll('#collaborationDialog button')].some(b=>b.textContent==='Chấp nhận')`);
        await check('machine proposal origin visible before approval',`document.querySelector('#collaborationDialog').textContent.includes('Bản dịch máy · Chưa duyệt')`);
        await evaluate(`[...document.querySelectorAll('#collaborationDialog button')].find(b=>b.textContent==='Chấp nhận').click()`);await pause(400);
        await check('accept changes canonical version with proposer attribution', `currentLines[0].new_vi==='Xin chào {0}'&&currentLines[0].status==='approved'&&currentLines[0].translator==='Guide QA'`);
        await evaluate(`document.querySelector('.collab-close').click();switchMode('game');document.querySelector('#vietnameseInput').value='Nháp VN {0}';onTranslationDraftInput();navigateLine(1);navigateLine(-1)`);
        await check('VN draft survives navigation without canonical mutation', `document.querySelector('#vietnameseInput').value==='Nháp VN {0}'&&currentLines[0].new_vi==='Xin chào {0}'`);
        for(const width of [1440,390,320]){
            await call('Emulation.setDeviceMetricsOverride',{width,height:width===1440?1000:844,deviceScaleFactor:1,mobile:width<700});
            for(const theme of ['light','dark']){
                await evaluate(`document.documentElement.dataset.theme=${JSON.stringify(theme)};switchMode('list')`);
                await check(`list layout ${width} ${theme}`,`document.documentElement.scrollWidth<=innerWidth`);await screenshot(`list-${width}-${theme}`);
                await evaluate(`document.querySelector('.table-row-card button').click()`);await pause(100);
                await check(`proposal layout ${width} ${theme}`,`(()=>{const d=document.querySelector('#collaborationDialog'),r=d.getBoundingClientRect(),body=d.querySelector('.collab-dialog-body');return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight&&body.scrollWidth<=body.clientWidth+1})()`);await screenshot(`proposal-${width}-${theme}`);
                await evaluate(`document.querySelector('.collab-close').click()`);
            }
        }
        if(workerMode){
            const exported=await(await fetch(url+'/api/export_chapter?id=Chuong_3_MainStory')).json();
            if(exported.scenes?.[0].lines[0].new_vi!=='Xin chào {0}')throw Error('Canonical export mismatch');
            checks.push({name:'export contains latest canonical text',passed:true});
            await evaluate(`Collaboration.clearDraft(currentLines[1]);CollaborationView.openEdit(currentLines[1])`);await pause(400);
            await evaluate(`document.querySelector('#collabDraft').value='Bản nháp của tôi';document.querySelector('#collabDraft').dispatchEvent(new Event('input'))`);
            await mutate('submit',await read('QA.2'),{text_vi:'Bản của người khác',origin:'human',notes:''});
            await evaluate(`document.querySelector('.collab-form').requestSubmit()`);await pause(400);
            await check('empty line concurrent save preserves my draft',`document.querySelector('.collab-error').textContent.includes('đã được cập nhật')&&document.querySelector('#collabDraft').value==='Bản nháp của tôi'`);
            await evaluate(`[...document.querySelectorAll('.collab-form button')].find(b=>b.textContent==='Tải bản mới để đối chiếu').click()`);await pause(400);
            await check('rebase empty to filled requires proposal reason',`document.querySelectorAll('.collab-form select').length===2&&document.querySelectorAll('.collab-form select')[1].required&&document.querySelector('.collab-form button[type=submit]').textContent==='Gửi đề xuất sửa'&&document.querySelector('#collaborationDialog .collab-current-text').textContent==='Bản của người khác'`);
            await evaluate(`document.querySelector('.collab-form').requestSubmit()`);await pause(100);
            await check('missing reason prevents submission after rebase',`document.querySelector('#collaborationDialog').open&&document.querySelectorAll('.collab-form select')[1].value===''`);
            await evaluate(`document.querySelector('.collab-close').click();CollaborationView.openEdit(currentLines[0])`);await pause(400);
            await qa('source',{line_id:'QA.1',en:'Hello {1}'});
            await evaluate(`document.querySelector('#collabDraft').value='Nháp nguồn cũ {0}';document.querySelector('#collabDraft').dispatchEvent(new Event('input'));document.querySelectorAll('.collab-form select')[1].value='meaning';document.querySelector('.collab-form').requestSubmit()`);await pause(400);
            await evaluate(`[...document.querySelectorAll('.collab-form button')].find(b=>b.textContent==='Tải bản mới để đối chiếu').click()`);await pause(400);
            await check('source rebase displays fresh EN and preserves draft',`document.querySelector('.collab-source').textContent==='Hello {1}'&&document.querySelector('#collabDraft').value==='Nháp nguồn cũ {0}'`);
            await evaluate(`document.querySelector('.collab-form').requestSubmit()`);await pause(100);
            await check('rebase validates tokens against fresh source',`document.querySelector('.collab-error').textContent.includes('thiếu token')`);
            await mutate('report',await read('QA.1'),{reason:'Force next conflict'});
            await evaluate(`document.querySelector('#collabDraft').value='Nháp {1}';document.querySelector('.collab-form').requestSubmit()`);await pause(400);
            await evaluate(`(async()=>{window.originalGetLine=Collaboration.getLine;window.delayedLine=await originalGetLine(currentLines[0]);Collaboration.getLine=()=>new Promise(r=>window.resolveRebase=r);[...document.querySelectorAll('.collab-form button')].find(b=>b.textContent==='Tải bản mới để đối chiếu').click()})()`);
            await evaluate(`document.querySelector('.collab-close').click();Collaboration.getLine=originalGetLine;CollaborationView.openEdit(currentLines[2])`);await pause(400);
            await evaluate(`resolveRebase(delayedLine)`);await pause(100);
            await check('late rebase response cannot mutate another dialog',`document.querySelector('#collaborationDialog .collab-line-id').textContent==='#QA.3'&&document.querySelector('.collab-source').textContent==='AI line'`);
            await evaluate(`document.querySelector('.collab-close').click();Collaboration.logout();window.originalLogin=Collaboration.login;Collaboration.login=()=>new Promise(r=>window.resolveLogin=r);openReviewerAccess();document.querySelector('.collab-form input').value='qa-review-key';document.querySelector('.collab-form').requestSubmit()`);
            await evaluate(`document.querySelector('.collab-close').click();CollaborationView.openEdit(currentLines[2])`);await pause(400);
            await evaluate(`resolveLogin();Collaboration.login=originalLogin`);await pause(100);
            await check('late reviewer login cannot close another dialog',`document.querySelector('#collaborationDialog').open&&document.querySelector('#collaborationDialog .collab-line-id').textContent==='#QA.3'`);
            await evaluate(`document.querySelector('.collab-close').click()`);
        }
        }
        const report={scope:publicMode?'Public production readonly GET and browser; no submissions':workerMode?'Actual local Wrangler Worker+D1 with synthetic chapter; external services blocked':'Isolated browser UI fixture only; SQLite/API semantics tested separately',checks,exceptions,externalWrites:requests.filter(x=>!x.startsWith('GET ')&&!x.includes('/api/collab/')),passed:checks.every(x=>x.passed)&&exceptions.length===0};
        await fs.writeFile(path.join(out,'BROWSER_QA.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(!report.passed)throw Error('UI fixture failed');await call('Browser.close').catch(()=>{});
    }finally{if(ws)ws.close();chrome.kill();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
