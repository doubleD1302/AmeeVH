'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const content = window.STELLA_CONTENT || {sections: [], faq: [], paymentMethods: []};
  const ICON = name => 'game_icons/' + name + '.webp';

  const initial = {
    busy:false,mutating:false,devOptionsEnabled:true,phase:'',message:'',progress:{percent:0,indeterminate:false,label:''},
    device:{manufacturer:'',brand:'',model:'',release:'',sdk:0,oemFamily:'generic'},
    lastError:{},
    adb:{connected:false,paired:false,hasIdentity:false,host:'127.0.0.1',pairingPort:0,connectionPort:0,status:'Chưa nối',notificationPairing:{active:false,stage:'',message:''}},
    game:{installed:false,package:'com.YoStarEN.StellaSora',root:'',gameVersion:'',resourceVersion:'',versionsKnown:false,noData:false,wrongEdition:''},
    github:{repo:'doubleD1302/AmeeVH',branch:'main',announcementStatus:'Chưa đọc',releaseVersion:'',manifestStatus:'Chưa đọc',translationVersion:'',manifestSha256:'',message:'Chưa đồng bộ.'},
    notifications:[],payload:{available:false,compatible:false,updateAvailable:false,mismatchKind:'',supportedGameVersion:'',supportedResourceVersion:'',reason:'Đồng bộ GitHub để xem gói Android.'},
    config:{repo:'doubleD1302/AmeeVH',branch:'main',host:'127.0.0.1',connectionPort:0,theme:'system'},
    update:{available:false,downloaded:false,message:'Chưa kiểm tra bản mới.'},recovery:{pending:false,message:''},receipt:{present:false,manifestSha256:''},
    officialUpdate:{checked:false,updateAvailable:false,vhModified:false,needsRestore:false,localGameVersion:'',localResourceVersion:'',latestGameVersion:'',latestResourceVersion:'',checkedAt:0},
    guard:{accessibilityEnabled:false,overlayEnabled:false,canPinShortcut:true,pendingRestore:false},
    support:{methods:[]},
    app:{versionName:'2.1.4',versionCode:27,variant:'localadb',theme:'system',resolvedTheme:'light'}
  };

  let state = initial, currentPage = 'overview';
  let previousBusyPhase = '', lastOutcome = '';
  let firstConfig = true;
  let copyResetTimer = 0, safetyCopyTimer = 0, toastTimer = 0, currentReportId = '', activeProbeInModal = false;
  let currentSafetyTopic = 'a11y', lastChibiIdx = -1;

  const CHIBI_CAST = [
    {id:'103', name:'Amber',   quote:'"Cứ kiểm tra kỹ mọi thứ trước khi bật nhé, tớ đảm bảo sạch sẽ 100%!"'},
    {id:'107', name:'Tilia',   quote:'"Với danh dự Hiệp sĩ Chính Nghĩa, mọi quyền ở đây đều minh bạch rõ ràng!"'},
    {id:'110', name:'Firenze', quote:'"Đừng tin lời suông — cậu cứ dán mã nguồn vào AI kiểm chứng tận mắt nhé."'},
    {id:'111', name:'Iris',    quote:'"Đừng lo lắng nhé, mình đã chuẩn bị sẵn hướng dẫn tự kiểm tra bằng AI rồi nè!"'},
    {id:'112', name:'Noya',    quote:'"Mọi dòng code đều mở công khai đó, cậu bấm 1 chạm là kiểm tra được ngay ♪"'},
    {id:'114', name:'Chaton',  quote:'"Chỉ canh đúng cửa Stella Sora thôi, không tò mò mấy ứng dụng khác đâu nha~"'},
    {id:'117', name:'Jinglin', quote:'"An toàn dữ liệu là trên hết! Cậu xem cam kết bên dưới là yên tâm liền."'},
    {id:'118', name:'Coronis', quote:'"Quyền nào cũng chỉ xin đúng phần tối thiểu nhất, hoàn toàn có thể tự kiểm tra."'},
    {id:'119', name:'Nanoha',  quote:'"Cậu có thể tự nhờ ChatGPT, Gemini hay Claude đọc code xác nhận hộ đấy!"'},
    {id:'120', name:'Canace',  quote:'"Dựa theo mã nguồn công khai trên GitHub, mọi thứ đều có thể kiểm chứng độc lập."'},
    {id:'123', name:'Ann',     quote:'"Để tụi mình giải thích thật nhẹ nhàng để cậu yên tâm cài Việt hoá nha!"'},
    {id:'134', name:'Fuyuka',  quote:'"Mở code lên soi thoải mái luôn — minh bạch từ đầu đến cuối cho cậu yên tâm!"'}
  ];

  const SAFETY_TOPICS = {
    a11y: {
      title: 'Vì sao cần quyền Trợ năng?',
      sourcePath: 'android/app/src/main/java/com/stellasora/viethoa/localadb/GameLaunchGuardService.java',
      why: [
        'Chỉ nhận biết đúng lúc bạn bấm mở icon Stella Sora khi máy chủ Yostar có bản cập nhật mới.',
        'Lập tức hiện hộp thoại nhắc bạn khôi phục dữ liệu gốc trước, tránh lỗi hỏng bản vá game.',
        'Android 13+ mặc định khoá quyền này cho app cài ngoài Play Store nên mới hiện mục "Cài đặt bị hạn chế".'
      ],
      pledges: [
        'Đã khoá cứng packageNames = com.YoStarEN.StellaSora và canRetrieveWindowContent = false.',
        'Tuyệt đối KHÔNG đọc nội dung màn hình, mật khẩu, tin nhắn, bàn phím hay ứng dụng ngân hàng.',
        '100% mã nguồn mở trên GitHub — miễn phí, không quảng cáo, không gửi dữ liệu cá nhân ra ngoài.'
      ],
      promptFiles: [
        'android/app/src/main/res/xml/game_guard_accessibility.xml',
        'android/app/src/main/java/com/stellasora/viethoa/localadb/GameLaunchGuardService.java',
        'android/app/src/main/AndroidManifest.xml'
      ],
      promptFocus: 'quyền Trợ năng (AccessibilityService) của tính năng Bảo vệ cập nhật game'
    },
    overlay: {
      title: 'Vì sao cần Hiển thị nổi (OEM)?',
      sourcePath: 'android/app/src/main/java/com/stellasora/viethoa/localadb/GameLaunchGuardService.java',
      why: [
        'Một số máy Xiaomi (HyperOS/MIUI), OPPO, Vivo, Samsung chặn lớp phủ Trợ năng mặc định khi mở game.',
        'Quyền Hiển thị trên ứng dụng khác (SYSTEM_ALERT_WINDOW) làm lớp dự phòng để popup cảnh báo hiện lên ngay trên màn hình game.',
        'Bạn chỉ cần bật quyền này nếu thấy mở game lúc có bản vá mới mà popup chưa tự hiện.'
      ],
      pledges: [
        'Chỉ vẽ duy nhất hộp thoại cảnh báo cập nhật Stella Sora khi bản dịch cần khôi phục gốc.',
        'KHÔNG chạy nền hiển thị quảng cáo, không che nút hệ thống hay can thiệp ứng dụng khác.',
        'Có thể tắt lại bất kỳ lúc nào trong Cài đặt ứng dụng Android.'
      ],
      promptFiles: [
        'android/app/src/main/java/com/stellasora/viethoa/localadb/GameLaunchGuardService.java',
        'android/app/src/main/java/com/stellasora/viethoa/localadb/GameAlertViewBuilder.java',
        'android/app/src/main/AndroidManifest.xml'
      ],
      promptFocus: 'quyền Hiển thị trên ứng dụng khác (SYSTEM_ALERT_WINDOW)'
    },
    adb: {
      title: 'Vì sao cần Local ADB?',
      sourcePath: 'android/app/src/main/java/com/stellasora/viethoa/localadb/GamePatcher.java',
      why: [
        'Từ Android 11+, hệ thống chặn app thông thường đọc/ghi thư mục Android/data/com.YoStarEN.StellaSora/files.',
        'Local ADB dùng chính tính năng Gỡ lỗi không dây có sẵn của Android (kết nối nội bộ 127.0.0.1 ngay trên máy bạn, không cần PC hay Root).',
        'Chỉ sao lưu bản gốc, chép tệp ngôn ngữ/ảnh Việt hoá đã kiểm tra SHA256 và khôi phục lại khi game cập nhật.'
      ],
      pledges: [
        'Đường dẫn bị khoá chặt trong đúng thư mục dữ liệu của com.YoStarEN.StellaSora (chặn vượt thư mục & symlink).',
        'Khoá ghép đôi ADB sinh cục bộ trong bộ nhớ riêng của máy, không bao giờ gửi ra internet.',
        'Không đụng tới tệp hệ thống, ảnh cá nhân, danh bạ hay tài khoản game của bạn.'
      ],
      promptFiles: [
        'android/app/src/main/java/com/stellasora/viethoa/localadb/GamePatcher.java',
        'android/app/src/main/java/com/stellasora/viethoa/localadb/AdbBrokerService.java',
        'android/app/src/main/AndroidManifest.xml'
      ],
      promptFocus: 'tính năng Local ADB (Gỡ lỗi không dây nội bộ) và quy trình ghi/khôi phục tệp game'
    }
  };

  const QUICK_FIX_MAP = {
    open_device_info:     {label:'Thông tin điện thoại', icon:'gear', action:'openDeviceInfo', close:false},
    open_dev_settings:    {label:'Nhà phát triển', icon:'sparkle', action:'openDevSettings', close:false},
    open_wireless:        {label:'Gỡ lỗi không dây', icon:'wifi', action:'openWirelessSettings', close:false},
    open_wifi:            {label:'Cài đặt Wi-Fi', icon:'wifi', action:'openWifiSettings', close:false},
    open_app_notif:       {label:'Quyền thông báo', icon:'bell', action:'openAppNotifications', close:false},
    open_app_battery:     {label:'Bỏ hạn chế pin', icon:'shield', action:'openBatterySettings', close:false},
    open_unknown_sources: {label:'Cấp quyền cài APK', icon:'download', action:'openUnknownSources', close:false},
    auto_connect:         {label:'Kết nối nhanh ADB', icon:'wifi', action:'autoConnect', close:true},
    start_pair:           {label:'Ghép đôi thông báo', icon:'push', action:'startPairingNotification', close:true},
    probe_network:        {label:'Đo mạng & DNS', icon:'globe', action:'probeNetwork', close:false},
    sync_github:          {label:'Đồng bộ GitHub', icon:'refresh', action:'sync', close:true},
    detect_game:          {label:'Quét tìm game', icon:'search', action:'detect', close:true},
    launch_game:          {label:'Mở Stella Sora', icon:'play', action:'launchGame', close:true},
    open_play_store:      {label:'Mở Google Play', icon:'download', action:'openPlayStore', close:false},
    recover:              {label:'Phục hồi ngay', icon:'restore', action:'recover', close:true},
    install_patch:        {label:'Cài Việt hoá', icon:'download', action:'install', close:true},
    reset_channel:        {label:'Kênh mặc định', icon:'refresh', action:'resetChannel', close:true}
  };

  const OEM_TIPS = {
    xiaomi: {
      title: 'Lưu ý Xiaomi / Redmi / POCO (HyperOS)',
      body: '• Bật thêm "Gỡ lỗi USB (Cài đặt bảo mật)" trong Tuỳ chọn nhà phát triển.\n• Bật Thông báo nổi, Hiển thị nổi và đặt Pin "Không hạn chế".'
    },
    oppo: {
      title: 'Lưu ý OPPO / Realme / OnePlus',
      body: '• Cuộn xuống cuối Tuỳ chọn nhà phát triển và BẬT "Tắt giám sát quyền" (Disable permission monitoring).'
    },
    samsung: {
      title: 'Lưu ý Samsung Galaxy (One UI)',
      body: '• Số hiệu bản tạo nằm trong Thông tin phần mềm.\n• Có thể Chia đôi màn hình để nhập mã 6 số nhanh.'
    },
    vivo: {
      title: 'Lưu ý Vivo / iQOO',
      body: '• Đặt Pin của launcher thành "Không hạn chế" để giữ kết nối Local ADB ổn định.'
    },
    huawei: {
      title: 'Lưu ý Huawei / Honor',
      body: '• Chuyển quản lý pin sang thủ công để không bị ngắt Local ADB giữa chừng.'
    },
    transsion: {
      title: 'Lưu ý Tecno / Infinix / Itel',
      body: '• Tắt hạn chế pin nền cho launcher trong cài đặt pin.'
    }
  };

  function haptic() {
    try { if (window.StellaNative && typeof window.StellaNative.haptic === 'function') window.StellaNative.haptic(); }
    catch (_) {}
  }
  function text(id, value) { const e = $(id); if (e) e.textContent = value == null ? '' : String(value); }
  function empty(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }

  let marqueeRaf = 0;
  function refreshMarquees() {
    if (marqueeRaf) cancelAnimationFrame(marqueeRaf);
    marqueeRaf = requestAnimationFrame(() => {
      marqueeRaf = 0;
      const nodes = document.querySelectorAll(
        '#hero-status-text, .row-title, .safety-banner-btn > span, .notice-row > span, #safety-title, #message-title, .safety-tag, .guard-head-text strong'
      );
      nodes.forEach(el => {
        if (!el || el.clientWidth <= 0) return;
        let inner = el.querySelector(':scope > .mq-inner');
        const currentText = inner ? inner.textContent : el.textContent;
        if (!inner) {
          el.classList.add('mq-host');
          inner = document.createElement('span');
          inner.className = 'mq-inner';
          inner.textContent = currentText;
          el.textContent = '';
          el.appendChild(inner);
        }
        el.classList.remove('mq-active');
        const overflow = Math.ceil(inner.scrollWidth - el.clientWidth);
        if (overflow > 3) {
          const dist = -(overflow + 8);
          const dur = Math.max(5.5, Math.min(18, (overflow / 26) * 2 + 3.4));
          el.style.setProperty('--mq-shift', dist + 'px');
          el.style.setProperty('--mq-dur', dur.toFixed(2) + 's');
          el.classList.add('mq-active');
        } else {
          el.style.removeProperty('--mq-shift');
          el.style.removeProperty('--mq-dur');
        }
      });
    });
  }
  window.addEventListener('resize', refreshMarquees);

  function showToast(msg) {
    const el = $('toast'); if (!el || !msg) return;
    el.textContent = String(msg);
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, 2800);
  }

  function setBadge(el, label, variant) {
    if (!el) return;
    el.className = 'chip-badge ' + (variant || 'neutral');
    el.textContent = label;
    el.prepend(document.createElement('i'));
  }

  function applyTheme(pref, resolved) {
    const mode = (resolved === 'dark' || resolved === 'light') ? resolved
      : (pref === 'dark' ? 'dark' : pref === 'light' ? 'light'
      : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
    document.documentElement.dataset.theme = mode;
    const icon = $('theme-toggle-icon');
    if (icon) icon.src = ICON(mode === 'dark' ? 'sun' : 'moon');
    document.querySelectorAll('[data-theme-choice]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.themeChoice === (pref || 'system'));
    });
    text('theme-status-note', pref === 'dark' ? 'Chế độ tối (Starry Twilight).' : pref === 'light' ? 'Chế độ sáng (Stella Porcelain).' : ('Theo hệ thống Android (' + (mode === 'dark' ? 'Tối' : 'Sáng') + ').'));
  }

  function setCopyLabel(label, copied=false) {
    const btn = $('message-copy'); if (!btn) return;
    const s = btn.querySelector('span'); if (s) s.textContent = label;
    btn.classList.toggle('copied', !!copied);
  }

  function renderDiagGrid(rows) {
    const wrap = $('message-diag-wrap'), grid = $('message-diag-grid');
    if (!wrap || !grid) return;
    empty(grid);
    if (!Array.isArray(rows) || !rows.length) { wrap.hidden = true; return; }
    rows.forEach((row, idx) => {
      const cell = document.createElement('div');
      cell.className = 'diag-cell' + (row.tone === 'mono' || (idx === rows.length - 1 && rows.length % 2 === 1) ? ' span-2' : '');
      const lbl = document.createElement('span'); lbl.className = 'diag-label'; lbl.textContent = row.label || '';
      const val = document.createElement('span'); val.className = 'diag-value tone-' + (row.tone || 'neutral'); val.textContent = row.value || '';
      cell.append(lbl, val);
      grid.appendChild(cell);
    });
    wrap.hidden = false;
  }

  function renderProbePanel(panelId, verdictId, linesId, probe) {
    const panel = $(panelId); if (!panel) return;
    if (!probe || !probe.verdict) { panel.hidden = true; return; }
    const v = String(probe.verdict);
    const tone = v === 'ok' ? 'ok' : (v === 'dns_blocked' || v === 'dns_broken' ? 'warn' : 'danger');
    panel.className = 'probe-panel tone-' + tone;
    text(verdictId, probe.verdictText || ('Đo mạng: ' + v));
    text(linesId, Array.isArray(probe.lines) ? probe.lines.join('\n') : '');
    panel.hidden = false;
  }

  function renderQuickActions(actions) {
    const wrap = $('message-quickfix-wrap'), grid = $('message-quickfix-grid');
    if (!wrap || !grid) return;
    empty(grid);
    const list = Array.isArray(actions) ? actions.filter(a => QUICK_FIX_MAP[a]) : [];
    if (!list.length) { wrap.hidden = true; return; }
    list.forEach((id, idx) => {
      const spec = QUICK_FIX_MAP[id];
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'qf-btn' + (list.length === 1 || (idx === list.length - 1 && list.length % 2 === 1) ? ' span-2' : '');
      btn.dataset.qfId = id;
      const img = document.createElement('img'); img.src = ICON(spec.icon); img.alt = ''; img.width = 16; img.height = 16; img.decoding = 'async';
      const span = document.createElement('span'); span.textContent = spec.label;
      btn.append(img, span);
      btn.addEventListener('click', () => {
        haptic();
        if (id === 'probe_network') { startModalProbe(btn); return; }
        if (spec.close) $('message-overlay').hidden = true;
        request(spec.action);
      });
      grid.appendChild(btn);
    });
    wrap.hidden = false;
  }

  function startModalProbe(btn) {
    activeProbeInModal = true;
    const panel = $('message-probe-panel');
    if (panel) { panel.className = 'probe-panel'; text('message-probe-verdict', 'Đang đo DNS & GitHub…'); text('message-probe-lines', ''); panel.hidden = false; }
    if (btn) { btn.disabled = true; const s = btn.querySelector('span'); if (s) s.textContent = 'Đang đo…'; }
    request('probeNetwork', {id: currentReportId});
  }

  function message(title, body, error=false, meta={}) {
    meta = meta || {};
    const explain = meta.explain ? String(meta.explain) : '';
    const steps = Array.isArray(meta.steps) ? meta.steps : [];
    const card = $('message-dialog-card');
    if (card) card.dataset.level = meta.level || (error ? 'error' : 'info');

    currentReportId = meta && meta.reportId ? String(meta.reportId) : '';
    const hasReport = !!currentReportId;
    if ($('message-badges')) $('message-badges').hidden = !hasReport;
    text('message-code-pill', meta.code || 'E-UNKNOWN');
    text('message-report-id', hasReport ? '#' + currentReportId : '');

    text('message-title', meta.errorTitle || title || (error ? 'Chưa hoàn tất' : 'Thông tin'));
    text('message-body', explain || body || '');

    const stepsWrap = $('message-steps-wrap'), list = $('message-steps');
    empty(list);
    steps.forEach(step => { const li = document.createElement('li'); li.textContent = String(step); list.appendChild(li); });
    if (stepsWrap) stepsWrap.hidden = !steps.length;

    renderDiagGrid(meta.contextRows);
    renderProbePanel('message-probe-panel', 'message-probe-verdict', 'message-probe-lines', meta.probe);
    renderQuickActions(meta.quickActions);

    const technical = explain && body && String(body).trim() !== explain.trim() ? String(body) : '';
    const preview = meta.reportPreview ? String(meta.reportPreview) : '';
    text('message-tech-body', technical);
    $('message-tech-body').hidden = !technical;
    $('message-raw-label').hidden = !technical;
    text('message-report-preview', preview);
    $('message-report-preview').hidden = !preview;
    $('message-preview-label').hidden = !preview;
    $('message-tech').hidden = !technical && !preview;
    $('message-tech').open = false;

    $('message-copy').hidden = !hasReport;
    clearTimeout(copyResetTimer);
    setCopyLabel('Sao chép báo lỗi', false);
    $('message-overlay').hidden = false;
    const scroll = $('message-scroll'); if (scroll) scroll.scrollTop = 0;
    refreshMarquees();
  }

  function request(action, payload={}) {
    const bridge = window.StellaNative;
    if (!bridge || typeof bridge.request !== 'function') {
      if (action !== 'state') message('Mở trên Android', 'Chức năng này cần ứng dụng APK trên điện thoại.');
      return;
    }
    try { bridge.request(action, JSON.stringify(payload)); }
    catch (_) { message('Chưa gửi được thao tác', 'Hãy thử lại.', true); }
  }

  function showPage(page) {
    if (page === 'support') {
      haptic();
      message('Đang bảo trì', 'Bản Việt hoá Stella Sora luôn luôn miễn phí!');
      return;
    }
    if (!$('page-' + page)) return;
    if (page !== currentPage) haptic();
    currentPage = page;
    document.querySelectorAll('.page').forEach(e => e.classList.toggle('active', e.id === 'page-' + page));
    document.querySelectorAll('.bottom-nav button').forEach(e => e.classList.toggle('active', e.dataset.page === page));
    window.scrollTo({top: 0, behavior: 'instant'});
    refreshMarquees();
  }

  function statusLabel(v) {
    return ({online:'trực tuyến',empty:'không có mục mới',cached:'bản lưu',bundled:'đi kèm app',error:'lỗi tải',available:'sẵn sàng',unavailable:'chưa có',missing:'chưa có',none:'chưa có'})[v] || String(v || 'chưa đọc');
  }

  function fillInput(id, value, force=false) {
    const e = $(id); if (!e || document.activeElement === e) return;
    if (force || !e.dataset.edited) e.value = value == null || value === 0 ? '' : String(value);
  }

  function renderOemTip(device) {
    const card = $('oem-adb-tip'); if (!card) return;
    const tip = OEM_TIPS[(device && device.oemFamily) || 'generic'];
    if (!tip) { card.hidden = true; return; }
    text('oem-tip-title', tip.title);
    text('oem-tip-body', tip.body);
    card.hidden = false;
  }

  function primaryAction() {
    if (state.devOptionsEnabled === false) return {page:'adb',caption:'Bật Tuỳ chọn nhà phát triển',icon:'repair',note:'Cần bật 1 lần để dùng Gỡ lỗi không dây.'};
    if (!state.adb.connected) {
      if (state.adb.hasIdentity) return {action:'autoConnect',caption:'Kết nối nhanh Local ADB',icon:'wifi',note:'Bật Wi-Fi + Gỡ lỗi không dây rồi chạm.'};
      return {page:'adb',caption:'Kết nối Local ADB',icon:'shield',note:'Ghép đôi 1 lần trực tiếp trên điện thoại.'};
    }
    if (!state.game.installed || !state.game.root || !state.game.versionsKnown) {
      if (state.game.wrongEdition) return {action:'detect',caption:'Tìm lại bản Global EN',icon:'search',note:'Đang thấy bản ' + state.game.wrongEdition + '.'};
      if (state.game.noData) return {action:'launchGame',caption:'Mở game tải dữ liệu',icon:'play',note:'Mở Stella Sora 1 lần rồi quay lại.'};
      return {action:'detect',caption:'Tìm và kiểm tra game',icon:'search',note:'Quét tìm Stella Sora trên điện thoại.'};
    }
    if (!state.payload.available) return {action:'sync',caption:'Đồng bộ gói Android',icon:'refresh',note:'Tải danh sách gói Việt hoá từ GitHub.'};
    if (!state.payload.compatible) {
      if (state.payload.mismatchKind === 'game_older') {
        const tgt = state.payload.supportedGameVersion ? ('v' + state.payload.supportedGameVersion) : 'bản mới';
        const cur = state.game.gameVersion ? ('v' + state.game.gameVersion) : 'bản cũ';
        return {
          action:'launchGame',
          caption:'Mở game cập nhật (' + cur + ' → ' + tgt + ')',
          icon:'play',
          note:'Mở Stella Sora cập nhật lên ' + tgt + ', thoát hẳn game rồi quay lại cài.'
        };
      }
      if (state.payload.mismatchKind === 'game_newer') {
        const tgt = state.payload.supportedGameVersion ? ('v' + state.payload.supportedGameVersion) : '?';
        const cur = state.game.gameVersion ? ('v' + state.game.gameVersion) : '?';
        return {
          action:'sync',
          caption:'Kiểm tra bản dịch mới',
          icon:'refresh',
          note:'Game (' + cur + ') mới hơn gói dịch (' + tgt + ') — chờ nhóm dịch cập nhật.'
        };
      }
      return {action:'sync',caption:'Kiểm tra gói mới',icon:'refresh',note:state.payload.reason || 'Gói chưa khớp phiên bản game trên máy.'};
    }
    if (!state.receipt.present) return {action:'install',caption:'Cài Việt hoá ngay',icon:'download',note:'Thoát hẳn game rồi bấm cài đặt.'};
    if (state.payload.updateAvailable || state.receipt.stale) return {action:'install',caption:'Cập nhật Việt hoá',icon:'download',note:'Đã có bản dịch mới. Thoát game rồi bấm.'};
    return {action:'install',caption:'Cài lại Việt hoá',icon:'check',note:'Bản dịch đã mới nhất — có thể Mở game ngay!'};
  }

  function renderState(data) {
    const nested = ['progress','adb','game','github','config','payload','update','recovery','receipt','officialUpdate','guard','support','app','device','lastError'];
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

    applyTheme(state.app.theme || state.config.theme || 'system', state.app.resolvedTheme);
    renderOemTip(state.device);

    const devInfo = state.device || {};
    if (devInfo.model) {
      text('settings-device-info', (devInfo.manufacturer || '') + ' ' + devInfo.model + ' · Android ' + (devInfo.release || '?'));
    }

    const devEnabled = data.devOptionsEnabled !== undefined ? !!data.devOptionsEnabled : (state.devOptionsEnabled !== undefined ? !!state.devOptionsEnabled : true);
    state.devOptionsEnabled = devEnabled;
    if ($('dev-mode-warning')) $('dev-mode-warning').hidden = devEnabled;
    document.querySelectorAll('.needs-idle').forEach(e => { e.disabled = !!state.busy; });

    const adb = state.adb, game = state.game, p = state.payload, gh = state.github, off = state.officialUpdate || {}, grd = state.guard || {}, rc = state.receipt || {};

    // Hero status pill
    const heroPill = $('hero-status-pill');
    if (heroPill) {
      let hCls = 'hero-pill', hTxt = 'Chưa kết nối ADB';
      if (off.needsRestore) { hCls += ' danger'; hTxt = 'Cần khôi phục gốc!'; }
      else if (rc.present && !rc.stale && !p.updateAvailable) { hCls += ' ok'; hTxt = 'Việt hoá ' + (rc.version || '') + ' · Sẵn sàng'; }
      else if (rc.present && (rc.stale || p.updateAvailable)) { hCls += ' warn'; hTxt = 'Có bản dịch mới'; }
      else if (adb.connected && game.versionsKnown) { hCls += ' ok'; hTxt = 'Game v' + (game.gameVersion || '') + ' · Sẵn sàng'; }
      else if (adb.connected) { hCls += ' ok'; hTxt = 'Local ADB đã nối'; }
      else if (adb.hasIdentity) { hTxt = 'Đã ghép đôi ADB'; }
      heroPill.className = hCls;
      text('hero-status-text', hTxt);
    }

    const verChip = $('payload-ver-chip');
    if (verChip) {
      if (rc.present && !rc.stale && !p.updateAvailable) { verChip.className = 'ver-chip ok'; verChip.textContent = 'Đã cài ' + (rc.version || ''); }
      else if (p.available && (p.version || gh.translationVersion)) { verChip.className = 'ver-chip' + (rc.present ? ' warn' : ''); verChip.textContent = 'Gói ' + (p.version || gh.translationVersion); }
      else { verChip.className = 'ver-chip'; verChip.textContent = 'Android'; }
    }

    const adbEl = $('adb-status');
    if (adbEl) {
      text('adb-status', adb.connected ? 'Đã kết nối' : (adb.hasIdentity ? 'Đã ghép đôi' : 'Chưa nối'));
      adbEl.prepend(document.createElement('i'));
      adbEl.classList.toggle('connected', !!adb.connected);
      adbEl.classList.toggle('warning', !adb.connected && !adb.hasIdentity);
    }
    setBadge($('adb-page-status'), adb.connected ? 'Đã nối' : (adb.hasIdentity ? 'Đã ghép' : 'Chưa nối'), adb.connected ? 'ok' : (adb.hasIdentity ? 'neutral' : 'warning'));

    const quickCard = $('quick-reconnect-card');
    if (quickCard) {
      quickCard.hidden = !adb.hasIdentity;
      if (adb.hasIdentity) {
        setBadge($('paired-identity-badge'), adb.connected ? 'Đã nối' : 'Đã ghép', 'ok');
        text('quick-reconnect-caption', adb.connected ? 'Kiểm tra kết nối' : 'Kết nối nhanh (1 chạm)');
      }
    }
    const pairBtn = $('pair-notification-btn');
    if (pairBtn) {
      pairBtn.classList.toggle('primary', !adb.hasIdentity);
      pairBtn.classList.toggle('secondary', !!adb.hasIdentity);
    }
    text('pairing-card-heading', adb.hasIdentity ? 'Ghép đôi lại' : 'Ghép đôi nhanh');
    text('adb-summary', adb.connected ? ('Đã nối ' + (adb.host || '') + ':' + (adb.connectionPort || '')) : 'Bật Wi-Fi + Gỡ lỗi không dây, nhập mã trên thông báo.');
    text('connection-details', adb.connected ? ('Cổng: ' + (adb.host || '') + ':' + (adb.connectionPort || '')) : (adb.status || 'Chưa kết nối.'));
    text('pairing-note', adb.notificationPairing.message || 'Giữ cửa sổ mã 6 số mở khi nhập trên thanh thông báo.');
    text('cancel-pairing', adb.notificationPairing.stage === 'discovering_connect' ? 'Huỷ tìm cổng' : 'Huỷ ghép đôi');
    $('cancel-pairing').hidden = !adb.notificationPairing.active;
    $('cancel-pairing').disabled = !!state.mutating;

    text('game-name', game.installed ? 'Stella Sora ✓' : 'Stella Sora');
    text('game-summary', game.versionsKnown ? ('v' + game.gameVersion + ' · ' + game.resourceVersion) : (game.wrongEdition ? 'Sai bản khu vực' : (game.noData ? 'Chưa có data' : 'Chưa thấy')));
    text('game-root', game.root || 'Chưa tìm thấy');

    const main = primaryAction();
    text('install-caption', main.caption);
    $('main-action-icon').src = ICON(main.icon);
    text('payload-note', main.note);

    let whyCode = '', whyId = '';
    if (!p.available && gh.errorCode) { whyCode = gh.errorCode; whyId = gh.errorReportId || ''; }
    else if (!(p.available && p.compatible) && p.reasonCode && p.reasonCode !== 'E-ADB-NOT-CONNECTED' && p.reasonCode !== 'E-SYNC-PENDING') {
      whyCode = p.reasonCode;
    }
    const why = $('why-blocked');
    why.hidden = !whyCode || !!state.busy;
    if (whyCode) {
      why.dataset.code = whyCode;
      why.dataset.id = whyId;
      why.querySelector('span').textContent = 'Vì sao chưa cài được? [' + whyCode + ']';
    }

    const le = state.lastError || {};
    const hasLastErr = !!(le && le.code && le.reportId);
    const outcomeHasCode = /\[E-[A-Z0-9-]+\]/.test(lastOutcome || state.message || '');
    const strip = $('last-error-strip');
    if (strip) {
      strip.hidden = state.busy || !hasLastErr || !outcomeHasCode;
      if (!strip.hidden) {
        text('last-error-code', le.code);
        text('last-error-title', le.errorTitle || le.message || 'Lỗi thao tác');
        strip.dataset.reportId = le.reportId;
      }
    }
    text('settings-last-error-meta', hasLastErr
      ? (le.code + ' (#' + le.reportId + ') · ' + (le.errorTitle || le.message || ''))
      : 'Chưa có lỗi nào gần đây.');

    let payloadText = p.reason || 'Chưa có gói Android.';
    if (p.available && p.compatible) {
      payloadText = (p.version || gh.translationVersion || '') + (p.fileCount ? ' · ' + p.fileCount + ' tệp' : '');
    }
    text('payload-details', payloadText);
    text('operation-details', state.message || 'Chưa có thao tác');
    text('native-status', state.message || '');

    $('operation').hidden = !state.busy;
    text('operation-label', state.progress.label || state.message || 'Đang xử lý…');
    $('operation-outcome').hidden = state.busy || !lastOutcome || !strip.hidden;
    text('operation-outcome', lastOutcome.length > 140 ? lastOutcome.slice(0, 137) + '…' : lastOutcome);
    const percent = Number(state.progress.percent);
    $('progress-fill').style.width = Math.max(0, Math.min(100, Number.isFinite(percent) ? percent : 0)) + '%';
    $('progress-fill').classList.toggle('indeterminate', !!state.progress.indeterminate);
    $('recover-alert').hidden = !state.recovery.pending;

    $('receipt-stale').hidden = !(rc.present && rc.stale);
    if (rc.present && rc.stale) text('receipt-stale', 'Game đã đổi phiên bản kể từ lần cài trước. Hãy bấm Cập nhật Việt hoá.');

    // Guard banner & rows
    const guardAlertCard = $('official-guard-card');
    if (guardAlertCard) {
      guardAlertCard.hidden = !off.needsRestore;
      if (off.needsRestore) {
        text('official-guard-ver', (off.localResourceVersion || '?') + ' → ' + (off.latestResourceVersion || '?'));
      }
    }
    const launchBtn = $('launch');
    if (launchBtn) {
      launchBtn.classList.toggle('guard-locked', !!off.needsRestore);
      const lbl = launchBtn.querySelector('span');
      if (lbl) lbl.textContent = off.needsRestore ? 'Khoá game' : 'Mở game';
    }
    setBadge($('guard-a11y-status'), grd.accessibilityEnabled ? 'Đang bật' : 'Chưa bật', grd.accessibilityEnabled ? 'ok' : 'warning');
    setBadge($('guard-overlay-status'), grd.overlayEnabled ? 'Đang bật' : 'Tắt', grd.overlayEnabled ? 'ok' : 'neutral');

    const yChip = $('guard-yostar-chip');
    if (yChip) {
      if (off.checked && (off.latestGameVersion || off.latestResourceVersion)) {
        yChip.className = 'ver-chip ' + (off.needsRestore ? 'danger' : 'ok');
        yChip.textContent = 'Yostar ' + (off.latestGameVersion ? 'v' + off.latestGameVersion : off.latestResourceVersion);
      } else {
        yChip.className = 'ver-chip';
        yChip.textContent = 'Yostar';
      }
    }
    text('guard-yostar-summary', off.checked && off.latestResourceVersion
      ? ('RES ' + off.latestResourceVersion + (off.needsRestore ? ' · Cần khôi phục gốc ngay!' : (off.vhModified ? ' · Bản Việt hoá an toàn.' : ' · Game đang ở bản gốc.')))
      : 'Tự kiểm tra Yostar trên cả Wi-Fi & 4G/5G.');
    if ($('btn-pin-guard')) $('btn-pin-guard').hidden = grd.canPinShortcut === false;

    const lines = [gh.message || 'Chưa đồng bộ.'];
    lines.push('Thông báo: ' + statusLabel(gh.announcementStatus) + ' · Gói: ' + statusLabel(gh.manifestStatus));
    if (gh.translationVersion) lines.push('Bản dịch: ' + gh.translationVersion);
    text('github-state', lines.join('\n'));

    text('github-summary', p.available ? ('Gói Android ' + (p.version || gh.translationVersion || '') + ' sẵn sàng.') : (gh.message || 'Chưa đồng bộ GitHub.'));
    text('app-version', 'v' + (state.app.versionName || '2.1.4') + ' (' + (state.app.versionCode || 27) + ')');
    text('update-state', state.update.message || 'Chưa kiểm tra bản mới.');
    $('install-update').hidden = !state.update.available && !state.update.downloaded;
    $('install-update').querySelector('span').textContent = state.update.downloaded ? 'Cài APK mới' : 'Tải bản cập nhật';

    fillInput('repo', state.config.repo || gh.repo, firstConfig);
    fillInput('branch', state.config.branch || gh.branch, firstConfig);
    fillInput('adb-host', state.config.host || adb.host, firstConfig);
    fillInput('connect-port', state.config.connectionPort || adb.connectionPort, firstConfig);
    if (adb.pairingPort) fillInput('pair-port', adb.pairingPort);
    firstConfig = false;
    renderNotices();
    refreshMarquees();
  }

  function notices() { return Array.isArray(state.notifications) ? state.notifications : []; }
  function noticeRow(n) {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'notice-row';
    const span = document.createElement('span'); span.textContent = n.title || 'Thông báo';
    const img = document.createElement('img'); img.src = ICON('chevron_right'); img.alt = ''; img.width = 13; img.height = 13; img.decoding = 'async';
    b.append(span, img); b.addEventListener('click', () => { haptic(); openNotice(n); }); return b;
  }
  function renderNotices() {
    const preview = $('notification-preview'); empty(preview);
    const items = notices();
    if (!items.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'Chưa có thông báo.'; preview.append(p); }
    else items.slice(0, 2).forEach(n => preview.append(noticeRow(n)));
    const list = $('notice-all-list'); empty(list);
    const query = $('notice-search').value.trim().toLocaleLowerCase('vi');
    const filtered = items.filter(n => !query || ((n.title || '') + ' ' + (n.content || '')).toLocaleLowerCase('vi').includes(query));
    if (!filtered.length) { const p = document.createElement('p'); p.className = 'empty-note'; p.textContent = 'Không tìm thấy.'; list.append(p); }
    else filtered.forEach(n => list.append(noticeRow(n)));
    refreshMarquees();
  }
  function openNotice(n) {
    $('notices-overlay').hidden = false; $('notice-all-list').hidden = true; $('notice-search').hidden = true; $('notice-detail').hidden = false;
    text('notice-title', n.title || 'Thông báo'); text('notice-date', n.date || ''); text('notice-body', n.content || '');
  }
  function openNoticeList() { $('notices-overlay').hidden = false; $('notice-detail').hidden = true; $('notice-all-list').hidden = false; $('notice-search').hidden = false; renderNotices(); }

  function renderGuide() {
    const target = $('guide-content'); empty(target);
    content.sections.forEach(section => {
      const panel = document.createElement('details'); panel.className = 'card disclosure';
      const heading = document.createElement('summary'); heading.textContent = section.title;
      const bodyWrap = document.createElement('div'); bodyWrap.className = 'disclosure-body';
      const ol = document.createElement('ol'); ol.className = 'steps';
      section.steps.forEach((step, index) => {
        const li = document.createElement('li'), num = document.createElement('span'), wrap = document.createElement('div'), title = document.createElement('strong'), body = document.createElement('p');
        num.textContent = String(index + 1); title.textContent = step.title; body.textContent = step.detail; wrap.append(title, body); li.append(num, wrap); ol.append(li);
      });
      bodyWrap.append(ol); panel.append(heading, bodyWrap); target.append(panel);
    });
  }

  function renderFaq() {
    const list = $('faq-list'); empty(list);
    content.faq.forEach(f => {
      const item = document.createElement('div'); item.className = 'faq-item';
      const b = document.createElement('button'); b.type = 'button'; b.className = 'faq-question'; b.setAttribute('aria-expanded', 'false');
      const label = document.createElement('span'); label.textContent = f.question;
      const icon = document.createElement('img'); icon.src = ICON('chevron_right'); icon.alt = ''; icon.width = 13; icon.height = 13; icon.decoding = 'async';
      b.append(label, icon);
      const answer = document.createElement('div'); answer.className = 'faq-answer'; answer.hidden = true; answer.textContent = f.answer;
      b.addEventListener('click', () => { haptic(); answer.hidden = !answer.hidden; b.setAttribute('aria-expanded', String(!answer.hidden)); }); item.append(b, answer); list.append(item);
    });
  }

  function port(id) {
    const v = $(id).value.trim();
    if (!/^\d{4,5}$/.test(v) || Number(v) < 1024 || Number(v) > 65535) {
      message('Cổng chưa hợp lệ', 'Nhập số cổng 1024–65535 trong Gỡ lỗi không dây.', false, {level:'warning'});
      return null;
    }
    return Number(v);
  }

  function buildAiCheckPrompt(topicKey) {
    const spec = SAFETY_TOPICS[topicKey] || SAFETY_TOPICS.a11y;
    const repo = (state.config && state.config.repo) || 'doubleD1302/AmeeVH';
    const branch = (state.config && state.config.branch) || 'main';
    const base = 'https://github.com/' + repo;
    const fileLines = spec.promptFiles.map(f => '- ' + base + '/blob/' + branch + '/' + f).join('\n');
    return 'Hãy đóng vai chuyên gia bảo mật Android, kiểm tra giúp tôi ' + spec.promptFocus
      + ' trong ứng dụng mã nguồn mở Stella Sora Việt Hoá có an toàn không:\n'
      + '- Kho mã nguồn công khai: ' + base + '\n'
      + fileLines + '\n\n'
      + 'Hãy đọc kỹ các tệp trên và trả lời ngắn gọn, dễ hiểu cho người dùng phổ thông:\n'
      + '1. Tính năng này có đọc màn hình, mật khẩu, tin nhắn hay theo dõi ứng dụng khác ngoài game com.YoStarEN.StellaSora không?\n'
      + '2. Có dấu hiệu mã độc, gửi dữ liệu cá nhân ra ngoài hay hành vi ngầm nguy hiểm không?\n'
      + '3. Kết luận tổng thể: Có an toàn để cấp quyền hay không?';
  }

  function pickRandomChibi(animate=false) {
    if (!CHIBI_CAST.length) return;
    let idx = Math.floor(Math.random() * CHIBI_CAST.length);
    if (CHIBI_CAST.length > 1 && idx === lastChibiIdx) idx = (idx + 1) % CHIBI_CAST.length;
    lastChibiIdx = idx;
    const ch = CHIBI_CAST[idx];
    const img = $('safety-chibi-img');
    if (img) img.src = 'chibis/chibi_' + ch.id + '.webp';
    text('safety-char-name', ch.name);
    text('safety-char-quote', ch.quote);
    if (animate) {
      const btn = $('safety-chibi-btn');
      if (btn) {
        btn.classList.remove('pop');
        void btn.offsetWidth;
        btn.classList.add('pop');
      }
    }
  }

  function renderSafetyTopic(topicKey) {
    const key = SAFETY_TOPICS[topicKey] ? topicKey : 'a11y';
    currentSafetyTopic = key;
    const spec = SAFETY_TOPICS[key];
    text('safety-title', spec.title);
    document.querySelectorAll('[data-safety-tab]').forEach(t => {
      const active = t.dataset.safetyTab === key;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', String(active));
    });
    const whyEl = $('safety-why-list');
    empty(whyEl);
    spec.why.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      whyEl.appendChild(li);
    });
    const pledgeEl = $('safety-pledge-list');
    empty(pledgeEl);
    spec.pledges.forEach(item => {
      const li = document.createElement('li');
      const ic = document.createElement('img');
      ic.src = ICON('check'); ic.alt = ''; ic.width = 14; ic.height = 14; ic.decoding = 'async';
      const sp = document.createElement('span'); sp.textContent = item;
      li.append(ic, sp);
      pledgeEl.appendChild(li);
    });
    text('safety-prompt-text', buildAiCheckPrompt(key));
    const det = $('safety-prompt-details'); if (det) det.open = false;
    const copyBtn = $('safety-copy-ai');
    if (copyBtn) {
      copyBtn.classList.remove('copied');
      const sp = copyBtn.querySelector('span'); if (sp) sp.textContent = 'Chép prompt kiểm tra AI';
    }
    const sc = $('safety-scroll'); if (sc) sc.scrollTop = 0;
    refreshMarquees();
  }

  function openSafetyModal(topicKey) {
    haptic();
    pickRandomChibi(true);
    renderSafetyTopic(topicKey || 'a11y');
    $('safety-overlay').hidden = false;
    refreshMarquees();
  }

  document.querySelectorAll('[data-page]').forEach(b => b.addEventListener('click', () => showPage(b.dataset.page)));
  document.querySelectorAll('[data-action]').forEach(b => b.addEventListener('click', () => { haptic(); request(b.dataset.action); }));
  document.querySelectorAll('[data-safety-topic]').forEach(b => b.addEventListener('click', () => openSafetyModal(b.dataset.safetyTopic)));
  document.querySelectorAll('[data-safety-tab]').forEach(b => b.addEventListener('click', () => { haptic(); renderSafetyTopic(b.dataset.safetyTab); }));
  $('safety-chibi-btn').addEventListener('click', () => { haptic(); pickRandomChibi(true); });
  ['safety-close','safety-ok'].forEach(id => $(id).addEventListener('click', () => { $('safety-overlay').hidden = true; }));
  $('safety-copy-ai').addEventListener('click', () => {
    haptic();
    request('copyAiPrompt', {text: buildAiCheckPrompt(currentSafetyTopic)});
  });
  $('safety-open-source').addEventListener('click', () => {
    haptic();
    const spec = SAFETY_TOPICS[currentSafetyTopic] || SAFETY_TOPICS.a11y;
    request('openSourceCode', {path: spec.sourcePath});
  });
  ['adb-host','pair-port','connect-port','repo','branch'].forEach(id => $(id).addEventListener('input', () => { $(id).dataset.edited = '1'; }));

  $('theme-toggle').addEventListener('click', () => {
    haptic();
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(next, next);
    request('setTheme', {theme: next});
    showToast(next === 'dark' ? 'Đã bật Chế độ tối' : 'Đã bật Chế độ sáng');
  });
  document.querySelectorAll('[data-theme-choice]').forEach(btn => btn.addEventListener('click', () => {
    haptic();
    const choice = btn.dataset.themeChoice || 'system';
    applyTheme(choice, choice === 'system' ? null : choice);
    request('setTheme', {theme: choice});
  }));

  $('main-action').addEventListener('click', () => {
    if (state.busy) return;
    haptic();
    const main = primaryAction();
    if (main.page) showPage(main.page); else request(main.action);
  });

  $('manual-pair').addEventListener('click', () => {
    haptic();
    const pairingPort = port('pair-port'), code = $('pair-code').value.trim();
    if (pairingPort == null) return;
    if (!/^\d{6}$/.test(code)) { message('Cần mã 6 số', 'Nhập đủ 6 chữ số đang hiển thị trên cửa sổ ghép đôi.', false, {level:'warning'}); return; }
    request('pair', {host:$('adb-host').value.trim(), pairingPort, code}); $('pair-code').value = '';
  });
  $('manual-connect').addEventListener('click', () => { haptic(); const connectionPort = port('connect-port'); if (connectionPort != null) request('connect', {host:$('adb-host').value.trim(), connectionPort}); });
  $('save-settings').addEventListener('click', () => { haptic(); const raw = $('connect-port').value.trim(); const connectionPort = raw ? port('connect-port') : 0; if (connectionPort == null) return; request('saveSettings', {repo:$('repo').value.trim(), branch:$('branch').value.trim(), host:$('adb-host').value.trim(), connectionPort}); });

  $('last-error-open').addEventListener('click', () => { haptic(); request('openLastError', {id: $('last-error-strip').dataset.reportId || ''}); });
  $('last-error-copy').addEventListener('click', () => { haptic(); request('copyError', {id: $('last-error-strip').dataset.reportId || ''}); });
  $('settings-probe-btn').addEventListener('click', () => {
    haptic();
    activeProbeInModal = false;
    const btn = $('settings-probe-btn');
    btn.disabled = true;
    const s = btn.querySelector('span'); if (s) s.textContent = 'Đang đo…';
    const box = $('settings-probe-box');
    if (box) { box.className = 'probe-panel'; text('settings-probe-verdict', 'Đang đo DNS & GitHub…'); text('settings-probe-lines', ''); box.hidden = false; }
    request('probeNetwork', {id: (state.lastError && state.lastError.reportId) || ''});
  });

  $('all-notifications').addEventListener('click', () => { haptic(); openNoticeList(); });
  $('notice-search').addEventListener('input', renderNotices);
  $('notice-back').addEventListener('click', () => { haptic(); openNoticeList(); });
  $('notices-close').addEventListener('click', () => { $('notices-overlay').hidden = true; });
  ['message-close','message-ok'].forEach(id => $(id).addEventListener('click', () => { $('message-overlay').hidden = true; }));
  $('message-copy').addEventListener('click', () => { haptic(); request('copyError', {id: currentReportId}); });
  $('why-blocked').addEventListener('click', () => { haptic(); const w = $('why-blocked'); request('explain', {code: w.dataset.code || 'E-UNKNOWN', id: w.dataset.id || ''}); });

  window.Stella = {
    onEvent(event) {
      try {
        if (typeof event === 'string') event = JSON.parse(event);
        if (!event || typeof event !== 'object') return;
        if (event.type === 'state') renderState(event.data || {});
        else if (event.type === 'navigate' && (event.data || {}).page) showPage(event.data.page);
        else if (event.type === 'message') message((event.data || {}).title, (event.data || {}).message, !!(event.data || {}).error, event.data || {});
        else if (event.type === 'probeResult') {
          const d = event.data || {};
          const sBtn = $('settings-probe-btn');
          if (sBtn) { sBtn.disabled = false; const sp = sBtn.querySelector('span'); if (sp) sp.textContent = 'Đo mạng'; }
          const mBtn = document.querySelector('#message-quickfix-grid [data-qf-id="probe_network"]');
          if (mBtn) { mBtn.disabled = false; const sp = mBtn.querySelector('span'); if (sp) sp.textContent = 'Đo mạng & DNS'; }
          if (activeProbeInModal || !$('message-overlay').hidden) {
            renderProbePanel('message-probe-panel', 'message-probe-verdict', 'message-probe-lines', d);
            if (Array.isArray(d.contextRows)) renderDiagGrid(d.contextRows);
            if (d.reportPreview) {
              text('message-report-preview', d.reportPreview);
              $('message-report-preview').hidden = false;
              $('message-preview-label').hidden = false;
              $('message-tech').hidden = false;
            }
          }
          if (!$('settings-probe-box').hidden || currentPage === 'settings') {
            renderProbePanel('settings-probe-box', 'settings-probe-verdict', 'settings-probe-lines', d);
          }
        }
        else if (event.type === 'copied') {
          const d = event.data || {};
          const isDiag = d.kind === 'diagnostics';
          const isAi = d.kind === 'ai_prompt';
          if (isAi) {
            const btn = $('safety-copy-ai');
            if (btn) {
              btn.classList.add('copied');
              const sp = btn.querySelector('span'); if (sp) sp.textContent = 'Đã sao chép prompt ✓';
              clearTimeout(safetyCopyTimer);
              safetyCopyTimer = setTimeout(() => {
                btn.classList.remove('copied');
                if (sp) sp.textContent = 'Chép prompt kiểm tra AI';
              }, 2600);
            }
            showToast('Đã sao chép prompt — dán vào ChatGPT / Gemini / Claude!');
          } else {
            if (!$('message-overlay').hidden && !$('message-copy').hidden && !isDiag) {
              setCopyLabel('Đã sao chép ✓', true);
              clearTimeout(copyResetTimer);
              copyResetTimer = setTimeout(() => setCopyLabel('Sao chép báo lỗi', false), 2400);
            }
            showToast(isDiag ? 'Đã sao chép chẩn đoán hệ thống' : ('Đã sao chép báo lỗi' + (d.code ? ' [' + d.code + ']' : '')));
          }
        }
      } catch (_) {
        message('Chưa đọc được trạng thái', 'Hãy mở lại trang Tổng quan.', true);
      }
    },
    navigate(page) { showPage(page); },
    goBack() {
      if (!$('safety-overlay').hidden) { $('safety-overlay').hidden = true; return true; }
      if (!$('message-overlay').hidden) { $('message-overlay').hidden = true; return true; }
      if (!$('notices-overlay').hidden) { $('notices-overlay').hidden = true; return true; }
      if (currentPage !== 'overview') { showPage('overview'); return true; }
      return false;
    }
  };

  renderGuide(); renderFaq(); renderState(initial); request('state');
})();
