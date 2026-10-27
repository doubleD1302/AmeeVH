'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const content = window.STELLA_CONTENT || {sections: [], faq: [], paymentMethods: []};
  const initial = {
    busy:false,mutating:false,phase:'',message:'',progress:{percent:0,indeterminate:false,label:''},
    adb:{connected:false,paired:false,host:'127.0.0.1',pairingPort:0,connectionPort:0,status:'Chưa kết nối',notificationPairing:{active:false,stage:'',message:''}},
    game:{installed:false,package:'com.YoStarEN.StellaSora',root:'',gameVersion:'',resourceVersion:'',versionsKnown:false},
    github:{repo:'doubleD1302/AmeeVH',branch:'main',announcementStatus:'Chưa đọc',releaseVersion:'',manifestStatus:'Chưa đọc',translationVersion:'',message:'Chưa đồng bộ GitHub.'},
    notifications:[],payload:{available:false,compatible:false,reason:'Đồng bộ GitHub để xem gói Android tương thích.'},
    config:{repo:'doubleD1302/AmeeVH',branch:'main',host:'127.0.0.1',connectionPort:0},
    update:{available:false,downloaded:false,message:'Chưa kiểm tra bản mới.'},recovery:{pending:false,message:''},receipt:{present:false},support:{methods:[]},app:{versionName:'0.1.1',versionCode:2,variant:'localadb'}
  };
  let state = initial, currentPage = 'overview', selectedMethod = 'bank';
  let previousBusyPhase = '', lastOutcome = ''; 
  let firstConfig = true;
  function text(id, value) { const e = $(id); if (e) e.textContent = value == null ? '' : String(value); }
  function empty(node) { while (node.firstChild) node.removeChild(node.firstChild); }
  function message(title, body, error=false) {
    text('message-title', title || (error ? 'Chưa thể hoàn tất' : 'Thông tin'));
    text('message-body', body || ''); $('message-overlay').hidden = false;
    $('message-ok').focus();
  }
  function request(action, payload={}) {
    const bridge = window.StellaNative;
    if (!bridge || typeof bridge.request !== 'function') {
      if (action !== 'state') message('Mở bằng ứng dụng Android', 'Chức năng này cần launcher APK và kết nối Local ADB trên điện thoại.');
      return;
    }
    try { bridge.request(action, JSON.stringify(payload)); }
    catch (_) { message('Chưa gửi được thao tác', 'Hãy trở lại ứng dụng và thử lại.', true); }
  }
  function showPage(page) {
    if (!$('page-' + page)) return;
    currentPage = page;
    document.querySelectorAll('.page').forEach(e => e.classList.toggle('active', e.id === 'page-' + page));
    document.querySelectorAll('.bottom-nav button').forEach(e => e.classList.toggle('active', e.dataset.page === page));
    window.scrollTo(0, 0);
  }
  function statusLabel(v) {
    return ({online:'đã đọc trực tuyến',empty:'trực tuyến, chưa có mục mới',cached:'đang dùng bản lưu',bundled:'thông tin đi kèm ứng dụng',error:'chưa tải được',available:'đã đọc gói Android',unavailable:'chưa có dữ liệu',missing:'chưa có gói Android'})[v] || String(v || 'chưa đọc');
  }
  function fillInput(id, value, force=false) {
    const e = $(id); if (!e || document.activeElement === e) return;
    if (force || !e.dataset.edited) e.value = value == null || value === 0 ? '' : String(value);
  }
  function primaryAction() {
    if (!state.adb.connected) return {page:'adb',caption:'Kết nối Local ADB',icon:'shield',note:'Kết nối trên điện thoại trước khi cài bản dịch.'};
    if (!state.game.installed || !state.game.root || !state.game.versionsKnown) return {action:'detect',caption:'Tìm và kiểm tra game',icon:'search',note:state.game.installed ? 'Cần đọc đủ phiên bản game trước khi cài.' : 'Tìm Stella Sora và đọc phiên bản trên điện thoại.'};
    if (!state.payload.available) return {action:'sync',caption:'Đồng bộ gói Android',icon:'refresh',note:'Chưa có gói Android tương thích để cài.'};
    if (!state.payload.compatible) return {action:'sync',caption:'Kiểm tra gói Android mới',icon:'refresh',note:'Gói hiện có chưa tương thích. Xem lý do trong chi tiết.'};
    return {action:'install',caption:state.receipt.present ? 'Cập nhật Việt hoá' : 'Cài Việt hoá',icon:'download',note:'Đã có thông tin gói tương thích. Thoát game trước khi cài.'};
  }
  function renderState(data) {
    const nested = ['progress','adb','game','github','config','payload','update','recovery','receipt','support','app'];
    const merged = {...initial, ...data};
    nested.forEach(key => { merged[key] = {...initial[key], ...(data[key] || {})}; });
    merged.adb.notificationPairing = {...initial.adb.notificationPairing, ...((data.adb || {}).notificationPairing || {})};
    merged.notifications = Array.isArray(data.notifications) ? data.notifications : [];
    if (state.busy) previousBusyPhase = state.phase;
    if (!merged.busy && state.busy) {
      const routine = ['sync','checkUpdate','prepareUpdate'];
      lastOutcome = routine.includes(previousBusyPhase) ? '' : (merged.message || '');
    }
    if (merged.busy) lastOutcome = '';
    state = merged;
    document.querySelectorAll('.needs-idle').forEach(e => { e.disabled = !!state.busy; });
    const adb = state.adb, game = state.game, p = state.payload, gh = state.github;
    text('adb-status', adb.connected ? 'Đã kết nối' : 'Chưa kết nối');
    $('adb-status').prepend(Object.assign(document.createElement('i'), {}));
    $('adb-status').classList.toggle('connected', !!adb.connected);
    text('adb-page-status', adb.connected ? 'Đã kết nối' : 'Chưa kết nối');
    $('adb-page-status').classList.toggle('connected', !!adb.connected);
    text('adb-summary', adb.status || (adb.connected ? 'Thiết bị đã phản hồi. Bạn có thể tìm game và kiểm tra gói bản dịch.' : 'Ghép đôi trực tiếp trên điện thoại, không cần máy tính.'));
    text('connection-details', adb.connected ? ('Đã xác nhận kết nối · ' + (adb.host || '') + ':' + (adb.connectionPort || '')) : (adb.status || 'Chưa xác nhận kết nối với thiết bị.'));
    text('pairing-note', adb.notificationPairing.message || 'Cần Android 11 trở lên. Cho phép thông báo để nhập mã mà không cần chuyển ứng dụng.');
    $('cancel-pairing').hidden = !adb.notificationPairing.active;
    $('cancel-pairing').disabled = !!state.mutating;
    text('game-name', game.installed ? 'Stella Sora · đã tìm thấy' : 'Stella Sora');
    text('game-summary', game.versionsKnown ? ('Game ' + game.gameVersion + ' · tài nguyên ' + game.resourceVersion) : (game.installed ? 'Chưa đọc đủ phiên bản game' : 'Chưa tìm thấy game trên điện thoại'));
    text('game-root', game.root || 'Chưa xác định đường dẫn');
    const main = primaryAction();
    text('install-caption', main.caption);
    $('main-action-icon').src = 'icons/' + main.icon + '.svg';
    text('payload-note', main.note);
    let payloadText = p.reason || 'Chưa có thông tin gói Android tương thích.';
    if (p.available && p.compatible) payloadText = 'Bản dịch ' + (p.version || gh.translationVersion || '') + (p.fileCount ? ' · ' + p.fileCount + ' tệp' : '') + '. Đã có thông tin gói Android.';
    text('payload-details', payloadText);
    text('operation-details', state.message || 'Chưa có thao tác');
    text('native-status', state.message || 'Chưa có thao tác');
    $('operation').hidden = !state.busy;
    text('operation-label', state.progress.label || state.message || 'Đang xử lý…');
    $('operation-outcome').hidden = state.busy || !lastOutcome;
    text('operation-outcome', lastOutcome.length > 180 ? lastOutcome.slice(0, 177) + '…' : lastOutcome);
    const percent = Number(state.progress.percent);
    $('progress-fill').style.width = Math.max(0, Math.min(100, Number.isFinite(percent) ? percent : 0)) + '%';
    $('progress-fill').classList.toggle('indeterminate', !!state.progress.indeterminate);
    $('recover-alert').hidden = !state.recovery.pending;
    if (state.recovery.message) $('recover-alert').title = state.recovery.message;
    const lines = [gh.message || 'Chưa đồng bộ GitHub.'];
    lines.push('Thông báo: ' + statusLabel(gh.announcementStatus));
    if (gh.releaseVersion) lines.push('Bản phát hành: ' + gh.releaseVersion);
    lines.push('Gói Android: ' + statusLabel(gh.manifestStatus));
    if (gh.translationVersion) lines.push('Bản dịch: ' + gh.translationVersion);
    if (game.versionsKnown) lines.push('Game: ' + game.gameVersion + ' · tài nguyên ' + game.resourceVersion);
    text('github-state', lines.join('\n'));
    const ghRead = ['online','empty','cached','bundled'].includes(gh.announcementStatus);
    text('github-summary', p.available ? (p.compatible ? 'Đã đọc gói Android tương thích.' : 'Đã đọc gói Android; cần kiểm tra tương thích.') : (ghRead || gh.message !== initial.github.message ? 'Chưa có gói Android tương thích. Xem trạng thái chi tiết bên dưới.' : 'Chưa đồng bộ GitHub.'));
    text('app-version', 'Launcher Android ' + (state.app.versionName || '0.1.1') + ' · Local ADB');
    text('update-state', state.update.message || 'Chưa kiểm tra bản mới.');
    $('install-update').hidden = !state.update.available && !state.update.downloaded;
    $('install-update').querySelector('span').textContent = state.update.downloaded ? 'Mở trình cài đặt Android' : 'Tải bản cập nhật';
    fillInput('repo', state.config.repo || gh.repo, firstConfig);
    fillInput('branch', state.config.branch || gh.branch, firstConfig);
    fillInput('adb-host', state.config.host || adb.host, firstConfig);
    fillInput('connect-port', state.config.connectionPort || adb.connectionPort, firstConfig);
    if (adb.pairingPort) fillInput('pair-port', adb.pairingPort);
    firstConfig = false;
    renderNotices();
    renderPayment();
  }
  function notices() { return Array.isArray(state.notifications) ? state.notifications : []; }
  function noticeRow(n) {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'notice-row';
    const span = document.createElement('span'); span.textContent = n.title || 'Thông báo';
    const img = document.createElement('img'); img.src = 'icons/chevron_right.svg'; img.alt = '';
    b.append(span, img); b.addEventListener('click', () => openNotice(n)); return b;
  }
  function renderNotices() {
    const preview = $('notification-preview'); empty(preview);
    const items = notices();
    if (!items.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'Chưa có thông báo.'; preview.append(p); }
    else items.slice(0, 2).forEach(n => preview.append(noticeRow(n)));
    const list = $('notice-all-list'); empty(list);
    const query = $('notice-search').value.trim().toLocaleLowerCase('vi');
    const filtered = items.filter(n => !query || ((n.title || '') + ' ' + (n.content || '')).toLocaleLowerCase('vi').includes(query));
    if (!filtered.length) { const p = document.createElement('p'); p.className = 'empty-note'; p.textContent = 'Không có thông báo phù hợp.'; list.append(p); }
    else filtered.forEach(n => list.append(noticeRow(n)));
  }
  function openNotice(n) {
    $('notices-overlay').hidden = false; $('notice-all-list').hidden = true; $('notice-search').hidden = true; $('notice-detail').hidden = false;
    text('notice-title', n.title || 'Thông báo'); text('notice-date', n.date || ''); text('notice-body', n.content || '');
  }
  function openNoticeList() { $('notices-overlay').hidden = false; $('notice-detail').hidden = true; $('notice-all-list').hidden = false; $('notice-search').hidden = false; renderNotices(); }
  function paymentMethods() { const dynamic = (state.support || {}).methods; return Array.isArray(dynamic) && dynamic.length ? dynamic : content.paymentMethods; }
  function renderPayment() {
    const methods = paymentMethods() || [], row = $('payment-methods'); empty(row);
    if (!methods.length) { text('payment-account','Chưa có thông tin nhận ủng hộ.'); $('payment-qr').hidden = true; $('copy-account').disabled = true; return; }
    const chosen = methods.find(m => m.id === selectedMethod) || methods[0]; selectedMethod = chosen.id;
    methods.forEach(method => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'button secondary' + (method.id === selectedMethod ? ' selected' : ''); b.setAttribute('aria-pressed', String(method.id === selectedMethod));
      const img = document.createElement('img'); img.src = 'icons/' + (method.id === 'bank' ? 'bank' : 'wallet') + '.svg'; img.alt = '';
      const span = document.createElement('span'); span.textContent = method.label; b.append(img,span); b.addEventListener('click', () => { selectedMethod = method.id; renderPayment(); }); row.append(b);
    });
    // Names are never accepted as URLs or HTML; bundled images only.
    const file = String(chosen.qr_file || '');
    $('payment-qr').hidden = !/^[A-Za-z0-9_-]+\.png$/.test(file);
    if (!$('payment-qr').hidden) $('payment-qr').src = 'support/' + file;
    text('payment-provider', chosen.provider || ''); text('payment-recipient', chosen.recipient_name || '');
    text('payment-account', chosen.account_number || chosen.account_masked || 'Quét mã để xem người nhận');
    $('copy-account').disabled = !chosen.account_number;
    text('copy-account-caption', chosen.account_number ? 'Sao chép số tài khoản' : 'Số ví đang được ẩn');
  }
  function renderGuide() {
    const target = $('guide-content'); empty(target);
    content.sections.forEach(section => {
      const panel = document.createElement('details'); panel.className = 'glass disclosure';
      const heading = document.createElement('summary'); heading.textContent = section.title;
      const bodyWrap = document.createElement('div'); bodyWrap.className = 'disclosure-body';
      const sub = document.createElement('p'); sub.className = 'guide-copy'; sub.textContent = section.subtitle;
      const ol = document.createElement('ol'); ol.className = 'steps';
      section.steps.forEach((step,index) => {
        const li = document.createElement('li'), num = document.createElement('span'), wrap = document.createElement('div'), title = document.createElement('strong'), body = document.createElement('p');
        num.textContent = String(index+1); title.textContent = step.title; body.textContent = step.detail; wrap.append(title,body); li.append(num,wrap); ol.append(li);
      });
      bodyWrap.append(sub,ol); panel.append(heading,bodyWrap); target.append(panel);
    });
  }
  function renderFaq() {
    const list = $('faq-list');
    content.faq.forEach(f => {
      const item = document.createElement('div'); item.className = 'faq-item';
      const b = document.createElement('button'); b.type = 'button'; b.className = 'faq-question'; b.setAttribute('aria-expanded','false');
      const label = document.createElement('span'); label.textContent = f.question; const icon = document.createElement('img'); icon.src = 'icons/chevron_right.svg'; icon.alt = ''; b.append(label,icon);
      const answer = document.createElement('div'); answer.className = 'faq-answer'; answer.hidden = true; answer.textContent = f.answer;
      b.addEventListener('click', () => { answer.hidden = !answer.hidden; b.setAttribute('aria-expanded',String(!answer.hidden)); }); item.append(b,answer); list.append(item);
    });
  }
  function port(id) {
    const v = $(id).value.trim(); if (!/^\d{1,5}$/.test(v) || Number(v)<1 || Number(v)>65535) { message('Cổng chưa hợp lệ','Nhập số cổng từ 1 đến 65535 đang hiển thị trong Gỡ lỗi không dây.'); return null; } return Number(v);
  }
  document.querySelectorAll('[data-page]').forEach(b => b.addEventListener('click', () => showPage(b.dataset.page)));
  document.querySelectorAll('[data-action]').forEach(b => b.addEventListener('click', () => request(b.dataset.action)));
  ['adb-host','pair-port','connect-port','repo','branch'].forEach(id => $(id).addEventListener('input', () => { $(id).dataset.edited = '1'; }));
  $('main-action').addEventListener('click', () => {
    if (state.busy) return;
    const main = primaryAction();
    if (main.page) showPage(main.page); else request(main.action);
  });
  $('manual-pair').addEventListener('click', () => {
    const pairingPort = port('pair-port'), code = $('pair-code').value.trim();
    if (pairingPort == null) return;
    if (!/^\d{6}$/.test(code)) { message('Cần mã ghép đôi 6 số','Giữ cửa sổ mã ghép đôi của Android đang mở, rồi nhập đủ 6 số.'); return; }
    request('pair',{host:$('adb-host').value.trim(),pairingPort,code}); $('pair-code').value = '';
  });
  $('manual-connect').addEventListener('click', () => { const connectionPort = port('connect-port'); if (connectionPort != null) request('connect',{host:$('adb-host').value.trim(),connectionPort}); });
  $('save-settings').addEventListener('click', () => { const raw=$('connect-port').value.trim(); const connectionPort=raw?port('connect-port'):0; if(connectionPort==null)return; request('saveSettings',{repo:$('repo').value.trim(),branch:$('branch').value.trim(),host:$('adb-host').value.trim(),connectionPort}); });
  $('copy-account').addEventListener('click', () => request('copyAccount',{method:selectedMethod}));
  $('all-notifications').addEventListener('click',openNoticeList); $('notice-search').addEventListener('input',renderNotices); $('notice-back').addEventListener('click',openNoticeList);
  $('notices-close').addEventListener('click', () => { $('notices-overlay').hidden=true; });
  ['message-close','message-ok'].forEach(id => $(id).addEventListener('click', () => { $('message-overlay').hidden=true; }));
  window.Stella = {
    onEvent(event) {
      try { if (typeof event === 'string') event=JSON.parse(event); if(!event || typeof event!=='object')return;
        if(event.type==='state')renderState(event.data||{});
        else if(event.type==='message')message((event.data||{}).title,(event.data||{}).message,!!(event.data||{}).error);
      } catch (_) { message('Chưa đọc được trạng thái','Hãy mở lại trang Tổng quan hoặc kết nối lại Local ADB.',true); }
    },
    goBack() {
      if(!$('message-overlay').hidden){$('message-overlay').hidden=true;return true;}
      if(!$('notices-overlay').hidden){$('notices-overlay').hidden=true;return true;}
      if(currentPage!=='overview'){showPage('overview');return true;}return false;
    }
  };
  renderGuide(); renderFaq(); renderState(initial); request('state');
})();
