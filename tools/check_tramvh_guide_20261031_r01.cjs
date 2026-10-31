// Isolated browser regression test: serve static files, block external requests,
// reject non-GETs, never sync translations or invoke the game/backend.
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { spawn } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const base = path.join(root, 'web/story_translator');
const publicMode = process.argv.includes('--public');
const out = path.join(root, 'reports/tramvh_guide_concise_20261031_r01', ...(publicMode ? ['public_runtime'] : []));
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
    await fs.mkdir(out, { recursive: true });
    const requests = [], exceptions = [], checks = [];
    const server = http.createServer(async (req, res) => {
        requests.push(req.method + ' ' + req.url);
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
    const url = publicMode ? 'https://tramvh.doubled1302.workers.dev' : `http://127.0.0.1:${server.address().port}`;
    const profile = path.join(root, 'work/runs/tramvh_guide_concise_20261031_r01/chrome-' + Date.now());
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
                call(request.url.startsWith(url + '/') && request.method === 'GET' ? 'Fetch.continueRequest' : 'Fetch.failRequest', { requestId, ...(request.url.startsWith(url + '/') && request.method === 'GET' ? {} : { errorReason: 'BlockedByClient' }) }).catch(() => {});
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
        const check = async (name, expression) => { const result = await evaluate(expression); checks.push({ name, passed: result === true, result }); if (result !== true) throw Error(name + ': ' + JSON.stringify(result)); };
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
        await evaluate(`closeProfileModal(); document.querySelector('#vietnameseInput').value='Bản nháp {0} đang viết'; window.beforeGuide={index:currentIndex,rows:JSON.stringify(currentLines),profile:localStorage.getItem('stella_user_profile')}; document.querySelector('#translationGuideBtn').focus(); document.querySelector('#translationGuideBtn').click();`);
        await check('native modal and two usage sections', `document.querySelector('#translationGuideDialog').matches(':modal') && document.querySelectorAll('[data-guide-section]').length === 2`);
        await check('initial search focus and body scroll lock', `document.activeElement.id==='guideSearch' && document.body.style.overflow==='hidden'`);
        await check('literal token examples escaped correctly', `['{name}', '$'+'{value}', '<color=#FFCC00>…</color>', String.fromCharCode(92)+'n'].every(t=>document.querySelector('[data-guide-section="tokens"]').textContent.includes(t)) && !document.querySelector('[data-guide-section="tokens"] color')`);
        await check('unaccented search', `(()=>{const input=document.querySelector('#guideSearch');input.value='thuat ngu';input.dispatchEvent(new Event('input'));const visible=document.querySelectorAll('[data-guide-section]:not([hidden])').length;return !document.querySelector('[data-guide-section="workflow"]').hidden && visible>0 && visible<2 && document.querySelector('#guideResultCount').textContent===visible+'/2 mục hướng dẫn'})()`);
        await check('empty search results and safe literal query', `(()=>{const i=document.querySelector('#guideSearch');i.value='<img src=x onerror=alert(1)>';i.dispatchEvent(new Event('input'));return !document.querySelector('#guideEmpty').hidden && !document.querySelector('#guideSearch img')})()`);
        await check('clear search restores sections', `(()=>{document.querySelector('#guideClearSearch').click();return document.querySelector('#guideSearch').value==='' && [...document.querySelectorAll('[data-guide-section]')].every(e=>!e.hidden)})()`);
        await check('topic selection shows tokens', `(()=>{document.querySelector('[data-guide-topic="tokens"]').click();return document.querySelectorAll('[data-guide-section]:not([hidden])').length===1 && !document.querySelector('[data-guide-section="tokens"]').hidden && document.querySelector('[data-guide-topic="tokens"]').getAttribute('aria-pressed')==='true'})()`);
        await check('removed topics and checklist controls are absent', `(()=>{const d=document.querySelector('#translationGuideDialog');return !/Văn phong|Xưng hô|Checklist/i.test(d.textContent) && !d.querySelector('[data-guide-section="style"],[data-guide-section="pronouns"],[data-guide-section="checklist"],input[type="checkbox"]') && document.querySelector('#guideTopicSelect').options.length===3})()`);
        await evaluate(`document.querySelector('#guideSearch').focus()`);
        await key('s', 83, 1); await key('ArrowRight', 39, 1); await key('Enter', 13, 2);
        await check('editor shortcuts blocked while guide is open', `currentIndex===beforeGuide.index && JSON.stringify(currentLines)===beforeGuide.rows && localStorage.getItem('stella_user_profile')===beforeGuide.profile && document.querySelector('#vietnameseInput').value==='Bản nháp {0} đang viết'`);
        await evaluate(`document.querySelector('#guideClose').focus()`); await key('Tab', 9, 8);
        await check('focus stays in dialog', `document.querySelector('#translationGuideDialog').contains(document.activeElement)`);
        await key('Escape', 27); await pause(60);
        await check('escape closes and restores trigger focus', `!document.querySelector('#translationGuideDialog').open && document.activeElement.id==='translationGuideBtn' && document.body.style.overflow===''`);
        await evaluate(`document.querySelector('#translationGuideBtn').click()`);
        await check('reopen resets search and category', `document.querySelector('#guideSearch').value==='' && document.querySelector('[data-guide-topic="all"]').getAttribute('aria-pressed')==='true'`);
        for (const [width, height] of [[1440,1000],[900,900],[390,844],[320,568],[320,480],[844,390],[390,360]]) {
            await call('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 700 });
            for (const theme of ['light', 'dark']) {
                await evaluate(`document.querySelector('#guideClose').click();document.documentElement.dataset.theme=${JSON.stringify(theme)};document.querySelector('#translationGuideBtn').click()`);
                await check(`layout ${width}x${height} ${theme}`, `(()=>{const d=document.querySelector('#translationGuideDialog'),r=d.getBoundingClientRect(),reading=d.querySelector('.guide-reading');return r.left>=0 && r.right<=innerWidth && r.top>=0 && r.bottom<=innerHeight && reading.clientHeight>80 && reading.scrollWidth<=reading.clientWidth+1 && document.documentElement.scrollWidth<=innerWidth && getComputedStyle(d).color!=='rgb(0, 0, 0)'})()`);
                if (width<=700 || height<=500) {
                    await check(`mobile controls ${width}x${height} ${theme}`, `(()=>{const d=document.querySelector('#translationGuideDialog'),select=d.querySelector('#guideTopicSelect'),close=d.querySelector('#guideClose'),search=d.querySelector('#guideToggleSearch');return document.activeElement.id==='translationGuideTitle' && !d.querySelector('#guideSearchTools').classList.contains('is-open') && getComputedStyle(d.querySelector('.guide-nav')).display==='none' && [select,close,search].every(e=>e.getBoundingClientRect().height>=44) && d.getBoundingClientRect().height===innerHeight})()`);
                    await check(`native topic selection ${width}x${height} ${theme}`, `(()=>{const s=document.querySelector('#guideTopicSelect');s.value='tokens';s.dispatchEvent(new Event('change'));return !document.querySelector('[data-guide-section="tokens"]').hidden && document.querySelectorAll('[data-guide-section]:not([hidden])').length===1 && s.selectedOptions[0].textContent==='Token & tag'})()`);
                    await screenshot(`guide-topic-${width}x${height}-${theme}`);
                    await evaluate(`document.querySelector('#guideTopicSelect').value='all';document.querySelector('#guideTopicSelect').dispatchEvent(new Event('change'))`);
                }
                await screenshot(`guide-${width}x${height}-${theme}`);
            }
        }
        await check('mobile search expands on request and filters without accents', `(()=>{document.querySelector('#guideToggleSearch').click();const i=document.querySelector('#guideSearch');i.value='xuong dong';i.dispatchEvent(new Event('input'));return document.activeElement===i && document.querySelector('#guideToggleSearch').getAttribute('aria-expanded')==='true' && !document.querySelector('[data-guide-section="tokens"]').hidden})()`);
        await screenshot('guide-mobile-search-keyboard-height');
        await check('mobile search collapses and clears query', `(()=>{document.querySelector('#guideToggleSearch').click();return document.querySelector('#guideSearch').value==='' && document.querySelector('#guideToggleSearch').getAttribute('aria-expanded')==='false' && [...document.querySelectorAll('[data-guide-section]')].every(e=>!e.hidden)})()`);
        await call('Emulation.setDeviceMetricsOverride', { width:390,height:844,deviceScaleFactor:1,mobile:true });
        await evaluate(`document.querySelector('#guideTopicSelect').value='tokens';document.querySelector('#guideTopicSelect').dispatchEvent(new Event('change'))`); await screenshot('guide-tokens-mobile-dark');
        await evaluate(`document.querySelector('#guideClose').click()`);
        await check('close preserves draft and line state', `document.querySelector('#vietnameseInput').value==='Bản nháp {0} đang viết' && currentIndex===beforeGuide.index && JSON.stringify(currentLines)===beforeGuide.rows`);
        await check('no duplicate IDs', `(()=>{const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);return ids.length===new Set(ids).size})()`);
        await check('guide uses only dedicated matching SVG icons', `(()=>{const images=[...document.querySelectorAll('#translationGuideDialog img,#translationGuideBtn img')];return images.length>0 && images.every(image=>image.getAttribute('src').startsWith('assets/translation-guide-r01/') && image.getAttribute('src').endsWith('.svg') && image.complete && image.naturalWidth>0)})()`);
        await check('list mode entry and draft preservation', `(()=>{switchMode('list');const row=document.querySelector('.table-row-input');row.value='Bản nháp danh sách';row.focus();openTranslationGuide();document.querySelector('#guideClose').click();return viewMode==='list' && row.value==='Bản nháp danh sách' && document.activeElement===row})()`);
        await check('glossary and navigation remain available', `(()=>{switchMode('game');const before=currentIndex;navigateLine(1);const moved=currentIndex===before+1;navigateLine(-1);openGlossaryModal();const opened=document.querySelector('#glossaryModal').classList.contains('open');closeGlossaryModal();return moved && currentIndex===before && opened})()`);
        const report = { scope: publicMode ? 'Live Cloudflare Chrome runtime; non-GET and other-origin requests blocked' : 'Isolated static Chrome runtime; non-GET and external requests blocked', checks, exceptions, nonGetRequests: requests.filter(request=>!request.startsWith('GET ')), realDevice: 'not_tested', passed: checks.every(check=>check.passed) && exceptions.length===0 && requests.every(request=>request.startsWith('GET ')) };
        await fs.writeFile(path.join(out, 'BROWSER_QA.json'), JSON.stringify(report, null, 2));
        console.log(JSON.stringify(report));
        if (!report.passed) throw Error('Guide QA failed');
        await call('Browser.close').catch(()=>{});
    } finally {
        if (ws) ws.close(); chrome.kill();
        server.closeAllConnections(); await new Promise(resolve=>server.close(resolve));
    }
})().catch(error=>{ console.error(error); process.exitCode=1; });
